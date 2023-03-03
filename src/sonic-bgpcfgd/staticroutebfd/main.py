import os
import signal
import sys
import syslog
import threading
import traceback
from collections import defaultdict
from ipaddress import IPv4Address, IPv6Address

from swsscommon import swsscommon

g_debug = True
g_run = True

ROUTE_ADVERTISE_ENABLE_TAG = '1'
ROUTE_ADVERTISE_DISABLE_TAG = '2'

CONFIG_DB_NAME = "CONFIG_DB"
APPL_DB_NAME = "APPL_DB"
STATE_DB_NAME = "STATE_DB"

LOOPBACK_TABLE_NAME = "LOOPBACK_INTERFACE"
INTERFACE_TABLE_NAME = "INTERFACE"
PORTCHANNEL_INTERFACE_TABLE_NAME = "PORTCHANNEL_INTERFACE"
STATIC_ROUTE_TABLE_NAME = "STATIC_ROUTE"
BFD_SESSION_TABLE_NAME = "BFD_SESSION_TABLE"

LOCAL_CONFIG_TABLE = "config"
LOCAL_NEXTHOP_TABLE = "nexthop"
LOCAL_SR_TABLE = "sr"
LOCAL_BFD_TABLE = "bfd"
LOCAL_INTERFACE_TABLE = "interface"
LOCAL_LOOPBACK_TABLE = "loopback"

LOOPBACK0_NAME = "Loopback0"
LOOPBACK4096_NAME = "Loopback4096"

def log_debug(msg):
    """ Send a message msg to the syslog as DEBUG """
    if g_debug:
        syslog.syslog(syslog.LOG_DEBUG, msg)

def log_notice(msg):
    """ Send a message msg to the syslog as NOTICE """
    syslog.syslog(syslog.LOG_NOTICE, msg)

def log_info(msg):
    """ Send a message msg to the syslog as INFO """
    syslog.syslog(syslog.LOG_INFO, msg)

def log_warn(msg):
    """ Send a message msg to the syslog as WARNING """
    syslog.syslog(syslog.LOG_WARNING, msg)

def log_err(msg):
    """ Send a message msg to the syslog as ERR """
    syslog.syslog(syslog.LOG_ERR, msg)

def log_crit(msg):
    """ Send a message msg to the syslog as CRIT """
    syslog.syslog(syslog.LOG_CRIT, msg)

def signal_handler(_, __):  # signal_handler(signum, frame)
    """ signal handler """
    global g_run
    g_run = False

def static_route_split_key(key):
    """
    Split key into vrf name and prefix.
    :param key: key to split
    :return: valid, vrf name extracted from the key, ip prefix extracted from the key
    """
    l = tuple(key.split('|'))

    if len(l) == 1:
        return True, 'default', l[0]

    return True, l[0], l[1]

def check_ip(ip):
    if len(ip) == 0:
        return False, False, ""

    value = ip.split('/',1)
    v = value[0]
    try:
        IPv4Address(v)
        valid = True
        is_ipv4 = True
    except:
        is_ipv4 = False
        try:
            IPv6Address(v)
            valid = True
        except:
            valid = False
    return valid, is_ipv4, v

class StaticRouteBfd(object):

    SELECT_TIMEOUT = 1000
    BFD_DEFAULT_CFG = {"multihop": "true", "rx_interval": "600", "tx_interval": "600"}

    def __init__(self):
        self.local_db = defaultdict(dict)
        self.local_db[LOCAL_CONFIG_TABLE] = defaultdict(dict)
        self.local_db[LOCAL_NEXTHOP_TABLE] = defaultdict(set)
        self.local_db[LOCAL_SR_TABLE] = defaultdict(set)
        self.local_db[LOCAL_BFD_TABLE] = defaultdict(dict)
        #interface, portchannel_interface and loopback_interface share same table, assume name is unique
        #assume only one ipv4  and/or one ipv6 for each interface
        self.local_db[LOCAL_INTERFACE_TABLE] = defaultdict(dict)

        self.config_db  = swsscommon.DBConnector(CONFIG_DB_NAME, 0, True)
        self.appl_db = swsscommon.DBConnector(APPL_DB_NAME, 0, True)
        self.state_db = swsscommon.DBConnector(STATE_DB_NAME, 0, True)

        self.bfd_appl_tbl = swsscommon.ProducerStateTable(self.appl_db, BFD_SESSION_TABLE_NAME)

        self.static_route_appl_tbl = swsscommon.Table(self.appl_db, STATIC_ROUTE_TABLE_NAME)

        #to use SonicV2Connector get_all method, DBConnector doesn't have get_all
        self.db = swsscommon.SonicV2Connector()
        self.db.connect(self.db.CONFIG_DB)
        self.db.connect(self.db.APPL_DB)
        self.db.connect(self.db.STATE_DB)

        self.selector = swsscommon.Select()
        self.callbacks = defaultdict(lambda: defaultdict(list))  # db -> table -> handlers[]
        self.subscribers = set()
        self.first_time = True

    def get_ip_from_key(self, key):
        """
        Get ip address from key for LOOPBACK/INTERFACE/PORTCHANNEL_INTERFACE table
        :param key: key in the tables
        :return: valid, is_ipv4, ip address
        """
        if '|' not in key:
            return False, False, "", ""
        else:
            if_ip = key.split('|')
            if len(if_ip) < 2:
                return False, False, "", ""
            if_name = if_ip[0]
            value = if_ip[1]
            valid, is_ipv4, ip = check_ip(value)
            log_debug("get ip from intf key: valid %s is_ipv4 %s, if_name %s ip %s"%(str(valid), str(is_ipv4), if_name, ip))
            return valid, is_ipv4, if_name, ip

    def set_local_db(self, table, key, data):
        try:
            self.local_db[table][key] = data
            return
        except:
            log_err("set_local_db error, table %s key %s"%(table, key))
            pass

    def get_local_db(self, table, key):
        #FIXME how to handle key does not exist case, to add item
        try:
            v = self.local_db[table][key]
            return v
        except:
            return {}

    def remove_from_local_db(self, table, key):
        if table in self.local_db:
            if key in self.local_db[table]:
                del self.local_db[table][key]

    def append_to_nh_table_entry(self, nh_key, ip_prefix):
        #FIXME consider first time adding nh_key
        entry = self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key)
        entry.add(ip_prefix)

    def remove_from_nh_table_entry(self, nh_key, ip_prefix):
        entry = self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key)
        if ip_prefix in entry:
            entry.remove(ip_prefix)
            if len(entry) == 0:
                self.remove_from_local_db(LOCAL_NEXTHOP_TABLE, nh_key)

    def set_bfd_session_into_appl_db(self, key, data):
        fvs = swsscommon.FieldValuePairs(list(data.items()))
        self.bfd_appl_tbl.set(key, fvs)
        log_debug("set bfd session to appl_db, key %s, data %s"%(key, str(data)))

    def del_bfd_session_from_appl_db(self, key):
        self.bfd_appl_tbl.delete(key)

    def interface_set_handler(self, key, data):
        valid, is_ipv4, if_name, ip = self.get_ip_from_key(key)
        if not valid:
            return True
        value = self.get_local_db(LOCAL_INTERFACE_TABLE, if_name)
        if len(value) == 0:
            value = {is_ipv4: ip}
        else:
            value[is_ipv4] = ip
        self.set_local_db(LOCAL_INTERFACE_TABLE, if_name, value)
        return True

    def interface_del_handler(self, key):
        valid, is_ipv4, if_name, ip = self.get_ip_from_key(key)
        if not valid:
            return True
        value = self.get_local_db(LOCAL_INTERFACE_TABLE, if_name)
        if len(value) == 0:
            return
        else:
            value[is_ipv4] = ""  #remove the IP address for the interface
        self.set_local_db(LOCAL_INTERFACE_TABLE, if_name, value)

    def find_interface_ip(self, if_name, ip_example):
        valid, is_ipv4, nh = check_ip(ip_example)
        if not valid:
            return False, ""

        value = self.get_local_db(LOCAL_INTERFACE_TABLE, if_name)
        ip = value.get(is_ipv4, "")
        if len(ip)>0: #ip should be verified when add to local_db
            return True, ip

        #if there is no ip for the interface, try loopback ip address
        value = self.get_local_db(LOCAL_INTERFACE_TABLE, LOOPBACK4096_NAME)

        lp4096_ip = value.get(is_ipv4, "")
        if len(lp4096_ip)>0:
            return True, lp4096_ip
        value = self.get_local_db(LOCAL_INTERFACE_TABLE, LOOPBACK0_NAME)

        lp0_ip = value.get(is_ipv4, "")
        if len(lp0_ip)>0:
            return True, lp0_ip

        return False, ""

    def strip_table_name(self, key, splitter):
        return key.split(splitter, 1)[1]

    def reconciliation(self):
        #MUST keep the restore sequene
        #restore interface(loopback/interface/portchannel_interface) tables

        #restore interface tables
        log_info("restore interface table -->")
        keys = self.db.keys(self.db.CONFIG_DB, "LOOPBACK_INTERFACE|*")
        for key in keys:
            key_new = self.strip_table_name(key, "|")
            self.interface_set_handler(key_new, "")
        keys = self.db.keys(self.db.CONFIG_DB, "INTERFACE|*")
        for key in keys:
            key_new = self.strip_table_name(key, "|")
            self.interface_set_handler(key_new, "")
        keys = self.db.keys(self.db.CONFIG_DB, "PORTCHANNEL_INTERFACE|*")
        for key in keys:
            key_new = self.strip_table_name(key, "|")
            self.interface_set_handler(key_new, "")

        #restore bfd session table, static route won't create bfd session if it is already in appl_db
        log_info("restore bfd session table -->")
        keys = self.db.keys(self.db.APPL_DB, "BFD_SESSION_TABLE:*")
        for key in keys:
            data = self.db.get_all(self.db.APPL_DB, key)
            key_new = self.strip_table_name(key, ":")
            self.set_local_db(LOCAL_BFD_TABLE, key_new, data)

        #restore static route table
        log_info("restore static route table -->")
        keys = self.db.keys(self.db.CONFIG_DB, "STATIC_ROUTE|*")
        for key in keys:
            data = self.db.get_all(self.db.CONFIG_DB, key)
            key_new = self.strip_table_name(key, "|")
            self.static_route_set_handler(key_new, data)

        #clean up local bfd table, remove non static route bfd session
        log_info("cleanup bfd session table -->")
        self.cleanup_local_bfd_table()

        #restore bfd state table
        log_info("restore bfd state table -->")
        keys = self.db.keys(self.db.STATE_DB, "BFD_SESSION_TABLE|*")
        for key in keys:
            data = self.db.get_all(self.db.STATE_DB, key)
            key_new = self.strip_table_name(key, "|")
            self.bfd_state_set_handler(key_new, data)

    def cleanup_local_bfd_table(self):
        kl=[]
        for key in self.local_db[LOCAL_BFD_TABLE]:
            kl.append(key)
        for key in kl:
            bfd_session = self.local_db[LOCAL_BFD_TABLE][key]
            if "static_route" not in bfd_session or bfd_session["static_route"] != "true":
                self.local_db[LOCAL_BFD_TABLE].pop(key)

    def check_skip(self, bfd_enable):
        if isinstance(bfd_enable, list):
            if len(bfd_enable) == 1:
                if isinstance(bfd_enable[0], str):
                    if bfd_enable[0].lower() == "true":
                        return False
        return True

    def refresh_active_nh(self, route_cfg_key):
        data = self.get_local_db(LOCAL_CONFIG_TABLE, route_cfg_key)

        arg_list    = lambda v: v.split(',') if len(v.strip()) != 0 else None
        nh_list     = arg_list(data['nexthop']) if 'nexthop' in data else None
        nh_vrf_list = arg_list(data['nexthop-vrf']) if 'nexthop-vrf' in data else None

        for index in range(len(nh_list)):
            nh_ip = nh_list[index]
            nh_vrf = nh_vrf_list[index]
            nh_key = nh_vrf + "|" + nh_ip
            bfd_key = nh_vrf + ":default:" + nh_ip

            bfd_session = self.get_local_db(LOCAL_BFD_TABLE, bfd_key)
            if len(bfd_session) == 0:
                continue
            if "state" in bfd_session and bfd_session["state"].upper() == "UP":
                self.append_to_sr_table_entry(route_cfg_key, (nh_vrf, nh_ip))

        new_config = self.reconstruct_static_route_config(data, self.get_local_db(LOCAL_SR_TABLE, route_cfg_key))
        self.set_static_route_into_appl_db(route_cfg_key.replace("|", ":"), new_config)

    def static_route_set_handler(self, key, data):
        global ROUTE_ADVERTISE_ENABLE_TAG
        global ROUTE_ADVERTISE_DISABLE_TAG

        #sanity checking
        if len(data) == 0:
            return True

        valid, vrf, ip_prefix = static_route_split_key(key)
        route_cfg_key = vrf + "|" + ip_prefix
        if not valid:
            return True

        valid, is_ipv4, ip = check_ip(ip_prefix)
        if not valid:
            log_err("invalid ip prefix for static route: ", key)
            return True

        arg_list    = lambda v: v.split(',') if len(v.strip()) != 0 else None
        bfd_enable  = arg_list(data['bfd']) if 'bfd' in data else False
        # this process, staticroutebfd, only handle the bfd enabled case, other cases would be handled in bgpcfgd/StaticRouteMgr
        if self.check_skip(bfd_enable):
            return True

        bkh_list    = arg_list(data['blackhole']) if 'blackhole' in data else None
        nh_list     = arg_list(data['nexthop']) if 'nexthop' in data else None
        intf_list   = arg_list(data['ifname']) if 'ifname' in data else None
        dist_list   = arg_list(data['distance']) if 'distance' in data else None
        nh_vrf_list = arg_list(data['nexthop-vrf']) if 'nexthop-vrf' in data else None
        route_tag   = ROUTE_ADVERTISE_DISABLE_TAG if 'advertise' in data and data['advertise'] == "false" else ROUTE_ADVERTISE_ENABLE_TAG
        if nh_vrf_list is None:
            nh_vrf_list = [vrf] * len(nh_list) if len(nh_list) > 0 else None
            data['nexthop-vrf'] = ','.join(nh_vrf_list) if nh_vrf_list else ''
        if intf_list is None or nh_list is None or nh_vrf_list is None or \
                len(intf_list) != len(nh_list) or len(intf_list) != len(nh_vrf_list):
            log_err("Static route bfd set Failed, nexthop, interface and vrf lists do not match.")
            return True


        data_exist = self.get_local_db(LOCAL_CONFIG_TABLE, route_cfg_key)
        if data_exist:
            # route with the prefix already exist, remove the deleted nexthops
            nh_list_exist = arg_list(data_exist['nexthop']) if 'nexthop' in data else None
            nh_vrf_list_exist = arg_list(data_exist['nexthop-vrf']) if 'nexthop-vrf' in data else None
            if nh_vrf_list_exist is None:
                nh_vrf_list_exist = []
                for nh in nh_list:
                    nh_vrf_list_exist.append(vrf)

            intf_list_exist   = arg_list(data_exist['ifname']) if 'ifname' in data else None
            nh_key_list_exist = list(zip(nh_vrf_list_exist, intf_list_exist, nh_list_exist))
            nh_key_list_new = list(zip(nh_vrf_list, intf_list, nh_list))
            for nh in nh_key_list_exist:
                if nh not in nh_key_list_new:
                    nh_vrf = nh[0]
                    nh_ip = nh[2]
                    nh_key = nh_vrf + "|" + nh_ip
                    self.remove_from_sr_table_entry(route_cfg_key, (nh_vrf, nh_ip))
                    self.remove_from_nh_table_entry(nh_key, route_cfg_key)
                    if len(self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key)) == 0:
                        bfd_key = nh_vrf + ":default:" + nh_ip
                        self.remove_from_local_db(LOCAL_BFD_TABLE, bfd_key)
                        self.del_bfd_session_from_appl_db(bfd_key)

        self.set_local_db(LOCAL_CONFIG_TABLE, route_cfg_key, data)
        for index in range(len(nh_list)):
            nh_ip = nh_list[index]
            intf = intf_list[index]
            nh_vrf = nh_vrf_list[index]
            nh_key = nh_vrf + "|" + nh_ip

            #check if the bfd session is already created
            bfd_key = nh_vrf  + ":default:" + nh_ip
            bfd_session = self.get_local_db(LOCAL_BFD_TABLE, bfd_key)
            if len(bfd_session)>0:
                self.local_db[LOCAL_BFD_TABLE][bfd_key]["static_route"] = "true"

            if len(self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key)) == 0 and len(bfd_session) == 0:
                valid, local_addr = self.find_interface_ip(intf, nh_ip)
                if not valid:
                    log_warn("cannot find ip for interface: %s" %intf)
                    continue
                bfd_entry_cfg = self.BFD_DEFAULT_CFG.copy()
                bfd_entry_cfg["local_addr"] = local_addr
                self.set_bfd_session_into_appl_db(bfd_key, bfd_entry_cfg)
                bfd_entry_cfg["static_route"] = "true"
                self.set_local_db(LOCAL_BFD_TABLE, bfd_key, bfd_entry_cfg)

            self.append_to_nh_table_entry(nh_key, vrf + "|" + ip_prefix)

        self.refresh_active_nh(route_cfg_key)

        return True

    def static_route_del_handler(self, key):
        valid, vrf, ip_prefix = static_route_split_key(key)
        if not valid:
            return True
        route_cfg_key = vrf + "|" + ip_prefix

        valid, is_ipv4, ip = check_ip(ip_prefix)
        if not valid:
            return True

        data = self.get_local_db(LOCAL_CONFIG_TABLE, route_cfg_key)
        if len(data) == 0:
            # this route is not handled by StaticRouteBfd, skip
            return True

        arg_list    = lambda v: v.split(',') if len(v.strip()) != 0 else None
        nh_list     = arg_list(data['nexthop']) if 'nexthop' in data else None
        nh_vrf_list = arg_list(data['nexthop-vrf']) if 'nexthop-vrf' in data else None
        for index in range(len(nh_list)):
            nh_ip = nh_list[index]
            nh_vrf = nh_vrf_list[index]
            nh_key = nh_vrf + "|" + nh_ip
            self.remove_from_nh_table_entry(nh_key, route_cfg_key)

            if len(self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key)) == 0:
                bfd_key = nh_vrf + ":default:" + nh_ip
                self.remove_from_local_db(LOCAL_BFD_TABLE, bfd_key)
                self.del_bfd_session_from_appl_db(bfd_key)

        self.del_static_route_from_appl_db(route_cfg_key.replace("|", ":"))
        self.remove_from_local_db(LOCAL_INTERFACE_TABLE, route_cfg_key)

        return True

    def interface_callback(self, key, op, data):
        if op == swsscommon.SET_COMMAND:
            self.interface_set_handler(key, data)
        elif op == swsscommon.DEL_COMMAND:
            self.interface_del_handler(key)
        else:
            log_err("Invalid operation '%s' for key '%s'" % (op, key))

    def static_route_callback(self, key, op, data):
        global ROUTE_ADVERTISE_ENABLE_TAG
        global ROUTE_ADVERTISE_DISABLE_TAG
        ROUTE_ADVERTISE_ENABLE_TAG = '1'
        ROUTE_ADVERTISE_DISABLE_TAG = '2'

        if op == swsscommon.SET_COMMAND:
            self.static_route_set_handler(key, data)
        elif op == swsscommon.DEL_COMMAND:
            self.static_route_del_handler(key)
        else:
            log_err("Invalid operation '%s' for key '%s'" % (op, key))

    def bfd_state_split_key(self, key):
        """
        Split key into table name, vrf name, interface name and peer ip.
        :param key: key to split
        :return: table name, vrf name, interface name and peer ip extracted from the key
        """
        if key.count("|") < 2:
            return 'default', 'default', key
        else:
            return tuple(key.split('|'))

    def append_to_sr_table_entry(self, sr_key, nh_info):
        entry = self.get_local_db(LOCAL_SR_TABLE, sr_key)
        entry.add(nh_info)

    def remove_from_sr_table_entry(self, sr_key, nh_info):
        entry = self.get_local_db(LOCAL_SR_TABLE, sr_key)
        if nh_info in entry:
            entry.remove(nh_info)
            if len(entry) == 0:
                self.remove_from_local_db(LOCAL_SR_TABLE, sr_key)

    def set_static_route_into_appl_db(self, key, data):
        fvs = swsscommon.FieldValuePairs(list(data.items()))
        self.static_route_appl_tbl.set(key, fvs)
        log_debug("set static route to appl_db, key %s, data %s"%(key, str(data)))

    def del_static_route_from_appl_db(self, key):
        self.static_route_appl_tbl.delete(key)

    def reconstruct_static_route_config(self, original_config, reachable_nexthops):
        arg_list    = lambda v: v.split(',') if len(v.strip()) != 0 else None
        bkh_list    = arg_list(original_config['blackhole']) if 'blackhole' in original_config else None
        nh_list     = arg_list(original_config['nexthop']) if 'nexthop' in original_config else None
        intf_list   = arg_list(original_config['ifname']) if 'ifname' in original_config else None
        dist_list   = arg_list(original_config['distance']) if 'distance' in original_config else None
        nh_vrf_list = arg_list(original_config['nexthop-vrf']) if 'nexthop-vrf' in original_config else None

        bkh_candidate = ""
        nh_candidate = ""
        intf_candidate = ""
        dist_candidate = ""
        nh_vrf_candidate = ""


        for i in range(len(nh_list)):
            if (nh_vrf_list[i], nh_list[i]) in reachable_nexthops:
                bkh_candidate += "," + (bkh_list[i] if bkh_list else "")
                nh_candidate += "," + (nh_list[i] if nh_list else "")
                intf_candidate += "," + (intf_list[i] if intf_list else "")
                dist_candidate += "," + (dist_list[i] if dist_list else "")
                nh_vrf_candidate += "," + (nh_vrf_list[i] if nh_vrf_list else "")

        new_config = dict()
        for key in original_config:
            if key == "bfd":
                continue
            if key == "blackhole":
                new_config[key] = bkh_candidate[1:]
            elif key == "nexthop":
                new_config[key] = nh_candidate[1:]
            elif key == "ifname":
                new_config[key] = intf_candidate[1:]
            elif key == "distance":
                new_config[key] = dist_candidate[1:]
            elif key == "nexthop-vrf":
                new_config[key] = nh_vrf_candidate[1:]
            else:
                new_config[key] = original_config[key]
        new_config["expiry"] = "false"

        return new_config


    def bfd_state_set_handler(self, key, data):
        #key are diff in state db and appl_db,
        #intf is always default for multihop bfd
        vrf, intf, peer_ip = self.bfd_state_split_key(key)
        bfd_key = vrf + ":" + intf + ":" + peer_ip

        #check if the BFD session is in local table
        bfd_session = self.get_local_db(LOCAL_BFD_TABLE, bfd_key)
        if len(bfd_session) == 0:
            return True

        nh_key = vrf + "|" + peer_ip
        state = data['state'] if 'state' in data else "DOWN"
        log_info("bfd seesion %s state %s" %(bfd_key, state))

        self.local_db[LOCAL_BFD_TABLE][bfd_key]["state"] = state

        if state.upper() == "UP":
            for prefix in self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key):
                sr_key =  prefix
                config_key =  prefix
                self.append_to_sr_table_entry(sr_key, (vrf, peer_ip))
                config_data = self.get_local_db(LOCAL_CONFIG_TABLE, config_key)
                new_config = self.reconstruct_static_route_config(config_data, self.get_local_db(LOCAL_SR_TABLE, sr_key))
                self.set_static_route_into_appl_db(sr_key.replace("|", ":"), new_config)

        elif state.upper() == "DOWN":
            for prefix in self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key):
                sr_key =  prefix
                config_key =  prefix
                self.remove_from_sr_table_entry(sr_key, (vrf, peer_ip))
                if len(self.get_local_db(LOCAL_SR_TABLE, sr_key)) == 0:
                    self.del_static_route_from_appl_db(sr_key.replace("|", ":"))
                else:
                    config_data = self.get_local_db(LOCAL_CONFIG_TABLE, config_key)
                    new_config = self.reconstruct_static_route_config(config_data, self.get_local_db(LOCAL_SR_TABLE, sr_key))
                    self.set_static_route_into_appl_db(sr_key.replace("|", ":"), new_config)


    def bfd_state_del_handler(self, key):
        vrf, intf, peer_ip = self.bfd_state_split_key(key)
        bfd_key = vrf + ":" + intf + ":" + peer_ip

        nh_key = vrf + "|" + peer_ip

        for prefix in self.get_local_db(LOCAL_NEXTHOP_TABLE, nh_key):
            sr_key =  prefix
            config_key = prefix
            self.remove_from_sr_table_entry(sr_key, (vrf, peer_ip))
            if len(self.get_local_db(LOCAL_SR_TABLE, sr_key)) == 0:
                self.del_static_route_from_appl_db(sr_key.replace("|", ":"))
            else:
                config_data = self.get_local_db(LOCAL_CONFIG_TABLE, config_key)
                new_config = self.reconstruct_static_route_config(config_data, self.get_local_db(LOCAL_SR_TABLE, sr_key))
                self.set_static_route_into_appl_db(sr_key.replace("|", ":"), new_config)

    def bfd_state_callback(self, key, op, data):
        if op == swsscommon.SET_COMMAND:
            self.bfd_state_set_handler(key, data)
        elif op == swsscommon.DEL_COMMAND:
            self.bfd_state_del_handler(key)
        else:
            log_err("Invalid operation '%s' for key '%s'" % (op, key))


    def prepare_selector(self):
        interface_subscriber = swsscommon.SubscriberStateTable(self.config_db, INTERFACE_TABLE_NAME)
        portchannel_interface_subscriber = swsscommon.SubscriberStateTable(self.config_db, PORTCHANNEL_INTERFACE_TABLE_NAME)
        static_route_subscriber = swsscommon.SubscriberStateTable(self.config_db, STATIC_ROUTE_TABLE_NAME)
        bfd_state_subscriber = swsscommon.SubscriberStateTable(self.state_db, swsscommon.STATE_BFD_SESSION_TABLE_NAME)

        self.selector.addSelectable(interface_subscriber)
        self.selector.addSelectable(portchannel_interface_subscriber)
        self.selector.addSelectable(static_route_subscriber)
        self.selector.addSelectable(bfd_state_subscriber)

        self.subscribers.add(interface_subscriber)
        self.subscribers.add(portchannel_interface_subscriber)
        self.subscribers.add(static_route_subscriber)
        self.subscribers.add(bfd_state_subscriber)

        self.callbacks[self.config_db.getDbId()][LOOPBACK_TABLE_NAME].append(self.interface_callback)
        self.callbacks[self.config_db.getDbId()][INTERFACE_TABLE_NAME].append(self.interface_callback)
        self.callbacks[self.config_db.getDbId()][PORTCHANNEL_INTERFACE_TABLE_NAME].append(self.interface_callback)
        self.callbacks[self.config_db.getDbId()][STATIC_ROUTE_TABLE_NAME].append(self.static_route_callback)
        self.callbacks[self.state_db.getDbId()][swsscommon.STATE_BFD_SESSION_TABLE_NAME].append(self.bfd_state_callback)

    def run(self):
        self.prepare_selector()
        while g_run:
            state, _ = self.selector.select(self.SELECT_TIMEOUT)
            if state == self.selector.TIMEOUT:
                continue
            elif state == self.selector.ERROR:
                raise Exception("Received error from select")

            if self.first_time:
                self.first_time = False
                self.reconciliation()

            for sub in self.subscribers:
                while True:
                    key, op, fvs = sub.pop()
                    if len(key) == 0:
                        break
                    log_debug("Received message : '%s'" % str((key, op, fvs)))
                    for callback in self.callbacks[sub.getDbConnector().getDbId()][sub.getTableName()]:
                        callback(key, op, dict(fvs))


def do_work():
    sr_bfd = StaticRouteBfd()
    sr_bfd.run()

def main():
    rc = 0
    try:
        syslog.openlog('staticroutebfd')
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        do_work()
    except KeyboardInterrupt:
        syslog.syslog(syslog.LOG_NOTICE, "Keyboard interrupt")
        pass
    except RuntimeError as exc:
        syslog.syslog(syslog.LOG_CRIT, str(exc))
        rc = -2
        if g_debug:
            raise
    except Exception as exc:
        syslog.syslog(syslog.LOG_CRIT, "Got an exception %s: Traceback: %s" % (str(exc), traceback.format_exc()))
        rc = -1
        if g_debug:
            raise
    finally:
        syslog.closelog()
    try:
        sys.exit(rc)
    except SystemExit:
        os._exit(rc)
