#!/usr/bin/env python

########################################
#
# Vnet ping
#
########################################


import argparse
import logging
from scapy.all import *
from sys import argv, exit
from swsscommon import swsscommon
import netaddr

#
# Config
#

DEFAULT_DST_PORT = 1021
DEFAULT_TCP_OPTIONS = 253
DEFAULT_TTL = 2
REDIS_TIMEOUT_MS = 0
CFG_VLAN_TABLE_NAME = 'VLAN'
CFG_VLAN_VLANID_KEY_NAME = 'vlanid'
CFG_VLAN_MONVLAN_KEY_NAME = 'host_ifname'
CFG_METADATA_LOCALHOST_ENTRY_NAME = 'localhost'
CFG_METADATA_MAC_KEY_NAME = 'mac'


###

#
# Get an ipv4 address from a given string.
# Return None if the given string is not a valid ipv4 address.
#

def get_ipv4_address(value):
    if not value:
        return None

    try:
        addr = netaddr.IPNetwork(str(value))
    except (netaddr.NotRegisteredError, netaddr.AddrFormatError, netaddr.AddrConversionError):
        return None

    if addr.version == 4:
        return str(addr.ip)
    else:
        return None

#
# Get a value of a key from ConfigDB's tablename|entry_name
#

def get_configdb_info(table_name, entry_name, key_name):
    ret_value = None
    if entry_name is None or key_name is None:
        return ret_value

    try:
        config_db = swsscommon.DBConnector("CONFIG_DB", REDIS_TIMEOUT_MS, True)
        vlan_table = swsscommon.Table(config_db, table_name)
        (status, tuples) = vlan_table.get(entry_name)
        entry_info = dict(tuples)
        ret_value = entry_info[key_name]
    except KeyError as ke:
        print "KeyError %s" %(str(ke))

    return ret_value

#
# Extract Loopback0 ipv4 address
#

def get_loopback_ipv4():
    loopback0_ipv4 = None

    try:
        config_db = swsscommon.DBConnector("CONFIG_DB", REDIS_TIMEOUT_MS, True)
        loopback_interface = swsscommon.Table(config_db, swsscommon.CFG_LOOPBACK_INTERFACE_TABLE_NAME)
        for loopback in loopback_interface.getKeys():
            if loopback.startswith("Loopback0|"):
                loopback0_prefix_str = loopback.replace("Loopback0|", "")
                ipv4_address = get_ipv4_address(loopback0_prefix_str)
                if ipv4_address is not None:
                    loopback0_ipv4 = ipv4_address
                    break
    except ValueError as ve:
        print "ValueError %s" %(str(ve))

    return loopback0_ipv4


#
# Get the vlanid from Vlan interface name
#

def get_mon_vlan_id(vlan_interface_name):
    return get_configdb_info(CFG_VLAN_TABLE_NAME, vlan_interface_name, CFG_VLAN_VLANID_KEY_NAME)


####

class TcpSession:

    #
    # Initialize an instance.
    #

    def __init__(self,target):
        self.seq = 0
        self.ack = 0
        self.srcip = target[0]
        self.dstip = target[1]
        self.dport = target[2]
        self.vlanid = target[3]
        self.loopbackip = target[4]
        self._ackThread = None
        self._timeout = 3
        self.ip = IP(src=self.srcip, dst=self.dstip)
        self.ttl = DEFAULT_TTL
        self.sentpackets = 0
        self.receivedpackets = 0
        self.rttms = 0
        self.verbose = 0


    #
    # Connect to a TCP server.
    #

    def connect(self):
        self.seq = random.randrange(0,(2**32)-1)

        ip = IP(src=self.srcip, dst=self.dstip, ttl=self.ttl)

        if self.vlanid is None:
            tcpsync = ip/TCP(dport=self.dport, seq=self.seq, flags='S', options=[(DEFAULT_TCP_OPTIONS, b'\0')])
        else:
            tcpsync = Dot1Q(vlan=int(self.vlanid))/ip/TCP(dport=self.dport, seq=self.seq, flags='S', options=[(DEFAULT_TCP_OPTIONS, b'\0')])

        syn_ack = sr1(tcpsync, timeout=self._timeout, verbose=self.verbose)
        self.seq += 1
        self.sentpackets += 1

        if syn_ack:
            self.receivedpackets += 1
            if syn_ack.time and tcpsync.sent_time:
                self.rttms = (syn_ack.time - tcpsync.sent_time) * 1000
                print "Reply from %s: time=%.2fms TTL=%d" %(self.dstip, self.rttms, self.ttl)
            else:
                print "Reply from %s: TTL=%d" %(self.dstip, self.ttl)
        elif self.srcip == self.loopbackip:
            print "Request timed out."


    #
    # Close a connect to a TCP server.
    #

    def close(self):
        self.seq = random.randrange(0, (2**32)-1)
        ack = self.ip/TCP(dport=self.dport, seq=self.seq, flags='R', options=[(DEFAULT_TCP_OPTIONS, b'\0')])
        send(ack, verbose = self.verbose)

####


#
# Main function
#

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', dest='vnetname', metavar='vnetname', type=str, required=False, help='Source VNET name to inject packet to')
    parser.add_argument('-i', dest='vnetinterface', metavar='vnetinterface', type=str, required=False, help='VLAN interface name that belongs to vnet_name')
    parser.add_argument('-s', dest='srcip', metavar='srcip', type=str, required=False, help='Overlay source ip')
    parser.add_argument('-d', dest='dstip', metavar='dstip', type=str, required=True, help='Overlay destination ip')
    args = parser.parse_args()

    logging.getLogger("scapy").setLevel(logging.CRITICAL)

    vnetname = args.vnetname
    srcip = args.srcip
    dstip = args.dstip
    dstport = DEFAULT_DST_PORT
    loopbackip = get_loopback_ipv4()
    monvlanid = get_mon_vlan_id(args.vnetinterface)

    if srcip is None:
        if loopbackip is None:
            print "srcip and loopbackip can't be None in the same time"
            sys.exit(1)
        else:
            srcip = loopbackip

    tcp_hs = TcpSession((srcip, dstip, dstport, monvlanid, loopbackip))

    for x in range(4):
        tcp_hs.connect()
        tcp_hs.close()
        time.sleep(0.5)

    if srcip == loopbackip:
        lostrate = (tcp_hs.sentpackets - tcp_hs.receivedpackets) * 100 / tcp_hs.sentpackets
        print "Ping statistics for %s:" %(dstip)
        print "    Packets: Sent = %d, Received = %d, Lost = %d (%d%% loss)" %(tcp_hs.sentpackets, tcp_hs.receivedpackets, lostrate, lostrate)
    else:
        print "%d packets sent" %(tcp_hs.sentpackets)


#
# Program entry
#

if __name__ == '__main__':
    main(sys.argv[1:])
