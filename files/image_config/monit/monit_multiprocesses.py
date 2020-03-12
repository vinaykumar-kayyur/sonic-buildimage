#!/usr/bin/python
'''
This script is used to monitor teamd process and dhcrelay process in teamd and dhcp_relay
docker container respectively. Since Monit can only monitor the process with unique name,
it is unable to do this monitoring for teamd and dhcrelay processes. Usually there will be
multiple teamd and dhcrelay processes which executes a same commad but with different arguments. 
The number of teamd processes is decided by the number of port channels in Config_DB and
the number of dhcrelay processes is determined by Vlans which have non-empry list of dhcp servers.
As such, we let Monit to monitor this script which will read number of port channles and
vlans with no-empty list of dhcp servers form Config_DB, then find whether there exist a 
process in Linux corresponding to a port channel or a vlan. If this script fails to find 
such process, it will write an alert message into syslog file.
'''

import os
import subprocess
import re
import sys
import syslog
import argparse

from swsssdk import ConfigDBConnector


def retrieve_portchannels():
    port_channels = []

    config_db = ConfigDBConnector()
    config_db.connect()
    port_channel_table = config_db.get_table('PORTCHANNEL')

    for key in port_channel_table.keys():
        port_channels.append(key)

    return port_channels

def check_teamd_process():
    port_channels = retrieve_portchannels()
    cmd = "sudo monit procmatch '/usr/bin/teamd -r -t '"
    cmd_res = subprocess.check_output(cmd, shell=True)
 
    for port_channel in port_channels:
        found_process = re.findall(port_channel, cmd_res)
        if len(found_process) == 0:
            syslog.syslog(syslog.LOG_ERR, "Teamd process with {} is not running.".format(port_channel))

def retrieve_vlans():
    vlans = []

    config_db = ConfigDBConnector()
    config_db.connect()
    vlan_table = config_db.get_table('VLAN')

    for vlan in vlan_table.keys():
        if vlan_table[vlan].has_key('dhcp_servers') and len(vlan_table[vlan]['dhcp_servers']) != 0:
            vlans.append(vlan)

    return vlans

def check_dhcp_relay_process():
    vlans = retrieve_vlans()
    cmd = "sudo monit procmatch '/usr/sbin/dhcrelay -d -m discard'"
    cmd_res = subprocess.check_output(cmd, shell=True)
    
    for vlan in vlans:
        found_process = re.findall(vlan, cmd_res)
        if len(found_process) == 0:
            syslog.syslog(syslog.LOG_ERR, "dhcrelay process with {} is not running.".format(vlan))

       
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--container-name')
    args = parser.parse_args()
    if args.container_name == '':
        syslog.syslog(syslog.LOG_ERR, "contianer name is not specified. Exiting...")
        sys.exit(1)

    if args.container_name == 'teamd':
        check_teamd_process()
    elif args.container_name == 'dhcp_relay':
        check_dhcp_relay_process()

if __name__ == '__main__':
    main()
