#!/usr/bin/env python

import signal
import sys
import syslog
import traceback
from ctypes import CDLL
from ctypes.util import find_library
from swsssdk import SonicV2Connector, port_util
from swsscommon import swsscommon

SYSLOG_IDENTIFIER = 'port_index_mapper'


class PortIndexMapper(object):

    def __init__(self):
        REDIS_TIMEOUT_MS = 0
        # Update this list to support more interfaces
        tbl_lst = [swsscommon.STATE_PORT_TABLE_NAME,
                   swsscommon.STATE_VLAN_TABLE_NAME]
        self.appl_db = swsscommon.DBConnector("STATE_DB",
                                              REDIS_TIMEOUT_MS,
                                              True)

        self.state_db = SonicV2Connector(host='127.0.0.1')
        self.state_db.connect(self.state_db.STATE_DB, False)
        self.sel = swsscommon.Select()
        self.tlbs = [swsscommon.SubscriberStateTable(self.appl_db, t)
                     for t in tbl_lst]

        self.cur_interfaces = {}
        self.libc = CDLL(find_library('c'))

        for t in self.tlbs:
            self.sel.addSelectable(t)

    def ifname_to_index(self, ifname):
        ret = self.libc.if_nametoindex(ifname)
        return ret if ret else None

    def set_port_index_table_entry(self, key, index, ifindex):
        self.state_db.set(self.state_db.STATE_DB, key, 'index', index)
        self.state_db.set(self.state_db.STATE_DB, key, 'ifindex', ifindex)

    def update_db(self, ifname, op):
        index = port_util.get_index_from_str(ifname)
        if op == 'SET' and index is None:
            return
        ifindex = self.ifname_to_index(ifname)
        if op == 'SET' and ifindex is None:
            return

        # Check if ifname already exist or if index/ifindex changed due to
        # syncd restart

        if (ifname in self.cur_interfaces and
                self.cur_interfaces[ifname] == (index, ifindex)):
            return

        _hash = '{}|{}'.format('PORT_INDEX_TABLE', ifname)

        if op == 'SET':
            self.cur_interfaces[ifname] = (index, ifindex)
            self.set_port_index_table_entry(_hash, str(index), str(ifindex))
        elif op == 'DEL':
            del self.cur_interfaces[ifname]
            self.state_db.delete(self.state_db.STATE_DB, _hash)

    def listen(self):
        SELECT_TIMEOUT_MS = -1  # Infinite wait

        while True:
            (state, c) = self.sel.select(SELECT_TIMEOUT_MS)
            if state == swsscommon.Select.OBJECT:
                for t in self.tlbs:
                    (key, op, cfvs) = t.pop()
                    if op == 'DEL' and key in self.cur_interfaces:
                        self.update_db(key, op)
                    elif (op == 'SET' and key != 'PortInitDone' and
                            key not in self.cur_interfaces):
                        self.update_db(key, op)
            elif state == swsscomm.Select.ERROR:
                syslog.syslog(syslog.LOG_ERR, "Receieved error from select()")
                break

    def populate(self):
        SELECT_TIMEOUT_MS = 0

        while True:
            (state, c) = self.sel.select(SELECT_TIMEOUT_MS)
            if state == swsscommon.Select.OBJECT:
                for t in self.tlbs:
                    (key, op, cfvs) = t.pop()
                    if key and key != 'PortInitDone':
                        self.update_db(key, op)
            else:
                break


def signal_handler(signum, frame):
    syslog.syslog(syslog.LOG_NOTICE, "got signal %d" % signum)
    sys.exit(0)


def main():
    port_mapper = PortIndexMapper()
    port_mapper.populate()
    port_mapper.listen()

if __name__ == '__main__':
    rc = 0
    try:
        syslog.openlog(SYSLOG_IDENTIFIER)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        main()
    except Exception, e:
        tb = sys.exc_info()[2]
        traceback.print_tb(tb)
        syslog.syslog(syslog.LOG_CRIT, "%s" % str(e))
        rc = -1
    finally:
        syslog.closelog()
        sys.exit(rc)
