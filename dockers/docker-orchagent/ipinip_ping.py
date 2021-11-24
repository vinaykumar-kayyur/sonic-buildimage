#! /usr/bin/env python3
"""
Adds neighbor to kernel for undeliverable IPinIP packets

When receiving IPinIP packets, if the hardware doesn't contain neighbor
information for the inner packet's destination IP, the entire encapsulated
packet is trapped to the CPU. In this case, we should ping the inner
destination IP to trigger the process of obtaining neighbor information
"""
import subprocess
import time

from datetime import datetime
from ipaddress import ip_interface
from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6
from scapy.sendrecv import sniff
from swsssdk import ConfigDBConnector, SonicV2Connector
from sonic_py_common import logger as log

logger = log.Logger()

STATE_DB = 'STATE_DB'
PORTCHANNEL_INTERFACE_TABLE = 'PORTCHANNEL_INTERFACE'
TUNNEL_TABLE = 'TUNNEL'
PEER_SWITCH_TABLE = 'PEER_SWITCH'
INTF_TABLE_TEMPLATE = 'INTERFACE_TABLE|{}|{}'
STATE_KEY = 'state'
TUNNEL_TYPE_KEY = 'tunnel_type'
DST_IP_KEY = 'dst_ip'
ADDRESS_IPV4_KEY = 'address_ipv4'
IPINIP_TUNNEL = 'ipinip'


class IPinIPListener(object):

    def __init__(self):
        self.config_db = ConfigDBConnector()
        self.config_db.connect()
        self.state_db = SonicV2Connector()
        self.state_db.connect(STATE_DB)
        self._portchannel_intfs = None

    @property
    def portchannel_intfs(self):
        """
        Gets all portchannel interfaces and IPv4 addresses in config DB

        Returns:
            (list) Tuples of a portchannel interface name (str) and
                   associated IPv4 address (str)
        """
        if self._portchannel_intfs is None:
            intf_keys = self.config_db.get_keys(PORTCHANNEL_INTERFACE_TABLE)
            portchannel_intfs = []

            for key in intf_keys:
                if isinstance(key, tuple) and len(key) > 1:
                    if ip_interface(key[1]).version == 4:
                        portchannel_intfs.append(key)

            self._portchannel_intfs = portchannel_intfs

        return self._portchannel_intfs

    def all_portchannels_up(self):
        """
        Checks if the portchannel interfaces are up

        Returns:
            (bool) True, if all interfaces are up
                   False, otherwise
        """
        intfs = self.portchannel_intfs
        for intf in intfs:
            intf_table_name = INTF_TABLE_TEMPLATE.format(intf[0], intf[1])
            intf_state = self.state_db.get(
                                STATE_DB,
                                intf_table_name,
                                STATE_KEY
                              )

            if intf_state and intf_state.lower() != 'ok':
                return False

        return True

    def wait_for_portchannels(self, interval=5, timeout=60):
        """
        Continuosly checks if all portchannel member host interfaces are up

        Args:
            interval: the interval (in seconds) at which to perform the check
            timeout: maximum allowed duration (in seconds) to wait for
                     interfaces to come up

        Raises:
            RuntimeError if the timeout duration is reached and interfaces are
                still not up
        """
        start = datetime.now()

        while (datetime.now() - start).seconds < 60:
            if self.all_portchannels_up():
                logger.log_info("All portchannel intfs are up")
                return None
            logger.log_info("Not all portchannel intfs are up")
            time.sleep(interval)

        raise RuntimeError('Portchannel intfs did not come '
                           'up within {}'.format(timeout))

    def get_ipinip_tunnel_addrs(self):
        """
        Get the IP addresses used for the IPinIP tunnel

        These should be the Loopback0 addresses for this device and the
        peer device

        Returns:
            ((str) self_loopback_ip, (str) peer_loopback_ip)
            or
            (None, None) If the tunnel type is not IPinIP
                         or
                         if an error is encountered. This most likely means
                         the host device is not a dual ToR device
        """
        try:
            peer_switch = self.config_db.get_keys(PEER_SWITCH_TABLE)[0]
            tunnel = self.config_db.get_keys(TUNNEL_TABLE)[0]
        except IndexError:
            logger.log_warning('PEER_SWITCH or TUNNEL table'
                               'not found in config DB')
            return None, None

        try:
            tunnel_table = self.config_db.get_entry(TUNNEL_TABLE, tunnel)
            tunnel_type = tunnel_table[TUNNEL_TYPE_KEY].lower()
            self_loopback_ip = tunnel_table[DST_IP_KEY]
            peer_loopback_ip = self.config_db.get_entry(
                                    PEER_SWITCH_TABLE, peer_switch
                                    )[ADDRESS_IPV4_KEY]
        except KeyError as e:
            logger.log_warning(
                'PEER_SWITCH or TUNNEL table missing data, '
                'could not find key {}'
                .format(e)
            )
            return None, None

        if tunnel_type == IPINIP_TUNNEL:
            return self_loopback_ip, peer_loopback_ip

        return None, None

    def get_inner_pkt_type(self, packet):
        """
        Get the type of an inner encapsulated packet

        Returns:
            (str)  'v4' if the inner packet is IPv4
            (str)  'v6' if the inner packet is IPv6
            (bool) False if `packet` is not an IPinIP packet
        """
        if packet.haslayer(IP):
            # Determine inner packet type based on IP protocol number
            # The outer packet type should always be IPv4
            if packet[IP].proto == 4:
                return IP
            elif packet[IP].proto == 41:
                return IPv6
        return False

    def listen_for_ipinip(self):
        """
        Listens for IPinIP packets that are trapped to CPU

        These packets may be trapped if there is no neighbor info for the
        inner packet destination IP in the hardware.
        """

        def _ping_inner_dst(packet):
            """
            Pings the inner destination IP for an IPinIP packet

            Args:
                packet: The IPinIP packet received
            """
            inner_packet_type = self.get_inner_pkt_type(packet)
            if inner_packet_type and packet[IP].dst == self_ip:
                cmds = ['timeout', '0.2', 'ping', '-c1',
                        '-W1', '-i0', '-n', '-q']
                if inner_packet_type == IPv6:
                    cmds.append('-6')
                dst_ip = packet[IP][inner_packet_type].dst
                cmds.append(dst_ip)
                logger.log_info("Running command '{}'".format(' '.join(cmds)))
                subprocess.run(cmds, stdout=subprocess.DEVNULL)

        self_ip, peer_ip = self.get_ipinip_tunnel_addrs()
        if self_ip is None or peer_ip is None:
            logger.log_error('Could not get IPinIP tunnel addresses from '
                             'config DB, exiting...')
            return None

        packet_filter = 'host {} and host {}'.format(self_ip, peer_ip)
        logger.log_notice('Starting IPinIP listener for {}'
                          .format(packet_filter))

        portchannel_intfs = self.portchannel_intfs
        portchannels = [pair[0] for pair in portchannel_intfs]
        logger.log_info("Listening on interfaces {}".format(portchannels))

        while True:
            sniff(
                iface=portchannels,
                filter=packet_filter,
                prn=_ping_inner_dst
                )

    def run(self):
        self.wait_for_portchannels()
        self.listen_for_ipinip()


def main():
    logger.set_min_log_priority_info()
    listener = IPinIPListener()
    listener.run()


if __name__ == "__main__":
    main()
