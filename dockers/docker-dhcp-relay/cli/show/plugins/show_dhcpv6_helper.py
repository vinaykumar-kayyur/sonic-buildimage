import click
from tabulate import tabulate
from swsscommon.swsscommon import ConfigDBConnector

import utilities_common.cli as clicommon

DHCP_RELAY = 'DHCP_RELAY'

@click.group(cls=clicommon.AliasedGroup, name="dhcp_relay_helper")
def dhcp_relay_helper():
    """Show DHCP_Relay helper information"""
    pass

@dhcp_relay_helper.command('ip')
def get_dhcpv6_helper_address():
    config_db = ConfigDBConnector()
    if config_db is not None:
        config_db.connect()
        table_data = config_db.get_table(DHCP_RELAY)
        if table_data is not None:
            for vlan in config_db.get_keys(DHCP_RELAY):
                vlan_data = table_data.get(vlan)
                helpers_data = vlan_data.get('dhcpv6_server')
                if helpers_data is not None:
                    addr = {vlan:[]}
                    for ip in helpers_data.split(','):
                        addr[vlan].append(ip)
                print(tabulate({'Interface':[vlan], vlan:addr.get(vlan)}, tablefmt='simple', stralign='right') + '\n')

def register(cli):
    cli.commands['dhcp_relay_helper'].add_command(dhcp_relay_helper)