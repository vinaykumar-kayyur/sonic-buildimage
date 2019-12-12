/**
 * @file dhcp_device.h
 *
 *  device (interface) module
 */

#ifndef DHCP_DEVICE_H_
#define DHCP_DEVICE_H_

#include <pcap.h>
#include <stdint.h>
#include <pthread.h>
#include <net/if.h>
#include <netinet/in.h>
#include <net/ethernet.h>

/** packet direction */
typedef enum
{
    DHCP_RX,    /** RX DHCP packet */
    DHCP_TX,    /** TX DHCP packet */

    DHCP_DIR_COUNT
} dhcp_packet_direction_t;

/** dhcp health status */
typedef enum
{
    DHCP_MON_STATUS_HEALTHY,        /** DHCP relay is healthy */
    DHCP_MON_STATUS_UNHEALTHY,      /** DHCP relay is unhealthy and is missing out on some packets */
    DHCP_MON_STATUS_INDETERMINATE,  /** DHCP relay health could not be determined */
} dhcp_mon_status_t;

/** DHCP device (interface) health counters */
typedef struct
{
    uint64_t discovery;     /** DHCP discovery packets */
    uint64_t offer;         /** DHCP offer packets */
    uint64_t request;       /** DHCP request packets */
    uint64_t ack;           /** DHCP ack packets */
} dhcp_device_counters_t;

/** DHCP device (interface) context */
typedef struct
{
    pcap_t *cap;                    /** libpcap cap struct */
    struct bpf_program fp;          /** lippcap bpf code/program */
    in_addr_t ip;                   /** network address of this device (interface) */
    uint8_t mac[ETHER_ADDR_LEN];    /** hardware address of this device (interface) */
    uint8_t is_uplink;              /** north interface? */
    char intf[IF_NAMESIZE];         /** device (interface) name */
    char err_buf[PCAP_ERRBUF_SIZE]; /** error buffer for libpcap APIs */
    pthread_t bpf_thread;           /** packet capture thread */
    dhcp_device_counters_t counters[DHCP_DIR_COUNT];
                                    /** current coutners of DORA packets */
    dhcp_device_counters_t counters_snapshot[DHCP_DIR_COUNT];
                                     /** counter snapshot */
} dhcp_device_context_t;

/**
 * @code dhcp_device_init(context, intf, snaplen, timeout_ms, is_uplink);
 *
 * @brief initializes device (interface) that handles packet capture per interface.
 *
 * @param context(inout)    pointer to device (interface) context
 * @param intf              interface name
 * @param snaplen           length of packet capture
 * @aparam timeout_ms       timeout for libpacp to report packets captured
 * @param is_uplink         uplink interface
 *
 * @return 0 on success, otherwise for failure
 */
int dhcp_device_init(dhcp_device_context_t **context, const char *intf, int snaplen, int timeout_ms, uint8_t is_uplink);

/**
 * @code dhcp_device_shutdown(context);
 *
 * @brief shuts down device (interface). Also, stops packet capture on interface and cleans up any allocated memory
 *
 * @param context   Device (interface) context
 *
 * @return nonedhcp_device_shutdown
 */
void dhcp_device_shutdown(dhcp_device_context_t *context);

/**
 * @code dhcp_device_start_capture(context);
 *
 * @brief start packet capture on the device (interface)
 *
 * @param context   Device (interface) context
 *
 * @return 0 on success, nonzero otherwise
 */
int dhcp_device_start_capture(dhcp_device_context_t *context);

/**
 * @code dhcp_device_stop_capture(context);
 *
 * @brief stops packet capture.
 *
 * @param context   Device (interface) context
 *
 * @return none
 */
void dhcp_device_stop_capture(dhcp_device_context_t *context);

/**
 * @code dhcp_device_get_status(context);
 *
 * @brief collects DHCP relay status info for a given interface. If context is null, it will report aggregate
 *        status
 *
 * @param context   Device (interface) context
 *
 * @return DHCP_MON_STATUS_HEALTHY, DHCP_MON_STATUS_UNHEALTHY, or DHCP_MON_STATUS_INDETERMINATE
 */
dhcp_mon_status_t dhcp_device_get_status(dhcp_device_context_t *context);

/**
 * @code dhcp_device_print_status();
 *
 * @brief prints status counters to syslog. If context is null, it will print aggregate status
 *
 * @return none
 */
void dhcp_device_print_status(dhcp_device_context_t *context);

#endif /* DHCP_DEVICE_H_ */
