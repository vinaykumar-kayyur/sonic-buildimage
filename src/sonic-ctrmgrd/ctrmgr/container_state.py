#!/usr/bin/python3 -u

import argparse
import datetime
import inspect
import subprocess
import sys
import syslog
import time

from swsscommon import swsscommon

# DB field names
SET_OWNER = "set_owner"

CURRENT_OWNER = "current_owner"
UPD_TIMESTAMP = "update_time"
DOCKER_ID = "container_id"
REMOTE_STATE = "remote_state"
VERSION = "container_version"
SYSTEM_STATE = "system_state"

KUBE_LABEL_TABLE = "KUBE_LABELS"
KUBE_LABEL_SET_KEY = "SET"
KUBE_LABEL_UNSET_KEY = "UNSET"

state_db = None
set_owner = "local"
state_data = {
        CURRENT_OWNER: "none",
        UPD_TIMESTAMP: "",
        DOCKER_ID: "",
        REMOTE_STATE: "none",
        VERSION: "0.0.0",
        SYSTEM_STATE: ""
        }


def debug_msg(m):
    msg = "{}: {}".format(inspect.stack()[1][3], m)
    # print(msg)
    syslog.syslog(syslog.LOG_DEBUG, msg)


def _get_version_key(feature, version):
    return "{}_{}_enabled".format(feature, version)


def read_data(feature):
    global state_db, set_owner, state_data

    db = swsscommon.DBConnector("CONFIG_DB", 0)
    tbl = swsscommon.Table(db, 'FEATURE')
    data = dict(tbl.get(feature)[1])

    if (SET_OWNER in data):
        set_owner = data[SET_OWNER]

    state_db = swsscommon.DBConnector("STATE_DB", 0)
    tbl = swsscommon.Table(state_db, 'FEATURE')
    state_data.update(dict(tbl.get(feature)[1]))


def read_fields(feature, fields):
    tbl = swsscommon.Table(state_db, 'FEATURE')
    ret = []

    # tbl.get for non-existing feature would return
    # [False, {} ]
    #
    data = dict(tbl.get(feature)[1])
    for (field, default) in fields:
        val = data[field] if field in data else default
        ret += [val]

    return tuple(ret)


def check_unset_labels(feature, version):
    # check if this feature is in unset list or not 
    tbl = swsscommon.Table(state_db, KUBE_LABEL_TABLE)
    labels = dict(tbl.get(KUBE_LABEL_UNSET_KEY)[1])
    return _get_version_key(feature, version) in labels


def drop_label(feature, version):
    # Set/drop label as required
    # Update is done in state-db.
    # ctrmgrd sets it with kube API server as required
    
    tbl = swsscommon.Table(state_db, KUBE_LABEL_TABLE)
    name = _get_version_key(feature, version)
    labels = dict(tbl.get(KUBE_LABEL_UNSET_KEY)[1])
    if name not in labels:
        tbl.set(KUBE_LABEL_UNSET_KEY, [ (name, "")])
        tbl.hdel(KUBE_LABEL_SET_KEY, name)
        

def update_data(feature, data):
    debug_msg("{}: {}".format(feature, str(data)))
    tbl = swsscommon.Table(state_db, "FEATURE")
    tbl.set(feature, list(data.items()))


def get_docker_id():
    cmd = 'cat /proc/self/cgroup | grep -e ":memory:" | rev | cut -f1 -d\'/\' | rev'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = proc.communicate()[0].decode("utf-8")
    return output.strip()[:12]


def instance_lower(feature, version):
    if ((state_data[REMOTE_STATE] == "none") or
            (state_data[REMOTE_STATE] == "stopped")):
        # No one running to compare version
        return False

    ct_version = state_data[VERSION]
    ct = ct_version.split('.') if ct_version else "0.0.0".split('.')
    nxt = version.split('.') if version else "0.0.0".split('.')
    ret = False
    for cs, ns in zip(ct, nxt):
        c = int(cs)
        n = int(ns)
        if n < c:
            ret = True
            break
        elif n > c:
            break

    debug_msg("compare version: new:{} current:{} res={}".format(
        version, ct_version, ret))
    return ret


def is_active(feature):
    if state_data[SYSTEM_STATE] == "up":
        return True
    else:
        syslog.syslog(syslog.LOG_ERR, "Found inactive for {}".format(feature))
        return False


def update_state(is_up, feature, owner=None, version=None):
    data = {
            CURRENT_OWNER: owner if is_up else "none",
            DOCKER_ID: get_docker_id() if is_up else "",
            UPD_TIMESTAMP: str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
    if is_up:
        data[VERSION] = version

        if (owner == "local"):
            # Disable deployment of this version as available locally
            drop_label(feature, version)
        else:
            data[REMOTE_STATE] = "running"

    elif state_data[CURRENT_OWNER] != "local":
        state = state_data[REMOTE_STATE]
        if state != "pending":
            if state != "running":
                syslog.syslog(syslog.LOG_ERR,
                        "{} kube down state: {} != running", feature, state)
            else:
                data[REMOTE_STATE] = "stopped"

    debug_msg("{} up= {} data:{}".format(feature, is_up, str(data)))
    update_data(feature,  data)
    state_data.update(data)


def do_exit(feat, m):
    # Exiting will kick off the container to run.
    # So sleep forever with periodic logs.
    #
    while True:
        syslog.syslog(syslog.LOG_ERR, "Exiting .... feat:{} docker_id:{} msg:{}".format(
            feat, get_docker_id(), m))
        time.sleep(60)
    

def container_up(feature, owner, version):
    debug_msg("BEGIN")
    read_data(feature)

    debug_msg("args: feature={}, owner={}, version={} DB: set_owner={} state_data={}".format(
        feature, owner, version, set_owner, state_data))

    if owner == "local":
        update_state(True, feature, owner, version)
    else:
        if (set_owner == "local"):
            do_exit(feature, "bail out as set_owner is local")

        if not is_active(feature):
            do_exit(feature, "bail out as system state not active")

        if check_unset_labels(feature, version):
            do_exit(feature, "This version is marked disabled. Exiting ...")

        if instance_lower(feature, version):
            # Remove label <feature_name>_<version>_enabled
            # Else kubelet will continue to re-deploy every 5 mins, until
            # master removes the lable to un-deploy.
            #
            do_exit(feature, "bail out as current deploy id is lower")

        update_data(feature, { VERSION: version })

        mode = state_data[REMOTE_STATE]
        if mode in ("none", "running", "stopped"):
            update_data(feature, { REMOTE_STATE: "pending" })
            mode = "pending"
        else:
            debug_msg("{}: Skip remote_state({}) update".format(feature, mode))

        
        i = 0
        while (mode != "ready"):
            if i == 0:
                debug_msg("{}: remote_state={}. Waiting to go ready".format(feature, mode))
                i = 1
            elif i == 9:
                i = 0
            else:
                i += 1

            time.sleep(2)
            mode, db_version = read_fields(feature, [(REMOTE_STATE, "none"), (VERSION, "")])
            if version != db_version:
                # looks like another instance has overwritten. Exit for now.
                # If this happens to be higher version, next deploy by kube will fix
                # This is a very rare window of opportunity, for this version to be higher.
                #
                do_exit(feature, "bail out as current deploy version={} is different than {}. re-deploy higher one".
                        format(version, db_version))


        update_state(True, feature, owner, version)

    debug_msg("END")


def container_down(feature):
    debug_msg("BEGIN")
    read_data(feature)

    debug_msg("feature={} set_owner={} state_data={}".format(
        feature, set_owner, state_data))

    ct_docker_id = state_data[DOCKER_ID]
    caller_docker_id = get_docker_id()
    if caller_docker_id != ct_docker_id:
        syslog.syslog(syslog.LOG_ERR, "{} down mismatch docker-id. caller_docker_id={} current:{}".
                format(feature, caller_docker_id, ct_docker_id))
    else:
        update_state(False, feature)
    debug_msg("END")



def parser_container_up(args):
    container_up(feature=args.feature, owner=args.owner, version=args.version)


def parser_container_down(args):
    container_down(feature=args.feature)


# e.g. container_state <feature> up/down local/kube <docker id>
def main():
    parser = argparse.ArgumentParser(description="state up/down <feature> kube/local [<docker id> <instance id>]")
    subparsers = parser.add_subparsers(title='actions')

    parser_up = subparsers.add_parser('up')
    parser_up.add_argument("-f", "--feature", required=True)
    parser_up.add_argument("-o", "--owner", choices=["local", "kube"], required=True)
    parser_up.add_argument("-v", "--version", default="")
    parser_up.set_defaults(func=parser_container_up)
    
    parser_down = subparsers.add_parser('down')
    parser_down.add_argument("-f", "--feature", required=True)
    parser_down.set_defaults(func=parser_container_down)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

