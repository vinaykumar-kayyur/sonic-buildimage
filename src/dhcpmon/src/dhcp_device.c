/**
 * @file dhcp_device.c
 *
 *  device (interface) module
 */

#include <err.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <pthread.h>
#include <net/ethernet.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <netinet/ether.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <syslog.h>
#include <libexplain/ioctl.h>

#include "dhcp_device.h"

/** We are not interesting in putting the interface into promiscuous mode */
#define DHCP_PROMISC_MODE 0
/** Enable libpcap BPF compile optimization */
#define DHCP_BPF_COMPILE_OPTIMIZE 1
/** DHCP BPF libpcap netmask */
#define DHCP_BPF_NETMASK 0
/** Start of Ether header of a captured frame */
#define ETHER_START_OFFSET  0
/** Start of IP header of a captured frame */
#define IP_START_OFFSET (ETHER_START_OFFSET + ETHER_HDR_LEN)
/** Start of UDP header of a captured frame */
#define UDP_START_OFFSET (IP_START_OFFSET + sizeof(struct ip))
/** Start of DHCP header of a captured frame */
#define DHCP_START_OFFSET (UDP_START_OFFSET + sizeof(struct udphdr))
/** Start of DHCP Options segment of a captured frame */
#define DHCP_OPTIONS_HEADER_SIZE 240

/**  DHCP Berkley Packet Filter */
static const char *DHCP_BPF = "udp and (port 67 or port 68)";

/** global aggregate counter for DHCP interfaces */
static dhcp_device_counters_t glob_counters[DHCP_DIR_COUNT] = {
    [DHCP_RX] = { .discovery = 0, .offer = 0, .request = 0, .ack = 0 },
    [DHCP_TX] = { .discovery = 0, .offer = 0, .request = 0, .ack = 0 },
};

/** global aggregate counter snapshot for DHCP interfaces */
static dhcp_device_counters_t glob_counters_snapshot[DHCP_DIR_COUNT] = {
    [DHCP_RX] = { .discovery = 0, .offer = 0, .request = 0, .ack = 0 },
    [DHCP_TX] = { .discovery = 0, .offer = 0, .request = 0, .ack = 0 },
};


/**
 * @code handle_dhcp_option_53(context, dhcp_option, dir);
 *
 * @brief handle the logic related to DHCP option 53
 *
 * @param context       Device (interface) context
 * @param dhcp_option   pointer to DHCP option buffer space
 * @param dir           packet direction
 *
 * @return none
 */
static void handle_dhcp_option_53(dhcp_device_context_t *context, const u_char *dhcp_option, dhcp_packet_direction_t dir)
{
    switch (dhcp_option[2])
    {
    case 1:
        context->counters[dir].discovery++;
        if ((context->is_uplink && dir == DHCP_TX) || (!context->is_uplink && dir == DHCP_RX)) {
            __atomic_fetch_add(&glob_counters[dir].discovery, 1, __ATOMIC_SEQ_CST);
        }
        break;
    case 2:
        context->counters[dir].offer++;
        if ((!context->is_uplink && dir == DHCP_TX) || (context->is_uplink && dir == DHCP_RX)) {
            __atomic_fetch_add(&glob_counters[dir].offer, 1, __ATOMIC_SEQ_CST);
        }
        break;
    case 3:
        context->counters[dir].request++;
        if ((context->is_uplink && dir == DHCP_TX) || (!context->is_uplink && dir == DHCP_RX)) {
            __atomic_fetch_add(&glob_counters[dir].request, 1, __ATOMIC_SEQ_CST);
        }
        break;
    case 5:
        context->counters[dir].ack++;
        if ((!context->is_uplink && dir == DHCP_TX) || (context->is_uplink && dir == DHCP_RX)) {
            __atomic_fetch_add(&glob_counters[dir].ack, 1, __ATOMIC_SEQ_CST);
        }
        break;
    case 6 ... 8:
        // options NAK, Release, Inform
        break;
    default:
        syslog(LOG_WARNING, "pcap_callback(%s): Unknown DHCP option 53 type %d", context->intf,
                dhcp_option[2]);
        break;
    }
}

/**
 * @code pcap_callback(arg, pcap_pkthdr, packet);
 *
 * @brief callback for libpcap which is called every time out in order to process queued packet capture
 *
 * @param arg           user provided argument for callback (interface context)
 * @param header        libpcap header for packet capture
 * @param packet        pointer to packet data
 *
 * @return none
 */
static void pcap_callback(u_char *arg, const struct pcap_pkthdr *header, const u_char *packet)
{
    dhcp_device_context_t *context = (dhcp_device_context_t*) arg;
    struct ether_header *ethhdr = (struct ether_header*) packet;
    struct udphdr *udp = (struct udphdr*) (packet + UDP_START_OFFSET);
    int dhcp_option_offset = DHCP_START_OFFSET + DHCP_OPTIONS_HEADER_SIZE;

    if (header->caplen > UDP_START_OFFSET + sizeof(struct udphdr) + DHCP_OPTIONS_HEADER_SIZE) {
        int dhcp_sz = ntohs(udp->len) < header->caplen - UDP_START_OFFSET - sizeof(struct udphdr) ?
                      ntohs(udp->len) : header->caplen - UDP_START_OFFSET - sizeof(struct udphdr);
        int dhcp_option_sz = dhcp_sz - DHCP_OPTIONS_HEADER_SIZE;

        const u_char *dhcp_option = packet + dhcp_option_offset;
        int offset = 0;

        dhcp_packet_direction_t dir = (ethhdr->ether_shost[0] == context->mac[0] &&
                                       ethhdr->ether_shost[1] == context->mac[1] &&
                                       ethhdr->ether_shost[2] == context->mac[2] &&
                                       ethhdr->ether_shost[3] == context->mac[3] &&
                                       ethhdr->ether_shost[4] == context->mac[4] &&
                                       ethhdr->ether_shost[5] == context->mac[5]) ?
                                       DHCP_TX : DHCP_RX;

        int stop_dhcp_rpocessing = 0;
        while (offset < dhcp_option_sz && dhcp_option[offset] != 255) {
            switch (dhcp_option[offset])
            {
            case 53:
                handle_dhcp_option_53(context, &dhcp_option[offset], dir);
                stop_dhcp_rpocessing = 1; // break while loop since we are only interested in Option 53
                break;
            default:
                break;
            }

            if (stop_dhcp_rpocessing == 1) {
                break;
            }

            if (dhcp_option[offset] == 0) { // DHCP Option Padding
                offset++;
            } else {
                offset += dhcp_option[offset + 1] + 2;
            }
        }
    } else {
        syslog(LOG_ALERT, "pcap_callback(%s): snap length is too low to capture DHCP options", context->intf);
        exit(EXIT_FAILURE);
    }
}

/**
 * @code dhcp_device_process(arg);
 *
 * @brief validate current interface counters by comparing aggregate counter with snapshot counters.
 *
 * @param arg   user provided argument for capturing process (interface context)
 *
 * @return none
 */
static void* dhcp_device_process(void *arg)
{
    dhcp_device_context_t *context = (dhcp_device_context_t*) arg;

    if (pcap_loop(context->cap, -1, pcap_callback, arg) < 0) {
        syslog(LOG_ALERT, "pcap_loop(%s): %s", context->intf, pcap_geterr(context->cap));
        exit(EXIT_FAILURE);
    }

    pthread_exit(NULL);
}

/**
 * @code dhcp_device_validate(counters, counters_snapshot);
 *
 * @brief validate current interface counters by comparing aggregate counter with snapshot counters.
 *
 * @param counters              recent interface counter
 * @param counters_snapshot     snapshot counters
 *
 * @return DHCP_MON_STATUS_HEALTHY, DHCP_MON_STATUS_UNHEALTHY, or DHCP_MON_STATUS_INDETERMINATE
 */
static dhcp_mon_status_t dhcp_device_validate(dhcp_device_counters_t *counters,
                                              dhcp_device_counters_t *counters_snapshot)
{
    dhcp_mon_status_t rv = DHCP_MON_STATUS_HEALTHY;

    if ((counters[DHCP_RX].discovery == counters_snapshot[DHCP_RX].discovery) &&
        (counters[DHCP_RX].offer == counters_snapshot[DHCP_RX].offer) &&
        (counters[DHCP_RX].request == counters_snapshot[DHCP_RX].request) &&
        (counters[DHCP_RX].ack == counters_snapshot[DHCP_RX].ack)) {
        rv = DHCP_MON_STATUS_INDETERMINATE;
    } else {
        // if we have rx DORA then we should have corresponding tx DORA (DORA being relayed)
        if (((counters[DHCP_RX].discovery > counters_snapshot[DHCP_RX].discovery ) &&
             (counters[DHCP_TX].discovery <= counters_snapshot[DHCP_TX].discovery)    ) ||
            ((counters[DHCP_RX].offer > counters_snapshot[DHCP_RX].offer ) &&
             (counters[DHCP_TX].offer <= counters_snapshot[DHCP_TX].offer)            ) ||
            ((counters[DHCP_RX].request > counters_snapshot[DHCP_RX].request ) &&
             (counters[DHCP_TX].request <= counters_snapshot[DHCP_TX].request)        ) ||
            ((counters[DHCP_RX].ack > counters_snapshot[DHCP_RX].ack ) &&
             (counters[DHCP_TX].ack <= counters_snapshot[DHCP_TX].ack)                )) {
            rv = DHCP_MON_STATUS_UNHEALTHY;
        }
    }

    return rv;
}

/**
 * @code dhcp_print_counters(counters);
 *
 * @brief prints DHCP counters to sylsog.
 *
 * @param counters  interface counter
 */
static void dhcp_print_counters(dhcp_device_counters_t *counters)
{
    syslog(LOG_NOTICE, "DHCP Discover rx: %lu, tx:%lu, Offer rx: %lu, tx:%lu, Request rx: %lu, tx:%lu, ACK rx: %lu, tx:%lu\n",
           counters[DHCP_RX].discovery, counters[DHCP_TX].discovery,
           counters[DHCP_RX].offer, counters[DHCP_TX].offer,
           counters[DHCP_RX].request, counters[DHCP_TX].request,
           counters[DHCP_RX].ack, counters[DHCP_TX].ack);
}

/**
 * @code init_libpcap(context, intf, snaplen, timeout_ms);
 *
 * @brief initializes libpacp for a device (interface)
 *
 * @param context           pointer to device (interface) context
 * @param intf              interface name
 * @param snaplen           length of packet capture
 * @aparam timeout_ms       timeout for libpacp to report packets captured
 *
 * @return 0 on success, otherwise for failure
 */
static int init_libpcap(dhcp_device_context_t *context, const char *intf, int snaplen, int timeout_ms)
{
    int rv = -1;

    do {
        strncpy(context->intf, intf, sizeof(context->intf) - 1);
        context->intf[sizeof(context->intf) - 1] = '\0';

        context->cap = pcap_open_live(context->intf, snaplen, DHCP_PROMISC_MODE, timeout_ms, context->err_buf);
        if (context->cap == NULL) {
            syslog(LOG_ALERT, "pcap_open_live(): %s", context->err_buf);
            break;
        }

        if (pcap_compile(context->cap, &context->fp, DHCP_BPF,
                         DHCP_BPF_COMPILE_OPTIMIZE, DHCP_BPF_NETMASK) != 0) {
            syslog(LOG_ALERT, "pcap_compile: %s", pcap_geterr(context->cap));
            break;
        }

        if (pcap_setfilter(context->cap, &context->fp) != 0) {
            syslog(LOG_ALERT, "pcap_setfilter: %s", pcap_geterr(context->cap));
            break;
        }

        rv = 0;
    } while (0);

    return rv;
}

/**
 * @code initialize_intf_mac_and_ip_addr(context);
 *
 * @brief initializes device (interface) mac/ip addresses
 *
 * @param context           pointer to device (interface) context
 *
 * @return 0 on success, otherwise for failure
 */
static int initialize_intf_mac_and_ip_addr(dhcp_device_context_t *context)
{
    int rv = -1;

    do {
        int fd;
        struct ifreq ifr;
        if ((fd = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
            syslog(LOG_ALERT, "socket: %s", strerror(errno));
            break;
        }

        ifr.ifr_addr.sa_family = AF_INET;
        strncpy(ifr.ifr_name, context->intf, sizeof(ifr.ifr_name) - 1);
        ifr.ifr_name[sizeof(ifr.ifr_name) - 1] = '\0';

        // Get network address
        if (ioctl(fd, SIOCGIFADDR, &ifr) == -1) {
            syslog(LOG_ALERT, "ioctl: %s", explain_ioctl(fd, SIOCGIFADDR, &ifr));
            break;
        }
        context->ip = ((struct sockaddr_in*) &ifr.ifr_addr)->sin_addr.s_addr;

        // Get mac address
        if (ioctl(fd, SIOCGIFHWADDR, &ifr) == -1) {
            syslog(LOG_ALERT, "ioctl: %s", explain_ioctl(fd, SIOCGIFHWADDR, &ifr));
            break;
        }
        memcpy(context->mac, ifr.ifr_hwaddr.sa_data, sizeof(context->mac));

        close(fd);

        rv = 0;
    } while (0);

    return rv;
}

/**
 * @code dhcp_device_init(context, intf, snaplen, timeout_ms, is_uplink);
 *
 * @brief initializes device (interface) that handles packet capture per interface.
 */
int dhcp_device_init(dhcp_device_context_t **context, const char *intf, int snaplen, int timeout_ms, uint8_t is_uplink)
{
    int rv = -1;
    dhcp_device_context_t *dev_context = NULL;

    if ((context != NULL) && (strlen(intf) < sizeof(dev_context->intf))) {

        dev_context = (dhcp_device_context_t *) malloc(sizeof(dhcp_device_context_t));
        if ((dev_context != NULL) &&
            (init_libpcap(dev_context, intf, snaplen, timeout_ms) == 0) &&
            (initialize_intf_mac_and_ip_addr(dev_context) == 0)) {

            dev_context->is_uplink = is_uplink;

            memset(&dev_context->counters, 0, sizeof(dev_context->counters));
            memset(&dev_context->counters_snapshot, 0, sizeof(dev_context->counters_snapshot));

            *context = dev_context;
            rv = 0;
        }
    }

    return rv;
}

/**
 * @code dhcp_device_shutdown(context);
 *
 * @brief shuts down device (interface). Also, stops packet capture on interface and cleans up any allocated memory
 */
void dhcp_device_shutdown(dhcp_device_context_t *context)
{
    dhcp_device_stop_capture(context);
    free(context);
}

/**
 * @code dhcp_device_start_capture(context);
 *
 * @brief start packet capture on the device (interface)
 */
int dhcp_device_start_capture(dhcp_device_context_t *context)
{
    int rv = -1;

    if (context != NULL) {
        rv = pthread_create(&context->bpf_thread, NULL, dhcp_device_process, context);
    }

    return rv;
}

/**
 * @code dhcp_device_stop_capture(context);
 *
 * @brief stops packet capture.
 */
void dhcp_device_stop_capture(dhcp_device_context_t *context)
{
    if (context != NULL) {
        pcap_breakloop(context->cap);
    }
}

/**
 * @code dhcp_device_get_status(context);
 *
 * @brief collects DHCP relay status info for a given interface. If context is null, it will report aggregate
 *        status
 */
dhcp_mon_status_t dhcp_device_get_status(dhcp_device_context_t *context)
{
    dhcp_mon_status_t rv = 0;

    if (context != NULL) {
        rv = dhcp_device_validate(context->counters, context->counters_snapshot);
        memcpy(context->counters_snapshot, context->counters, sizeof(context->counters_snapshot));
    } else {
        rv = dhcp_device_validate(glob_counters, glob_counters_snapshot);
        memcpy(glob_counters_snapshot, glob_counters, sizeof(glob_counters_snapshot));
    }

    return rv;
}

/**
 * @code dhcp_device_print_status();
 *
 * @brief prints status counters to syslog. If context is null, it will print aggregate status
 */
void dhcp_device_print_status(dhcp_device_context_t *context)
{
    if (context != NULL) {
        dhcp_print_counters(context->counters);
    } else {
        dhcp_print_counters(glob_counters);
    }
}
