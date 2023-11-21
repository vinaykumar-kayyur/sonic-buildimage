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


@dhcp_server.group(cls=clicommon.AliasedGroup)
def ipv6():
    """Show ipv6 related dhcp_server info"""
    pass


@ipv4.command()
@click.argument('dhcp_interface', required=False)
@clicommon.pass_db
def lease(db, dhcp_interface):
    if not dhcp_interface:
        dhcp_interface = ""
    headers = ["Interface", "MAC Address", "PORT", "IP", "Lease Start", "Lease End"]
    table = []
    dbconn = db.db
    for key in dbconn.keys("STATE_DB"):
        if "DHCP_SERVER_IPV4_LEASE|" in key and dhcp_interface in key:
            entry = dbconn.get_all("STATE_DB", key)
            interface, mac = key.split("|")[1:]
            port = dbconn.get("STATE_DB", "FDB_TABLE|"+interface+":"+mac, "port")
            table.append([interface, mac, port, entry["ip"], entry["lease_start"], entry["lease_end"]])
    print(tabulate(table, headers=headers))


@ipv6.command()
@click.argument('dhcp_interface', required=False)
@clicommon.pass_db
def lease(db, dhcp_interface):
    pass


def count_ipv4(start, end):
    ip1 = int(ipaddress.IPv4Address(start))
    ip2 = int(ipaddress.IPv4Address(end))
    return ip2 - ip1


def count_ipv6(start, end):
    ip1 = int(ipaddress.IPv6Address(start))
    ip2 = int(ipaddress.IPv6Address(end))
    return ip2 - ip1


@ipv4.command()
@click.argument('range_name', required=False)
@clicommon.pass_db
def range(db, range_name):
    if not range_name:
        range_name = ""
    headers = ["Range", "IP Start", "IP End", "IP Count"]
    table = []
    dbconn = db.db
    for key in dbconn.keys("CONFIG_DB"):
        if "DHCP_SERVER_IPV4_RANGE|" in key and range_name in key:
            entry = dbconn.get_all("CONFIG_DB", key)
            start, end = entry["ranges"].split(",")
            name = key.split("|")[1]
            table.append([name, start, end, count_ipv4(start, end)])
    print(tabulate(table, headers=headers))


@ipv6.command()
@click.argument('range_name', required=False)
@clicommon.pass_db
def range(db, range_name):
    pass


@ipv4.command()
@click.argument('dhcp_interface', required=False)
@click.option('--with_customized_options', default=False, is_flag=True)
@clicommon.pass_db
def info(db, dhcp_interface, with_customize_option):
    if not dhcp_interface:
        dhcp_interface = ""
    headers = ["Interface", "Mode", "Gateway", "Netmask", "Lease Time(s)", "IP Bind"]
    if with_customize_option:
        headers.append("Customize Option")
    table = []
    dbconn = db.db
    for key in dbconn.keys("CONFIG_DB"):
        if "DHCP_SERVER_IPV4|" in key and dhcp_interface in key:
            entry = dbconn.get_all("CONFIG_DB", key)
            interface = key.split("|")[1]
            table.append([interface, entry["mode"], entry["gateway"], entry["netmask"], entry["lease_time"], entry["state"]])
            if with_customize_option:
                table[-1].append(entry["customized_options"])
    print(tabulate(table, headers=headers))


@ipv6.command()
@click.argument('dhcp_interface', required=False)
@click.option('--with_customized_options', default=False, is_flag=True)
@clicommon.pass_db
def info(db, dhcp_interface, with_customize_option):
    pass


@ipv4.command()
@click.argument("option_name", required=False)
@clicommon.pass_db
def option(db, option_name):
    if not option_name:
        option_name = ""
    headers = ["Option Name", "Option", "Value", "Type"]
    table = []
    dbconn = db.db
    for key in dbconn.keys("CONFIG_DB"):
        if "DHCP_SERVER_IPV4_CUSTOMIZED_OPTIONS|" in key and option_name in key:
            entry = dbconn.get_all("CONFIG_DB", key)
            name = key.split("|")[1]
            table.append([name, entry["id"], entry["value"], entry["type"]])
    print(tabulate(table, headers=headers))


@ipv6.command()
@click.argument("option_name", required=False)
@clicommon.pass_db
def option(db, option_name):
    pass


def register(cli):
    cli.add_command(dhcp_server)
