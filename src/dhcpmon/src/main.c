/**
 * @file main.c
 *
 *  @brief: Main entry point for dhcpmon utility.
 *
 */

#include <err.h>
#include <errno.h>
#include <libgen.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <semaphore.h>
#include <syslog.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#include "dhcp_mon.h"
#include "dhcp_devman.h"

/** dhcpmon_active: semaphore main thread wait on before exiting */
static sem_t dhcpmon_active;
/** dhcpmon_default_snaplen: default snap length of packet being captured */
static const uint32_t dhcpmon_default_snaplen = 65535;
/** dhcpmon_default_pcap_timout_ms: default timeout of libpcap utility before delivering packets to awaiting thread */
static const uint32_t dhcpmon_default_pcap_timout_ms = 100;
/** dhcpmon_default_health_check_window: default value for a time window, during which DHCP DORA packet counts are being collected */
static const uint32_t dhcpmon_default_health_check_window = 12;
/** dhcpmon_default_unhealthy_max_count: default max consecutive unhealthy status reported before reporting an issue with DHCP relay */
static const uint32_t dhcpmon_default_unhealthy_max_count = 10;

/**
 * @code usage(prog);
 *
 * @brief prints help message about how to use dhcpmon utility
 *
 * @param prog program name
 *
 * @return none
 */
static void usage(const char *prog)
{
    printf("Usage: %s -id <south interface> {-iu <north interface>}+ [-w <snapshot window in sec>]"
            "[-c <unhealthy status count] [-s <snap length>] [-t <pcap timeout>] [-d]\n", prog);
    printf("where\n");
    printf("\tsouth interface: is a vlan interface,\n");
    printf("\tnorth interface: is a TOR-T1 interface,\n");
    printf("\tsnapshot window: during which DHCP counters are gathered and DHCP status is validated (default %d),\n",
            dhcpmon_default_health_check_window);
    printf("\tunhealthy status count: count of consecutive unhealthy status before writing an alert to syslog "
           "(default %d),\n",
           dhcpmon_default_unhealthy_max_count);
    printf("\tsnap length: snap length of packet capture (default %d),\n", dhcpmon_default_snaplen);
    printf("\tpcap timeout: pcap library time out (default %d).\n", dhcpmon_default_pcap_timout_ms);
    printf("\t-d: daemonize %s.\n", prog);
    exit(0);
}

/**
 * @code dhcpmon_signal_handler(signal);
 *
 * @brief signal handler for dhcpmon. It will initiate shutdown when signal is caught
 *
 * @param signal signal code that we received
 *
 * @return none
 */
static void dhcpmon_signal_handler(int signal)
{
    dhcp_devman_print_status();
    dhcp_devman_stop_capture();
    dhcp_mon_shutdown();
    sem_post(&dhcpmon_active);
}

/**
 * @code dhcpmon_daemonize();
 *
 * @brief make this utility run as a daemon.
 *
 * @return none
 */
static void dhcpmon_daemonize()
{
    pid_t pid, sid;
    pid = fork();
    if (pid < 0) {
        syslog(LOG_ALERT, "fork: %s", strerror(errno));
        exit(EXIT_FAILURE);
    }

    if (pid > 0) {
        exit(EXIT_SUCCESS);
    }

    // this is the daemon running now
    umask(0);
    // Create a new SID for the child process
    sid = setsid();
    if (sid < 0) {
        syslog(LOG_ALERT, "setsid: %s", strerror(errno));
        exit(EXIT_FAILURE);
    }

    // Change the current working directory
    if ((chdir("/")) < 0) {
        syslog(LOG_ALERT, "chdir: %s", strerror(errno));
        exit(EXIT_FAILURE);
    }

    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);
}

/**
 * @code main(argc, argv);
 *
 * @brief main entry point of dhcpmon utility
 *
 * @return int 0 on success, otherwise on failure
 */
int main(int argc, char **argv)
{
    int rv = EXIT_FAILURE;
    int i;
    int window_interval = dhcpmon_default_health_check_window;
    int max_unhealthy_count = dhcpmon_default_unhealthy_max_count;
    uint32_t snaplen = dhcpmon_default_snaplen;
    uint32_t pcap_timeout_ms = dhcpmon_default_pcap_timout_ms;
    int make_daemon = 0;

    setlogmask(LOG_UPTO(LOG_INFO));
    openlog(basename(argv[0]), LOG_CONS | LOG_PID | LOG_NDELAY, LOG_DAEMON);

    if (sem_init(&dhcpmon_active, 0, 0) != -1) {
        dhcp_devman_init();

        for (i = 1; i < argc;) {
            if ((argv[i] == NULL) || (argv[i][0] != '-')) {
                break;
            }
            switch (argv[i][1])
            {
            case 'h':
                usage(basename(argv[0]));
                break;
            case 'i':
                dhcp_devman_add_intf(argv[i + 1], argv[i][2] == 'u');
                i += 2;
                break;
            case 'd':
                make_daemon = 1;
                i++;
                break;
            case 's':
                snaplen = atoi(argv[i + 1]);
                i += 2;
                break;
            case 't':
                pcap_timeout_ms = atoi(argv[i + 1]);
                i += 2;
                break;
            case 'w':
                window_interval = atoi(argv[i + 1]);
                i += 2;
                break;
            case 'c':
                max_unhealthy_count = atoi(argv[i + 1]);
                i += 2;
                break;
            default:
                fprintf(stderr, "%s: %c: Unknown option\n", basename(argv[0]), argv[i][1]);
                usage(basename(argv[0]));
            }
        }

        if (make_daemon) {
            dhcpmon_daemonize();
        }

        if (dhcp_mon_init(window_interval, max_unhealthy_count) == 0) {

            signal(SIGINT, dhcpmon_signal_handler); /* control-c */
            signal(SIGTERM, dhcpmon_signal_handler); /* kill */

            if (dhcp_devman_start_capture(snaplen, pcap_timeout_ms) == 0) {
                sem_wait(&dhcpmon_active);
                rv = EXIT_SUCCESS;
            }

            dhcp_mon_shutdown();
        }

        dhcp_devman_shutdown();
    } else {
        syslog(LOG_ALERT, "sem_init: %s", strerror(errno));
    }

    closelog();

    return rv;
}
