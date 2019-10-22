/*
Copyright 2019 Broadcom. All rights reserved.
The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
*/

/*
 * Common code for NSS for RADIUS cached MPL(Management Privilege Attribute).
 * Used by both NSS module(uses the cache) and PAM module(updates the cache)
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
#include <sys/file.h>

static int debug = 0;
static int trace = 0;
static int many_to_one = 0;
static int allow_anonymous = 0;


#define RADIUS_MAX_MPL (15)
#define RADIUS_MIN_MPL (1)

#define RADIUS_NSS_CONF "/etc/radius_nss.conf"
#define RADIUS_MAX_NSS_CONF_SZ 2048

#define RADIUS_ATTRIBUTE_CACHE_DIR "/var/run/radius/user/"
#define RADIUS_CACHE_DIR "/var/run/radius/"
#define RADIUS_ATTR_MPL "Management-Privilege-Level"

#define ETC_PASSWD "/etc/passwd"

#if defined(TEST_RADIUS_NSS)
#undef RADIUS_NSS_CONF
#define RADIUS_NSS_CONF "radius_nss.conf"
#undef RADIUS_ATTRIBUTE_CACHE_DIR
#define RADIUS_ATTRIBUTE_CACHE_DIR "user"
#undef ETC_PASSWD
#define ETC_PASSWD "passwd"
#endif

typedef struct _radius_nss_mpl {
    uid_t       uid;
    gid_t       gid;
    char        * group;
    char        * gecos;
    char        * dir;
    char        * shell;
} RADIUS_NSS_MPL;


static void dump_rnm(int mpl, RADIUS_NSS_MPL * rnm) {

    syslog( LOG_DEBUG, "dump_rnm: "
      "mpl %d uid %d gid %d group \"%s\" gecos \"%s\" dir \"%s\" shell \"%s\"",
      mpl, rnm->uid, rnm->gid, rnm->group, rnm->gecos, rnm->dir, rnm->shell);
}

static char * parse_line(char * file_buf, char ** pscanpos, int * premain) {

    char * line = NULL;
    int skipline = 0;

    for( ; (*premain); (*pscanpos)++, (*premain)--) {
        if (skipline) {
            if (    ((**pscanpos) == '\n')
                 || ((**pscanpos) == '\r')
                 || ((**pscanpos) == '\f')) {
                 skipline = 0;
            }
            continue;
        } else if (line == NULL) {
            if (isspace(**pscanpos)) {
                continue;
            } else if ((**pscanpos) == '#') {
                skipline = 1;
            } else {
                line = *pscanpos;
            }
            continue;
        } else if (   ((**pscanpos) == '\n')
                   || ((**pscanpos) == '\r')
                   || ((**pscanpos) == '\f')) {
            break;
        }
    }

    if (line) {
        *((*pscanpos)++) = 0;
        if (*premain)
            (*premain)--;
    }

    if (trace)
        syslog(LOG_DEBUG, "parse_line: \"%s\"\n", line ? line : "");

    return line;
}

static char * parse_token(char ** pbufpos, int * premain) {
    char * token = NULL;

    for( token = *pbufpos;
         (*premain) && (**pbufpos) && ((**pbufpos) != ';') ;
         (*pbufpos)++, (*premain)--)
        ; /* Empty Body */

    if (*premain) {
        *((*pbufpos)++) = 0;
        (*premain)--;
    }

    if (trace)
        syslog(LOG_DEBUG, "parse_token: \"%s\"\n", token ? token : "");

    return token;
}

static int parse_user(char * line, RADIUS_NSS_MPL * rnm, int max_mpl) {
    RADIUS_NSS_MPL parse_rnm;
    char * token, * bufpos;
    int mpl;
    int ret = 0, remain;

    bufpos = line;
    remain = strlen(line);
    memset((char *) &parse_rnm, 0, sizeof(parse_rnm));

    while (remain && (token = parse_token(&bufpos, &remain))) {
        if (strncmp(token, "user_priv=", 10) == 0) {
            mpl = atoi(&token[10]);
        } else if (strncmp(token, "group=", 6) == 0) {
            parse_rnm.group = &(token[6]);
        } else if (strncmp(token, "pw_info=", 8) == 0) {
            parse_rnm.gecos = &(token[8]);
        } else if (strncmp(token, "uid=", 4) == 0) {
            parse_rnm.uid = atol(&(token[4]));
        } else if (strncmp(token, "gid=", 4) == 0) {
            parse_rnm.gid = atol(&(token[4]));
        } else if (strncmp(token, "dir=", 4) == 0) {
            parse_rnm.dir = &(token[4]);
        } else if (strncmp(token, "shell=", 6) == 0) {
            parse_rnm.shell = &(token[6]);
        }
    }

    if (trace)
        dump_rnm(mpl, &parse_rnm);

    if (   ((RADIUS_MIN_MPL > mpl) || (mpl > RADIUS_MAX_MPL))
        || (parse_rnm.uid == 0)
        || (parse_rnm.gid == 0)
        || (parse_rnm.group == NULL)
        || (parse_rnm.gecos == NULL)
        || (parse_rnm.dir == NULL)
        || (parse_rnm.shell == NULL)) {

        syslog( LOG_WARNING, "%s: Bad user_priv line \"%s\"", RADIUS_NSS_CONF,
            line);
        ret = 1;
    } else {
        rnm[mpl-1] = parse_rnm;
    }

    return ret;
}

static void init_rnm(RADIUS_NSS_MPL * rnm, int max_mpl) {

      /* Set rnm[0,max_mpl-1].
       */

    memset((char *) rnm, 0, sizeof(*rnm) * max_mpl);
    rnm[0].uid   = 65534;
    rnm[0].gid   = 65534;
    rnm[0].group = "users";
    rnm[0].gecos = "remote_user";
    rnm[0].dir   = "/var/tmp";
    rnm[0].shell = "/bin/rbash";
    rnm[max_mpl-1].uid   = 1000;
    rnm[max_mpl-1].gid   = 1000;
    rnm[max_mpl-1].group = "sudo,docker";
    rnm[max_mpl-1].gecos = "remote_user_su";
    rnm[max_mpl-1].dir   = "/home/admin";
    rnm[max_mpl-1].shell = "/bin/bash";

}

static int parse_nss_config(RADIUS_NSS_MPL * rnm, int max_mpl,
    char * file_buf, int file_buf_sz, int * errnop, int * plockfd) {

      /* Slurp the whole file.
       */
    int ncfd = -1;
    int ret = 0;
    int i = 0, remain;
    struct stat sb;
    char errbuf[128];
    int flags;
    char * scanpos, * line;

    init_rnm(rnm, max_mpl);

    debug = trace = 0;

    many_to_one = allow_anonymous = 0;

      /* Read the file.
       */
    if (((ncfd = open(RADIUS_NSS_CONF, O_RDONLY)) == -1)
        || (fstat(ncfd, &sb) == -1)
        || (((flags = fcntl(ncfd, F_GETFL, 0)) == -1) && ((flags = 0) != 0))
        || (fcntl(ncfd, F_SETFL, flags | O_NONBLOCK) == -1)) {

        if (errnop)
            *errnop = errno;
        ret = 1;
        errbuf[0] = 0; strerror_r(errno, errbuf, sizeof(errbuf));
        syslog( LOG_WARNING, "%s: %s", RADIUS_NSS_CONF, errbuf);
        goto parse_nss_config_exit;
    }

      /* The maximum file size is 1 less than the buffer, to allow space for
       * a NULL byte in the case where the last line has no \n, \r, \l char.
       * (which could have been substituted with a NULL).
       */
    if (sb.st_size >= file_buf_sz) {
        syslog( LOG_WARNING, "%s: size greater than %d. Ignoring",
            RADIUS_NSS_CONF, file_buf_sz-1);
        goto parse_nss_config_exit;
    }

    if ((i = read(ncfd, file_buf, file_buf_sz)) != sb.st_size) {
        syslog( LOG_WARNING, "%s: read %d of %ld. Ignoring", RADIUS_NSS_CONF,
            i, sb.st_size);
        goto parse_nss_config_exit;
    }

      /* Parse each line from file.
       */

    scanpos = file_buf;
    remain = sb.st_size;
    while((line = parse_line(file_buf, &scanpos, &remain)) != NULL) {

        if (strncmp(line, "debug=", 6) == 0) {

            if (strncmp(&(line[6]), "on", 2) == 0) {

          /* Handle "debug".
           */

                debug = 1;

            } else if (strncmp(&(line[6]), "trace", 5) == 0) {

                debug = 1;
                trace = 1;

            }

        } else if (strncmp(line, "user_priv=", 10) == 0) {

          /* Handle "user_priv"
           */

            parse_user(line, rnm, max_mpl);

        } else if (strncmp(line, "many_to_one=", 12) == 0) {

          /* Handle "many_to_one"
           */

            if (strncmp(&(line[12]), "y", 1) == 0) {

                many_to_one = 1;

            } else if (strncmp(&(line[12]), "a", 1) == 0) {

                    /* Either we've been asked to lock the file,
                     * (done just before exiting), or we need to
                     * ensure that we can allow_anonymous.
                     * An existing exclusive lock on the file, indicates
                     * that disabling of allow_anonymous is requested
                     * before useradd is run (otherwise useradd will
                     * complain about the user being present, and
                     * not create the user).
                     */
                if (plockfd || (flock(ncfd, LOCK_EX|LOCK_NB) == 0))
                    allow_anonymous = 1;
                else
                    syslog( LOG_DEBUG, "%s: %d: many_to_one=a: is locked out",
                        RADIUS_NSS_CONF, (int) getpid());
            }

        } else {

            syslog( LOG_WARNING, "%s: Ignorning \"%s\"", RADIUS_NSS_CONF,
                line);
        }
    }

parse_nss_config_exit:

    if (ncfd != -1) {
            /* If the caller requested a lock, do it now.
             */
        if (plockfd && (flock(ncfd, LOCK_EX|LOCK_NB) == 0)) {
            syslog( LOG_DEBUG, "%s: %d: many_to_one=a: lock success",
                RADIUS_NSS_CONF, (int) getpid());
            *plockfd = ncfd;
        } else {
            if (plockfd) {
                syslog( LOG_ERR, "%s: %d: many_to_one=a: lock fail",
                    RADIUS_NSS_CONF, (int) getpid());
                *plockfd = -1;
            }
            close(ncfd); /* This should release the lock, if we placed one */
        }
    }

      /* Fix up rnm.
       */
    for ( i = 1; i < max_mpl - 1; i++) {
        if (rnm[i].uid == 0) {
            rnm[i] = rnm[i-1];
        }
    }

    return ret;
}

/* Releases any memory.
 * Closes any fds.
 */
static int unparse_nss_config(RADIUS_NSS_MPL * rnm, int max_mpl, int * errnop,
        int * plockfd) {

        /* If the caller had requested a lock in parse_nss_config(),
         * we should now release that lock.
         */
    if (plockfd && (*plockfd != -1)) {
        if (flock(*plockfd, LOCK_UN|LOCK_NB) == 0) {
            syslog( LOG_DEBUG, "%s: %d: many_to_one=a: unlock success",
                RADIUS_NSS_CONF, (int) getpid());
        } else {
            syslog( LOG_DEBUG, "%s: %d: many_to_one=a: unlock fail",
                RADIUS_NSS_CONF, (int) getpid());
        }
        close(*plockfd);
        *plockfd = -1;
    }
    return 0;
}

static int radius_lookup_cache( const char * nam, int * pmpl) {
    int rafd = -1;
    int i;
    char cache_filename[PATH_MAX];
    char file_buf[10];
    struct stat sb;
    int ret = 0;
    int flags;
    int written;
    int mpl;

    *pmpl = RADIUS_MIN_MPL;

    if ((written = snprintf(cache_filename, sizeof(cache_filename), "%s/%s/%s",
        RADIUS_ATTRIBUTE_CACHE_DIR, nam, RADIUS_ATTR_MPL)
          >= sizeof(cache_filename))) {
        syslog( LOG_ERR, "%s: \"%s\": too long.", RADIUS_NSS_CONF,
            cache_filename);
        ret = 1;
        goto radius_lookup_cache_exit;
    }

      /* Ensure the user's cache exists
       */
    if (((rafd = open(cache_filename, O_RDONLY)) == -1)
        || (fstat(rafd, &sb) == -1)
        || (((flags = fcntl(rafd, F_GETFL, 0)) == -1) && ((flags = 0) != 0))
        || (fcntl(rafd, F_SETFL, flags | O_NONBLOCK) == -1)) {
        syslog( LOG_DEBUG, "%s: \"%s\": Absent.", RADIUS_NSS_CONF,
            cache_filename);
        ret = 1;
        goto radius_lookup_cache_exit;
    }

      /* Read the privilege attribute file.
       */

    if (sb.st_size >= sizeof(file_buf)) {
        syslog( LOG_WARNING, "%s: size %ld greater than %ld. Ignoring",
            cache_filename, sb.st_size, sizeof(file_buf)-1);
        goto radius_lookup_cache_exit;
    }

    if ((i = read(rafd, file_buf, sizeof(file_buf))) != sb.st_size) {
        syslog( LOG_WARNING, "%s: read %d of %ld. Ignoring", RADIUS_NSS_CONF,
            i, sb.st_size);
        goto radius_lookup_cache_exit;
    }

    file_buf[sb.st_size] = 0;
    mpl = atoi(file_buf);

    if (((RADIUS_MIN_MPL <= mpl) && (mpl <= RADIUS_MAX_MPL)))
        *pmpl = mpl;

radius_lookup_cache_exit:

    if (rafd != -1)
        close(rafd);

    return ret;
}


static int radius_fill_pw( const char * nam, struct passwd * pwd,
    char * buffer, size_t buflen, RADIUS_NSS_MPL * rnm, int * errnop) {

    int ret = 0;
    size_t namlen, gecoslen, dirlen, shelllen;

    size_t totallen = (namlen = strlen(nam)) + 1
                 + (gecoslen = strlen(rnm->gecos)) + 1
                 + (dirlen = strlen(rnm->dir)) + 1
                 + (shelllen = strlen(rnm->shell)) + 1
                 + 1 + 1;

    if (totallen > buflen) {
        if (errnop)
            *errnop = ERANGE;
        ret = 1;
        if (debug)
            syslog(LOG_DEBUG, "%s: getpwnam_r ERANGE %ld < %ld\n",
                nam, buflen, totallen);
        goto radius_fill_pw_exit;
    }

    memcpy( buffer, nam, namlen + 1);
    pwd->pw_name = buffer;
    buffer += (namlen + 1);

    memcpy( buffer, "*", 1 + 1);
    pwd->pw_passwd = buffer;
    buffer += (1 + 1);

    pwd->pw_uid = rnm->uid;

    pwd->pw_gid = rnm->gid;

    memcpy( buffer, rnm->gecos, gecoslen + 1);
    pwd->pw_gecos = buffer;
    buffer += (gecoslen + 1);

    memcpy( buffer, rnm->dir, dirlen + 1);
    pwd->pw_dir = buffer;
    buffer += (dirlen + 1);

    memcpy( buffer, rnm->shell, shelllen + 1);
    pwd->pw_shell = buffer;
    buffer += (shelllen + 1);

radius_fill_pw_exit:

    return ret;
}


