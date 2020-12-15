#!/usr/bin/env python3

import yaml
from swsssdk import ConfigDBConnector

db = ConfigDBConnector()
db.connect()

with open('/etc/sonic/snmp.yml', 'r') as yaml_file:
    yaml_snmp_info = yaml.load(yaml_file)

full_snmp_comm_list = ['snmp_rocommunity', 'snmp_rocommunities', 'snmp_rwcommunity', 'snmp_rwcommunities']

for comm_type in full_snmp_comm_list:
    if comm_type in yaml_snmp_info.keys():
        if comm_type.startswith('snmp_rocommunities'):
            for community in yaml_snmp_info[comm_type]:
                db.set_entry('SNMP_COMMUNITY', community, {"TYPE": "RO"})
        elif comm_type.startswith('snmp_rocommunity'):
            community = yaml_snmp_info['snmp_rocommunity']
            db.set_entry('SNMP_COMMUNITY', community, {"TYPE": "RO"})
        elif comm_type.startswith('snmp_rwcommunities'):
            for community in yaml_snmp_info[comm_type]:
                db.set_entry('SNMP_COMMUNITY', community, {"TYPE": "RW"})
        elif comm_type.startswith('snmp_rwcommunity'):
            community = yaml_snmp_info['snmp_rwcommunity']
            db.set_entry('SNMP_COMMUNITY', community, {"TYPE": "RW"})

if yaml_snmp_info['snmp_location']:
    db.set_entry('SNMP', 'LOCATION', {'Location': yaml_snmp_info['snmp_location']})
