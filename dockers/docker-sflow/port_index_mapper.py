#!/usr/bin/env python3

""" port_index_mapper
    A mapper service that watches for NetLink NEWLINK and DELLINKs
    to construct a PORT_INDEX_TABLE in state DB which includes the
    interface name, the interface index and the ifindex.

    Note : Currently supports only interfaces supported by port_util.
"""

import os
import signal
import sys
import traceback

from pyroute2 import IPDB
from pyroute2.iproute import RTM_NEWLINK, RTM_DELLINK
from sonic_py_common.logger import Logger
from swsssdk import SonicV2Connector, port_util

PORT_INDEX_TABLE_NAME = 'PORT_INDEX_TABLE'
SYSLOG_IDENTIFIER = 'port_index_mapper'

ipdb = None
state_db = None

# Global logger instance
logger = Logger(SYSLOG_IDENTIFIER)
logger.set_min_log_priority_info()


def set_port_index_table_entry(key, index, ifindex):
    state_db.set(state_db.STATE_DB, key, 'index', index)
    state_db.set(state_db.STATE_DB, key, 'ifindex', ifindex)


def interface_callback(ipdb, nlmsg, action):
    global state_db

    try:
        msgtype = nlmsg['header']['type']
        if (msgtype != RTM_NEWLINK and msgtype != RTM_DELLINK):
            return

        # filter out unwanted messages
        change = nlmsg['change']
        if (change != 0xFFFFFFFF):
            return
    
        attrs = nlmsg['attrs']
        for list in attrs:
            if list[0] == 'IFLA_IFNAME':
                ifname = list[1]
                break
            else:
                return
    
        # Extract the port index from the interface name
        index = port_util.get_index_from_str(ifname)
        if index is None:
            return
    
        _hash = '{}|{}'.format(PORT_INDEX_TABLE_NAME, ifname)
    
        if msgtype == RTM_NEWLINK:
            set_port_index_table_entry(_hash, str(index), nlmsg['index'])
        elif msgtype == RTM_DELLINK:
            state_db.delete(state_db.STATE_DB, _hash)

    except Exception as e:
        t = sys.exc_info()[2]
        traceback.print_tb(t)
        logger.log_error(str(e))
        os.kill(os.getpid(), signal.SIGTERM)


def main():
    global state_db, ipdb
    state_db = SonicV2Connector(host='127.0.0.1', decode_responses=True)
    state_db.connect(state_db.STATE_DB, False)

    ipdb = IPDB()

    # Initialize the table at startup.
    ifnames = list(ipdb.by_name.keys())
    for ifname in ifnames:
        index = port_util.get_index_from_str(ifname)
        if index is None:
            continue
        ifindex = ipdb.interfaces[ifname]['index']
        _hash = '{}|{}'.format(PORT_INDEX_TABLE_NAME, ifname)
        set_port_index_table_entry(_hash, str(index), str(ifindex))

    ipdb.register_callback(interface_callback)

    signal.pause()


def signal_handler(signum, frame):
    logger.log_notice("got signal {}".format(signum))
    sys.exit(0)


if __name__ == '__main__':
    rc = 0
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        main()
    except Exception as e:
        t = sys.exc_info()[2]
        traceback.print_tb(t)
        logger.log_error(str(e))
        rc = -1
    finally:
        if ipdb is not None:
            ipdb.release()
        else:
            logger.log_error("ipdb undefined in signal_handler")

        sys.exit(rc)

