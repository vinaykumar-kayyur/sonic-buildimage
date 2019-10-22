/*
Copyright 2019 Broadcom. All rights reserved.
The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
*/

/*
 * plugin implements getpwnam_r for NSS for RADIUS cached MPL(Management
 *     Privilege Attribute).
 */

#include "nss_radius_common.c"

/*
 * NSS entry point for getpwnam().
 */
enum nss_status _nss_radius_getpwnam_r( const char * nam, struct passwd * pwd,
    char * buf, size_t buflen, int * errnop) {

    enum nss_status status = NSS_STATUS_NOTFOUND;
    int mpl = 1;
    RADIUS_NSS_MPL radius_nss_mpl[RADIUS_MAX_MPL];
    char file_buf[RADIUS_MAX_NSS_CONF_SZ];

      /* Ignore filename completion.
       */
    if (!nam || !strcmp(nam, "*") || !pwd || !buf || (buflen == 0))
        return NSS_STATUS_NOTFOUND;

    if (radius_lookup_cache(nam, &mpl) == 0) {

        status = NSS_STATUS_SUCCESS;
        if (debug)
            syslog( LOG_DEBUG, "nam: %s", nam);

        parse_nss_config(radius_nss_mpl, RADIUS_MAX_MPL,
            file_buf, RADIUS_MAX_NSS_CONF_SZ, errnop, NULL);

          /* Based on the mpl, fill the pwd
           */
        radius_fill_pw(nam, pwd, buf, buflen, &(radius_nss_mpl[mpl-1]), errnop);

        unparse_nss_config(radius_nss_mpl, RADIUS_MAX_MPL, errnop, NULL);

    } else {

        parse_nss_config(radius_nss_mpl, RADIUS_MAX_MPL,
            file_buf, RADIUS_MAX_NSS_CONF_SZ, errnop, NULL);

        if (allow_anonymous) {

           /* Could be an sshd doing a getpwnam() before pam_authenticate().
            * Give the least privileged user info.
            */

            status = NSS_STATUS_SUCCESS;
            init_rnm(radius_nss_mpl, RADIUS_MAX_MPL);
            radius_fill_pw(nam, pwd, buf, buflen, &(radius_nss_mpl[0]), errnop);
        }

        unparse_nss_config(radius_nss_mpl, RADIUS_MAX_MPL, errnop, NULL);
    }


    return status;
}

