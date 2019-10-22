/*
Copyright 2019 Broadcom. All rights reserved.
The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
*/

/*
 * cache_radius to be invoked after a successful pam_radius_auth.so
 * module invocation as:
 *
 *   auth  [success=1 default=ignore] pam_exec.so /usr/sbin/cache_radius
 *
 */

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <limits.h>
#include <string.h>
#include <syslog.h>
#include <stdlib.h>
#include <pwd.h>
#include <errno.h>
#include <fcntl.h>
#include <ctype.h>
#include <netdb.h>
#include <nss.h>

#define USERADD "/usr/sbin/useradd"
#define ETC_NSSWITCHCONF "/etc/nsswitch.conf"

#if defined(TEST_RADIUS_NSS)
#define syslog(priority,format, ...) printf("priority:%d " format "\n", priority, __VA_ARGS__)

#undef USERADD
#define USERADD "/bin/echo"

#undef ETC_NSSWITCHCONF
#define ETC_NSSWITCHCONF "nsswitch.conf"

#endif

#include "nss_radius_common.c"

#define BUFLEN 4096

static int local_files_user_status(char * prog, const char * nam) {
    struct passwd pw, * pwd = NULL;
    FILE * fp = NULL;
    int status = 1;
    char buf[BUFLEN];

    if ((fp = fopen(ETC_PASSWD, "r")) == NULL) {
        syslog(LOG_WARNING, "%s: fopen(\"/etc/passwd\") failed\n", prog);
        status = 2;
        goto lfus_exit;

    }

    while((status = fgetpwent_r(fp, &pw, buf, sizeof(buf), &pwd)) == 0) {
        if (pwd && pwd->pw_name && (strcmp(pwd->pw_name, nam) == 0)) {
            status = 0;
            break;
        }
    }

lfus_exit:

    if (fp)
        fclose(fp);

    return status;
}

static int radius_update_cache( char * prog, const char * nam, int mpl) {

    mode_t  mask;
    char filename[PATH_MAX];
    int written;
    int status = 0;
    struct stat sb;
    FILE * fp = NULL;

    /* Umask save, change.
     */
    mask = umask(022);

    if (((written = snprintf( filename, sizeof(filename), "%s/%s",
        RADIUS_ATTRIBUTE_CACHE_DIR, nam)) + sizeof(RADIUS_ATTR_MPL) + 1)
            >= sizeof(filename)) {
        syslog( LOG_ERR, "%s: \"%s\": too long.", prog, filename);
        status = 1;
        goto radius_update_cache_exit;
    }

    /* Create the directory.
     */
    if ((!((stat( RADIUS_CACHE_DIR, &sb) == 0) && S_ISDIR(sb.st_mode))
            && (mkdir( RADIUS_CACHE_DIR, 0755) == -1))
    || (!((stat( RADIUS_ATTRIBUTE_CACHE_DIR, &sb) == 0) && S_ISDIR(sb.st_mode))
        && (mkdir( RADIUS_ATTRIBUTE_CACHE_DIR, 0755) == -1))
    || (!((stat( filename, &sb) == 0) && S_ISDIR(sb.st_mode))
        && (mkdir( filename, 0755) == -1))) {
        syslog( LOG_ERR, "%s: \"%s\": mkdir() fails. Or ! dir errno %d",
            prog, filename, errno);
        status = 2;
        goto radius_update_cache_exit;
    }

    /* Create the file.
     */
    strcat( filename, "/");
    strcat( filename, RADIUS_ATTR_MPL);

    if (   ((fp = fopen( filename, "w")) == NULL)
        || (fprintf(fp, "%d\n", mpl) < 0)) {
        syslog( LOG_ERR,
          "%s: \"%s\": fopen(): %p or fprintf() fails. errno %d", prog,
          filename, (void *) fp, errno);
        status = 2;
        goto radius_update_cache_exit;
    }

    syslog(LOG_INFO, "%s: MPL %d updated for user %s", prog, mpl, nam);

radius_update_cache_exit:

    /* Umask restore.
     */
    umask(mask);

    if (fp)
        fclose(fp);


    return status;
}


static int invoke_popen(char * prog, char * cmd) {
    FILE * fp;
    int status = 0;

    if (debug)
        syslog(LOG_DEBUG, "%s:%s", prog, cmd);

    if (((fp = popen(cmd, "r")) == NULL) || (pclose(fp) == -1)) {
        syslog(LOG_ERR, "%s: %s: popen()/pclose() failed %p, errno=%d",
            prog, cmd, fp, errno);
            status = 1;
    }

    return status;
}



int main(int ac, char * av[]) {

    int mpl = 1;
    int status = 0;
    int my_errno = 0;
    int written = 0;
    int parsed = 0;
    char * user = NULL, * privilege;
    RADIUS_NSS_MPL radius_nss_mpl[RADIUS_MAX_MPL], * rnm;
    char file_buf[RADIUS_MAX_NSS_CONF_SZ];
    char useradd[4096];
    int ncfd = -1;

    /* Read environment PAM_USER.
     */

    if (   ((user = getenv("PAM_USER")) == NULL)
        || (user[0] == 0)) {
        status = 1;
        syslog(LOG_WARNING,
            "%s: Missing or bad PAM_USER in environment:\"%s\"\n",
            av[0], user ? user : "");
        goto main_exit;
    }

    /* Read environment Privilege.
     */

    if ((privilege = getenv("Privilege")) != NULL) {
      mpl = atoi(privilege);
      if (!((RADIUS_MIN_MPL <= mpl) && (mpl <= RADIUS_MAX_MPL))) {
          syslog(LOG_WARNING, "%s: Invalid mpl %d detected\n", av[0], mpl);
          mpl = 1;
      }
    } else {
      syslog(LOG_INFO, "%s: Missing or bad Privilege in environment:\"%s\"\n",
          av[0], privilege ? privilege : "");
    }

      /* If the user is present locally.
       */
    if (local_files_user_status(av[0], user) == 0) {
        goto main_exit;
    }

    parse_nss_config(radius_nss_mpl, RADIUS_MAX_MPL,
        file_buf, RADIUS_MAX_NSS_CONF_SZ, &my_errno, &ncfd);
    parsed = 1;

    if (many_to_one) {
        goto main_exit;
    }

      /* Create the user.
       */
    syslog(LOG_INFO, "%s: Adding user %s", av[0], user);

    rnm = &(radius_nss_mpl[mpl-1]);

    if (trace)
        dump_rnm(mpl, rnm);

    written = snprintf(useradd, sizeof(useradd),
        "%s -g %d -G %s -c \"%s\" -d /home/%s -m -s %s \"%s\"",
        USERADD, rnm->gid, rnm->group, rnm->gecos, user,
         rnm->shell, user);

    if (written >= sizeof(useradd)) {
        status = 2;
        syslog(LOG_WARNING,
            "%s: truncated useradd cmd. Skipping:\"%s\"\n",
            av[0], useradd);
        goto main_exit;
    }

#if NEED_BLOCK_RADIUS_NSS
    if (   allow_anonymous
        && (invoke_popen(av[0],
            "/bin/sed -i -e '/^passwd/s/ radius//' " ETC_NSSWITCHCONF) != 0)) {
        status = 3;
        goto main_exit;
    }
#endif

    invoke_popen(av[0], useradd);

#if NEED_BLOCK_RADIUS_NSS
    if (   allow_anonymous
        && (invoke_popen(av[0],
            "/bin/sed -i -e '/^passwd/s/compat$/& radius/' " ETC_NSSWITCHCONF)
            != 0)) {
        status = 4;
        goto main_exit;
    }
#endif

main_exit:

    if (status == 0) {
        radius_update_cache(av[0], user, mpl);
    }

    if (parsed)
        unparse_nss_config(radius_nss_mpl, RADIUS_MAX_MPL, &my_errno, &ncfd);

    exit(status);
}
