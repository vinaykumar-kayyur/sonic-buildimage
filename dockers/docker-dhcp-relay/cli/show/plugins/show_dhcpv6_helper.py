import click
from tabulate import tabulate
from swsscommon.swsscommon import ConfigDBConnector
import os
import sys

import utilities_common.cli as clicommon

DHCP_RELAY = 'DHCP_RELAY'

@click.group(cls=clicommon.AliasedGroup, name="dhcp_relay_helper")
def dhcp_relay_helper():
    """Show DHCP_Relay helper information"""
    pass

@dhcp_relay_helper.command('ipv6')
def get_dhcpv6_helper_address():
    """Parse through DHCP_RELAY table for each interface in config_db.json and print dhcpv6 helpers in table format"""
    config_db = ConfigDBConnector()
    if config_db is not None:
        config_db.connect()
        table_data = config_db.get_table(DHCP_RELAY)
        if table_data is not None:
            vlans = config_db.get_keys(DHCP_RELAY)
            for vlan in vlans: 
                vlan_data = table_data.get(vlan)
                helpers_data = vlan_data.get('dhcpv6_servers')
                if helpers_data is not None:
                    addr = {vlan:[]}
                    for ip in helpers_data.split(','):
                        addr[vlan].append(ip)
                print(tabulate({'Interface':[vlan], vlan:addr.get(vlan)}, tablefmt='simple', stralign='right') + '\n')

def register(cli):
    cli.add_command(dhcp_relay_helper)

if __name__ == '__main__':
    dhcp_relay_helper()
    