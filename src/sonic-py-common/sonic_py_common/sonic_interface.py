import sys

"""
 Dictionary of SONIC interface name prefixes. Each entry in the format
 "Human readable interface string":"Sonic interface prefix"
 Currently this is a static mapping, but in future could be stored as metadata in DB.
"""

SONIC_INTERFACE_PREFIXES = {
  "Ethernet-FrontPanel":"Ethernet",
  "PortChannel":"PortChannel",
  "Vlan":"Vlan",
  "Loopback":"Loopback",
  "Ethernet-Backplane":"Ethernet-BP"
}

def sonic_fp_interface_prefix():
    """
    Retrieves the SONIC front panel interface name prefix.
    """
    return SONIC_INTERFACE_PREFIXES["Ethernet-FrontPanel"]

def sonic_bp_interface_prefix():
    """
    Retrieves the SONIC backplane interface name prefix.
    """
    return SONIC_INTERFACE_PREFIXES["Ethernet-Backplane"]

def sonic_portchannel_interface_prefix():
    """
    Retrieves the SONIC PortChannel interface name prefix.
    """
    return SONIC_INTERFACE_PREFIXES["PortChannel"]

def sonic_vlan_interface_prefix():
    """
    Retrieves the SONIC Vlan interface name prefix.
    """
    return SONIC_INTERFACE_PREFIXES["Vlan"]

def sonic_lo_interface_prefix():
    """
    Retrieves the SONIC Loopback interface name prefix.
    """
    return SONIC_INTERFACE_PREFIXES["Loopback"]
