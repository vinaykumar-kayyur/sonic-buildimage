import click
import utilities_common.cli as clicommon

import ipaddress


@click.group(cls=clicommon.AbbreviationGroup, name="dhcp_server")
def dhcp_server():
    """config DHCP Server information"""
    pass


@dhcp_server.group(cls=clicommon.AliasedGroup)
def ipv4():
    """Show ipv4 related dhcp_server info"""
    pass


@dhcp_server.group(cls=clicommon.AliasedGroup)
def ipv6():
    """Show ipv6 related dhcp_server info"""
    pass


def sanity_check_add(mode, lease_time, infer_gw_nm, gateway, netmask, dhcp_interface):
    if mode != "PORT":
        raise Exception("Only mode PORT is supported")
    if not lease_time.isdigit():
        raise Exception("lease_time is required and must be nonnegative integer")
    if not inter_gw_nm:
        ipaddress.ip_address(gateway)
        ipaddress.ip_address(netmask)


def infer_param_for_add(dhcp_interface):
    pass


@ipv4.command()
@click.argument("dhcp_interface", required=True)
@click.option("--mode", required=True)
@click.option("--lease_time", required=False, default="900")
@click.option("--infer_gw_nm", required=False, default=False, is_flag=True)
@click.option("--gateway", required=False)
@click.option("--netmask", required=False)
@clicommon.pass_db
def add(db, mode, lease_time, infer_gw_nm, gateway, netmask, dhcp_interface):
    sanity_check_add(mode, lease_time, infer_gw_nm, gateway, netmask, dhcp_interface):
    if infer_gw_nm:
        gateway, netmask = infer_param_for_add(dhcp_interface)
    dbconn = db.db
    key = "DHCP_SERVER_IPV4|" + dhcp_interface
    dbconn.hmset("CONFIG_DB", key, {
        "mode": mode,
        "lease_time": lease_time,
        "gateway": gateway,
        "netmask": netmask,
        "customized_options": "",
        "state": "disabled",
        })


@ipv6.command()
@click.argument("dhcp_interface", required=True)
@click.option("--mode", required=True)
@click.option("--lease_time", required=False, default="900")
@click.option("--infer_gw_nm", required=False, default=False, is_flag=True)
@click.option("--gateway", required=False)
@click.option("--netmask", required=False)
@clicommon.pass_db
def add(db, mode, lease_time, infer_gw_nm, gateway, netmask, dhcp_interface):
    pass


@ipv4.command()
@click.argument("dhcp_interface", required=True)
@clicommon.pass_db
def del(db, dhcp_interface):
    dbconn = db.db
    key = "DHCP_SERVER_IPV4|" + dhcp_interface
    dbconn.delete("CONFIG_DB", key)


@ipv6.command()
@click.argument("dhcp_interface", required=True)
@clicommon.pass_db
def del(db, dhcp_interface):
    pass


@ipv4.command()
@click.argument("dhcp_interface", required=True)
@clicommon.pass_db
def enable(db, dhcp_interface):
    dbconn = db.db
    key = "DHCP_SERVER_IPV4|" + dhcp_interface
    dbconn.set("CONFIG_DB", key, "state", "enabled")


@ipv6.command()
@click.argument("dhcp_interface", required=True)
@clicommon.pass_db
def enable(db, dhcp_interface):
    pass


@ipv4.command()
@click.argument("dhcp_interface", required=True)
@clicommon.pass_db
def disable(db, dhcp_interface):
    dbconn = db.db
    key = "DHCP_SERVER_IPV4|" + dhcp_interface
    dbconn.set("CONFIG_DB", key, "state", "disabled")


@ipv6.command()
@click.argument("dhcp_interface", required=True)
@clicommon.pass_db
def disable(db, dhcp_interface):
    pass


@ipv4.command()
@clicommon.pass_db
def update(db):
    pass


@ipv6.command()
@clicommon.pass_db
def update(db):
    pass


@ipv4.group(cls=clicommon.AliasedGroup)
def range():
    pass


@range.command()
@click.argument("range_name", required=True)
@click.argument("ip_start", required=True)
@click.argument("ip_end", required=False)
@clicommon.pass_db
def add(db, range_name, ip_start, ip_end):
    if not ip_end:
        ip_end = ip_start
    ipaddress.ip_address(ip_start)
    ipaddress.ip_address(ip_end)
    dbconn = db.db
    key = "DHCP_SERVER_IPV4_RANGE|" + range_name
    db.hmset("CONFIG_DB", key, {"ranges": ip_start + "," + ip_end})


@range.command()
@click.argument("range_name", required=True)
@click.argument("ip_start", required=True)
@click.argument("ip_end", required=False)
@clicommon.pass_db
def update(db, range_name, ip_start, ip_end):
    if not ip_end:
        ip_end = ip_start
    ipaddress.ip_address(ip_start)
    ipaddress.ip_address(ip_end)
    dbconn = db.db
    key = "DHCP_SERVER_IPV4_RANGE|" + range_name
    db.hmset("CONFIG_DB", key, {"ranges": ip_start + "," + ip_end})


@range.command()
@click.argument("range_name", required=True)
@clicommon.pass_db
def del(db, range_name)
    dbconn = db.db
    key = "DHCP_SERVER_IPV4_RANGE|" + range_name
    db.delete("CONFIG_DB", key)


@ipv6.group(cls=clicommon.AliasedGroup)
def range():
    pass


@range.command()
@click.argument("range_name", required=True)
@click.argument("ip_start", required=True)
@click.argument("ip_end", required=False)
@clicommon.pass_db
def add(db, range_name, ip_start, ip_end):
    pass


@range.command()
@click.argument("range_name", required=True)
@click.argument("ip_start", required=True)
@click.argument("ip_end", required=False)
@clicommon.pass_db
def update(db, range_name, ip_start, ip_end):
    pass


@range.command()
@click.argument("range_name", required=True)
@clicommon.pass_db
def del(db, range_name)
    pass


@ipv4.group(cls=clicommon.AliasedGroup)
def ip():
    pass


@ip.command()
@click.argument("vlan_interface", required=True)
@click.argument("interface", required=True)
@click.options("--range", required=False, nargs=-1)
@click.argument("ip_list", required=False, nargs=-1)
@clicommon.pass_db
def bind(db, vlan_interface, interface, range_, ip_list):
    dbconn = db.db
    key = "DHCP_SERVER_IPV4_PORT|" + vlan_interface + "|" + interface
    if range_:
        dbconn.hmset("CONFIG_DB", key, {"ranges": ",".join(range_)})
    elif ip_list:
        dbconn.hmset("CONFIG_DB", key, {"ips": ",".join(ip_list)})
    else:
        raise Exception("One of range and ip_list should be provided")


@ip.command()
@click.argument("vlan_interface", required=True)
@click.argument("interface", required=True)
@click.options("--range", required=False, nargs=-1)
@click.argument("ip_list", required=False, nargs=-1)
@clicommon.pass_db
def unbind(db, vlan_interface, interface, range_, ip_list):
    pass


@ipv6.group(cls=clicommon.AliasedGroup)
def ip():
    pass


@ip.command()
@click.argument("vlan_interface", required=True)
@click.argument("interface", required=True)
@click.options("--range", required=False, nargs=-1)
@click.argument("ip_list", required=False, nargs=-1)
@clicommon.pass_db
def bind(db, vlan_interface, interface, range_, ip_list):
    pass


@ip.command()
@click.argument("vlan_interface", required=True)
@click.argument("interface", required=True)
@click.options("--range", required=False, nargs=-1)
@click.argument("ip_list", required=False, nargs=-1)
@clicommon.pass_db
def unbind(db, vlan_interface, interface, range_, ip_list):
    pass


@ipv4.group(cls=clicommon.AliasedGroup)
def option():
    pass


@option.command()
@click.argument("option_name", required=True)
@click.argument("option_id", required=True)
@click.argument("type", required=True)
@click.argument("value", required=True)
@clicommon.pass_db
def add(db, option_name, option_id, type_, value):
    assert option_id.isdigit()
    assert type_ == "string"
    dbconn = db.db
    key = "DHCP_SERVER_IPV4_CUSTOMIZED_OPTIONS|" + option_name
    dbconn.hmset("CONFIG_DB", key, {
        "option_id": option_id,
        "type": type_,
        "value": value,
        })


@option.command()
@click.argument("option_name", required=True)
@clicommon.pass_db
def del(db, option_name):
    dbconn = db.db
    key = "DHCP_SERVER_IPV4_CUSTOMIZED_OPTIONS|" + option_name
    dbconn.delete("CONFIG_DB", key)


@option.command()
@click.argument("dhcp_interface", required=True)
@click.argument("option_list", nargs=-1)
@clicommon.pass_db
def bind(db, dhcp_interface, option_list):
    dbconn = db.db
    key = "DHCP_SERVER_IPV4|" + dhcp_interface
    if dbconn.exists("CONFIG_DB", key) and option_list:
        old_value = dbconn.get("CONFIG_DB", key, "customized_options")
        if old_value:
            option_list = [old_value] + option_list
        dbconn.set("CONFIG_DB", key, "customized_options", ",".join(option_list))


@option.command()
@click.argument("dhcp_interface", required=True)
@click.argument("option_list", nargs=-1)
@click.option("--all", required=False, default=False, is_flag=True)
@clicommon.pass_db
def unbind(db, dhcp_interface, option_list, all_):
    dbconn = db.db
    key = "DHCP_SERVER_IPV4|" + dhcp_interface
    if all_:
        dbconn.set("CONFIG_DB", key, "customized_options", "")
    else:
        old_options = dbconn.get("CONFIG_DB", key, "customized_options")
        option_set = set(old_options.split(","))
        new_option_set = option_set - set(option_list)
        new_options = ",".join(new_option_set)
        dbconn.set("CONFIG_DB", key, "customized_options", new_options)


@ipv6.group(cls=clicommon.AliasedGroup)
def option():
    pass


@option.command()
@click.argument("option_name", required=True)
@click.argument("option_id", required=True)
@click.argument("type", required=True)
@click.argument("value", required=True)
@clicommon.pass_db
def add(db, option_name, option_id, type_, value):
    pass


@option.command()
@click.argument("option_name", required=True)
@clicommon.pass_db
def del(db, option_name):
    pass


@option.command()
@click.argument("dhcp_interface", required=True)
@click.argument("option_list", nargs=-1)
@clicommon.pass_db
def bind(db, dhcp_interface, option_list):
    pass


@option.command()
@click.argument("dhcp_interface", required=True)
@click.argument("option_list", nargs=-1)
@click.option("--all", required=False, default=False, is_flag=True)
@clicommon.pass_db
def unbind(db, dhcp_interface, option_list, all_):
    pass


def register(cli):
    # cli.add_command(dhcp_server)
    pass


if __name__ == '__main__':
    dhcp_server()
