#!/usr/bin/env python
import os
import sys
from natsort import natsorted

def generate_sample_config(data, setting_name):
    if setting_name.lower() == 't1':
        return generate_t1_sample_config(data)

def generate_t1_sample_config(data):
    data['DEVICE_METADATA']['localhost']['hostname'] = 'sonic'
    data['DEVICE_METADATA']['localhost']['type'] = 'LeafRouter'
    data['DEVICE_METADATA']['localhost']['bgp_asn'] = '65100'
    data['LOOPBACK_INTERFACE'] = {"Loopback0|10.1.0.1/32": {}}
    data['BGP_NEIGHBOR'] = {}
    data['DEVICE_NEIGHBOR'] = {}
    data['INTERFACE'] = {}
    port_count = 0
    total_port_amount = len(data['PORT'])
    for port in natsorted(data['PORT'].keys()):
        data['PORT'][port]['admin_status'] = 'up'
        data['PORT'][port]['mtu'] = '9100'
        local_addr = '10.0.{}.{}'.format(2 * port_count / 256, 2 * port_count % 256)
        peer_addr = '10.0.{}.{}'.format(2 * port_count / 256, 2 * port_count % 256 + 1)
        peer_name='ARISTA{0:02d}{1}'.format(1+port_count%(total_port_amount/2), 'T2' if port_count < (total_port_amount/2) else 'T0')
        peer_asn = 65200 if port_count < total_port_amount/2 else 64001 + port_count - total_port_amount/2
        data['INTERFACE']['{}|{}/31'.format(port, local_addr)] = {}
        data['BGP_NEIGHBOR'][peer_addr] = {
                'rrclient': 0,
                'name': peer_name,
                'local_addr': local_addr,
                'nhopself': 0,
                'holdtime': '180',
                'asn': str(peer_asn),
                'keepalive': '60'
                }
        port_count += 1
    return data;

