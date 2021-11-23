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
from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6
from scapy.sendrecv import sniff
from swsssdk import ConfigDBConnector
from sonic_py_common import logger as log

logger = log.Logger()


class IPinIPListener(object):

    def __init__(self):
        self.config_db = ConfigDBConnector()
        self.config_db.connect()

    def get_portchannel_members(self):
        """
        Gets all interfaces which are portchannel members in config DB

        Returns:
            (list) Interface names which are portchannel members, stored
                   as strings
        """
        raw_members = self.config_db.get_keys('PORTCHANNEL_MEMBER')
        members = [pair[1] for pair in raw_members]
        return members

    def all_ports_ok(self):
        """
        Checks if the host interfaces corresponding to portchannel
        members are up

        Returns:
            (bool) True, if all interfaces are up
                   False, otherwise
        """
        members = self.get_portchannel_members()
        for intf in members:
            cmds = ['ip', 'link', 'show', intf]
            try:
                output = subprocess.check_output(cmds)
            except subprocess.CalledProcessError:
                return False
            if 'state UP' not in str(output):
                return False
        return True

    def wait_for_ports_up(self, interval=5, timeout=60):
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
            if self.all_ports_ok():
                logger.log_info("All portchannel members are up")
                return None
            logger.log_info("Not all portchannel members are up")
            time.sleep(interval)

        raise RuntimeError('Portchannel member interfaces did not come '
                           'up within {}'.format(timeout))

    def get_ipinip_tunnel_addrs(self):
        """
        Get the IP addresses used for the IPinIP tunnel

        These should be the Loopback0 addresses for this device and the
        peer device

        Returns:
            ((str) self_loopback_ip, (str) peer_loopback_ip)
            or
            (None, None) if an error is encountered. This most likely means
                        the host device is not a dual ToR device
        """
        try:
            peer_switch = self.config_db.get_keys('PEER_SWITCH')[0]
            tunnel = self.config_db.get_keys('TUNNEL')[0]
        except IndexError:
            logger.log_warning('PEER_SWITCH or TUNNEL table'
                               'not found in config DB')
            return None, None

        try:
            peer_loopback_ip = self.config_db.get_entry(
                                    'PEER_SWITCH', peer_switch
                                    )['address_ipv4']
            self_loopback_ip = self.config_db.get_entry(
                                    'TUNNEL', tunnel
                                    )['dst_ip']
        except KeyError as e:
            logger.log_warning(
                'PEER_SWITCH or TUNNEL table missing data, '
                'could not find key {}'
                .format(e)
            )
            return None, None

        return self_loopback_ip, peer_loopback_ip

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
                cmds = ['ping', '-c1', '-W1']
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
        logger.log_notice('Starting IPinIP listener for IPs {} and {}'
                          .format(self_ip, peer_ip))
        while True:
            sniff(
                iface=self.get_portchannel_members(),
                filter=packet_filter,
                prn=_ping_inner_dst
                )

    def run(self):
        self.wait_for_ports_up()
        self.listen_for_ipinip()


def main():
    logger.set_min_log_priority_info()
    listener = IPinIPListener()
    listener.run()


if __name__ == "__main__":
    main()
