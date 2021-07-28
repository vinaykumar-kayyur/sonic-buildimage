#include <getopt.h>
#include <errno.h>
#include <unistd.h>
#include <event.h>
#include <sstream>
#include <event2/event.h>
#include <event2/bufferevent.h>
#include <syslog.h>
#include <signal.h>

#include "configdb.h"
#include "sonicv2connector.h"
#include "dbconnector.h" 
#include "configInterface.h"


struct event *listen_event;
struct event_base *base;
struct event *ev_sigint;
struct event *ev_sigterm;

bool serverListener = true;
std::shared_ptr<boost::thread> serverPtr;

bool is_addr_gua(in6_addr addr) {

    auto masked = addr.__in6_u.__u6_addr8[0] & 0xe0;
    return (masked ^ 0x20) == 0x00;
}

bool is_addr_link_local(in6_addr addr)  {
    auto masked = ntohs(addr.__in6_u.__u6_addr16[0]) & 0xffc0;
    return (masked ^ 0xfe80) == 0x0000;
}

const struct ether_header *parse_ether_frame(const uint8_t *buffer, const uint8_t **out_end) {
    (*out_end) = buffer + sizeof(struct ether_header);
    return (const struct ether_header *)buffer;
}

const struct ip6_hdr *parse_ip6_hdr(const uint8_t *buffer, const uint8_t **out_end) {
    (*out_end) = buffer + sizeof(struct ip6_hdr);
    return (struct ip6_hdr *)buffer;
}

const struct udphdr *parse_udp(const uint8_t *buffer, const uint8_t **out_end) {
    (*out_end) = buffer + sizeof(struct udphdr);
    return (const struct udphdr *)buffer;
}

const struct dhcpv6_msg *parse_dhcpv6_hdr(const uint8_t *buffer) {
    return (const struct dhcpv6_msg *)buffer;
}

const struct dhcpv6_relay_msg *parse_dhcpv6_relay(const uint8_t *buffer) {
    return (const struct dhcpv6_relay_msg *)buffer;
}

const struct dhcpv6_option *parse_dhcpv6_opt(const uint8_t *buffer, const uint8_t **out_end) {
    uint32_t size = 4; // option-code + option-len
    size += ntohs(*(uint16_t *)(buffer + 2));
    (*out_end) = buffer + size;

    return (const struct dhcpv6_option *)buffer;
}

void send_udp(int sock, uint8_t *buffer, struct sockaddr_in6 target, uint32_t n) {    
    if(sendto(sock, buffer, n, 0, (const struct sockaddr *)&target, sizeof(target)) == -1)
        syslog(LOG_ERR, "sendto: Failed to send to target address\n");
}

/**
 * @code                relay_forward(uint8_t *buffer, const struct dhcpv6_msg *msg, uint16_t msg_length);
 *
 * @brief               embed the DHCPv6 message received into DHCPv6 relay forward message
 *
 * @param buffer        pointer to buffer
 * @param msg           pointer to parsed DHCPv6 message
 * @param msg_length    length of DHCPv6 message
 *
 * @return              none
 */
void relay_forward(uint8_t *buffer, const struct dhcpv6_msg *msg, uint16_t msg_length) {
    struct dhcpv6_option option;
    option.option_code = htons(OPTION_RELAY_MSG);
    option.option_length = htons(msg_length);
    memcpy(buffer, &option, sizeof(struct dhcpv6_option));
    memcpy(buffer + sizeof(struct dhcpv6_option), msg, msg_length);
}

/**
 * @code                sock_open(int ifindex, const struct sock_fprog *fprog);
 *
 * @brief               prepare L2 socket to attach to "udp and port 547" filter 
 *
 * @param ifindex       interface index
 * @param fprog         bpf filter "udp and port 547"
 *
 * @return              socket descriptor
 */
int sock_open(int ifindex, const struct sock_fprog *fprog)
{
	if (!ifindex) {
		errno = EINVAL;
		return -1;
	}

	int s = socket(AF_PACKET, SOCK_RAW, 0);
	if (s == -1) {
		syslog(LOG_ERR, "socket: Failed to create socket\n");
		return -1;
	}

	struct sockaddr_ll sll = {
	    .sll_family = AF_PACKET,
	    .sll_protocol = htons(ETH_P_IPV6),
	    .sll_ifindex = ifindex
	};

	if (bind(s, (struct sockaddr *)&sll, sizeof sll) == -1) {
		syslog(LOG_ERR, "bind: Failed to bind to specified interface\n");
		(void) close(s);
	    return -1;
	}

	struct packet_mreq mreq = {
	    .mr_ifindex = ifindex,
	    .mr_type = PACKET_MR_PROMISC
	};

	if (setsockopt(s, SOL_PACKET, PACKET_ADD_MEMBERSHIP, &mreq, sizeof mreq) == -1)
	{
		syslog(LOG_ERR, "setsockopt: Failed to send PACkET_MR_PROMISC\n");
		(void) close(s);
	    return -1;
	}

	if (fprog && setsockopt(s, SOL_SOCKET, SO_ATTACH_FILTER, fprog, sizeof *fprog) == -1)
	{
		syslog(LOG_ERR, "setsockopt: Failed to attach filter\n");
		(void) close(s);
	    return -1;
	}

	return s;
}

/**
 * @code                        prepare_relay_config(relay_config *interface_config, int fd, const arg_config *context);
 * 
 * @brief                       prepare for specified relay interface config: server and link address
 *
 * @param interface_config      pointer to relay config to be prepared
 * @param local_sock            L3 socket used for relaying messages
 * @param filter                socket attached with filter
 * @param config                argument config that contains strings of server and interface addresses
 *
 * @return                      none
 */
void prepare_relay_config(relay_config *interface_config, int local_sock, int filter, const arg_config *context) {
    interface_config->local_sock = local_sock; 
    interface_config->filter = filter; 
    interface_config->is_option_79 = context->is_option_79; 

    for(auto server: context->servers) {
        sockaddr_in6 tmp;
        if(inet_pton(AF_INET6, server.c_str(), &tmp.sin6_addr) != 1)
        {
            syslog(LOG_WARNING, "inet_pton: Failed to convert IPv6 address\n");
        }
        tmp.sin6_family = AF_INET6;
        tmp.sin6_flowinfo = 0;
        tmp.sin6_port = htons(RELAY_PORT);
        tmp.sin6_scope_id = 0; 
        interface_config->servers.push_back(tmp);
    }

    sockaddr_in6 *non_link_local = NULL;    
    sockaddr_in6 *link_local = NULL;
    
    struct ifaddrs *ifa, *ifa_tmp;
    char addr[INET6_ADDRSTRLEN];
    addr[0] = 0;

    if (getifaddrs(&ifa) == -1) {
		syslog(LOG_WARNING, "getifaddrs: Unable to get network interfaces\n");
        exit(1);
	}

    ifa_tmp = ifa;
	while (ifa_tmp) {
		if ((ifa_tmp->ifa_addr) && (ifa_tmp->ifa_addr->sa_family == AF_INET6)) {
            struct sockaddr_in6 *in6 = (struct sockaddr_in6*) ifa_tmp->ifa_addr;
            inet_ntop(AF_INET6, &in6->sin6_addr, addr, sizeof(addr));
            if((strcmp(ifa_tmp->ifa_name, interface_config->interface.c_str()) == 0) && is_addr_gua(in6->sin6_addr)) {    
                non_link_local = in6;
                break;
            }
            if((strcmp(ifa_tmp->ifa_name, interface_config->interface.c_str()) == 0) && is_addr_link_local(in6->sin6_addr)) {    
                link_local = in6;
            }   
	    }
	    ifa_tmp = ifa_tmp->ifa_next;
	}
	freeifaddrs(ifa);

    if (non_link_local != NULL) {
        interface_config->link_address = *non_link_local;
    }
    else {
        interface_config->link_address = *link_local;
    }
}

/**
 * @code                prepare_socket(int *local_sock, arg_config *context);
 * 
 * @brief               prepare L3 socket for sending
 *
 * @param local_sock    pointer to socket to be prepared
 * @param context       argument config that contains strings of server and interface addresses
 *
 * @return              none
 */
void prepare_socket(int *local_sock, arg_config *context) {
    sockaddr_in6 addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin6_family = AF_INET6;
    addr.sin6_addr = in6addr_any;
    /*TO FIX AFTER TESTING IPV6 ADDR AUTO SELECTION. PLEASE IGNORE THE COMMENTED AREA*/
    /*struct ifaddrs *ifa, *ifa_tmp;
     char tmp[INET6_ADDRSTRLEN];
    tmp[0] = 0;

    if (getifaddrs(&ifa) == -1) {
            syslog(LOG_WARNING, "getifaddrs: Unable to get network interfaces\n");
            exit(1);
    } 

    ifa_tmp = ifa;
    while (ifa_tmp) {
            if ((ifa_tmp->ifa_addr) && (ifa_tmp->ifa_addr->sa_family == AF_INET6)) {                  
                struct sockaddr_in6 *in6 = (struct sockaddr_in6*) ifa_tmp->ifa_addr;
                inet_ntop(AF_INET6, &in6->sin6_addr, tmp, sizeof(tmp));
                if(strcmp(ifa_tmp->ifa_name, context->interface.c_str()) == 0 && (is_addr_gua(in6->sin6_addr))) {
                    inet_pton(AF_INET6, tmp, &addr.sin6_addr);
                }
                else {
                    syslog(LOG_ERR, "inet_pton: interface global address not configured\n");
                    sleep(10);
                    continue;
                }
            }
            ifa_tmp = ifa_tmp->ifa_next;
    }
    freeifaddrs(ifa);   */

    if ((*local_sock = socket(AF_INET6, SOCK_DGRAM, 0)) == -1) {
        syslog(LOG_ERR, "scoket: Failed to create socket\n");
    }

    addr.sin6_port = htons(RELAY_PORT);
    
    if (bind(*local_sock, (sockaddr *)&addr, sizeof(addr)) == -1) {
        syslog(LOG_ERR, "bind: Failed to bind to socket\n");
    }    
}


/**
 * @code                 relay_client(int sock, const uint8_t *msg, int32_t len, ip6_hdr *ip_hdr, const ether_header *ether_hdr, relay_config *config);
 * 
 * @brief                construct relay-forward message
 *
 * @param sock           L3 socket for sending data to servers
 * @param msg            pointer to dhcpv6 message header position
 * @param len            size of data received
 * @param ip_hdr         pointer to IPv6 header
 * @param ether_hdr      pointer to Ethernet header
 * @param config         pointer to the relay interface config
 *
 * @return none
 */
void relay_client(int sock, const uint8_t *msg, int32_t len, const ip6_hdr *ip_hdr, const ether_header *ether_hdr, relay_config *config) {    
    uint8_t buffer[4096];
    auto current_buffer_position = buffer;
    dhcpv6_relay_msg new_message;
    new_message.msg_type = RELAY_FORW;
    memcpy(&new_message.peer_address, &ip_hdr->ip6_src, sizeof(in6_addr));
    new_message.hop_count = 0;

    memcpy(&new_message.link_address, &config->link_address.sin6_addr, sizeof(in6_addr));
    memcpy(current_buffer_position, &new_message, sizeof(dhcpv6_relay_msg));
    current_buffer_position += sizeof(dhcpv6_relay_msg);


    auto dhcp_message_length = len;
    relay_forward(current_buffer_position, parse_dhcpv6_hdr(msg), dhcp_message_length);
    current_buffer_position += dhcp_message_length + sizeof(dhcpv6_option);

    if(config->is_option_79) {
        linklayer_addr_option option79;
        option79.link_layer_type = htons(1);
        option79.option_code = htons(OPTION_CLIENT_LINKLAYER_ADDR);
        option79.option_length = htons(2 + 6); // link_layer_type field + address
        
        memcpy(current_buffer_position, &option79, sizeof(linklayer_addr_option));
        current_buffer_position += sizeof(linklayer_addr_option);
    }

    memcpy(current_buffer_position, &ether_hdr->ether_shost, sizeof(ether_hdr->ether_shost));
    current_buffer_position += sizeof(ether_hdr->ether_shost);

    for(auto server: config->servers) {
        send_udp(sock, buffer, server, current_buffer_position - buffer);
    }
}

/**
 * @code                relay_relay_reply(int sock, const uint8_t *msg, int32_t len, relay_config *configs);
 * 
 * @brief               relay and unwrap a relay-reply message
 *
 * @param sock          L3 socket for sending data to servers
 * @param msg           pointer to dhcpv6 message header position
 * @param len           size of data received
 * @param config        relay interface config
 *
 * @return              none
 */
 void relay_relay_reply(int sock, const uint8_t *msg, int32_t len, relay_config *configs) {
    uint8_t buffer[4096];
    char ifname[configs->interface.size()];
    struct sockaddr_in6 target_addr;
    auto current_buffer_position = buffer;
    auto current_position = msg;
    const uint8_t *tmp = NULL;
    auto dhcp_relay_header = parse_dhcpv6_relay(msg);
    current_position += sizeof(struct dhcpv6_relay_msg);
    
    while ((current_position - msg) != len) {
        auto option = parse_dhcpv6_opt(current_position, &tmp);
        current_position = tmp;
        switch (ntohs(option->option_code)) {
            case OPTION_RELAY_MSG:
                memcpy(current_buffer_position, ((uint8_t *)option) + sizeof(struct dhcpv6_option), ntohs(option->option_length));
                current_buffer_position += ntohs(option->option_length);
                break;
            default:
                break;
        }
    }

    strcpy(ifname, configs->interface.c_str());
    memcpy(&target_addr.sin6_addr, &dhcp_relay_header->peer_address, sizeof(struct in6_addr));
    target_addr.sin6_family = AF_INET6;
    target_addr.sin6_flowinfo = 0;
    target_addr.sin6_port = htons(CLIENT_PORT);
    target_addr.sin6_scope_id = if_nametoindex(ifname);

    send_udp(sock, buffer, target_addr, current_buffer_position - buffer);
} 


/**
 * @code                callback(evutil_socket_t fd, short event, void *arg);
 * 
 * @brief               callback for libevent that is called everytime data is received at the filter socket
 *
 * @param fd            filter socket
 * @param event         libevent triggered event  
 * @param arg           callback argument provided by user
 *
 * @return              none
 */
void callback(evutil_socket_t fd, short event, void *arg) {
    struct relay_config *config = (struct relay_config *)arg;
    static uint8_t message_buffer[4096];
    uint32_t len = recv(config->filter, message_buffer, 4096, 0);
    if (len <= 0) {
        syslog(LOG_WARNING, "recv: Failed to receive data at filter socket\n");
    }

    char* ptr = (char *)message_buffer;
    const uint8_t *current_position = (uint8_t *)ptr; 
    const uint8_t *tmp = NULL;

    auto ether_header = parse_ether_frame(current_position, &tmp);
    current_position = tmp;

    auto ip_header = parse_ip6_hdr(current_position, &tmp);
    current_position = tmp;

    if (ip_header->ip6_ctlun.ip6_un1.ip6_un1_nxt != IPPROTO_UDP) {
        const struct ip6_ext *ext_header;
        do {
            ext_header = (const struct ip6_ext *)current_position;
            current_position += ext_header->ip6e_len;
        }
        while (ext_header->ip6e_nxt != IPPROTO_UDP);
    }  

    auto udp_header = parse_udp(current_position, &tmp);
    current_position = tmp;

    auto dhcp_header = parse_dhcpv6_hdr(current_position);

    if (((ntohs(udp_header->dest)) == RELAY_PORT) && (dhcp_header->msg_type == SOLICIT || REQUEST || CONFIRM || RENEW || REBIND || RELEASE || DECLINE)) {
        relay_client(config->local_sock, current_position, ntohs(udp_header->len) - sizeof(udphdr), ip_header, ether_header, config);
    }
}

/**
 * @code                listen_server(void *arg);
 * 
 * @brief               listen to the DHCPv6 server
 *
 * @param arg           callback argument provided by user
 *
 * @return              none
 */
void listen_server(relay_config *config) {
    while (serverListener) {
        sockaddr_in6 from;
        int32_t data = 0;
        uint8_t message_buffer[4096];

        if ((data = recvfrom(config->local_sock, message_buffer, 4096, 0, (sockaddr *)&from, (socklen_t *)sizeof(from))) == -1) {
            syslog(LOG_WARNING, "recv: Failed to receive data from server\n");
        }

        auto msg = parse_dhcpv6_hdr(message_buffer);
        if (msg->msg_type == RELAY_REPL) {
            relay_relay_reply(config->local_sock, message_buffer, data, config);
        }
    }
}

/**
*@code      initialize_server(relay_config *config);
*
*@brief     initialize server listening thread
*
*@return    none
*/
void initialize_server(relay_config *config)
{
    try {
        serverPtr = std::make_shared<boost::thread> (&listen_server, config);
    }
    catch (const std::bad_alloc &e) {
        syslog(LOG_ERR, "Failed to allocate memory. Exception details: %s", e.what());
    }
}

/**
*@code      stopServerListener();
*
*@brief     stop server listening thread
*
*@return    none
*/
void stopServerListener() {
    serverListener = false;
};

/**
*@code      deinitialize_server();
*
*@brief     join and stop server listening thread
*
*@return    none
*/
void deinitialize_server() {
    stopServerListener();
    serverPtr->interrupt();
}

/**
 * @code signal_init();
 *
 * @brief initialize DHCPv6 Relay libevent signals
 */
int signal_init() {
    int rv = -1;
     do {
        ev_sigint = evsignal_new(base, SIGINT, signal_callback, base);
        if (ev_sigint == NULL) {
            syslog(LOG_ERR, "Could not create SIGINT libevent signal\n");
            break;
        }

        ev_sigterm = evsignal_new(base, SIGTERM, signal_callback, base);
        if (ev_sigterm == NULL) {
            syslog(LOG_ERR, "Could not create SIGTERM libevent signal\n");
            break;
        }
        rv = 0;
    } while(0);
    return rv;
}

/**
 * @code signal_start();
 *
 * @brief start DHCPv6 Relay libevent base and add signals
 */
int signal_start()
{
    int rv = -1;
    do
    {
        if (evsignal_add(ev_sigint, NULL) != 0) {
            syslog(LOG_ERR, "Could not add SIGINT libevent signal\n");
            break;
        }

        if (evsignal_add(ev_sigterm, NULL) != 0) {
            syslog(LOG_ERR, "Could not add SIGTERM libevent signal\n");
            break;
        }

        if (event_base_dispatch(base) != 0) {
            syslog(LOG_ERR, "Could not start libevent dispatching loop\n");
        }

        rv = 0;
    } while (0);

    return rv;
}

/**
 * @code signal_callback(fd, event, arg);
 *
 * @brief signal handler for dhcp6relay. Initiate shutdown when signal is caught
 *
 * @param fd        libevent socket
 * @param event     event triggered
 * @param arg       pointer to libevent base
 *
 * @return none
 */
void signal_callback(evutil_socket_t fd, short event, void *arg)
{
    syslog(LOG_ALERT, "Received signal: '%s'\n", strsignal(fd));
    if ((fd == SIGTERM) || (fd == SIGINT)) {
        dhcp6relay_stop();
    }
}

/**
 * @code dhcp6relay_stop();
 *
 * @brief stop DHCPv6 Relay libevent loop upon signal
 */
void dhcp6relay_stop()
{
    event_base_loopexit(base, NULL);
}

/**
 * @code                loop_relay(arg_config context);
 * 
 * @brief               main loop: configure sockets, create libevent base, start server listener thread
 *
 * @param context       user argument that contains input interface and options
 */
void loop_relay(arg_config *context) {
    struct relay_config config;
    int filter = 0;
    int local_sock = 0; 
    const char *ifname = context->interface.c_str();
    int index = if_nametoindex(ifname);

    filter = sock_open(index, &ether_relay_fprog);

    prepare_socket(&local_sock, context);

    config.interface = context->interface;

    prepare_relay_config(&config, local_sock, filter, context);

    initialize_server(&config);

    evutil_make_listen_socket_reuseable(filter);
    evutil_make_socket_nonblocking(filter);

    base = event_base_new();
    if(base == NULL) {
        syslog(LOG_ERR, "libevent: Failed to create base\n");
    }

    listen_event = event_new(base, filter, EV_READ|EV_PERSIST, callback, (void *)&config);
    if (listen_event == NULL) {
        syslog(LOG_ERR, "libevent: Failed to create libevent\n");
    }
    event_add(listen_event, NULL);

    if((signal_init() == 0) && signal_start() == 0) {
        shutdown();
        close(local_sock);
    }
}

/**
 * @code shutdown();
 *
 * @brief free signals and terminate threads
 */
void shutdown() {
    event_del(ev_sigint);
    event_del(ev_sigterm);
    event_free(ev_sigint); 
    event_free(ev_sigterm);
    deinitialize_swss();
    deinitialize_server();
}
