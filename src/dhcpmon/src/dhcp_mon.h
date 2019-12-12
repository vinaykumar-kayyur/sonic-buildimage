/**
 * @file dhcp_mon.h
 *
 *  @brief dhcp relay monitor module
 *
 */

#ifndef DHCP_MON_H_
#define DHCP_MON_H_

/**
 * @code dhcp_mon_init(window_ssec, max_count);
 *
 * @brief initializes monitoring thread that continuously collects dhcp relay health status every window_sec seconds.
 *        It also write to syslog when dhcp relay has been unhealthy for consecutive max_count checks.
 *
 * @param window_sec time interval between health checks
 * @param max_count max count of consecutive unhealthy statuses before reporting to syslog
 *
 * @return 0 upon success, otherwise upon failure
 */
int dhcp_mon_init(int window_sec, int max_count);

/**
 * @code dhcp_mon_shutdown();
 *
 * @brief shuts down monitoring thread
 *
 * @return none
 */
void dhcp_mon_shutdown();

#endif /* DHCP_MON_H_ */
