from unittest.mock import call

"""
    hostcfgd test password hardening vector
"""
HOSTCFGD_TEST_PASSWH_VECTOR = [
    [
        "PASSWORD_HARDENING",
        {
            "default_values":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "disabled",
                        "expiration": "180",
                        "expiration_warning": "15",
                        "history_ctr": "10",
                        "len_min": "8",
                        "reject_user_passw_match": "True",
                        "lower_class": "True",
                        "upper_class": "True",
                        "digit_class": "True",
                        "special_class": "True"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            },
                        "default_values":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "disabled",
                        "expiration": "180",
                        "expiration_warning": "15",
                        "history_ctr": "10",
                        "len_min": "8",
                        "reject_user_passw_match": "True",
                        "lower_class": "True",
                        "upper_class": "True",
                        "digit_class": "True",
                        "special_class": "True"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            },
            "enable_feature":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "enabled",
                        "expiration": "180",
                        "expiration_warning": "15",
                        "history_ctr": "10",
                        "len_min": "8",
                        "reject_user_passw_match": "True",
                        "lower_class": "True",
                        "upper_class": "True",
                        "digit_class": "True",
                        "special_class": "True"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            },
            "enable_digit_class":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "enabled",
                        "expiration": "0",
                        "expiration_warning": "0",
                        "history_ctr": "0",
                        "len_min": "8",
                        "reject_user_passw_match": "False",
                        "lower_class": "False",
                        "upper_class": "False",
                        "digit_class": "True",
                        "special_class": "False"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            },
            "enable_lower_class":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "enabled",
                        "expiration": "0",
                        "expiration_warning": "0",
                        "history_ctr": "0",
                        "len_min": "8",
                        "reject_user_passw_match": "False",
                        "lower_class": "True",
                        "upper_class": "False",
                        "digit_class": "False",
                        "special_class": "False"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            },
            "enable_upper_class":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "enabled",
                        "expiration": "0",
                        "expiration_warning": "0",
                        "history_ctr": "0",
                        "len_min": "8",
                        "reject_user_passw_match": "False",
                        "lower_class": "False",
                        "upper_class": "True",
                        "digit_class": "False",
                        "special_class": "False"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            },
            "enable_special_class":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "enabled",
                        "expiration": "0",
                        "expiration_warning": "0",
                        "history_ctr": "0",
                        "len_min": "8",
                        "reject_user_passw_match": "False",
                        "lower_class": "False",
                        "upper_class": "False",
                        "digit_class": "False",
                        "special_class": "True"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            },
            "TODO: X":{
                "PASSW_HARDENING": {
                    "POLICIES":{
                        "state": "enabled",
                        "expiration": "180",
                        "expiration_warning": "15",
                        "history_ctr": "10",
                        "len_min": "8",
                        "reject_user_passw_match": "True",
                        "lower_class": "True",
                        "upper_class": "True",
                        "digit_class": "True",
                        "special_class": "True"
                    }
                },
                "DEVICE_METADATA": {
                    "localhost": {
                        "hostname": "radius",
                    }
                },
                "FEATURE": {
                    "dhcp_relay": {
                        "auto_restart": "enabled",
                        "has_global_scope": "True",
                        "has_per_asic_scope": "False",
                        "has_timer": "False",
                        "high_mem_alert": "disabled",
                        "set_owner": "kube",
                        "state": "enabled"
                    },
                },
                "KDUMP": {
                    "config": {
                        "enabled": "false",
                        "num_dumps": "3",
                        "memory": "0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M"
                    }
                },
                "AAA": {
                    "authentication": {
                        "login": "local"
                    },
                    "authorization": {
                        "login": "local"
                    },
                    "accounting": {
                        "login": "local"
                    }
                },
                "TACPLUS": {
                    "global": {
                            "auth_type": "chap",
                            "timeout": 5,
                            "passkey": "dellsonic",
                            "src_intf": "Ethernet0"
                    }
                },
                "TACPLUS_SERVER": {
                    "192.168.1.1" : {
                            "priority": 5,
                            "tcp_port": 50,
                            "timeout": 10,
                            "auth_type": "chap",
                            "passkey": "dellsonic",
                            "vrf": "default"
                    },
                    "192.168.1.2" : {
                            "priority": 2,
                            "tcp_port": 51,
                            "timeout": 15,
                            "auth_type": "pap",
                            "passkey": "dellsonic1",
                            "vrf": "mgmt"
                    }
                }
            }# TODO X

        }
    ]
]
