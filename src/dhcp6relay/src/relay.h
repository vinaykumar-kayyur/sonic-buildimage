#include <arpa/inet.h>
#include <net/if.h>
#include <linux/if_packet.h>
#include <netinet/if_ether.h>	
#include <netinet/ip6.h>
#include <netinet/udp.h>
#include <ifaddrs.h>
#include <linux/filter.h>
#include <string>
#include <vector>
#include <event2/util.h>


#define PACKED __attribute__ ((packed))

#define RELAY_PORT 547
#define CLIENT_PORT 546
#define HOP_LIMIT 32

#define lengthof(A) (sizeof (A) / sizeof (A)[0])

#define OPTION_RELAY_MSG 9
#define OPTION_CLIENT_LINKLAYER_ADDR 79

/* DHCPv6 message types */
typedef enum
{
    DHCPv6_MESSAGE_TYPE_SOLICIT = 1,
    DHCPv6_MESSAGE_TYPE_ADVERTISE = 2,
    DHCPv6_MESSAGE_TYPE_REQUEST = 3,
    DHCPv6_MESSAGE_TYPE_CONFIRM  = 4,
    DHCPv6_MESSAGE_TYPE_RENEW  = 5,
    DHCPv6_MESSAGE_TYPE_REBIND = 6,
    DHCPv6_MESSAGE_TYPE_REPLY = 7,
    DHCPv6_MESSAGE_TYPE_RELEASE = 8,
    DHCPv6_MESSAGE_TYPE_DECLINE = 9,
    DHCPv6_MESSAGE_TYPE_RELAY_FORW = 12,
    DHCPv6_MESSAGE_TYPE_RELAY_REPL = 13,

    DHCPv6_MESSAGE_TYPE_COUNT
} dhcp_message_type_t;

struct arg_config {
    std::vector<std::string> servers;
    std::string interface;
    bool is_option_79;
};

struct relay_config {
    int local_sock; 
    int filter;
    sockaddr_in6 link_address;
    swss::DBConnector *db;
    std::string interface;
    std::vector<sockaddr_in6> servers;
    bool is_option_79;
};


/* DHCPv6 messages and options */

struct dhcpv6_msg {
    uint8_t msg_type;
};

struct PACKED dhcpv6_relay_msg {
    uint8_t msg_type;
    uint8_t hop_count;
    struct in6_addr link_address;
    struct in6_addr peer_address;
};


struct dhcpv6_option {
    uint16_t option_code;
    uint16_t option_length;
};

struct linklayer_addr_option  {
    uint16_t option_code;
    uint16_t option_length;
    uint16_t link_layer_type;
};

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
int sock_open(int ifindex, const struct sock_fprog *fprog);

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
void prepare_socket(int *local_sock, arg_config *config);

/**
 * @code                prepare_server_socket(int *server_sock, arg_config *context);
 * 
 * @brief               prepare L3 socket for sending
 *
 * @param server_sock   pointer to socket receiving server packets to be prepared
 * @param context       argument config that contains strings of server and interface addresses
 *
 * @return              none
 */
void prepare_server_socket(int *server_sock, arg_config *context);

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
void prepare_relay_config(relay_config *interface_config, int local_sock, int filter, const arg_config *context);

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
void relay_forward(uint8_t *buffer, const struct dhcpv6_msg *msg, uint16_t msg_length);

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
void relay_client(int sock, const uint8_t *msg, int32_t len, const ip6_hdr *ip_hdr, const ether_header *ether_hdr, relay_config *config);

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
void relay_relay_reply(int sock, const uint8_t *msg, int32_t len, relay_config *configs);

/**
 * @code                loop_relay(std::vector<arg_config> *vlans, swss::DBConnector *db);
 * 
 * @brief               main loop: configure sockets, create libevent base, start server listener thread
 *  
 * @param vlans         list of vlans retrieved from config_db
 * @param db            state_db connector
 */
void loop_relay(std::vector<arg_config> *vlans, swss::DBConnector *db);

/**
 * @code signal_init();
 *
 * @brief initialize DHCPv6 Relay libevent signals
 */
int signal_init();

/**
 * @code signal_start();
 *
 * @brief start DHCPv6 Relay libevent base and add signals
 */
int signal_start();

/**
 * @code dhcp6relay_stop();
 *
 * @brief stop DHCPv6 Relay libevent loop upon signal
 */
void dhcp6relay_stop();

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
void signal_callback(evutil_socket_t fd, short event, void *arg);

/**
 * @code shutdown();
 *
 * @brief free signals and terminate threads
 */
void shutdown();

/**
 * @code                void update_counter(swss::DBConnector *db);
 *
 * @brief               update the counter in state_db with count of each DHCPv6 message type
 *
 * @param swss::DBConnector *db     state_db connector
 * 
 * @return              none
 */
void update_counter(swss::DBConnector *db);

/* Helper functions */

std::string toString(uint16_t count);

bool is_addr_gua(in6_addr addr);

bool is_addr_link_local(in6_addr addr);

const struct ether_header *parse_ether_frame(const uint8_t *buffer, const uint8_t **out_end);

const struct ip6_hdr *parse_ip6_hdr(const uint8_t *buffer, const uint8_t **out_end);

const struct udphdr *parse_udp(const uint8_t *buffer, const uint8_t **out_end);

const struct dhcpv6_msg *parse_dhcpv6_hdr(const uint8_t *buffer);

const struct dhcpv6_relay_msg *parse_dhcpv6_relay(const uint8_t *buffer);

const struct dhcpv6_option *parse_dhcpv6_opt(const uint8_t *buffer, const uint8_t **out_end);

void send_udp(int sock, struct sockaddr_in6 target, uint8_t *buffer, uint32_t n);

