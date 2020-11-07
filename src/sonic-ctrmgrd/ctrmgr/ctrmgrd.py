#!/usr/bin/python3 -u

import datetime
import inspect
import json
import os
import syslog

from collections import defaultdict

from swsscommon import swsscommon
from sonic_py_common import device_info

import kube_commands

# Kube config file
SONIC_CTR_CONFIG = "/etc/sonic/remote_ctr.config.json"

CONFIG_DB_NAME = "CONFIG_DB"
STATE_DB_NAME = "STATE_DB"

# DB SERVER
SERVER_TABLE = "KUBERNETES_MASTER"
SERVER_KEY = "SERVER"
CFG_SER_IP = "ip"
CFG_SER_PORT = "port"
CFG_SER_DISABLE = "disable"
CFG_SER_INSECURE = "insecure"

ST_SER_IP = "ip"
ST_SER_PORT = "port"
ST_SER_CONNECTED = "connected"
ST_SER_UPDATE_TS = "update_time"

# DB FEATURE
FEATURE_TABLE = "FEATURE"
CFG_FEAT_OWNER = "set_owner"
CFG_FEAT_NO_FALLBACK = "no_fallback_to_local"
CFG_FEAT_FAIL_DETECTION = "remote_fail_detection"

ST_FEAT_OWNER = "current_owner"
ST_FEAT_UPDATE_TS = "update_time"
ST_FEAT_CTR_ID = "container_id"
ST_FEAT_CTR_VER = "container_version"
ST_FEAT_REMOTE_STATE = "remote_state"
ST_FEAT_SYS_STATE = "system_state"

KUBE_LABEL_TABLE = "KUBE_LABELS"
KUBE_LABEL_SET_KEY = "SET"
KUBE_LABEL_UNSET_KEY = "UNSET"

remote_connected = False

dflt_cfg_ser = {
        CFG_SER_IP: "",
        CFG_SER_PORT: "6443",
        CFG_SER_DISABLE: "false",
        CFG_SER_INSECURE: "false"
        }

dflt_st_ser = {
        ST_SER_IP: "",
        ST_SER_PORT: "",
        ST_SER_CONNECTED: "",
        ST_SER_UPDATE_TS: ""
        }

dflt_cfg_feat= {
        CFG_FEAT_OWNER: "local",
        CFG_FEAT_NO_FALLBACK: "false",
        CFG_FEAT_FAIL_DETECTION: "300"
        }

dflt_st_feat= {
        ST_FEAT_OWNER: "none",
        ST_FEAT_UPDATE_TS: "",
        ST_FEAT_CTR_ID: "",
        ST_FEAT_CTR_VER: "",
        ST_FEAT_REMOTE_STATE: "none",
        ST_FEAT_SYS_STATE: ""
        }

JOIN_LATENCY = "join_latency_on_boot_seconds"
JOIN_RETRY = "retry_join_interval_seconds"
LABEL_RETRY = "retry_labels_update_seconds"

remote_ctr_config = {
    JOIN_LATENCY: 10,
    JOIN_RETRY: 10,
    LABEL_RETRY: 2
    }

def log_debug(m):
    msg = "{}: {}".format(inspect.stack()[1][3], m)
    # print(msg)
    syslog.syslog(syslog.LOG_DEBUG, msg)


def log_error(m):
    syslog.syslog(syslog.LOG_ERR, msg)


def log_info(m):
    syslog.syslog(syslog.LOG_INFO, msg)


def ts_now():
    return str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def is_systemd_active(feat):
    status = os.system('systemctl is-active --quiet {}'.format(feat))
    log_debug("system status for {}: {}".format(feat, str(status)))
    return status == 0


def restart_systemd_service(feat, owner):
    log_debug("Restart service {} to owner:{}".format(feat, owner))
    status = os.system("systemctl restart {}".format(feat))
    if status != 0:
        syslog.syslog(syslog.LOG_ERR,
                "Failed to restart {} to switch to {}".format(feat, owner))
    else:
        syslog.syslog(syslog.LOG_INFO,
                "Restarted {} to switch to {}".format(feat, owner))
    return status


def init():
    if os.path.exists(SONIC_CTR_CONFIG):
        with open(SONIC_CTR_CONFIG, "r") as s:
            d = json.load(s)
            remote_ctr_config.update(d)


class MainServer:
    """ Implements main io-loop of the application
        Accept handler registration per db/table.
        Call handler on update
    """

    SELECT_TIMEOUT = 1000

    def __init__(self):
        """ Constructor """
        self.db_connectors = {}
        self.selector = swsscommon.Select()
        self.callbacks = defaultdict(lambda: defaultdict(list))  # db -> table -> handlers[]
        self.timer_handlers = defaultdict(list)
        self.subscribers = set()

    def register_db(self, db_name):
        """ Get DB connector, if not there """
        if db_name not in self.db_connectors:
            self.db_connectors[db_name] = swsscommon.DBConnector(db_name, 0)


    def register_timer(self, ts, handler):
        """ Register timer based handler. 
            The handler will be called on/after give timestamp, ts
        """
        self.timer_handlers[ts].append(handler)


    def register_handler(self, db_name, table_name, handler):
        """
        Handler registration for any update in given table
        in given db. The handler will be called for any update
        to the table in this db.
        """
        self.register_db(db_name)

        if table_name not in self.callbacks[db_name]:
            conn = self.db_connectors[db_name]
            subscriber = swsscommon.SubscriberStateTable(conn, table_name)
            self.subscribers.add(subscriber)
            self.selector.addSelectable(subscriber)
        self.callbacks[db_name][table_name].append(handler)


    def get_db_entry(self, db_name, table_name, key):
        """ Return empty dict if key not present """
        conn = self.db_connectors[db_name]
        tbl = swsscommon.Table(conn, table_name)
        return dict(tbl.get(key)[1])


    def mod_db_entry(self, db_name, table_name, key, data):
        """ Modify entry for given table|key with given dict type data """
        conn = self.db_connectors[db_name]
        tbl = swsscommon.Table(conn, table_name)
        tbl.set(key, list(data.items()))


    def set_db_entry(self, db_name, table_name, key, data):
        """ Set given data as complete data, which includes 
            removing any fields that are in DB but not in data
        """
        conn = self.db_connectors[db_name]
        tbl = swsscommon.Table(conn, table_name)
        ct_data = dict(tbl.get(key)[1])
        for k in ct_data:
            if k not in data:
                # Drop fields that are not in data
                tbl.hdel(key, k)
        tbl.set(key, list(data.items()))


    def run(self):
        """ Main loop """
        while True:
            timeout = MainServer.SELECT_TIMEOUT
            ct_ts = datetime.datetime.now()
            while self.timer_handlers:
                k = sorted(self.timer_handlers.keys())[0]
                if k <= ct_ts:
                    lst = self.timer_handlers[k]
                    del self.timer_handlers[k]
                    for fn in lst:
                        fn()
                else:
                    timeout = (k - ct_ts).seconds
                    break

            state, _ = self.selector.select(timeout)
            if state == self.selector.TIMEOUT:
                continue
            elif state == self.selector.ERROR:
                raise Exception("Received error from select")

            for subscriber in self.subscribers:
                key, op, fvs = subscriber.pop()
                if not key:
                    continue
                log_debug("Received message : '%s'" % str((key, op, fvs)))
                for callback in (self.callbacks
                        [subscriber.getDbConnector().getDbName()]
                        [subscriber.getTableName()]):
                    callback(key, op, dict(fvs))


def update_labels(server, labels):
    """ Get current labels in DB.
        for given labels
            Add to SET/UNSET key based on value non-empty/empty
        Push the latest.
    """
    ct_set_labels = server.get_db_entry(STATE_DB_NAME,
            KUBE_LABEL_TABLE, KUBE_LABEL_SET_KEY)
    ct_unset_labels = server.get_db_entry(STATE_DB_NAME,
            KUBE_LABEL_TABLE, KUBE_LABEL_UNSET_KEY)

    for (k, v) in labels.items():
        if v:
            if k not in ct_set_labels:
                ct_set_labels[k] = v
                to_upd_set = True
            elif ct_set_labels[k] != v:
                log_error("Label {}  value can't change {} to {}".format(
                    k, ct_set_labels[k], v))
            if k in ct_unset_labels:
                del ct_unset_labels[k]
                to_upd_unset = True
        else:
            if k in ct_set_labels:
                del ct_set_labels[k]
                to_upd_set = True
            if k not in ct_unset_labels:
                ct_unset_labels[k] = ""
                to_upd_unset = True

    log_debug("set={} unset={}".format(str(ct_set_labels), str(ct_unset_labels)))

    # Always call update, as update_labels are called only when there
    # is a change in status. Even if current DB is in sync, do an
    # update to force a notification to labels-handler, which will
    # ensure that labels are indeed in sync with API-Server.
    # There are many scenarios where DB is not in sync with API server.
    #
    server.set_db_entry(STATE_DB_NAME,
            KUBE_LABEL_TABLE, KUBE_LABEL_SET_KEY, ct_set_labels)
    server.set_db_entry(STATE_DB_NAME,
            KUBE_LABEL_TABLE, KUBE_LABEL_UNSET_KEY, ct_unset_labels)


def set_node_labels(server):
    labels = {}

    version_info = device_info.get_sonic_version_info()
    dev_data = server.get_db_entry(CONFIG_DB_NAME, 'DEVICE_METADATA',
            'localhost')
    dep_type = dev_data['type'] if 'type' in dev_data else "Unknown"

    labels["sonic_version"] = version_info['build_version']
    labels["hwsku"] = device_info.get_hwsku()
    labels["deployment_type"] = dep_type
    update_labels(server, labels)


def _update_entry(ct, upd):
    # Helper function, to update with case lowered.
    ret = dict(ct)
    for (k, v) in upd.items():
        ret[k.lower()] = v.lower()

    return ret


#
# SERVER-config changes:
#   Act if IP or disable changes.
#   If disabled or IP removed:
#       reset connection
#   else:
#       join
#   Update state-DB appropriately
#
class RemoteServerHandler:
    def __init__(self, server):
        """ Register self for updates """
        self.server = server

        server.register_handler(
                CONFIG_DB_NAME, SERVER_TABLE, self.on_config_update)
        self.cfg_server = _update_entry(dflt_cfg_ser, server.get_db_entry(
            CONFIG_DB_NAME, SERVER_TABLE, SERVER_KEY))

        log_debug("startup config: {}".format(str(self.cfg_server)))

        server.register_db(STATE_DB_NAME)
        self.st_server = _update_entry(dflt_st_ser, server.get_db_entry(
            STATE_DB_NAME, SERVER_TABLE, SERVER_KEY))

        self.start_time = datetime.datetime.now()

        if not self.st_server[ST_FEAT_UPDATE_TS]:
            # This is upon system start. Sleep 10m before join
            self.start_time += datetime.timedelta(
                    seconds=remote_ctr_config[JOIN_LATENCY])
            server.register_timer(self.start_time, self.handle_update)
            self.pending = True
            log_debug("Pause to join {} seconds @ {}".format(
                remote_ctr_config[JOIN_LATENCY], self.start_time))
        else:
            self.pending = False
            self.handle_update()



    def on_config_update(self, key, op, data):
        """ On config update """
        if key != SERVER_KEY:
            return

        cfg_data = _update_entry(dflt_cfg_ser, data)
        if self.cfg_server == cfg_data:
            log_debug("No change in server config")
            return

        log_debug("Received config update: {}".format(str(data)))
        self.cfg_server = cfg_data

        if self.pending:
            tnow = datetime.datetime.now()
            if tnow < self.start_time:
                # Pausing for initial latency since reboot or last retry
                due_secs = (self.start_time - tnow).seconds
            else:
                due_secs = 0
            log_debug("Pending to start in {} seconds at {}".format(
                due_secs, self.start_time))
            return

        self.handle_update()


    def handle_update(self):
        # Called upon start and upon any config-update only.
        # Called by timer / main thread.
        # Main thread calls only if timer is not running.
        #
        self.pending = False

        ip = self.cfg_server[CFG_SER_IP]
        disable = self.cfg_server[CFG_SER_DISABLE] != "false"
        
        pre_state = dict(self.st_server)
        log_debug("server: handle_update: disable={} ip={}".format(disable, ip))
        if disable or not ip:
            self.do_reset()
        else:
            self.do_join(ip, self.cfg_server[ST_SER_PORT],
                    self.cfg_server[CFG_SER_INSECURE])

        if pre_state != self.st_server:
            self.st_server[ST_SER_UPDATE_TS] = ts_now()
            self.server.set_db_entry(STATE_DB_NAME,
                    SERVER_TABLE, SERVER_KEY, self.st_server)
            log_debug("Update server state={}".format(str(self.st_server)))


    def do_reset(self):
        global remote_connected

        kube_commands.kube_reset_master(True)

        self.st_server[ST_SER_CONNECTED] = "false"
        log_debug("kube_reset_master called")

        remote_connected = False


    def do_join(self, ip, port, insecure):
        global remote_connected
        (ret, out, err) = kube_commands.kube_join_master(
                ip, port, insecure)

        if ret == 0:
            self.st_server[ST_SER_CONNECTED] = "true"
            self.st_server[ST_SER_IP] = ip
            self.st_server[ST_SER_PORT] = port
            remote_connected = True

            set_node_labels(self.server)
            log_debug("kube_join_master succeeded")
        else:
            # Ensure state reflects the current status
            self.st_server[ST_SER_CONNECTED] = "false"
            remote_connected = False

            # Join failed. Retry after an interval
            self.start_time = datetime.datetime.now()
            self.start_time += datetime.timedelta(
                    seconds=remote_ctr_config[JOIN_RETRY])
            self.server.register_timer(self.start_time, self.handle_update)
            self.pending = True

            log_debug("kube_join_master failed retry after {} seconds @{}".
                    format(remote_ctr_config[JOIN_RETRY], self.start_time))


#
# Feature changes
#
#   Handle Set_owner change:
#       restart service and/or label add/drop
#
#   Handle remote_state change: 
#       When pending, trigger restart
#
class FeatureTransitionHandler:
    def __init__(self, server):
        self.server = server
        self.cfg_data = defaultdict(lambda: defaultdict(str))
        self.st_data = defaultdict(lambda: defaultdict(str))
        server.register_handler(
                CONFIG_DB_NAME, FEATURE_TABLE, self.on_config_update)
        server.register_handler(
                STATE_DB_NAME, FEATURE_TABLE, self.on_state_update)
        return


    def handle_update(self, feat, set_owner, ct_owner, remote_state):
        # Called upon startup once for every feature in config & state DBs.
        # There after only called upon changes in either that requires action
        #
        if not is_systemd_active(feat):
            # Nothing todo, if system state is down
            return

        label_add = set_owner == "kube"
        service_restart = False

        if set_owner == "local":
            if ct_owner != "local":
                service_restart = True
        else:
            if remote_state == "pending":
                service_restart = True

        log_debug(
                "feat={} set={} ct={} state={} restart={} label_add={}".format(
                    feat, set_owner, ct_owner, remote_state, service_restart,
                    label_add))
        # read labels and add/drop if different
        update_labels(self.server,
                { "{}_enabled".format(feat): ("true" if label_add else "") })


        # service_restart
        if service_restart:
            restart_systemd_service(feat, set_owner)



    def on_config_update(self, key, op, data):
        # Hint/Note:
        # If the key don't pre-exist:
        #   This attempt to read will create the key for given
        #   field with empty string as value and return empty string

        init = key not in self.cfg_data
        old_set_owner = self.cfg_data[key][CFG_FEAT_OWNER]

        self.cfg_data[key] = _update_entry(dflt_cfg_feat, data)
        set_owner = self.cfg_data[key][CFG_FEAT_OWNER]

        if (not init) and (old_set_owner == set_owner):
            # No change, bail out
            log_debug("No change in feat={} set_owner={}. Bail out.".format(
                key, set_owner))
            return
        
        if key in self.st_data:
            log_debug("{} init={} old_set_owner={} owner={}".format(key, init, old_set_owner, set_owner))
            self.handle_update(key, set_owner, 
                    self.st_data[key][ST_FEAT_OWNER],
                    self.st_data[key][ST_FEAT_REMOTE_STATE])

        else:
            # Handle it upon data from state-db, which must come
            # if systemd is up
            log_debug("Yet to get state info key={}. Bail out.".format(key))
            return


    def on_state_update(self, key, op, data):
        # Hint/Note:
        # If the key don't pre-exist:
        #   This attempt to read will create the key for given
        #   field with empty string as value and return empty string

        init = key not in self.st_data
        old_remote_state = self.st_data[key][ST_FEAT_REMOTE_STATE]

        self.st_data[key] = _update_entry(dflt_st_feat, data)
        remote_state = self.st_data[key][ST_FEAT_REMOTE_STATE]

        if (not init) and (
                (old_remote_state == remote_state) or (remote_state != "pending")):
            # no change or nothing to do.
            return

        if key in self.cfg_data:
            log_debug("{} init={} old_remote_state={} remote_state={}".format(key, init, old_remote_state, remote_state))
            self.handle_update(key, self.cfg_data[key][CFG_FEAT_OWNER],
                    self.st_data[key][ST_FEAT_OWNER],
                    remote_state)
        return


#
# Label re-sync
#   When labels applied at remote are pending, start monitoring
#   API server reachability and trigger the label handler to
#   apply the labels
#
#   Non-empty KUBE_LABELS|PENDING, monitor API Server reachability
#
class LabelsPendingHandler:
    def __init__(self, server):
        server.register_handler(STATE_DB_NAME, KUBE_LABEL_TABLE, self.on_update)
        self.pending = False
        self.set_labels = {}
        self.unset_labels = {}
        return


    def on_update(self, key, op, data):
        # For any update sync with kube API server.
        # Don't optimize, as API server could differ with DB's contents
        # in many ways.
        #
        if (key == KUBE_LABEL_SET_KEY):
            self.set_labels = dict(data)
        elif (key == KUBE_LABEL_UNSET_KEY):
            self.unset_labels = dict(data)
        else:
            return

        if remote_connected and not self.pending:
            self.update_node_labels()
        else:
            log_debug("Skip label update: connected:{} pending:{}".
                    format(remote_connected, self.pending))



    def update_node_labels(self):
        # Called on config update by main thread upon init or config-change or
        # it was not connected during last config update
        # NOTE: remote-server-handler forces a config update notification upon
        # join.
        # Or it could be called by timer thread, if last upate to API server
        # failed.
        #
        self.pending = False
        ret = kube_commands.kube_write_labels(self.set_labels, self.unset_labels)
        if (ret != 0):
            self.pending = True
            pause = remote_ctr_config[LABEL_RETRY]
            ts += (datetime.datetime.now() + datetime.timedelta(seconds=pause))
            server.register_timer(ts, self.update_node_labels)

        log_debug("ret={} set={} unset={} pending={}".format(ret,
            str(self.set_labels), str(self.unset_labels), self.pending))
        return


def main():
    init()
    server = MainServer()
    RemoteServerHandler(server)
    FeatureTransitionHandler(server)
    LabelsPendingHandler(server)
    server.run()


if __name__ == '__main__':
    if os.geteuid() != 0:
        exit("Please run as root. Exiting ...")
    main()

