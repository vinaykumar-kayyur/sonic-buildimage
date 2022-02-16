from unittest.mock import call

"""
    caclmgrd ip2me block test vector
"""
CACLMGRD_IP2ME_TEST_VECTOR = [
    [
        "Only MGMT interface, no block",
        {
            "config_db": {
                "MGMT_INTERFACE": {
                    "eth0|172.18.0.100/24": {
                        "gwaddr": "172.18.0.1"
                    }
                },
                "LOOPBACK_INTERFACE": {},
                "VLAN_INTERFACE": {},
                "PORTCHANNEL_INTERFACE": {},
                "INTERFACE": {},
                "DEVICE_METADATA": {
                    "localhost": {
                    }
                },
            },
            "return": [
            ],
        },
    ],
    [
        "One interface of each type, /32 - block all interfaces but MGMT",
        {
            "config_db": {
                "LOOPBACK_INTERFACE": {
                    "Loopback0|10.10.10.10/32": {},
                },
                "VLAN_INTERFACE": {
                    "Vlan110|10.10.11.10/32": {},
                },
                "PORTCHANNEL_INTERFACE": {
                    "PortChannel0001|10.10.12.10/32": {},
                },
                "INTERFACE": {
                    "Ethernet0|10.10.13.10/32": {}
                },
                "MGMT_INTERFACE": {
                    "eth0|172.18.0.100/24": {
                        "gwaddr": "172.18.0.1"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                    }
                },
            },
            "return": [
                "iptables -A INPUT -d 10.10.10.10 -j DROP -m comment --comment 'Block IP2ME on interface Loopback0'",
                "iptables -A INPUT -d 10.10.11.10 -j DROP -m comment --comment 'Block IP2ME on interface Vlan110'",
                "iptables -A INPUT -d 10.10.12.10 -j DROP -m comment --comment 'Block IP2ME on interface PortChannel0001'",
                "iptables -A INPUT -d 10.10.13.10 -j DROP -m comment --comment 'Block IP2ME on interface Ethernet0'"
            ],
        },
    ],
    [
        "One interface of each type, /25 - block all interfaces but MGMT",
        {
            "config_db": {
                "LOOPBACK_INTERFACE": {
                    "Loopback0|10.10.10.150/25": {},
                },
                "VLAN_INTERFACE": {
                    "Vlan110|10.10.11.100/25": {},
                },
                "PORTCHANNEL_INTERFACE": {
                    "PortChannel0001|10.10.12.100/25": {},
                },
                "INTERFACE": {
                    "Ethernet0|10.10.13.1/25": {}
                },
                "MGMT_INTERFACE": {
                    "eth0|172.18.0.100/24": {
                        "gwaddr": "172.18.0.1"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                    }
                },
            },
            "return": [
                "iptables -A INPUT -d 10.10.10.150 -j DROP -m comment --comment 'Block IP2ME on interface Loopback0'",
                "iptables -A INPUT -d 10.10.11.100 -j DROP -m comment --comment 'Block IP2ME on interface Vlan110'",
                "iptables -A INPUT -d 10.10.11.1 -j DROP -m comment --comment 'Block IP2ME (first IP) on interface Vlan110'",
                "iptables -A INPUT -d 10.10.12.100 -j DROP -m comment --comment 'Block IP2ME on interface PortChannel0001'",
                "iptables -A INPUT -d 10.10.13.1 -j DROP -m comment --comment 'Block IP2ME on interface Ethernet0'"
            ],
        },
    ],
    [
        "One VLAN interface, /24, we are .1 -- regression testing to ensure compatibility with old behavior",
        {
            "config_db": {
                "MGMT_INTERFACE": {
                    "eth0|172.18.0.100/24": {
                        "gwaddr": "172.18.0.1"
                    }
                },
                "LOOPBACK_INTERFACE": {},
                "VLAN_INTERFACE": {
                    "Vlan110|10.10.11.1/24": {},
                },
                "PORTCHANNEL_INTERFACE": {},
                "INTERFACE": {},
                "DEVICE_METADATA": {
                    "localhost": {
                    }
                },
            },
            "return": [
                "iptables -A INPUT -d 10.10.11.1 -j DROP -m comment --comment 'Block IP2ME on interface Vlan110'",
            ],
        },
    ],
    [
        "One interface of each type, IPv6, /64 - block all interfaces but MGMT",
        {
            "config_db": {
                "LOOPBACK_INTERFACE": {
                    "Loopback0|2001:db8:10::/64": {},
                },
                "VLAN_INTERFACE": {
                    "Vlan110|2001:db8:11::/64": {},
                },
                "PORTCHANNEL_INTERFACE": {
                    "PortChannel0001|2001:db8:12::/64": {},
                },
                "INTERFACE": {
                    "Ethernet0|2001:db8:13::/64": {}
                },
                "MGMT_INTERFACE": {
                    "eth0|2001:db8:200::200/64": {
                        "gwaddr": "2001:db8:200::100"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                    }
                },
            },
            "return": [
                "ip6tables -A INPUT -d 2001:db8:10:: -j DROP -m comment --comment 'Block IP2ME on interface Loopback0'",
                "ip6tables -A INPUT -d 2001:db8:11:: -j DROP -m comment --comment 'Block IP2ME on interface Vlan110'",
                "ip6tables -A INPUT -d 2001:db8:11::1 -j DROP -m comment --comment 'Block IP2ME (first IP) on interface Vlan110'",
                "ip6tables -A INPUT -d 2001:db8:12:: -j DROP -m comment --comment 'Block IP2ME on interface PortChannel0001'",
                "ip6tables -A INPUT -d 2001:db8:13:: -j DROP -m comment --comment 'Block IP2ME on interface Ethernet0'"
            ],
        },
    ]

]
