#!/usr/bin/python
#
# Test script for wpaspy
# Copyright (c) 2013, Jouni Malinen <j@w1.fi>
#
# This software may be distributed under the terms of the BSD license.
# See README for more details.
import os
import sys
import time
import socket
import select
import threading

import json
import os

import click
from natsort import natsorted
from sonic_py_common.logger import Logger
from swsscommon.swsscommon import ConfigDBConnector, SonicV2Connector
from portconfig import get_child_ports
import ast

SYSLOG_IDENTIFIER = 'hostapd_wrapper'
# Global logger instance
logger = Logger(SYSLOG_IDENTIFIER)
logger.set_min_log_priority_info()

counter = 0

class Ctrl:
    def __init__(self, path, port=9878):
        global counter
        self.started = False
        self.attached = False
        self.path = path
        self.port = port
        try:
            mode = os.stat(path).st_mode
            if stat.S_ISSOCK(mode):
                self.udp = False
            else:
                self.udp = True
        except:
            self.udp = False

        if not self.udp:
            self.s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.dest = path
            self.local = "/tmp/wpa_ctrl_" + str(os.getpid()) + '-' + str(counter)
            counter += 1
            self.s.bind(self.local)
            try:
                self.s.connect(self.dest)
            except Exception as e:
                logger.log_error("exception in hostapd socket connect {}".format(e))
                self.s.close()
                os.unlink(self.local)
                cmd = 'systemctl restart hostapd'
                logger.log_notice("Restarted hostapd service")
                os.system(cmd)
                time.sleep(5)
                logger.log_notice("Re-attempting hostapddd socketttt connectttt")
                self.s.connect(self.dest)
                raise
        else:
            try:
                self.s = None
                ai_list = socket.getaddrinfo(path, port, socket.AF_INET,
                                             socket.SOCK_DGRAM)
                for af, socktype, proto, cn, sockaddr in ai_list:
                    self.sockaddr = sockaddr
                    break
                self.s = socket.socket(af, socktype)
                self.s.settimeout(5)
                self.s.sendto(b"GET_COOKIE", sockaddr)
                reply, server = self.s.recvfrom(4096)
                self.cookie = reply
                self.port = port
            except:
                logger.log_error("hostapd connect exception path {}".format(path))
                logger.log_error("hostapd connect exception port {}".format(str(port)))
                if self.s != None:
                    self.s.close()
                raise
        self.started = True

    def __del__(self):
        self.close()

    def close(self):
        if self.attached:
            try:
                self.detach()
            except Exception as e:
                # Need to ignore this allow the socket to be closed
                self.attached = False
                pass
        if self.started:
            self.s.close()
            if not self.udp:
                os.unlink(self.local)
            self.started = False

    def request(self, cmd, timeout=10):
        if type(cmd) == str:
            try:
                cmd2 = cmd.encode()
                cmd = cmd2
            except UnicodeDecodeError as e:
                pass
        if self.udp:
            self.s.sendto(self.cookie + cmd, self.sockaddr)
        else:
            self.s.send(cmd)
        [r, w, e] = select.select([self.s], [], [], timeout)
        if r:
            res = self.s.recv(4096).decode()
            try:
                r = str(res)
            except UnicodeDecodeError as e:
                r = res
            return r
        raise Exception("Timeout on waiting response")

    def attach(self):
        if self.attached:
            return None
        res = self.request("ATTACH")
        if "OK" in res:
            self.attached = True
            return None
        raise Exception("ATTACH failed")

    def detach(self):
        if not self.attached:
            return None
        if self.s.fileno() == -1:
            self.attached = False
            return None
        while self.pending():
            ev = self.recv()
        res = self.request("DETACH")
        if "FAIL" not in res:
            self.attached = False
            return None
        raise Exception("DETACH failed")

    def terminate(self):
        if self.attached:
            try:
                self.detach()
            except Exception as e:
                # Need to ignore this to allow the socket to be closed
                self.attached = False
        self.request("TERMINATE")
        self.close()

    def pending(self, timeout=0):
        [r, w, e] = select.select([self.s], [], [], timeout)
        if r:
            return True
        return False

    def recv(self):
        res = self.s.recv(4096).decode()
        try:
            r = str(res)
        except UnicodeDecodeError as e:
            r = res
        return r

wpas_ctrl = '/var/run/hostapd'

def wpas_connect(host=None, port=9878):
    ifaces = []
    idict = {}

    if host != None:
        try:
            wpas = Ctrl(host, port)
            return wpas
        except:
            logger.log_error("Could not connect to host: {}". format(host))
            return None

    if os.path.isdir(wpas_ctrl):
        try:
            ifaces = [os.path.join(wpas_ctrl, i) for i in os.listdir(wpas_ctrl)]
            index = 0
            for i in os.listdir(wpas_ctrl):
                idict[ifaces[index]] = i
                index = index + 1
            logger.log_info('Found hostapd interfaces {}'.format(ifaces))
        except OSError as error:
            logger.log_error("Could not find hostapd: {}".format(error))
            return None

    if len(ifaces) < 1:
        logger.log_error("No hostapd control interface found")
        return None

    for ctrl in ifaces:
        try:
            wpas = Ctrl(ctrl)
            logger.log_info('Connected to hostapd at interface: {}'.format(ctrl))
            #creating thread
            t = threading.Thread(target=hostapd_ev_monitor, args=(wpas,idict[ctrl],))
            # starting thread 1
            t.start()
        except Exception as e:
            logger.log_error("found an exception {}".format(e))
            pass
    req_hdlr_t = threading.Thread(target=hostapd_cmd_monitor, args=())
    req_hdlr_t.start()

    t.join()
    req_hdlr_t.join()
    return None

def fdb_clear_all():
    appl_db = SonicV2Connector(host="127.0.0.1")
    appl_db.connect(appl_db.APPL_DB)
    opdata = ["ALL", "ALL"]
    dbmsg = json.dumps(opdata, separators=(',',':'))
    appl_db.publish('APPL_DB', 'FLUSHFDBREQUEST', dbmsg) 

def hostapd_req_monitor():
    config_db = ConfigDBConnector()
    config_db.connect()

    nac_session_dict = config_db.get_table('NAC_SESSION')
    for intf_name in nac_session_dict.keys():
        if intf_name != 'all':
            mon1 = wpas_connect(os.path.join(wpas_ctrl, intf_name))
            if mon1 is not None:
                if nac_session_dict[intf_name].get('admin_state') == 'up':
                    mon1.request('ENABLE')
                    logger.log_notice('Enabling PNAC at Port {} '.format(intf_name))
                else:
                    mon1.request('DISABLE')
                    logger.log_notice('Disabling PNAC at Port {} '.format(intf_name))

PORT_STATUS_TABLE_PREFIX = "PORT_TABLE:"

PORT_OPER_STATUS = "oper_status"

def hostapd_config_update(intf_name):
    config_db = ConfigDBConnector()
    config_db.connect()
    port_dict = config_db.get_table('PORT')
    nac_profile_dict = config_db.get_table('NAC_PROFILE')
    #for intf_name in port_dict.keys():
    if (port_dict[intf_name]):
        logger.log_notice("hostapd config update handling for interface {}".format(intf_name))
        if port_dict[intf_name].get('nac'):
            port_nac_profile_name = port_dict[intf_name]['nac']
            logger.log_notice("NAC Profile {} assigned to Port {}:".format(port_nac_profile_name, intf_name))
            for nac_profile in nac_profile_dict.keys():
                if nac_profile == port_nac_profile_name:
                    em = nac_profile_dict[nac_profile].get('eap_auth_method')
                    qp = nac_profile_dict[nac_profile].get('quiet_period')
                    st = nac_profile_dict[nac_profile].get('supp_timeout')
                    tp = nac_profile_dict[nac_profile].get('tx_period')
                    ert = nac_profile_dict[nac_profile].get('eap_reauth_timeout')
                    logger.log_notice("NAC Profile Config Params QP:{} EAM:{} ST:{} TP:{} ERT:{}".format(qp, em, st, tp, ert))

                    intf_num = intf_name.strip('Ethernet')
                    hostapd_conf_file = '/etc/hostapd/hostapd_e'+intf_num+'.conf'
                    logger.log_notice("Updating hostapd configuration file {} with value {} for param eap_reauth_period".format(hostapd_conf_file, ert))

                    with open(hostapd_conf_file, 'r') as file:
                        contents = file.readlines()

                    for i in range(len(contents)):
                        if contents[i].startswith('eap_reauth_period=') or contents[i].startswith('#eap_reauth_period='):
                            contents[i] = f'eap_reauth_period={ert}\n'

                    with open(hostapd_conf_file, 'w') as file:
                        contents = "".join(contents)
                        file.write(contents)

                    logger.log_notice("Reloading hostapd configuration file of interface {}".format(intf_name))
                    hostapd_hndlr = wpas_connect(os.path.join(wpas_ctrl, intf_name))
                    if hostapd_hndlr is not None:
                        hostapd_hndlr.request('RELOAD')
    else:
        logger.log_notice("No hostapd config update handling for interface {}".format(intf_name))


def hostapd_cmd_monitor():
    appl_db = SonicV2Connector(host="127.0.0.1")
    appl_db.connect(appl_db.APPL_DB)
    config_db = ConfigDBConnector()
    config_db.connect()
    idict = {}
    ios_dict = {}

    while True:
        nac_tbl = config_db.get_table('NAC')
        if nac_tbl:
            if nac_tbl['global']['admin_state'] == 'up':
                break
        time.sleep(5)

    logger.log_notice("NAC feature enabled, starting monitoring for hostapd commands")
    nac_session_dict = config_db.get_table('NAC_SESSION')
    for intf_name in nac_session_dict.keys():
        if intf_name != 'all':
            ios_dict[intf_name] = appl_db.get(appl_db.APPL_DB, PORT_STATUS_TABLE_PREFIX + intf_name, PORT_OPER_STATUS)
            idict[intf_name] = nac_session_dict[intf_name].get('admin_state')
            mon1 = wpas_connect(os.path.join(wpas_ctrl, intf_name))
            if mon1 is not None:
                if nac_session_dict[intf_name].get('admin_state') == 'up':
                    mon1.request('ENABLE')
                else:
                    mon1.request('DISABLE')
    nac_session_dict.clear()
    while True:
        nac_session_dict = config_db.get_table('NAC_SESSION')
        for intf_name in nac_session_dict.keys():
            if intf_name != 'all':
                if idict[intf_name] != nac_session_dict[intf_name].get('admin_state'):
                    mon2 = wpas_connect(os.path.join(wpas_ctrl, intf_name))
                    if nac_session_dict[intf_name].get('admin_state') == 'up':
                        hostapd_config_update(intf_name)
                        mon2.request('ENABLE')
                        idict[intf_name] = 'up'
                        logger.log_notice('Enabling PNAC at Port {} '.format(intf_name))
                    else:
                        mon2.request('DISABLE')
                        idict[intf_name] = 'down'
                        logger.log_notice('Disabling PNAC at Port {} '.format(intf_name))
                oper_status = appl_db.get(appl_db.APPL_DB, PORT_STATUS_TABLE_PREFIX + intf_name, PORT_OPER_STATUS)
                if oper_status != ios_dict[intf_name]:
                    if oper_status == 'down':
                         config_db.mod_entry('NAC_SESSION', intf_name, {'nac_status': 'unauthorized'})
                         config_db.mod_entry('PORT', intf_name, {'learn_mode': 'drop'})
                         fdb_clear_all()
                         logger.log_notice("NAC unauthorized on {} interface as it is operationally down ".format(intf_name))
                    ios_dict[intf_name] = oper_status
        nac_session_dict.clear()
        time.sleep(5)

def hostapd_ev_monitor(mon, ifname):
    mon.attach()
    logger.log_notice("Monitoring Port for NAC {}".format(ifname))
    config_db = ConfigDBConnector()
    config_db.connect()
    nac_session_dict = config_db.get_table('NAC_SESSION')
    port_dict = config_db.get_table('PORT')

    while True:
        time.sleep(1)
        if not nac_session_dict:
            nac_session_dict = config_db.get_table('NAC_SESSION')

        while mon.pending(10):
            ev = mon.recv()
            logger.log_notice(ev)
            if 'EAP-SUCCESS' in ev:
                if nac_session_dict and ifname in nac_session_dict:
                    config_db.mod_entry('NAC_SESSION', ifname, {'nac_status': 'authorized'})
                    config_db.mod_entry('PORT', ifname, {'learn_mode': 'hardware'})
                    logger.log_notice("Port Authorized: {}".format(ifname))
                else:
                    logger.log_error("EA: DB Table not present or port not configured in DB")
            elif 'EAP-FAILURE' in ev:
                if nac_session_dict and ifname in nac_session_dict:
                    config_db.mod_entry('NAC_SESSION', ifname, {'nac_status': 'unauthorized'})
                    config_db.mod_entry('PORT', ifname, {'learn_mode': 'drop'})
                    fdb_clear_all()
                    logger.log_notice("Port UnAuthorized: {}".format(ifname))
                else:
                    logger.log_error("EF: DB Table not present or port not configured in DB")
            elif 'EAP-TIMEOUT-FAILURE' in ev:
                if nac_session_dict and ifname in nac_session_dict:
                    config_db.mod_entry('NAC_SESSION', ifname, {'nac_status': 'unauthorized'})
                    config_db.mod_entry('PORT', ifname, {'learn_mode': 'drop'})
                    fdb_clear_all()
                    logger.log_notice("Port UnAuthorized: {}".format(ifname))
                else:
                    logger.log_error("ETF: DB Table not present or port not configured in DB")

def main(host=None, port=9878):
    mon = wpas_connect(host, port)
    if mon is None:
        logger.log_error("Could not open event monitor connection")
        return


if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(host=sys.argv[1], port=int(sys.argv[2]))
    else:
        main()

