/**
 * @file dhcp_mon.c
 *
 *  @brief dhcp relay monitor module
 */

#include <signal.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <syslog.h>
#include <assert.h>

#include "dhcp_mon.h"
#include "dhcp_devman.h"

/** window_interval_sec monitoring window for dhcp relay health checks */
static int window_interval_sec = 12;
/** dhcp_unhealthy_max_count max count of consecutive unhealthy statuses before reporting to syslog */
static int dhcp_unhealthy_max_count = 10;
/** dhcp_mon_active control monitoring thread main loop */
static int dhcp_mon_active = 0;

/**
 * @code dhcp_mon_process(arg);
 *
 * @brief monitoring thread main loop. It creates a timer that delivers SIGALRM every window_sec seconds.
 *        when signal is delivered, dhcp relay status is queried from devman.
 *
 * @param arg pointer to user argument
 *
 * @return pointer to exist status
 */
static void* dhcp_mon_process(void *arg)
{
    int rv;
    struct itimerspec ts;
    sigset_t sigset;
    struct sigevent se;
    timer_t timer_id;
    static int count = 0;

    sigemptyset(&sigset);
    sigaddset(&sigset, SIGALRM);

    /* setup timer */
    ts.it_interval.tv_sec = window_interval_sec;
    ts.it_interval.tv_nsec = 0;
    ts.it_value.tv_sec = window_interval_sec;
    ts.it_value.tv_nsec = 0;

    se.sigev_value.sival_ptr = NULL;  // data passed with the notification
    se.sigev_signo = SIGALRM;
    se.sigev_notify = SIGEV_THREAD_ID;
    se._sigev_un._tid = syscall(__NR_gettid);

    rv = timer_create(CLOCK_REALTIME, &se, &timer_id);
    if (rv != 0) {
        syslog(LOG_ERR, "Timer creation failed with '%s'\n", strerror(errno));
        exit(EXIT_FAILURE);
    } else {
        timer_settime(timer_id, 0, &ts, NULL);
    }

    /* endless loop to wait for and handle a signal repeatedly */
    while (dhcp_mon_active) {
        int sig;
        int error;

        error = sigwait(&sigset, &sig);
        if (error == 0) {
            assert(sig == SIGALRM);

            dhcp_mon_status_t dhcp_mon_status = dhcp_devman_get_status();
            switch (dhcp_mon_status)
            {
            case DHCP_MON_STATUS_UNHEALTHY:
                if (++count > dhcp_unhealthy_max_count) {
                    syslog(LOG_ALERT, "DHCP Relay is not healthy after %d health checks\n", count);
                }
                break;
            case DHCP_MON_STATUS_HEALTHY:
                if (count > 0) {
//                    syslog(LOG_INFO, "DHCP Relay became healthy after %d health checks\n", count);
                    count = 0;
                }
                break;
            case DHCP_MON_STATUS_INDETERMINATE:
                if (count > 0) {
//                    syslog(LOG_DEBUG, "DHCP Relay stays healthy after indeterminate status\n");
                }
                break;
            default:
                syslog(LOG_ERR, "DHCP Relay returned unknown status %d\n", dhcp_mon_status);
                break;
            }
        } else {
            syslog(LOG_ERR, "Received unknown signal %d\n", sig);
        }
    }

    pthread_exit(NULL);
}

/**
 * @code dhcp_mon_init(window_sec, max_count);
 *
 * initializes monitoring thread that continuously collects dhcp relay health status every window_sec seconds.
 * It also write to syslog when dhcp relay has been unhealthy for consecutive max_count checks.
 *
 */
int dhcp_mon_init(int window_sec, int max_count)
{
    int rv = 0;

    sigset_t sigset;
    pthread_t sig_thread;

    /* mask SIGALRM in all threads by default */
    sigemptyset(&sigset);
    sigaddset(&sigset, SIGALRM);
    sigprocmask(SIG_BLOCK, &sigset, NULL);

    window_interval_sec = window_sec;
    dhcp_unhealthy_max_count = max_count;

    dhcp_mon_active = 1;
    /* create SIGALRM looper thread */
    rv = pthread_create(&sig_thread, NULL, dhcp_mon_process, NULL);

    return rv;
}

/**
 * @code dhcp_mon_shutdown();
 *
 * @brief shuts down monitoring thread
 *
 * @return none
 */
void dhcp_mon_shutdown()
{
    dhcp_mon_active = 0;
}
