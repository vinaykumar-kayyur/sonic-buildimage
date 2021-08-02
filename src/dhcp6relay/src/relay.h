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
#include <memory>
#include <thread>

#define PACKED __attribute__ ((packed))

#define RELAY_PORT 547
#define CLIENT_PORT 546
#define HOP_LIMIT 32

#define lengthof(A) (sizeof (A) / sizeof (A)[0])

#define SOLICIT 1
#define REQUEST 3
#define CONFIRM 4
#define RENEW 5
#define REBIND 6
#define RELEASE 8 
#define DECLINE 9
#define RELAY_FORW 12
#define RELAY_REPL 13
#define OPTION_RELAY_MSG 9
#define OPTION_CLIENT_LINKLAYER_ADDR 79


/* Configuration */
static std::string config_interface;

struct arg_config {
    std::vector<std::string> servers;
    std::string interface;
    bool is_option_79;
};

struct relay_config {
    int local_sock; 
    int filter;
    sockaddr_in6 link_address;
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

int sock_open(int ifindex, const struct sock_fprog *fprog);

void prepare_socket(int *local_sock, arg_config *config);

void prepare_server_socket(int *server_sock, arg_config *context);

void prepare_relay_config(relay_config *interface_config, int local_sock, int filter, const arg_config *context);

void relay_forward(uint8_t *buffer, const struct dhcpv6_msg *msg, uint16_t msg_length);

void relay_client(int sock, const uint8_t *msg, int32_t len, const ip6_hdr *ip_hdr, const ether_header *ether_hdr, relay_config *config);

void relay_relay_reply(int sock, const uint8_t *msg, int32_t len, relay_config *configs);

void loop_relay(arg_config *config);

int signal_init();

int signal_start();

void dhcp6relay_stop();

void signal_callback(evutil_socket_t fd, short event, void *arg);

void shutdown();


/* Helper functions */

bool is_addr_gua(in6_addr addr);

bool is_addr_link_local(in6_addr addr);

const struct ether_header *parse_ether_frame(const uint8_t *buffer, const uint8_t **out_end);

const struct ip6_hdr *parse_ip6_hdr(const uint8_t *buffer, const uint8_t **out_end);

const struct udphdr *parse_udp(const uint8_t *buffer, const uint8_t **out_end);

const struct dhcpv6_msg *parse_dhcpv6_hdr(const uint8_t *buffer);

const struct dhcpv6_relay_msg *parse_dhcpv6_relay(const uint8_t *buffer);

const struct dhcpv6_option *parse_dhcpv6_opt(const uint8_t *buffer, const uint8_t **out_end);

void send_udp(int sock, struct sockaddr_in6 target, uint8_t *buffer, uint32_t n);

struct ArgumentException : std::exception {
    std::string msg;
    ArgumentException(std::string message) : msg(message) {}
    ~ArgumentException() throw() {}
    const char* what() const throw() { return msg.c_str(); }
};


/* DHCPv6 filter */
/* sudo tcpdump -dd "ip6 dst ff02::1:2 && udp dst port 547" */

static struct sock_filter ether_relay_filter[] = {
	
	{ 0x28, 0, 0, 0x0000000c },
	{ 0x15, 0, 13, 0x000086dd },
	{ 0x20, 0, 0, 0x00000026 },
	{ 0x15, 0, 11, 0xff020000 },
	{ 0x20, 0, 0, 0x0000002a },
	{ 0x15, 0, 9, 0x00000000 },
	{ 0x20, 0, 0, 0x0000002e },
	{ 0x15, 0, 7, 0x00000000 },
	{ 0x20, 0, 0, 0x00000032 },
	{ 0x15, 0, 5, 0x00010002 },
	{ 0x30, 0, 0, 0x00000014 },
	{ 0x15, 0, 3, 0x00000011 },
	{ 0x28, 0, 0, 0x00000038 },
	{ 0x15, 0, 1, 0x00000223 },
	{ 0x6, 0, 0, 0x00040000 },
	{ 0x6, 0, 0, 0x00000000 },
};
const struct sock_fprog ether_relay_fprog = {
	lengthof(ether_relay_filter),
	ether_relay_filter
};
