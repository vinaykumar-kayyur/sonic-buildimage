#! /usr/bin/env python3
"""
Adds neighbor to kernel for undeliverable IPinIP packets

When receiving IPinIP packets, if the hardware doesn't contain neighbor
information for the inner packet's destination IP, the entire encapsulated
packet is trapped to the CPU. In this case, we should ping the inner
destination IP to trigger the process of obtaining neighbor information
"""
import subprocess

from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6
from scapy.sendrecv import sniff
from swsssdk import ConfigDBConnector
from sonic_py_common import logger as log

logger = log.Logger()

def get_ipinip_tunnel_addrs():
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
    config_db = ConfigDBConnector()
    config_db.connect()

    try:
        peer_switch = config_db.get_keys('PEER_SWITCH')[0]
        tunnel = config_db.get_keys('TUNNEL')[0]
    except IndexError:
        logger.log_warning('PEER_SWITCH or TUNNEL table not found in config DB')
        return None, None

    try:
        peer_loopback_ip = config_db.get_entry('PEER_SWITCH', peer_switch)['address_ipv4']
        self_loopback_ip = config_db.get_entry('TUNNEL', tunnel)['dst_ip']
    except KeyError as e:
        logger.log_warning(
            'PEER_SWITCH or TUNNEL table missing data, could not find key {}'
                .format(e)
        )
        return None, None

    return self_loopback_ip, peer_loopback_ip


def get_inner_pkt_type(packet):
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


def listen_for_ipinip():
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
        inner_packet_type = get_inner_pkt_type(packet)
        if inner_packet_type and packet[IP].dst == self_ip:
            cmds = ['ping', '-c1', '-W1']
            if inner_packet_type == IPv6:
                cmds.append('-6')
            dst_ip = packet[IP][inner_packet_type].dst
            cmds.append(dst_ip)
            logger.log_info("Running command '{}'".format(' '.join(cmds)))
            subprocess.run(cmds, stdout=subprocess.DEVNULL)

    self_ip, peer_ip = get_ipinip_tunnel_addrs()
    if self_ip is None or peer_ip is None:
        logger.log_error('Could not get IPinIP tunnel addresses from config DB, exiting...')
        return None

    packet_filter = 'host {} and host {}'.format(self_ip, peer_ip)
    logger.log_notice('Starting IPinIP listener for IPs {} and {}'.format(self_ip, peer_ip))
    while True:
        sniff(filter=packet_filter, prn=_ping_inner_dst)


def main():
    logger.set_min_log_priority_info()
    listen_for_ipinip()


if __name__ == "__main__":
    main()
