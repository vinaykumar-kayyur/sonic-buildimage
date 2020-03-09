#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import sys
import syslog
import ipaddress
from swsssdk import ConfigDBConnector

APP_MGMT_INTF_TABLE = "MGMT_INTF_TABLE"

def update_dhcp_mgmt_ip_info():
    app_db = ConfigDBConnector()
    app_db.db_connect('APPL_DB', wait_for_init=False, retry_on=True)
    appdb_entry = {}
    appdb_entry["NULL"] = "NULL"

    op = sys.argv[2]
    plen = ipaddress.ip_network((0, sys.argv[4])).prefixlen
    key = sys.argv[1] + ":" + sys.argv[3] + "/" + str(plen)
    syslog.syslog(syslog.LOG_INFO, "update_dhcp_mgmt_ip_info : op -  {}, key - {}".format(op, key))
    if op == "add":
        app_db.set_entry(APP_MGMT_INTF_TABLE, key, appdb_entry)
    elif op == "del":
        app_db.delete_entry(APP_MGMT_INTF_TABLE, key)
    return

if __name__ == "__main__":
    if len(sys.argv) < 5:
        syslog.syslog(syslog.LOG_INFO, "number of arguments not correct")
        syslog.syslog(syslog.LOG_INFO, "usage:")
        syslog.syslog(syslog.LOG_INFO, "dhcp_mgmt_conf.py <add/del> <interface name> <ip address> <subnet mask>")
    else:
        syslog.syslog(syslog.LOG_INFO, "Args : {}".format(sys.argv))
        update_dhcp_mgmt_ip_info()
