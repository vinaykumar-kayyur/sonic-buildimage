import sys
import json

from collections import defaultdict
from ipaddress import ip_interface
from natsort import natsorted

#TODO: Remove once Python 2 support is removed
if sys.version_info.major == 3:
    UNICODE_TYPE = str
else:
    UNICODE_TYPE = unicode

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
    for port in natsorted(data['PORT']):
        data['PORT'][port]['admin_status'] = 'up'
        data['PORT'][port]['mtu'] = '9100'
        local_addr = '10.0.{}.{}'.format(2 * port_count // 256, 2 * port_count % 256)
        peer_addr = '10.0.{}.{}'.format(2 * port_count // 256, 2 * port_count % 256 + 1)
        peer_name='ARISTA{0:02d}{1}'.format(1+port_count%(total_port_amount // 2), 'T2' if port_count < (total_port_amount // 2) else 'T0')
        peer_asn = 65200 if port_count < (total_port_amount // 2) else 64001 + port_count - (total_port_amount // 2)
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
    return data

def generate_empty_config(data):
    new_data = {'DEVICE_METADATA': data['DEVICE_METADATA']}
    if 'hostname' not in new_data['DEVICE_METADATA']['localhost']:
        new_data['DEVICE_METADATA']['localhost']['hostname'] = 'sonic'
    if 'type' not in new_data['DEVICE_METADATA']['localhost']:
        new_data['DEVICE_METADATA']['localhost']['type'] = 'LeafRouter'
    return new_data

def port_is_uplink(port_info):
    return len(port_info['lanes'].split(',')) == 4

def port_is_downlink(port_info):
    return len(port_info['lanes'].split(',')) == 2

def get_uplinks_downlinks(port_table):
    # sort the ports based on the first lane number
    sorted_ports = sorted(port_table.items(), key=lambda x: int(x[1]['lanes'].split(',')[0]))
    uplinks = []
    downlinks = []
    ports_iter = iter(sorted_ports)
    for port_tuple in ports_iter:
        # Iterate over ports two at a time so we can get
        # used ports and the corresponding unused ports
        port_a_name, port_a_info = port_tuple
        port_b_name, port_b_info = next(ports_iter)
        if port_is_uplink(port_a_info) and port_is_uplink(port_b_info) :
            uplinks.append(port_a_name)
            uplinks.append(port_b_name)
        elif port_is_downlink(port_a_info) and port_is_downlink(port_b_info):
            downlinks.append(port_a_name)
            # don't use port_b in this case
        # this shouldn't happen
        else:
            raise ValueError("Error parsing port_config.ini for dual ToR")
    
    return uplinks, downlinks

def generate_global_dualtor_tables():
    data = defaultdict(lambda: defaultdict(dict))
    data['LOOPBACK_INTERFACE'] = {
                                    'Loopback2': {},
                                    'Loopback2|3.3.3.3': {}
                                    }
    data['MUX_CABLE'] = {}
    data['PEER_SWITCH'] = {
                            "peer_switch_hostname": {
                                "address_ipv4": "1.1.1.1"
                            }
                            }
    data['TUNNEL'] = {
                        "MuxTunnel0": {
                            "dscp_mode": "uniform",
                            "dst_ip": "2.2.2.2",
                            "ecn_mode": "copy_from_outer",
                            "encap_ecn_mode": "standard",
                            "ttl_mode": "pipe",
                            "tunnel_type": "IPINIP"
                        }
                    }
    return data

def generate_l2_config(data):
    # Check if dual ToR configs are needed
    if 'is_dualtor' in data and data['is_dualtor']:
        is_dualtor = True
        data.pop('is_dualtor')
    else:
        is_dualtor = False

    # VLAN initial data
    data['VLAN'] = {'Vlan1000': {'vlanid': '1000'}}
    data['VLAN_MEMBER'] = {}

    if is_dualtor:
        data['DEVICE_METADATA']['localhost']['subtype'] = 'DualToR'
        data['DEVICE_METADATA']['localhost']['peer_switch'] = 'peer_switch_hostname'
        data.update(generate_global_dualtor_tables())

        uplinks, downlinks = get_uplinks_downlinks(data['PORT'])
        server_ipv4_base = ip_interface(UNICODE_TYPE('192.168.0.1/32'))
        server_ipv6_base = ip_interface(UNICODE_TYPE('fc02:1000::1/128'))
        server_offset = 0
    for port in natsorted(data['PORT']):
        if is_dualtor:
            # Ports in use should be admin up, unused ports default to admin down
            if port in downlinks or port in uplinks:
                data['PORT'][port].setdefault('admin_status', 'up')
                data['VLAN_MEMBER']['Vlan1000|{}'.format(port)] = {'tagging_mode': 'untagged'}

            # 100G Uplinks (all 4 lanes assigned to one logical port) need FEC value set
            if port in uplinks:
                data['PORT'][port]['fec'] = 'rs'

            # Downlinks (connected to mux cable) need a MUX_CABLE entry
            # as well as the `mux_cable` field in the PORT table
            if port in downlinks:
                mux_cable_entry = {
                    'server_ipv4': str(server_ipv4_base + server_offset),
                    'server_ipv6': str(server_ipv6_base + server_offset),
                    'state': 'auto'
                }
                server_offset += 1
                data['MUX_CABLE'][port] = mux_cable_entry
                data['PORT'][port]['mux_cable'] = 'true'
        else:
            data['PORT'][port].setdefault('admin_status', 'up')
            data['VLAN_MEMBER']['Vlan1000|{}'.format(port)] = {'tagging_mode': 'untagged'}
    return data

_sample_generators = {
        't1': generate_t1_sample_config,
        'l2': generate_l2_config,
        'empty': generate_empty_config
        }

def get_available_config():
    return list(_sample_generators.keys())

def generate_sample_config(data, setting_name):
    return _sample_generators[setting_name.lower()](data)

