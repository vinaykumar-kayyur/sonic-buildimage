#!/usr/bin/python3

import argparse
import psutil
import os
import signal
import syslog
import time

from swsscommon.swsscommon import SubscriberStateTable, TableConsumable, Select
from swsscommon.swsscommon import DBConnector, Table, STATE_FDB_TABLE_NAME, APP_PORT_TABLE_NAME

from swsscommon import swsscommon

class DnsmasqStaticHostMonitor(object):

    def __init__(self, hosts_update_delay=300):
        self.appl_db = DBConnector("APPL_DB", 0)
        self.state_db = DBConnector("STATE_DB", 0)

        self.selector = Select()
        self.callbacks = dict()
        self.subscriber_map = dict()

        self.next_hosts_update = None
        self.hosts_update_delay = hosts_update_delay
        self.min_index = 1

        port_table = Table(self.appl_db, APP_PORT_TABLE_NAME)
        ports = port_table.getKeys()
        for port in ports:
            (status, index) = port_table.hget(port, "index")
            if not status:
                syslog.syslog(syslog.LOG_WARNING,
                        f"Unable to get port index for {port}")
                continue
            index = int(index)
            if self.min_index is None or index < self.min_index:
                self.min_index = index

    def new_host_update(self, key, op, data):
        current_time = time.clock_gettime(time.CLOCK_MONOTONIC)
        if self.next_hosts_update is None or current_time > self.next_hosts_update:
            self.update_static_dnsmasq_hosts_file()
        else:
            syslog.syslog(syslog.LOG_INFO | syslog.LOG_USER,
                    f"Not updating dnsmasq.hosts since the last update was within the last {self.hosts_update_delay} seconds")

    def update_static_dnsmasq_hosts_file(self):
        syslog.syslog(syslog.LOG_INFO | syslog.LOG_USER,
                "Updating dnsmasq.hosts with current MAC addresses")

        fdb_table = Table(self.state_db, STATE_FDB_TABLE_NAME)
        port_table = Table(self.appl_db, APP_PORT_TABLE_NAME)

        with open("/etc/dnsmasq.hosts", "w") as f:
            # Get all known MAC addresses
            vlan_mac_addresses = fdb_table.getKeys()
            for vlan_mac_address in vlan_mac_addresses:
                (vlan, mac_address) = vlan_mac_address.split(":", maxsplit=1)
                (status, port) = fdb_table.hget(vlan_mac_address, 'port')
                if not status:
                    continue

                # Get the index that corresponds to this ethernet port
                (status, port_index) = port_table.hget(port, 'index')
                port_index = int(port_index)
                if not status:
                    syslog.syslog(syslog.LOG_WARNING,
                            f"Unable to get port index for {port}")
                    continue

                # Write a host entry
                f.write(f"{mac_address},172.17.0.{(port_index - self.min_index) * 4 + 1},24h\n")

        # Update the next time we'll update /etc/dnsmasq.hosts
        current_time = time.clock_gettime(time.CLOCK_MONOTONIC)
        self.next_hosts_update = current_time + self.hosts_update_delay

        for proc in psutil.process_iter(['pid', 'name']):
           if proc.info["name"] == "dnsmasq":
               os.kill(proc.info["pid"], signal.SIGHUP)
               break

    def subscribe(self, db, table, callback, pri):
        try:
            if table not in self.callbacks:
                self.callbacks[table] = []
                subscriber = SubscriberStateTable(db, table, TableConsumable.DEFAULT_POP_BATCH_SIZE, pri)
                self.selector.addSelectable(subscriber) # Add to the Selector
                self.subscriber_map[subscriber.getFd()] = (subscriber, table) # Maintain a mapping b/w subscriber & fd

            self.callbacks[table].append(callback)
        except Exception as err:
            syslog.syslog(syslog.LOG_ERR, "Subscribe to table {} failed with error {}".format(table, err))

    def start(self):
        while True:
            select_timeout = 60
            state, selectable_ = self.selector.select(select_timeout)
            if state == self.selector.TIMEOUT:
                # Add a bit of a hack here where if we need to update the hosts file,
                # but there's no new change, then manually do the update here
                current_time = time.clock_gettime(time.CLOCK_MONOTONIC)
                if self.next_hosts_update is None or current_time >= self.next_hosts_update:
                    self.update_static_dnsmasq_hosts_file()
                continue
            elif state == self.selector.ERROR:
                syslog.syslog(syslog.LOG_ERR,
                        "error returned by select")
                continue

            fd = selectable_.getFd()
            # Get the Corresponding subscriber & table
            subscriber, table = self.subscriber_map.get(fd, (None, ""))
            if not subscriber:
                syslog.syslog(syslog.LOG_ERR,
                        "No Subscriber object found for fd: {}, subscriber map: {}".format(fd, subscriber_map))
                continue
            key, op, fvs = subscriber.pop()
            # Get the registered callback
            cbs = self.callbacks.get(table, None)
            for callback in cbs:
                callback(table, key, op, dict(fvs))

    def register_callbacks(self):
        #self.subscribe('KDUMP', lambda table, key, op, data: self.kdump_handler(key, op, data), HOSTCFGD_MAX_PRI)
        self.subscribe(self.state_db, "FDB_TABLE", lambda table, key, op, data: self.new_host_update(key, op, data), 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start a script to update /etc/dnsmasq.hosts with the currently-known MAC addresses.')
    parser.add_argument('--update-every', type=int, default=300, help='Set the frequency (in seconds) to update /etc/dnsmasq.hosts. (default: 300 seconds, or 5 minutes)')

    args = parser.parse_args()

    monitor = DnsmasqStaticHostMonitor(args.update_every)
    monitor.register_callbacks()
    monitor.update_static_dnsmasq_hosts_file()
    monitor.start()
