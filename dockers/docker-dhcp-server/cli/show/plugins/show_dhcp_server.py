import click
from tabulate import tabulate
from swsscommon.swsscommon import SonicV2Connector
import utilities_common.cli as clicommon


import ipaddress


@click.group(cls=clicommon.AliasedGroup)
def dhcp_server():
    """Show dhcp_server related info"""
    pass


@dhcp_server.group(cls=clicommon.AliasedGroup)
def ipv4():
    """Show ipv4 related dhcp_server info"""
    pass


@ipv4.command()
@click.argument('dhcp_interface', required=False)
@clicommon.pass_db
def lease(db, dhcp_interface):
    headers = ["Interface", "MAC Address", "IP", "Lease Start", "Lease End"]
    table = []
    dbconn = db.db
    for key in dbconn.keys("STATE_DB"):
        items = key.split("|")
        if len(items) != 3:
            continue
        if items[0] != "DHCP_SERVER_IPV4_LEASE":
            continue
        if dhcp_interface and items[1] != dhcp_interface:
            continue
        entry = dbconn.get_all("STATE_DB", key)
        interface = items[1]
        mac = items[2]
        port = dbconn.get("STATE_DB", "FDB_TABLE|" + interface + ":" + mac, "port")
        table.append([interface + "|" + port, mac, entry["ip"], entry["lease_start"], entry["lease_end"]])
    print(tabulate(table, headers=headers))


def register(cli):
    cli.add_command(dhcp_server)
