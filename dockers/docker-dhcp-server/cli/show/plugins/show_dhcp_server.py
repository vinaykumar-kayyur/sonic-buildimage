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
    if not dhcp_interface:
        dhcp_interface = ""
    headers = ["Interface", "MAC Address", "IP", "Lease Start", "Lease End"]
    table = []
    dbconn = db.db
    for key in dbconn.keys("STATE_DB"):
        if "DHCP_SERVER_IPV4_LEASE|" in key and dhcp_interface in key:
            entry = dbconn.get_all("STATE_DB", key)
            interface, mac = key.split("|")[1:]
            port = dbconn.get("STATE_DB", "FDB_TABLE|" + interface + ":" + mac, "port")
            table.append([interface + "|" + port, mac, entry["ip"], entry["lease_start"], entry["lease_end"]])
    print(tabulate(table, headers=headers))


def register(cli):
    cli.add_command(dhcp_server)
