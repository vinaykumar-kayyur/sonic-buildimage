#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''Test the PORT component'''
import time
import datetime
import os
import re
import io
import logging
import syslog
import subprocess
import portutil
import collections
import json
import collections
import traceback
import abc
import sys
import click
import copy
import yaml

from sfputil.main import *
from rjutil.baseutil import get_machine_info
from rjutil.baseutil import get_platform_info

SYSLOG_IDENTIFIER       = "PORT"
SAI_PROFILE             = "sai.profile"
SAI_PROFILE_PREDIX      = "SAI_INIT_CONFIG_FILE=/usr/share/sonic/hwsku/"
CONFIG_DB_JSON_PATH     = "/etc/sonic/config_db.json"
MACHINE_FILE            = "/host/machine.conf"
MACHINE_PLATFORM_PREDIX = "onie_platform="

LOG_DEBUG_LEVEL   = 1
LOG_INFO_LEVEL    = 2
LOG_WARNING_LEVEL = 3
LOG_ERROR_LEVEL   = 4

LANE_MAX          = 4
PACKETS_COUNT     = 10000
PACKETS_SIZE      = 64
PACKETS_DST_MAC   = "ff:ff:ff:ff:ff:ff"
PORT_TEST_VLAN    = 4048
KR_VLAN           = 4080
PRBS_BER_DEFAULT  = 1.0e-8
PRBS_TIME_DEFAULT = 120

###################### HSDK Config ######################
# --------------------------------------------------------------------- #
# Internal management port
global_mgmt_kr_ports = {
    "x86_64-ragile_b6510-48vs8cq-r0":{"eth1":66, "eth2":130},
}

global_prbs_port_range = {

}

# A device with an external PHY
global_extphy_device = {

}

# Use HSDK equipment
global_hsdk_device = {

}

# Device correspondingprbs ber
global_prbs_ber = {

}

# Device corresponding prbs test of time
global_prbs_time = {

}

# Port Test related configuration
PORT_FACTEST_CONFIG = {
    "port_frame_test_retrynum": 1,# Retry times of sending and receiving frames on the port
    "port_brcst_test_retrynum": 1,# Number of port broadcast test retries
    "port_prbs_test_retrynum": 1,# Port PRBS test retry count
    "port_kr_test_retrynum": 1,# Number of internal management port test retries
    "port_frame_del_time": 10,# Waiting time for sending and receiving frames on the port to recover the test environment(s)
    "port_brcst_del_time": 10,# Port broadcast test Recovery test environment wait time(s)
    "port_prbs_del_time": 10,# Port PRBS test Recovery test environment waiting time(s)
    "port_kr_del_time": 10,# Internal management port test Recovery test environment waiting time(s)
    "port_log_level": LOG_ERROR_LEVEL,# PORT Component log level
}
# --------------------------------------------------------------------- #

# True: Print the log at the same time (default False)
log_also_print_to_console = False
# True: Print CMD at the same time (default False)
cmd_also_print_to_console = False
# True: Print CMD execution results at the same time (default False)
cmd_output_also_print_to_console = False
# True: Prints the log of the entire test flow to the console when the test fails (default True)
port_log_info_print_to_console = False
# True: Enable input redirection  cmd + < /dev/null(default True)
sdk_cmd_redirect_console = True

# Test Port configurations
global_port_config = {
    "hsdk_device" : 1,# bcmcmdb devices
    "mgmt_kt_ports" : {},
    "prbs_port_range" : "",
    "extphy_device" : 0,
    "prbs_ber" : PRBS_BER_DEFAULT,
    "prbs_time" : PRBS_TIME_DEFAULT,
    "port_frame_test_retrynum": 1,# Retry times of sending and receiving frames on the port
    "port_brcst_test_retrynum": 1,# Number of port broadcast test retries
    "port_prbs_test_retrynum": 1,# Port PRBS test retry count)
    "port_kr_test_retrynum": 1,# Number of internal management port test retries
    "port_frame_del_time": 10,# Waiting time for sending and receiving frames on the port to recover the test environment(s)
    "port_brcst_del_time": 10,# Port broadcast test Recovery test environment wait time(s)
    "port_prbs_del_time": 10,# Port PRBS test Recovery test environment waiting time(s)
    "port_kr_del_time": 10,# Internal management interface Test Recovery Test environment Waiting time (s)
    "port_log_level": LOG_ERROR_LEVEL,# PORT Component log level
    "flag" : False # Whether the port configuration has been loaded
}

global_port_log_info = "port_log_info:\n"
global_prbs_info = ""
global_onie_platform = ""
global_unit_port_list = []

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

class AliasedGroup(click.Group):
    '''Command alias'''

    def get_command(self, ctx, cmd_name):
        '''Get command'''
        get_rv = click.Group.get_command(self, ctx, cmd_name)
        if get_rv is not None:
            return get_rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if matches:
            if len(matches) == 1:
                return click.Group.get_command(self, ctx, matches[0])
            ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))
        return None

###################### HSDK Config ######################


def prepare_kr_test():
    pk = PortKrTest()
    pk.install_pktgen_mode()

# Print the output according to the format
def port_totalprint(arr, tips):
    if len(arr) <= 0:
        return 
    print ("%-20s" % tips ,)
    for index in range(len(arr)):
        print ("%03d" % arr[index] ,)
        if (index + 1) % 8 == 0:
            print ("")
            print (" " * 20,)
    print ("")

def singleton(cls):
    '''singleton'''

    _instance = {}
    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton

def log_info_gather_fun(log_content):
    '''test process log collection'''

    global global_port_log_info
    global_port_log_info = global_port_log_info + "\n" + log_content

def prbs_info_gather_fun(prbs_content, clear=False):
    '''prbs test process information collection'''

    global global_prbs_info
    if clear == True:
        global_prbs_info = prbs_content
    else:
        global_prbs_info = global_prbs_info + "\n" + prbs_content

def log_debug(msg):
    '''debug log'''

    funcName = sys._getframe().f_back.f_code.co_name # Gets the name of the calling function
    lineNumber = sys._getframe().f_back.f_lineno     # obtain a line number
    dt_ms = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') # Date time in microseconds
    info_str = dt_ms + "| DEBUG PORT: " + funcName +": "+ str(lineNumber)
    log_info_gather = "%-40s| %s" % (info_str, str(msg))
    log_info_gather_fun(log_info_gather)
    if global_port_config["port_log_level"] <= LOG_DEBUG_LEVEL:
        try:
            syslog.openlog(SYSLOG_IDENTIFIER)
            syslog.syslog(syslog.LOG_DEBUG, msg)
            syslog.closelog()

            if log_also_print_to_console:
                click.echo(log_info_gather)
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)

def log_info(msg):
    '''info log'''

    funcName = sys._getframe().f_back.f_code.co_name # Gets the name of the calling function
    lineNumber = sys._getframe().f_back.f_lineno     # obtain a line number
    dt_ms = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') # Date time in microseconds
    info_str = dt_ms + "| INFO PORT: " + funcName +": "+ str(lineNumber)
    log_info_gather = "%-40s| %s" % (info_str, str(msg))
    log_info_gather_fun(log_info_gather)
    if global_port_config["port_log_level"] <= LOG_INFO_LEVEL:
        try:
            syslog.openlog(SYSLOG_IDENTIFIER)
            syslog.syslog(syslog.LOG_INFO, msg)
            syslog.closelog()

            if log_also_print_to_console:
                click.echo(log_info_gather)
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)

def log_warning(msg):
    '''warning log'''

    funcName = sys._getframe().f_back.f_code.co_name # Gets the name of the calling function
    lineNumber = sys._getframe().f_back.f_lineno     # obtain a line number
    dt_ms = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') # Date time in microseconds
    info_str = dt_ms + "| WARNING PORT: " + funcName +": "+ str(lineNumber)
    log_info_gather = "%-40s| %s" % (info_str, str(msg))
    log_info_gather_fun(log_info_gather)
    if global_port_config["port_log_level"] <= LOG_WARNING_LEVEL:
        try:
            syslog.openlog(SYSLOG_IDENTIFIER)
            syslog.syslog(syslog.LOG_WARNING, msg)
            syslog.closelog()

            if log_also_print_to_console:
                click.echo(log_info_gather)
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)

def log_error(msg):
    '''error log'''

    funcName = sys._getframe().f_back.f_code.co_name # Gets the name of the calling function
    lineNumber = sys._getframe().f_back.f_lineno     # obtain a line number
    dt_ms = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') # Date time in microseconds
    info_str = dt_ms + "| ERROR PORT: " + funcName +": "+ str(lineNumber)
    log_info_gather = "%-40s| %s" % (info_str, str(msg))
    log_info_gather_fun(log_info_gather)
    if global_port_config["port_log_level"] <= LOG_ERROR_LEVEL:
        try:
            syslog.openlog(SYSLOG_IDENTIFIER)
            syslog.syslog(syslog.LOG_ERR, msg)
            syslog.closelog()

            if log_also_print_to_console:
                click.echo(log_info_gather)
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)

def port_getstatusoutput(cmd, time_sleep=0):
    '''Obtain the execution result of the command'''

    ret, output = subprocess.getstatusoutput(cmd)

    t = int(time_sleep)
    if cmd_also_print_to_console:
        log_debug(cmd)
    if cmd_output_also_print_to_console:
        log_debug(output)
    if t != 0:
        log_debug("time sleep: %ds" % t)
        time.sleep(t)
    if ret == 0:
        if (re.search('hsdk msg connect fail', output.strip())):
            return -1, output
        return ret, output
    else:
        output_content = "cmd: %s execution fail, output:%s" % (cmd, output)
        return_output_content = output_content.replace("\"","'")
        log_error("%s" % output_content)
        return ret, "%s" % return_output_content

def get_sdk_cmd(cmd, time_out=0, grep=""):
    '''Combine the CMD passed in, return sdk_cmd'''

    cmd_str = ""
    sdk_cmd = ""
    t = int(time_out)
    if (hsdk_check()):
        sdk_cmd = "bcmcmdb "
    else:
        sdk_cmd = "bcmcmd "
    if t != 0:
        cmd_str = sdk_cmd + "-t %d \"" % t
    else:
        cmd_str = sdk_cmd + "\""
    if sdk_cmd_redirect_console == True:
        cmd_str = cmd_str + str(cmd) + "\" < /dev/null"
    else:
        cmd_str = cmd_str + str(cmd) + "\""
    if grep != "":
        cmd_str += " | grep \"%s\"" % str(grep)
    return cmd_str

class PortKrTest(object):

    def __get_onie_platform(self):
        with open(MACHINE_FILE, "r") as machine_f:
            for line in machine_f:
                if(re.search('%s(.*?)$' % MACHINE_PLATFORM_PREDIX, line)):
                    onie_platform = re.findall(r"%s(.*?)$" % MACHINE_PLATFORM_PREDIX, line)[0]
                    return onie_platform
        return None


    def install_pktgen_mode(self):
        try:
            cmd = "lsmod | grep pktgen"
            ret, output = subprocess.getstatusoutput(cmd)
            if not output or ret != 0:
                cmd = "modprobe pktgen"
                ret, output = subprocess.getstatusoutput(cmd)
            eth_list = list(global_mgmt_kr_ports[self.__get_onie_platform()].keys())
            eth_list.sort()
            for eth in eth_list:
                xe_port = self.get_mgmt_bcmport(eth)
                cmd = "bcmcmd \"port %s en=1\"" % xe_port
                ret, output = subprocess.getstatusoutput(cmd)

            time.sleep(3)

            for eth in eth_list:
                cmd = "ls /proc/net/pktgen/%s" % eth
                ret, output = subprocess.getstatusoutput(cmd)
                if "cannot" in output:
                    cmd = "ifconfig %s up" % eth
                    ret, output = subprocess.getstatusoutput(cmd)
                    cmd = "echo \"add_device %s\" > /proc/net/pktgen/kpktgend_0" % eth
                    ret, output = subprocess.getstatusoutput(cmd)

        except Exception as e:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)


    def get_mgmt_bcmport(self, port):
        cmd = "bcmcmd ps"
        ret, output = subprocess.getstatusoutput(cmd)
        lines = output.split("\n")
        logic_port = global_mgmt_kr_ports[self.__get_onie_platform()][port]
        for line in lines:
            line.strip()
            if re.search(r"^.*?\(.*?\)", line) and int(re.findall(r"^.*?\((.*?)\)", 
                line)[0].strip()) == logic_port:
                return re.findall("^(.*?)\(.*?\)", line)[0].strip()
        return None
 

    def start_send_port_packets(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff", vlan=4080):
        cmd = "echo \"pkt_size %d\" > /proc/net/pktgen/%s" % (size, port)
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"count %d\" > /proc/net/pktgen/%s" % (count, port)
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"dst_mac %s\" > /proc/net/pktgen/%s" % (dst_mac, port)
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"vlan_id %s\" > /proc/net/pktgen/%s" % (vlan, port)
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"start\" > /proc/net/pktgen/pgctrl"
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        time.sleep(2)
        cmd = "echo \"stop\" > /proc/net/pktgen/pgctrl"
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "cat /proc/net/pktgen/%s" % port
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def clear_port_packets(self):
        for port in global_mgmt_kr_ports[self.__get_onie_platform()]:
            cmd = "bcmcmd \"clear c %s\"" % self.get_mgmt_bcmport(port)
            ret, output = subprocess.getstatusoutput(cmd)
            if(ret != 0):
                return False, output
        return True, output


    def check_port_packets(self, port, count):
        cmd = "bcmcmd \"show c XLMIB_RPOK.%s\"" % self.get_mgmt_bcmport(port)
        ret, output = subprocess.getstatusoutput(cmd)
        lines = output.split("\n")
        if(lines[1].strip()):
            if (count == int(re.sub('[,]', '', lines[1].split()[2].strip("+-")))):
                return True, lines[1].split()[2]
            else:
                return False, lines[1].split()[2]
        return False, "fail"

class PortTest(object):
    __mode = 0
    
    interfaces = []
    porttabfile = " "
    bcm_ports = []

    def __init__(self, mode = "sdk"):
        self.__get_global_interfaces()
        self.__get_global_bcmports()
        if(mode == "sonic"):
            self.__mode = 1
        else:
            self.__mode = 0

    def __get_global_interfaces(self):
        if(len(self.interfaces)):
            # print("inited interfaces")
            pass
        else:
            cmd = "show interfaces status"
            strs = os.popen(cmd)
            for line in strs:
                line.strip()
                if(len(line.split()) and re.search("Ethernet[0-9]+", line.split()[0])): 
                    self.interfaces.append(line.split()[0])


    def __get_global_bcmports(self):
        if(len(self.bcm_ports)):
            pass
        else: 
            pu = portutil.PortUtil()
            cmd = "bcmcmd ps"
            strs = os.popen(cmd)
            lines = strs.readlines()
            for port in pu.device_port_list:
                for line in lines:
                    line.strip()
                    if re.search(r"^.*?\(.*?\)", line) and int(re.findall(r"^.*?\((.*?)\)", line)[0].strip()) == port.logic_port:
                        self.bcm_ports.append(re.findall("^(.*?)\(.*?\)", line)[0].strip())
                        break


    def __get_port_status_by_sonic(self, port):
        cmd = "show int status %s" % self.interfaces[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        return lines[-2].split()[5]


    def __get_port_status_by_sdk(self, port):
        cmd = "bcmcmd \"ps %s\"" % self.bcm_ports[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        if(re.search("up", lines[3])):
            return "up"
        elif(re.search("!ena", lines[3])):
            return "!ena"
        else:
            return "down"


    def __get_unit_port_by_bcm(self, port):
        cmd = "bcmcmd \"ps %s\"" % self.bcm_ports[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        unit_port = int(re.findall("%s\((.*?)\)" % self.bcm_ports[port - 1], lines[3])[0].strip())
        return unit_port


    def __start_send_port_packets_by_sonic(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff"):
        cmd = "echo \"add_device %s\" > /proc/net/pktgen/kpktgend_0" % self.interfaces[port - 1]
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"pkt_size %d\" > /proc/net/pktgen/%s" % (size,  self.interfaces[port - 1])
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"count %d\" > /proc/net/pktgen/%s" % (count, self.interfaces[port - 1])
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"dst_mac %s\" > /proc/net/pktgen/%s" % (dst_mac, self.interfaces[port - 1])
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"start\" > /proc/net/pktgen/pgctrl"
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "cat /proc/net/pktgen/%s" % self.interfaces[port - 1]
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def __start_send_port_packets_by_sdk(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff"):
        cmd = "bcmcmd \"pbmp %s\"" % self.bcm_ports[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        pbmp = re.findall("0x[0-9]+",lines[1].strip())[0]
        cmd = "bcmcmd \"tx %d VLantag=1 TXUnit=0 PortBitMap=%s Length=%d DestMac=%s\"" % (count, pbmp, size, dst_mac)
        ret, output = subprocess.getstatusoutput(cmd)
        # print output
        if(ret != 0 ):
            return False, output
        return True, output


    def __clear_port_packets_by_sonic(self):
        cmd = "show interfaces counters -c"
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def __clear_port_packets_by_sdk(self):
        cmd = "bcmcmd \"clear c\""
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def __check_port_packets_by_sonic(self, port, count, direc = "tx"):
        cmd = "show interfaces counters"
        strs = os.popen(cmd)
        lines = strs.readlines()
        for line in lines:
            line.strip()
            if(len(line.split()) and re.search("Ethernet[0-9]+", line.split()[0])): 
                if(self.interfaces[port - 1] == line.split()[0]):
                    if(direc == "tx"):
                        if(count == int(re.sub('[,]', '', line.split()[9]))):
                            return True, line.split()[9]
                        else:
                            #print("packets num = %s" % int(re.sub('[,]', '', line.split()[9]))) 
                            return False, line.split()[9]
                    elif(direc == "rx"):
                        if(count == int(re.sub('[,]', '', line.split()[2]))):
                            return True, line.split()[9]
                        else:
                            #print("packets num = %s" % int(re.sub('[,]', '', line.split()[2]))) 
                            return False, line.split()[9]
        return False, "fail"


    def __check_port_packets_by_sdk(self, port, count, direc = "tx"):
        if(direc == "tx"):
            cmd = "bcmcmd \"show c CLMIB_TPOK\""
            strs = os.popen(cmd)
            line = strs.read()
            if re.search(r"failed", line):
                showc = "CDMIB_TPKT"
            else :
                showc = "CLMIB_TPKT"
            cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
            strs = os.popen(cmd)
            lines = strs.readlines()
            if(lines[1].strip()):
                if(count == int(re.sub('[,]', '', lines[1].split()[2].strip("+-")))):
                    return True, lines[1].split()[2]
                else:
                    return False, lines[1].split()[2]
        elif(direc == "rx"):
            cmd = "bcmcmd \"show c CLMIB_RPOK\""
            strs = os.popen(cmd)
            line = strs.read()
            if re.search(r"failed", line):
                showc = "CDMIB_RPKT"
            else :
                showc = "CLMIB_RPKT"
            logging.debug(self.bcm_ports[port - 1])
            cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
            strs = os.popen(cmd)
            lines = strs.readlines()
            # logging.debug(lines)
            if(lines[1].strip()):
                if (count == int(re.sub('[,]', '', lines[1].split()[2].strip("+-")))):
                    return True, lines[1].split()[2]
                else:
                    return False, lines[1].split()[2]
        return False, "fail"


    ################################################################################################


    def get_port_status(self, port):
        if(self.__mode == 0):
            return self.__get_port_status_by_sdk(port)
        elif(self.__mode == 1):
            return self.__get_port_status_by_sonic(port)


    def get_port_fcs_status(self, port):
        tfcs = 0
        rfcs = 0
        cmd = "bcmcmd \"show c CLMIB_TPOK\""
        strs = os.popen(cmd)
        line = strs.read()
        if re.search(r"failed", line):
            showc = "CDMIB_TFCS"
        else :
            showc = "CLMIB_TFCS"
        cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
        strs = os.popen(cmd)
        lines = strs.readlines()
        if lines[1].strip():
            tfcs = int(re.sub('[,]', '', lines[1].split()[2]))
        cmd = "bcmcmd \"show c CLMIB_RPOK\""
        strs = os.popen(cmd)
        line = strs.read()
        if re.search(r"failed", line):
            showc = "CDMIB_RFCS"
        else :
            showc = "CLMIB_RFCS"
        cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
        strs = os.popen(cmd)
        lines = strs.readlines()
        if lines[1].strip():
            rfcs = int(re.sub('[,]', '', lines[1].split()[2]))
        if(tfcs == 0 and rfcs == 0):
            return True, (tfcs, rfcs)
        return False, (tfcs, rfcs)


    def start_send_port_packets(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff"):
        if(self.__mode == 0):
            return self.__start_send_port_packets_by_sdk(port, count, size, dst_mac)
        elif(self.__mode == 1):
            return self.__start_send_port_packets_by_sonic(port, count, size, dst_mac)
        return False, "fail"


    def stop_send_port_packets(self):
        cmd = "bcmcmd \"port xe,ce en=0\""
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        time.sleep(2)
        cmd = "bcmcmd \"port xe,ce en=1\""
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def clear_port_packets(self):
        if(self.__mode == 0):
            return self.__clear_port_packets_by_sdk()
        elif(self.__mode == 1):
            return self.__clear_port_packets_by_sonic()
        return False, "fail"


    def check_port_packets(self, port, count, direc = "tx"):
        if(self.__mode == 0):
            return self.__check_port_packets_by_sdk(port, count, direc)
        elif(self.__mode == 1):
            return self.__check_port_packets_by_sonic(port, count, direc)
        return False, "fail"


    def init_port_cpu(self):
        cmd = "bcmcmd \"cint /usr/share/sonic/platform/cpu.cint\""
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def reset_port_cpu(self):
        cmd = "bcmcmd \"cint;\r\n bcm_field_entry_destroy(0, 2048);\r\n bcm_field_group_destroy(0, 5);\r\n exit;\""
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def init_port_prbs(self):
        cmd = "bcmcmd \"cint /usr/share/sonic/platform/prbs.cint\""
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def reset_port_prbs(self):
        time.sleep(1)


    def set_port_prbs(self, port, enable):
        unit_port = self.__get_unit_port_by_bcm(port)
        cmd = "bcmcmd \"cint;\r\n set_port_prbs(%d, %d);\r\n exit;\"" % (unit_port, enable)
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def get_port_prbs_result(self, port):
        unit_port = self.__get_unit_port_by_bcm(port)
        cmd = "bcmcmd \"cint;\r\n print get_port_prbs_result(%d);\r\n exit;\"" % unit_port
        strs = os.popen(cmd)
        time.sleep(1)
        cmd = "bcmcmd \"cint;\r\n print get_port_prbs_result(%d);\r\n exit;\"" % unit_port
        strs = os.popen(cmd)
        lines = strs.readlines()
        status = int(re.findall(" = (.*?) ",lines[-5])[0])
        return status


    def test(self):
        circle = 0
        while True:
            print("circle %d:" % (circle + 1))
            self.init_port_cpu()
            self.clear_port_packets()
            for i in range(len(self.bcm_ports)):
                self.start_send_port_packets(i + 1, 10000, 1000)
            time.sleep(5)
            for i in range(len(self.bcm_ports)):
                if(self.check_port_packets(i + 1, 10000, "rx")):
                    print("port %d is ok" % (i + 1))
                else:
                    print ("error:%d" % (i + 1))
            self.reset_port_cpu()
            circle += 1

class PortPrbsTest(object):
    mac_output = []
    sys_output = []
    line_output = []
    bcm_ports = []
    standard = 0
    
    def __init__(self, standard = 1.0e-10):
        self.standard = standard
        self.__get_global_bcmports()


    def __get_global_bcmports(self):
        if(len(self.bcm_ports)):
            pass
        else: 
            pu = portutil.PortUtil()
            cmd = "bcmcmd ps"
            strs = os.popen(cmd)
            lines = strs.readlines()
            for port in pu.device_port_list:
                for line in lines:
                    line.strip()
                    if re.search(r"^.*?\(.*?\)", line) and int(re.findall(r"^.*?\((.*?)\)", line)[0].strip()) == port.logic_port:
                        self.bcm_ports.append(re.findall("^(.*?)\(.*?\)", line)[0].strip())
                        break


    def _get_mac_side_prbsstat_ber(self, port):
        results = []
        i = 0
        for line in self.mac_output:
            if ((self.bcm_ports[port - 1] + "[0]") in line) or ((self.bcm_ports[port - 1] + "[1]") in line):
                results.append(line)
                i = i + 1
        for result in results:
            i = i - 1
            ex = "[0-9]{0,}[.][0-9]{0,}[e][+][0-9]{0,}|[0-9]{0,}[.][0-9]{0,}[e][-][0-9]{0,}"
            ber = (re.search(ex,result))
            if (ber != None):
                if (float(ber.group()) > float(self.standard)):
                    return False, results
                elif(i == 0):
                    return True, results
        return False, results


    def _get_sys_side_prbsstat_ber(self, port):
        results = []
        icount = 2
        ex = "[0-9]+$"
        num = (re.search(ex, self.bcm_ports[port - 1])).group()
        num = int(num) * 2 + 1
        results.append(self.sys_output[num])
        results.append(self.sys_output[num+1])
        for result in results:
            icount = icount - 1
            ex = "[0-9]{0,}[.][0-9]{0,}[e][+][0-9]{0,}|[0-9]{0,}[.][0-9]{0,}[e][-][0-9]{0,}"
            ber = re.search(ex, result)
            if(ber != None):
                if(float(ber.group()) > float(self.standard)):
                    return False, results
                elif(icount == 0):
                    return True, results
        return False, results


    def _get_line_side_prbsstat_ber(self, port):
        results = []
        icount = 4
        ex = "[0-9]+$"
        num = (re.search(ex, self.bcm_ports[port - 1])).group()
        num = int(num) * 4 + 1
        results.append(self.line_output[num])
        results.append(self.line_output[num + 1])
        results.append(self.line_output[num + 2])
        results.append(self.line_output[num + 3])
        for result in results:
            icount = icount - 1
            ex = "[0-9]{0,}[.][0-9]{0,}[e][+][0-9]{0,}|[0-9]{0,}[.][0-9]{0,}[e][-][0-9]{0,}"
            ber = re.search(ex, result)
            if(ber != None):
                if(float(ber.group()) > float(self.standard)):
                    return False, results
                elif(icount == 0):
                    return True, results
        return False, results


    def init_port_prbs(self):
        cmd = 'bcmcmd "phy diag ce prbs set p=3"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=1 p=5"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0 p=5"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy diag ce prbs get"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy diag ce prbs get"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy diag ce prbsstat start i=120"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=1"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
             return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
             return False, output
        time.sleep(120)
        cmd = 'bcmcmd "phy control ce prbs lnside=1 time=120 cal=1"'
        ret, output = subprocess.getstatusoutput(cmd)
        self.sys_output = output.split("\r\n")
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0 time=120 cal=1"'
        ret, output = subprocess.getstatusoutput(cmd)
        self.line_output = output.split("\r\n")
        if(ret != 0):
            return False, output
        time.sleep(30)
        cmd = 'bcmcmd "phy diag ce prbsstat ber"'
        ret, output = subprocess.getstatusoutput(cmd)
        self.mac_output = output.split("\r\n")
        if(ret != 0):
            return False, output
        return True, output


    def clear_port_prbs(self):
        cmd = 'bcmcmd "phy diag ce prbs clear"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=1 clear=1"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0 clear=1"'
        ret, output = subprocess.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def get_port_prbs_result(self, flag, port):
        if (flag == "mac"):
            ret, output = self._get_mac_side_prbsstat_ber(port)
            return ret,output
        elif (flag == "sys"):
            ret, output = self._get_sys_side_prbsstat_ber(port)
            return ret, output
        elif (flag == "line"):
            ret, output = self._get_line_side_prbsstat_ber(port)
            return ret, output
        else:
            return False, "fail"

###################### HSDK Class ######################

class PortHsdkClass():
    '''PortHsdkClass is used to store aliases and related information of ports at different levels'''

    def __init__(self, **kwargs):

        lport = kwargs.get("lport", 0)
        bcm_port = kwargs.get("bcm_port", "")
        interface = kwargs.get("interface", "")
        unit_port = kwargs.get("unit_port", 0)
        phy_port = kwargs.get("phy_port", 0)

        self._lport = lport
        self._interface = interface
        self._bcm_port = bcm_port
        self._unit_port = unit_port
        self._phy_port = phy_port

    @property
    def lport(self):
        '''return lport'''

        return self._lport

    @property
    def interface(self):
        '''return interface'''

        return self._interface

    @property
    def bcm_port(self):
        '''return bcm_port'''

        return self._bcm_port

    @property
    def unit_port(self):
        '''return unit_port'''

        return self._unit_port

    @property
    def phy_port(self):
        '''return phy_port'''

        return self._phy_port

    def set_lport(self, lport):
        '''set lport'''

        self._lport = lport

    def set_interface(self, interface):
        '''set interface'''

        self._interface = interface

    def set_bcm_port(self, bcm_port):
        '''set bcm_port'''

        self._bcm_port = bcm_port

    def set_unit_port(self, unit_port):
        '''set unit_port'''

        self._unit_port = unit_port

    def set_phy_port(self, phy_port):
        '''set phy_port'''

        self._phy_port = phy_port

class PortHsdkUtil():
    '''Port utility class'''

    @staticmethod
    def get_config_bcm_path():
        '''return config_bcm address'''

        config_bcm_path = ""
        try:
            (platform, hwsku) = get_platform_and_hwsku()
            platform_path = "/".join([PLATFORM_ROOT_PATH, platform])
            hwsku_path = "/".join([platform_path, hwsku])
            saiprofile_path = "/".join([hwsku_path, SAI_PROFILE])
            with open(saiprofile_path, "r") as saiprofile_f:
                for line in saiprofile_f:
                    if re.search('%s(.*?)$' % SAI_PROFILE_PREDIX, line):
                        config_bcm = re.findall(r"%s(.*?)$" % SAI_PROFILE_PREDIX, line)[0]
                        config_bcm_path = "/".join([hwsku_path, config_bcm])
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)

        return config_bcm_path

    @staticmethod
    def get_port_config_path():
        '''return port_config address'''

        port_config_path = get_path_to_port_config_file()
        return port_config_path

    @staticmethod
    def get_onie_platform():
        '''get onie_platform'''

        log_debug("获取onie_platform")
        with open(MACHINE_FILE, "r") as machine_f:
            for line in machine_f:
                if(re.search('%s(.*?)$' % MACHINE_PLATFORM_PREDIX, line)):
                    onie_platform = re.findall(r"%s(.*?)$" % MACHINE_PLATFORM_PREDIX, line)[0]
                    global global_onie_platform
                    global_onie_platform = onie_platform
                    log_debug("onie_platform:%s" % global_onie_platform)
                    return onie_platform
        return None

    class ReUtil():
        '''regular utility class'''

        @staticmethod
        def is_port_id_line(line):
            '''determine whether port_id line'''

            if re.search('_PORT_ID:(.*?)$', line.strip()):
                return False
            elif re.search('PORT_ID: \[', line.strip()):
                return False
            elif re.search('PORT_ID:(.*?)$', line.strip()):
                return True
            return False

        @staticmethod
        def is_pc_phys_port_id_line(line):
            '''determine whether pc_phys_phy_port_id line'''

            if re.search('PC_PHYS_PORT_ID:(.*?)$', line.strip()):
                return True
            return False

        @staticmethod
        def yaml_getre_unit_port(line):
            return int(re.findall(r"PORT_ID:(.*?)$", line.strip())[0])

        @staticmethod
        def yaml_getre_phy_port(line):
            return int(re.findall(r"PC_PHYS_PORT_ID:(.*?)$", line.strip())[0])

        @staticmethod
        def getre_port_status(output):
            '''parse the return result,get port up/down status'''
            lines = output.split("\n")

            if len(lines) > 3:
                if re.search("up", lines[3]):
                    return True, "up"
                elif re.search("!ena", lines[3]):
                    return True, "!ena"
                elif re.search("down", lines[3]):
                    return True, "down"
                else:
                    return False, output
            else:
                return False, output

        @staticmethod
        def is_unit_port_line(line, unit_port):
            '''determine whether save unit_port line'''

            if (re.search(r"^.*?\(.*?\)", line) and
                    int(re.findall(r"^.*?\((.*?)\)", line)[0].strip()) == unit_port):
                return True
            return False

        @staticmethod
        def getre_output_bcm_port(output):
            '''parse the return result,get bcm_port/mgmt_bcm_port'''

            return re.findall(r"^(.*?)\(.*?\)", output)[0].strip()

        @staticmethod
        def getre_output_packets_count(line):
            '''parse the return result,get the number of received/sent packets'''
            if (len(line.split())) > 2:
                return int(re.sub('[,]', '', line.split()[2].strip("+-")))
            else:
                return 0

        @staticmethod
        def getre_output_unit_port(output):
            '''parse the return result,get unit_port'''

            return int((output.split(')')[0]).split('(')[1])

        @staticmethod
        def getre_output_speed(line):
            '''parse the return result,get speed'''

            if (len(line.split())) > 4:
                speed = (line.split("FD"))[0].split()[-1]
                if "G" in speed:
                    return speed
            return None

class PortHsdkTest():
    '''PortHsdkTest parent class'''

    device_port_list = []
    bcm_ports = []
    prbs_port_range = None
    standard_ber_val = None
    prbs_time = None

    def __init__(self):
        if global_onie_platform == "":
            PortHsdkUtil.get_onie_platform()
        self.get_factest_port_config()
        if len(self.device_port_list) == 0:
            self._config_yaml_file = io.open(PortHsdkUtil.get_config_bcm_path(), 'r', encoding="utf-8")
            self._port_config_file = open(PortHsdkUtil.get_port_config_path(), 'r+')
            self.__parse_port_config()
            self.__parse_yaml_data()
            self.__get_global_bcmports()
            self._config_yaml_file.flush()
            self._port_config_file.flush()
            self._config_yaml_file.close()
            self._port_config_file.close()
        if self.prbs_time is None:
            self.prbs_time = global_port_config.get("prbs_time", PRBS_TIME_DEFAULT)
        if self.standard_ber_val is None:
            self.standard_ber_val = global_port_config.get("prbs_ber", PRBS_BER_DEFAULT)

    @abc.abstractmethod
    def init_test(self):
        '''abstract method, to be inherited'''

        return None

    @abc.abstractmethod
    def start_test(self, **kwargs):
        '''abstract method, to be inherited'''

        return None

    @abc.abstractmethod
    def check_test(self, **kwargs):
        '''abstract method, to be inherited'''

        return None

    @abc.abstractmethod
    def del_test(self):
        '''abstract method, to be inherited'''

        return None

    def __parse_port_config(self):
        '''parse port_config, get lport, interface, phy_port'''

        log_debug("解析port_config")
        lport_num = 0
        for line in self._port_config_file:
            line.strip()
            if len(line.split()) > 0 and re.search("Eth", line.split()[0]):
                lport_num = lport_num + 1
                phy_port_t = int(line.split()[1].split(',')[0])
                self.device_port_list.append(PortHsdkClass(lport=lport_num,
                                                           interface=line.split()[0],
                                                           phy_port=phy_port_t))

    def __parse_yaml_data(self):
        '''parse yaml port_id,phy_port_id of line configuration '''

        log_debug("解析yaml")
        unit_port = 0
        phy_port = 0
        curr_line_num = 0
        port_id_line = 0
        phy_port_id_line = 0
        reutil = PortHsdkUtil.ReUtil()
        for line in self._config_yaml_file:
            curr_line_num = curr_line_num + 1
            if reutil.is_port_id_line(line):
                port_id_line = curr_line_num
                unit_port = reutil.yaml_getre_unit_port(line)
            if (curr_line_num == (port_id_line + 2)):
                if reutil.is_pc_phys_port_id_line(line):
                    phy_port_id_line = curr_line_num
                    phy_port = reutil.yaml_getre_phy_port(line)
                    for port_obj in self.device_port_list:
                        if port_obj.phy_port == phy_port:
                            port_obj.set_unit_port(unit_port)
                            break

    def __get_global_bcmports(self):
        '''get ps returns the result bcm_port, unit_port part'''

        cmd = get_sdk_cmd("ps")
        ret, output = port_getstatusoutput(cmd)
        lines = output.split("\n")
        if ret == 0:
            for line in lines:
                if (re.search('(.*?)\((.*?)$', line.strip())):
                    unit_port = PortHsdkUtil.ReUtil.getre_output_unit_port(line)
                    bcm_port = PortHsdkUtil.ReUtil.getre_output_bcm_port(line)
                    for port_obj in self.device_port_list:
                        if port_obj.unit_port == unit_port:
                            port_obj.set_bcm_port(bcm_port)
                            break
            for port_obj in self.device_port_list:
                self.bcm_ports.append(str(port_obj.bcm_port))
            log_debug("bcm_ports:%s" % self.bcm_ports)

    def get_port_status(self, port):
        '''get port up/down status, return up/down/!ena'''

        # get bcm_port
        cmd = get_sdk_cmd("ps %s" % self.device_port_list[port - 1].bcm_port)
        ret, output = port_getstatusoutput(cmd)

        if ret == 0:
            return PortHsdkUtil.ReUtil.getre_port_status(output)
        return False, output

    @classmethod
    def clear_port_packets(cls):
        '''clear SDK statistical message'''

        # use SDK command clear port_packets
        # clear statistical message
        cmd = get_sdk_cmd("clear c")
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output

        log_debug("clear_port_packets success")
        return True, output

    def start_send_port_packets(self, port, count, size, dst_mac):
        '''use SDK command to send packets'''

        # ues tx Order contract
        cmd = get_sdk_cmd("tx %d VLantag=4048 PortBitMap=%s Length=%d DestMac=%s"
               % (count, self.device_port_list[port - 1].bcm_port, size, dst_mac))
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        return True, output

    def vlan_config(self, vlan):
        '''test vlan configuration'''

        # Clear the previously configured  vlan
        ret, output = self.vlan_config_clear()
        if ret is False:
            log_warning("vlan_config fail, output:%s" % output)
            return False, "vlan_config fail, output:%s" % output

        # Configure vlans for all ports
        for i in range(len(self.device_port_list)):
            bcm_port = self.device_port_list[i].bcm_port
            if i == 0:
                # set vlan,the first port create, And then add
                cmd = get_sdk_cmd("vlan create %d PortBitMap=%s UntagBitMap=%s" % (vlan,
                                                                                   bcm_port,
                                                                                   bcm_port))
            else:
                cmd = get_sdk_cmd("vlan add %d PortBitMap=%s UntagBitMap=%s" % (vlan,
                                                                                bcm_port,
                                                                                bcm_port))
            ret, output = port_getstatusoutput(cmd)
            if ret != 0:
                log_warning("vlan_config vlan create or add fail, output:%s" % output)
                return False, "vlan_config vlan create or add fail, output:%s" % output

            # set pvlan
            cmd = get_sdk_cmd("pvlan set %s %d" % (bcm_port, vlan))
            ret, output = port_getstatusoutput(cmd)
            if ret != 0:
                log_warning("vlan_config pvlan set fail, output:%s" % output)
                return False, "vlan_config pvlan set fail, output:%s" % output

        log_debug("vlan_config success")
        return True, "vlan_config success"

    @classmethod
    def vlan_config_clear(cls):
        '''ports test vlan environmental restoration'''

        cmd = get_sdk_cmd("vlan clear")
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            log_warning("vlan_config_clear fail, output:%s" % output)
            return False, "vlan_config_clear fail, output:%s" % output

        log_debug("vlan_config_clear success")
        return True, "vlan_config_clear success"

    def get_mgmt_bcmport(self, mgmt_eth):
        '''get mgmt bcmport'''

        cmd = get_sdk_cmd("ps")
        ret, output = port_getstatusoutput(cmd)
        lines = output.split("\n")
        if ret == 0:
            unit_port = global_port_config["mgmt_kt_ports"][mgmt_eth]
            for line in lines:
                line.strip()
                if PortHsdkUtil.ReUtil.is_unit_port_line(line, unit_port):
                    bcmport = PortHsdkUtil.ReUtil.getre_output_bcm_port(line)
                    log_debug("%s : %s" % (mgmt_eth, bcmport))
                    return bcmport
        return None

    def set_all_mgmt_enable(self, enable):
        '''control all mgmt enable'''

        # perform operations on all internal management ports,set en=0/1
        # enable = 1 up down
        # enable = 0 !ena
        cmd = None
        try:
            cmd = get_sdk_cmd("port %s en=%d" % (",".join(self.get_mgmt_bcmport(item)
                                                        for item
                                                        in global_port_config["mgmt_kt_ports"]), enable))
        except Exception as except_result:
            msg = traceback.format_exc()
            log_error("Exception_info:\n%s" % msg)
            return False, "set_all_mgmt_enable:%d fail, output:%s" % (enable, msg)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            log_warning("set_all_mgmt_enable:%d fail, output:%s" % (enable, output))
            return False, "set_all_mgmt_enable:%d fail, output:%s" % (enable, output)

        log_debug("set_all_mgmt_enable:%d success" % enable)
        return True, "set_all_mgmt_enable:%d success" % enable

    def port_stp_config(self, enable):
        '''Spanning tree protocol configuration'''

        if enable == 1:
            log_debug("开启STP")
            cmd = get_sdk_cmd("stg stp 1 all forward")
            ret, output = port_getstatusoutput(cmd)
            if ret == 0:
                # turn off spanning tree protocol of the internal management interface
                cmd = get_sdk_cmd("stg stp 1 %s disable" % (",".join(self.get_mgmt_bcmport(item)
                                                            for item
                                                            in global_port_config["mgmt_kt_ports"])))
                ret, output = port_getstatusoutput(cmd)
        else:
            log_debug("关闭STP")
            cmd = get_sdk_cmd("stg stp 1 all disable")
            ret, output = port_getstatusoutput(cmd)

        if ret != 0:
            return False, "port_stp_config fail, output:%s" % output
        return True, "port_stp_config success"

    def get_unit_port_list(self, port_list):
        '''get up port unit_port list'''

        self.set_global_unit_port_list_null()
        for port in port_list:
            unit_port = self.device_port_list[port - 1].unit_port
            global global_unit_port_list
            global_unit_port_list.append(unit_port)
        log_debug("unit_port_list:%s" % global_unit_port_list)

    @classmethod
    def get_min_max_unit_port(cls):
        '''get unit_port Smallest and largest in the list'''

        min_unit_port = 1
        max_unit_port = 1
        if len(global_unit_port_list) > 0:
            min_unit_port = int(min(global_unit_port_list))
            max_unit_port = int(max(global_unit_port_list))
        log_debug("min_unit_port = %d max_unit_port = %d" % (min_unit_port, max_unit_port))
        return min_unit_port, max_unit_port

    def get_prbs_port_range(self):
        '''obtain panel port unit_port range(exclusive mgmt port and loopback port)'''

        self.prbs_port_range = global_port_config.get("prbs_port_range", None)
        if self.prbs_port_range is None:
            min_unit_port, max_unit_port = self.get_min_max_unit_port()
            self.prbs_port_range = "%s-%s"  % (str(min_unit_port), str(max_unit_port))

    @classmethod
    def set_global_unit_port_list_null(cls):
        global global_unit_port_list
        global_unit_port_list = []

    def get_factest_port_config_flag(self):
        return global_port_config["flag"]

    def get_factest_port_config(self):
        if self.get_factest_port_config_flag() is False:
            port_config = {
                "hsdk_device" : 1,
                "mgmt_kt_ports" : {},
                "prbs_port_range" : "",
                "extphy_device" : 0,
                "prbs_ber" : PRBS_BER_DEFAULT,
                "prbs_time" : PRBS_TIME_DEFAULT,
                "port_frame_test_retrynum": 1,# Number of frame retries (internal retries)
                "port_brcst_test_retrynum": 1,# Number of port broadcast test retries (internal retries)
                "port_prbs_test_retrynum": 1,# Number of port PRBS test retries (internal retries)
                "port_kr_test_retrynum": 1,# Internal management port Test Retry count (Internal retry)
                "port_frame_del_time": 10,# Waiting time of recovering the test environment from sending and receiving frames on the port (s)
                "port_brcst_del_time": 10,# Port Broadcast Test Recovery Test environment Waiting time (s)
                "port_prbs_del_time": 10,# Port PRBS Test Recovery Test environment Waiting time (s)
                "port_kr_del_time": 10,# Internal management interface Test Recovery Test environment Waiting time (s)
                "port_log_level": LOG_ERROR_LEVEL,# PORT component log level
                "flag" : False
            }
            try:
                port_config["mgmt_kt_ports"] = copy.deepcopy(global_mgmt_kr_ports[global_onie_platform])
                log_debug("mgmt_kt_ports: %s" % port_config["mgmt_kt_ports"])

                port_config["prbs_port_range"] = global_prbs_port_range.get(global_onie_platform, None)
                log_debug("prbs_port_range: %s" % port_config["prbs_port_range"])

                port_config["hsdk_device"] = global_hsdk_device.get(global_onie_platform, 0)
                log_debug("hsdk_device: %s" % port_config["hsdk_device"])

                port_config["extphy_device"] = global_extphy_device.get(global_onie_platform, 0)
                log_debug("extphy_device: %s" % port_config["extphy_device"])

                port_config["prbs_ber"] = global_prbs_ber.get(global_onie_platform, PRBS_BER_DEFAULT)
                log_debug("prbs_ber: %s" % port_config["prbs_ber"])

                port_config["prbs_time"] = global_prbs_time.get(global_onie_platform, PRBS_TIME_DEFAULT)
                log_debug("prbs_time: %s" % port_config["prbs_time"])

                port_config["port_frame_test_retrynum"] = PORT_FACTEST_CONFIG["port_frame_test_retrynum"]
                log_debug("port_frame_test_retrynum: %s" % port_config["port_frame_test_retrynum"])

                port_config["port_brcst_test_retrynum"] = PORT_FACTEST_CONFIG["port_brcst_test_retrynum"]
                log_debug("port_brcst_test_retrynum: %s" % port_config["port_brcst_test_retrynum"])

                port_config["port_prbs_test_retrynum"] = PORT_FACTEST_CONFIG["port_prbs_test_retrynum"]
                log_debug("port_prbs_test_retrynum: %s" % port_config["port_prbs_test_retrynum"])

                port_config["port_kr_test_retrynum"] = PORT_FACTEST_CONFIG["port_kr_test_retrynum"]
                log_debug("port_kr_test_retrynum: %s" % port_config["port_kr_test_retrynum"])

                port_config["port_frame_del_time"] = PORT_FACTEST_CONFIG["port_frame_del_time"]
                log_debug("port_frame_del_time: %s" % port_config["port_frame_del_time"])

                port_config["port_brcst_del_time"] = PORT_FACTEST_CONFIG["port_brcst_del_time"]
                log_debug("port_brcst_del_time: %s" % port_config["port_brcst_del_time"])

                port_config["port_prbs_del_time"] = PORT_FACTEST_CONFIG["port_prbs_del_time"]
                log_debug("port_prbs_del_time: %s" % port_config["port_prbs_del_time"])

                port_config["port_kr_del_time"] = PORT_FACTEST_CONFIG["port_kr_del_time"]
                log_debug("port_kr_del_time: %s" % port_config["port_kr_del_time"])

                port_config["port_log_level"] = PORT_FACTEST_CONFIG["port_log_level"]
                log_debug("port_log_level: %s" % port_config["port_log_level"])
            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)

            port_config["flag"] = True
            global global_port_config
            global_port_config = copy.deepcopy(port_config)
            log_debug("global_port_config: %s" % global_port_config)

@singleton
class PortHsdkFrameTest(PortHsdkTest):
    '''port frame'''

    def init_test(self):
        '''port frame init test'''

        log_debug("init_test")
        ret, output = self.clear_port_packets()
        if ret is False:
            log_error("clear_port_packets fail, output:%s" % output)
            return False, "clear_port_packets fail, output:%s" % output

        ret, output = self.cpu_create()
        if ret is False:
            log_error("cpu_create fail, output:%s" % output)
            return False, "cpu_create fail, output:%s" % output

        ret, output = self.port_stp_config(1)
        if ret is False:
            log_error("port_stp_config fail, output:%s" % output)
            return False, "port_stp_config fail, output:%s" % output

        ret, output = self.vlan_config(PORT_TEST_VLAN)
        if ret is False:
            log_error("vlan_config fail, output:%s" % output)
            return False, "vlan_config fail, output:%s" % output

        log_debug("init_test success")
        return True, "init_test success"

    def start_test(self, **kwargs):
        '''port frame start test'''

        port = kwargs["port"]
        count = kwargs.get("count", PACKETS_COUNT)
        size = kwargs.get("size", PACKETS_SIZE)
        dst_mac = kwargs.get("dst_mac", PACKETS_DST_MAC)

        log_debug("start_test")
        return self.start_send_port_packets(port, count, size, dst_mac)

    def check_test(self, **kwargs):
        '''port frame check test'''

        port = kwargs["port"]
        count = kwargs.get("count", PACKETS_COUNT)
        direc = kwargs.get("direc", "tx")

        log_debug("check_test")
        return self.check_port_packets(port, count, direc)

    def del_test(self):
        '''port frame test environment recover'''

        log_debug("del_test")
        ret, output = self.vlan_config_clear()
        if ret is False:
            log_error("vlan_config_clear fail, output:%s" % output)
            return False, output

        ret, output = self.cpu_destroy()
        if ret is False:
            log_error("cpu_destroy fail,%s" % output)
            return False, "cpu_destroy fail,%s" % output

        ret, output = self.port_stp_config(0)
        if ret is False:
            log_error("port_stp_config fail, output:%s" % output)
            return False, output

        log_debug("del_test success")
        return True, "cpu_destroy success"

    def check_port_packets(self, port, count, direc="tx"):
        '''check port frame test result '''
        # Obtain the statistics result of a specific port,If the port receives the same number as it sends.
        # return port succeeded. Otherwise, the port failed and the failure cause are displayed.

        if direc == "tx":
            return self.check_port_packets_tx(port, count)
        if direc == "rx":
            return self.check_port_packets_rx(port, count)

        return False, "check_port_packets_fail"

    def check_port_packets_tx(self, port, count):
        '''direc == "tx"'''

        # View statistics on sent and received packets
        count_pkt = 0
        count_1518 = 0
        result_str = ""
        bcm_port = self.device_port_list[port - 1].bcm_port
        log_debug("bcm_port:%s direc:tx" % bcm_port)

        cmd = get_sdk_cmd("show c %s" % bcm_port)
        ret, output = port_getstatusoutput(cmd)
        lines = output.split("\n")
        if ret == 0:
            for line in lines:
                if (re.search('XLMIB_TPKT(.*?)$', line.strip())):
                    count_pkt = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
                elif (re.search('XLMIB_T1518(.*?)$', line.strip())):
                    count_1518 = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
        else:
            return False, output

        log_debug("count:%d" % count)
        log_debug("count_pkt:%d" % count_pkt)
        log_debug("count_1518:%d" % count_1518)
        result_str += "count:%d\n" % count
        result_str += "count_pkt:%d\n" % count_pkt
        result_str += "count_1518:%d\n" % count_1518

        if (count_pkt == 0 or count_1518 == 0):
            result_str += "output:%s\n" % output
            log_warning("output:%s" % output)
        if (count == count_pkt and count == count_1518):
            log_debug("check_port_packets tx success")
            return True, result_str

        log_warning("check_port_packets_tx_fail, output:%s" % output)
        return False, result_str

    def check_port_packets_rx(self, port, count):
        '''direc == "rx"'''

        # View statistics on sent and received packets
        count_pkt = 0
        count_1518 = 0
        result_str = ""
        bcm_port = self.device_port_list[port - 1].bcm_port
        log_debug("bcm_port:%s direc:rx" % bcm_port)

        cmd = get_sdk_cmd("show c %s" % bcm_port)
        ret, output = port_getstatusoutput(cmd)
        if ret == 0:
            lines = output.split("\n")
            for line in lines:
                if (re.search('XLMIB_RPKT(.*?)$', line.strip())):
                    count_pkt = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
                elif (re.search('XLMIB_R1518(.*?)$', line.strip())):
                    count_1518 = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
        else:
            return False, output

        log_debug("count:%d" % count)
        log_debug("count_pkt:%d" % count_pkt)
        log_debug("count_1518:%d" % count_1518)
        result_str += "count:%d\n" % count
        result_str += "count_pkt:%d\n" % count_pkt
        result_str += "count_1518:%d\n" % count_1518

        if (count_pkt == 0 or count_1518 == 0):
            result_str += "output:%s\n" % output
            log_warning("output:%s" % output)
        if (count == count_pkt and count == count_1518):
            log_debug("check_port_packets rx success")
            return True, result_str

        log_warning("check_port_packets_rx_fail, output:%s" % output)
        return False, result_str

    def cpu_create(self):
        '''use cpu_create.cint'''

        cmd = get_sdk_cmd("cint /usr/share/sonic/device/%s/cpu_create.cint" % global_onie_platform)
        ret, output = port_getstatusoutput(cmd)
        if(ret != 0):
            return False, output

        log_debug("cpu_create success")
        return True, output

    def cpu_destroy(self):
        '''use cpu_destroy.cint'''

        cmd = get_sdk_cmd("cint /usr/share/sonic/device/%s/cpu_destroy.cint" % global_onie_platform)
        ret, output = port_getstatusoutput(cmd)
        if(ret != 0):
            return False, output

        log_debug("cpu_destroy success")
        return True, output

@singleton
class PortHsdkBrcstTest(PortHsdkTest):
    '''port radio'''

    def init_test(self):
        '''port radio init test'''

        ret, output = self.clear_port_packets()
        if ret is False:
            log_error("clear_port_packets fail, output:%s" % output)
            return False, "clear_port_packets fail, output:%s" % output

        ret, output = self.port_stp_config(1)
        if ret is False:
            log_error("port_stp_config fail, output:%s" % output)
            return False, "port_stp_config fail, output:%s" % output

        ret, output = self.vlan_config(PORT_TEST_VLAN)
        if ret is False:
            log_error("vlan_config fail, output:%s" % output)
            return False, "vlan_config fail, output:%s" % output

        log_debug("init_test success")
        return True, "init_test success"

    def start_test(self, **kwargs):
        '''port radio start test'''

        port = kwargs["port"]
        count = kwargs["count"]
        size = kwargs.get("size", PACKETS_SIZE)
        dst_mac = kwargs.get("dst_mac", PACKETS_DST_MAC)

        log_debug("start_test")
        return self.start_send_port_packets(port, count, size, dst_mac)

    def check_test(self, **kwargs):
        '''check port radio test results'''

        port = kwargs["port"]

        log_debug("check_test")
        return self.get_port_fcs_status(port)

    def del_test(self):
        '''port radio test test environment recover'''

        log_debug("del_test")
        ret, output = self.vlan_config_clear()
        if ret is False:
            log_error("vlan_config_clear fail, output:%s" % output)
            return False, output

        ret, output = self.stop_send_port_packets()
        if ret is False:
            log_error("stop_send_port_packets fail, output:%s" % output)
            return False, output

        ret, output = self.port_stp_config(0)
        if ret is False:
            log_error("port_stp_config fail, output:%s" % output)
            return False, output

        return True, "del_test success"

    def get_port_fcs_status(self, port):
        '''check the port broadcast test result'''

        tfcs = 0
        rfcs = 0
        result_str = ""
        # View statistics on sent and received packets
        bcm_port = self.device_port_list[port - 1].bcm_port
        cmd = get_sdk_cmd("show c %s" % bcm_port)
        ret, output = port_getstatusoutput(cmd)
        if ret == 0:
            lines = output.split("\n")
            for line in lines:
                if (re.search('XLMIB_TFCS(.*?)$', line.strip())):
                    tfcs = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
                    log_warning("tfcs: %d" % tfcs)
                elif (re.search('XLMIB_RFCS(.*?)$', line.strip())):
                    rfcs = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
                    log_warning("rfcs: %d" % rfcs)

            result_str += "tfcs:%d\n" % tfcs
            result_str += "rfcs:%d\n" % rfcs

            if (tfcs == 0 and rfcs == 0):
                ret, output = self.get_port_fcs_status_f(bcm_port, lines)
                if ret is True:
                    return True, result_str
                else:
                    result_str += output
            return False, result_str
        else:
            return False, output

    def stop_send_port_packets(self):
        '''The port broadcast test stopped sending packets'''

        # do xe,ce operate,set en=0/1 -> change to  all
        # enable = 1 up down
        # enable = 0 !ena
        cmd = get_sdk_cmd("port all en=0")
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        time.sleep(5)

        cmd = get_sdk_cmd("port all en=1")
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output

        ret, output = self.set_all_mgmt_enable(0)
        if ret is False:
            log_error("stop_send_port_packets fail, output:%s" % output)
            return False, "stop_send_port_packets fail, output:%s" % output

        time.sleep(5)

        log_debug("stop_send_port_packets success")
        return True, "stop_send_port_packets success"

    def get_port_fcs_status_f(self, bcm_port, lines):
        '''Check the port broadcast test result to check whether the port receives and sends packets'''

        tpkt = 0
        rpkt = 0
        # View statistics on sent and received packets
        for line in lines:
            if (re.search('XLMIB_TPKT(.*?)$', line.strip())):
                tpkt = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
                log_debug("%s tpkt: %d" % (bcm_port, tpkt))

            elif (re.search('XLMIB_RPKT(.*?)$', line.strip())):
                rpkt = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
                log_debug("%s rpkt: %d" % (bcm_port, rpkt))

        if tpkt > 0 and rpkt > 0:
            log_debug("%s get_port_fcs_status_f success" % bcm_port)
            return True, "%s get_port_fcs_status_f success" % bcm_port
        else:
            log_error("%s get_port_fcs_status_f fail, tpkt:%d rpkt:%d" % (bcm_port, rpkt, tpkt))
            return False, "%s get_port_fcs_status_f fail, tpkt:%d rpkt:%d" % (bcm_port, rpkt, tpkt)

class PortHsdkPrbsTest(PortHsdkTest):
    '''port PRBS parent class'''

    def init_test(self):
        '''To inherit'''

        return None

    def start_test(self, **kwargs):
        '''To inherit'''

        return None

    def check_test(self, **kwargs):
        '''To inherit'''

        return None

    def del_test(self):
        '''To inherit'''

        return None

@singleton
class PortHsdkPrbsExtPhyTest(PortHsdkPrbsTest):
    '''ExtPhy prbs'''

    def init_test(self):
        '''port ExtPhy prbs init test'''

        log_debug("init_test")
        return self.clear_port_prbs()

    def start_test(self, **kwargs):
        '''port ExtPhy prbs start test'''

        test_type = kwargs["test_type"]

        log_debug("start_test")
        return self.start_port_prbs(test_type)

    def check_test(self, **kwargs):
        '''port ExtPhy prbs test result get'''

        test_type = kwargs["test_type"]
        upports = kwargs["uprt"]
        result_dict = kwargs["r_dict"]

        log_debug("check_test")
        return self.get_port_prbs_ext_result(test_type=test_type,
                                             uprt=upports,
                                             r_dict=result_dict)

    def del_test(self):
        ''' port ExtPhy prbs test environment recover'''

        log_debug("del_test")
        return self.clear_port_prbs()

    def start_port_prbs(self, test_type):
        '''ExtPhy prbs test result get'''

        if test_type == "prbs_mac":
            return self.start_port_prbs_mac()

        if test_type == "prbs_sys":
            return self.start_port_prbs_sys()

        if test_type == "prbs_line":
            return self.start_port_prbs_line()

        log_warning("start_port_prbs fail, test_type=%s" % str(test_type))
        return False, "start_port_prbs fail, test_type=%s" % str(test_type)

    def start_port_prbs_mac(self):
        '''start mac_sys port of prbs test,get mac port of prbs result'''

        # set mac port of PRBS,default configuration is PRBS31
        cmd = get_sdk_cmd("dsh -c 'phy diag %s prbs set p=3'" % self.prbs_port_range)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, "start_port_prbs_mac fail %s" % output

        # set sys port of PRBS,default configuration is PRBS31
        cmd = get_sdk_cmd("dsh -c 'phy control %s setprbs lnside=1 p=5'" % self.prbs_port_range)
        ret, output = port_getstatusoutput(cmd, time_sleep=5)
        if ret != 0:
            return False, "start_port_prbs_mac fail %s" % output

        cmd = get_sdk_cmd("dsh -c 'phy diag %s prbs get'" % self.prbs_port_range)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, "start_port_prbs_mac fail %s" % output

        cmd = get_sdk_cmd("dsh -c 'phy diag %s prbsstat start interval=%d'" % (self.prbs_port_range, self.prbs_time))
        ret, output = port_getstatusoutput(cmd, time_sleep=(self.prbs_time + 10))
        if ret != 0:
            return False, "start_port_prbs_mac fail %s" % output

        return True, "start_port_prbs_mac success"

    def start_port_prbs_sys(self):
        '''start mac_sys port of prbs test,get sys port of prbs result'''

        # set mac pert of PRBS,default configuration is PRBS31
        cmd = get_sdk_cmd("dsh -c 'phy diag %s prbs set p=3'" % self.prbs_port_range)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, "start_port_prbs_sys fail %s" % output

        # set sys port of PRBS,default configuration is PRBS31
        cmd = get_sdk_cmd("dsh -c 'phy control %s setprbs lnside=1 p=5'" % self.prbs_port_range)
        ret, output = port_getstatusoutput(cmd, time_sleep=5)
        if ret != 0:
            return False, "start_port_prbs_sys fail %s" % output

        # The newly packaged command to get PRBS test results contains get, so get is not needed here

        return True, "start_port_prbs_sys success"

    def start_port_prbs_line(self):
        '''start line poart prbs test,get line port prbs result'''

        # set line port of PRBS,default configuration is PRBS31
        cmd = get_sdk_cmd("dsh -c 'phy control %s setprbs lnside=0 p=5'" % self.prbs_port_range)
        ret, output = port_getstatusoutput(cmd, time_sleep=5)
        if ret != 0:
            return False, "start_port_prbs_line fail %s" % output

        # The newly packaged command to get PRBS test results contains get, so get is not needed here

        return True, "start_port_prbs_line success"

    def get_port_prbs_ext_result(self, **kwargs):
        '''ExtPhy prbs get test result'''
        test_type = kwargs["test_type"]
        upports = kwargs["uprt"]
        result_dict = kwargs["r_dict"]

        if test_type == "prbs_mac":
            return self.get_prbs_mac_result(upports, result_dict)

        if test_type == "prbs_sys":
            return self.get_prbs_sys_result(upports, result_dict)

        if test_type == "prbs_line":
            return self.get_prbs_line_result(upports, result_dict)

        log_warning("get_port_prbs_ext_result fail, test_type=%s" % str(test_type))
        return False, "get_port_prbs_ext_result fail, test_type=%s" % str(test_type)

    def get_prbs_mac_result(self, upports, result_dict):
        '''get mac port prbsstat_ber'''
        result_dict["successports"] = []
        result_dict["errorports"] = []

        cmd = get_sdk_cmd("dsh -c 'phy diag %s prbsstat ber'" % self.prbs_port_range)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            other_info = result_dict.get("other_info", "")
            result_dict["other_info"] = other_info + output
            return False, result_dict

        lines = output.split("\n")
        for port in upports:
            prbs_ber_flag = 0
            prbs_ber_test_fail = 0
            output_content = ""
            lport = self.device_port_list[port - 1].lport
            unit_port = self.device_port_list[port - 1].unit_port
            bcm_port = self.device_port_list[port - 1].bcm_port
            output_content_port_info = "port:%-3d %s(%d)" % (lport, bcm_port, unit_port)
            for line in lines:
                if (re.search('.*].*e', line.strip())):
                    line_unit_port = int(line.split('[')[0])
                    if unit_port == line_unit_port:
                        prbs_ber_flag = 1
                        lane_num = int((line.split(']')[0]).split('[')[1])
                        prbs_ber = line.split(' ')[-1]
                        if (float(prbs_ber) > float(self.standard_ber_val)):
                            prbs_ber_test_fail = 1
                            output_content = output_content + "%-20s Lane[%d] prbs_ber:%s > %s, test fail\n" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val)
                            prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                            log_error("%-20s lane:%d, prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                        else:
                            prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                            log_debug("%-20s lane:%d, prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
            if prbs_ber_flag == 1 and prbs_ber_test_fail == 0:
                result_dict["successports"].append(port)
            elif prbs_ber_flag == 1 and prbs_ber_test_fail == 1:
                result_dict["errorports"].append(port)
                result_dict["port_info_dict"][port]["log"] = output_content
            else:
                result_dict["errorports"].append(port)
                prbs_info_gather_fun("%-20s get prbs_ber fail, output:\n%s" % (output_content_port_info, output))
                result_dict["port_info_dict"][port]["log"] = "%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output)
                log_error("%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output))
            prbs_info_gather_fun("")

        if len(result_dict["errorports"]) > 0:
            return False, result_dict
        return True, result_dict

    def get_prbs_sys_result(self, upports, result_dict):
        '''Obtain the SYS prbsstat_ber'''
        result_dict["successports"] = []
        result_dict["errorports"] = []

        # The newly packaged command to get PRBS test results contains wait without additional wait
        cmd = get_sdk_cmd("dsh -c 'phy control %s calprbs lnside=1 time=%d'" % (self.prbs_port_range, self.prbs_time), time_out=300, grep="] Ber")
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            other_info = result_dict.get("other_info", "")
            result_dict["other_info"] = other_info + output
            return False, result_dict

        lines = output.split("\n")
        for port in upports:
            prbs_ber_flag = 0
            prbs_ber_test_fail = 0
            output_content = ""
            lport = self.device_port_list[port - 1].lport
            unit_port = self.device_port_list[port - 1].unit_port
            bcm_port = self.device_port_list[port - 1].bcm_port
            output_content_port_info = "port:%-3d %s(%d)" % (lport, bcm_port, unit_port)
            for line in lines:
                if (re.search('.*] Ber', line.strip())):
                    line_unit_port = int((line.split('Lane')[0]).split('Port')[1])
                    if unit_port == line_unit_port:
                        prbs_ber_flag = 1
                        lane_num = int((line.split(']')[0]).split('[')[1])
                        prbs_ber = line.split('Ber')[1]
                        if (float(prbs_ber) > float(self.standard_ber_val)):
                            prbs_ber_test_fail = 1
                            output_content = output_content + "%-20s Lane[%d] prbs_ber:%s > %s, test fail\n" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val)
                            prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                            log_error("%-20s lane:%d, prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                        else:
                            prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                            log_debug("%-20s lane:%d, prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
            if prbs_ber_flag == 1 and prbs_ber_test_fail == 0:
                result_dict["successports"].append(port)
            elif prbs_ber_flag == 1 and prbs_ber_test_fail == 1:
                result_dict["errorports"].append(port)
                result_dict["port_info_dict"][port]["log"] = output_content
            else:
                result_dict["errorports"].append(port)
                prbs_info_gather_fun("%-20s get prbs_ber fail, output:\n%s" % (output_content_port_info, output))
                result_dict["port_info_dict"][port]["log"] = "%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output)
                log_error("%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output))
            prbs_info_gather_fun("")

        if len(result_dict["errorports"]) > 0:
            return False, result_dict
        return True, result_dict

    def get_prbs_line_result(self, upports, result_dict):
        '''Get prbsstat_ber of the line end'''
        result_dict["successports"] = []
        result_dict["errorports"] = []

        # The newly packaged command to get PRBS test results contains wait without additional wait
        cmd = get_sdk_cmd("dsh -c 'phy control %s calprbs lnside=0 time=%d'" % (self.prbs_port_range, self.prbs_time), time_out=300, grep="] Ber")
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            other_info = result_dict.get("other_info", "")
            result_dict["other_info"] = other_info + output
            return False, result_dict

        lines = output.split("\n")
        for port in upports:
            prbs_ber_flag = 0
            prbs_ber_test_fail = 0
            output_content = ""
            lport = self.device_port_list[port - 1].lport
            unit_port = self.device_port_list[port - 1].unit_port
            bcm_port = self.device_port_list[port - 1].bcm_port
            output_content_port_info = "port:%-3d %s(%d)" % (lport, bcm_port, unit_port)
            for line in lines:
                if (re.search('.*] Ber', line.strip())):
                    line_unit_port = int((line.split('Lane')[0]).split('Port')[1])
                    if unit_port == line_unit_port:
                        prbs_ber_flag = 1
                        lane_num = int((line.split(']')[0]).split('[')[1])
                        prbs_ber = line.split('Ber')[1]
                        if (float(prbs_ber) > float(self.standard_ber_val)):
                            prbs_ber_test_fail = 1
                            output_content = output_content + "%-20s Lane[%d] prbs_ber:%s > %s, test fail\n" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val)
                            prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                            log_error("%-20s lane:%d, prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                        else:
                            prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                            log_debug("%-20s lane:%d, prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
            if prbs_ber_flag == 1 and prbs_ber_test_fail == 0:
                result_dict["successports"].append(port)
            elif prbs_ber_flag == 1 and prbs_ber_test_fail == 1:
                result_dict["errorports"].append(port)
                result_dict["port_info_dict"][port]["log"] = output_content
            else:
                result_dict["errorports"].append(port)
                prbs_info_gather_fun("%-20s get prbs_ber fail, output:\n%s" % (output_content_port_info, output))
                result_dict["port_info_dict"][port]["log"] = "%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output)
                log_error("%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output))
            prbs_info_gather_fun("")

        if len(result_dict["errorports"]) > 0:
            return False, result_dict
        return True, result_dict

    def clear_port_prbs(self):
        '''clear_port_prbs'''

        cmd = get_sdk_cmd("dsh -c 'phy diag %s prbs clear'" % (self.prbs_port_range))
        ret, output = port_getstatusoutput(cmd, time_sleep=3)
        if ret is False or "fail" in output:
            log_error("mac prbs clear fail, output:%s" % output)
            return False, "mac prbs clear fail, output:%s" % output

        cmd = get_sdk_cmd("dsh -c 'phy control %s clearprbs lnside=1'" % (self.prbs_port_range))
        ret, output = port_getstatusoutput(cmd, time_sleep=3)
        if ret is False or "fail" in output:
            log_error("sys prbs clear fail, output:%s" % output)
            return False, "sys prbs clear fail, output:%s" % output

        cmd = get_sdk_cmd("dsh -c 'phy control %s clearprbs lnside=0'" % (self.prbs_port_range))
        ret, output = port_getstatusoutput(cmd, time_sleep=3)
        if ret is False or "fail" in output:
            log_error("line prbs clear fail, output:%s" % output)
            return False, "line prbs clear fail, output:%s" % output

        log_debug("clear_port_prbs success")
        return True, "clear_port_prbs success"

@singleton
class PortHsdkPrbsIntPhyTest(PortHsdkPrbsTest):
    '''IntPhy prbs'''

    def init_test(self):
        '''Port internal PHY PRBS init test'''

        pass

    def start_test(self, **kwargs):
        '''Port internal PHY PRBS start test'''

        log_debug("start_test")
        return self.set_port_prbs(1)

    def check_test(self, **kwargs):
        '''Port internal PHY PRBS get test result'''

        port = kwargs["port"]

        log_debug("check_test")
        return self.get_port_prbs_int_result(port)

    def del_test(self):
        '''Port internal PHY PRBS test environment recover'''

        log_debug("del_test")
        return self.reset_port_prbs()

    def set_port_prbs(self, enable):
        '''set port prbs, start test'''

        if enable == 1:
            cmd = get_sdk_cmd("dsh -c 'phy diag %s prbs set p=3'" % self.prbs_port_range)
            ret, output = port_getstatusoutput(cmd)
            if(ret != 0):
                return False, output
            cmd = get_sdk_cmd("dsh -c 'phy diag %s prbs get'" % self.prbs_port_range)
            ret, output = port_getstatusoutput(cmd)
            if(ret != 0):
                return False, output
            cmd = get_sdk_cmd("dsh -c 'phy diag %s prbsstat start interval=%d'" % (self.prbs_port_range, self.prbs_time))
            ret, output = port_getstatusoutput(cmd, time_sleep=(self.prbs_time + 10))
            if(ret != 0):
                return False, output
            cmd = get_sdk_cmd("dsh -c 'phy diag %s prbsstat ber'" % self.prbs_port_range)
            ret, output = port_getstatusoutput(cmd, time_sleep=5)
            if(ret != 0):
                return False, output
            return True, output
        else:
            cmd = get_sdk_cmd("dsh -c 'phy diag %s prbs clear'" % self.prbs_port_range)
            ret, output = port_getstatusoutput(cmd)
            if(ret != 0):
                return False, output
            return True, output

    def get_port_prbs_int_result(self, port):
        '''get port PRBS test result'''

        prbs_ber_flag = 0
        prbs_ber_test_fail = 0
        output_content = ""
        lport = self.device_port_list[port - 1].lport
        bcm_port = self.device_port_list[port - 1].bcm_port
        unit_port = self.device_port_list[port - 1].unit_port
        output_content_port_info = "port:%-3d %s(%d)" % (lport, bcm_port, unit_port)

        cmd = get_sdk_cmd("dsh -c 'phy diag %d prbsstat ber'" % unit_port)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        log_debug(output)

        lines = output.split("\n")
        for line in lines:
            if (re.search('.*].*e', line.strip())):
                prbs_ber_flag = 1 # return information have prbs_ber info
                lane_num = int((line.split(']')[0]).split('[')[1])
                prbs_ber = line.split(' ')[-1]
                if (float(prbs_ber) > float(self.standard_ber_val)):
                    prbs_ber_test_fail = 1
                    prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                    output_content = output_content + "%-20s Lane[%d] prbs_ber:%s > %s, test fail\n" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val)
                    log_error("%-20s lane:%d, prbs_ber:%s > %s, test fail" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                else:
                    prbs_info_gather_fun("%-20s Lane[%d] prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
                    log_debug("%-20s lane:%d, prbs_ber:%s <= %s, test success" % (output_content_port_info, lane_num, prbs_ber, self.standard_ber_val))
        if prbs_ber_flag == 1 and prbs_ber_test_fail == 0:
            prbs_info_gather_fun("")
            return True, output
        elif prbs_ber_flag == 1 and prbs_ber_test_fail == 1:
            prbs_info_gather_fun("")
            return False, output_content
        else:
            prbs_info_gather_fun("%-20s get prbs_ber fail, output:\n%s" % (output_content_port_info, output))
            prbs_info_gather_fun("")
            log_error("%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output))
            return False, "%-20s get prbs_ber fail, output:%s" % (output_content_port_info, output)

    def reset_port_prbs(self):
        '''reset port rbs'''

        ret, output = self.set_port_prbs(0)
        if ret:
            time.sleep(10)
            log_debug("reset_port_prbs success")
            return True, "reset_port_prbs success"
        else:
            log_error("reset_port_prbs fail, output:%s" % output)
            return False, "reset_port_prbs fail, output:%s" % output

@singleton
class PortHsdkKrTest(PortHsdkTest):
    '''Internal management port receive and send packets'''

    def init_test(self):
        '''The internal management port test is initialized'''
        log_debug("init_test")
        self.install_pktgen_mode()
        ret, output = self.set_mgmt_antoneg_on()
        if ret is False:
            log_error("set_mgmt_antoneg_on fail, output:%s" % output)
            return False, "set_mgmt_antoneg_on fail, output:%s" % output

        ret, output = self.set_all_mgmt_enable(1)
        if ret is False:
            log_error("set_all_mgmt_enable fail, output:%s" % output)
            return False, "set_all_mgmt_enable fail, output:%s" % output

        ret, output = self.clear_all_mgmt_packets()
        if ret is False:
            log_error("clear_all_mgmt_packets fail, output:%s" % output)
            return False, "clear_all_mgmt_packets fail, output:%s" % output

        log_debug("init_test success")
        return True, "init_test success"

    def start_test(self, **kwargs):
        '''start Internal management port test '''

        mgmt_eth = kwargs["mgmt_eth"]
        count = kwargs.get("count", PACKETS_COUNT)
        size = kwargs.get("size", PACKETS_SIZE)
        dst_mac = kwargs.get("dst_mac", PACKETS_DST_MAC)
        vlan = kwargs.get("vlan", KR_VLAN)

        log_debug("start_test")
        return self.kr_start_send_port_packets(mgmt_eth=mgmt_eth, count=count, size=size,
                                               dst_mac=dst_mac, vlan=vlan)

    def check_test(self, **kwargs):
        '''get Internal management port test result'''

        mgmt_eth = kwargs["mgmt_eth"]
        count = kwargs.get("count", PACKETS_COUNT)

        log_debug("check_test")
        return self.check_port_packets(mgmt_eth, count)

    def del_test(self):
        '''The internal management port test environment is restored'''

        log_debug("del_test")
        ret, output = self.set_all_mgmt_enable(0)
        if ret is False:
            log_error("set_all_mgmt_enable fail, output:%s" % output)
            return False, "set_all_mgmt_enable fail, output:%s" % output

        ret, output = self.clear_all_mgmt_packets()
        if ret is False:
            log_error("clear_all_mgmt_packets fail, output:%s" % output)
            return False, "clear_all_mgmt_packets fail, output:%s" % output

        return True, "del_test success"

    def kr_start_send_port_packets(self, **kwargs):
        '''Began to contract'''

        mgmt_eth = kwargs["mgmt_eth"]
        count = kwargs.get("count", PACKETS_COUNT)
        size = kwargs.get("size", PACKETS_SIZE)
        dst_mac = kwargs.get("dst_mac", PACKETS_DST_MAC)
        vlan = kwargs.get("vlan", KR_VLAN)

        mgmt_bcmport = self.get_mgmt_bcmport(mgmt_eth)
        if mgmt_bcmport is None:
            return False, "kr_start_send_port_packets fail, get_mgmt_bcmport:%s None" % mgmt_eth

        ret, output = self.kr_vlan_config(vlan, mgmt_bcmport)
        if ret is False:
            return False, "kr_start_send_port_packets fail, output:%s" % output

        ret, output = self.kr_pktgen_config(mgmt_eth=mgmt_eth,
                                            count=count,
                                            size=size,
                                            dst_mac=dst_mac,
                                            vlan=vlan,
                                            mgmt_bcmport=mgmt_bcmport)
        if ret is False:
            return False, "kr_start_send_port_packets fail, output:%s" % output

        ret, output = self.kr_pktgen_start(mgmt_eth, vlan, mgmt_bcmport)
        if ret is False:
            return False, "kr_start_send_port_packets fail, output:%s" % output

        log_debug("start_send_port_packets success")
        return True, "start_send_port_packets success"

    def set_mgmt_antoneg_on(self):
        '''Call mgmt.cint to enable auto-negotiation of the internal management interface'''

        cmd = get_sdk_cmd("cint /usr/share/sonic/device/%s/mgmt.cint" % global_onie_platform)
        ret, output = port_getstatusoutput(cmd)
        if(ret != 0):
            log_error("set_mgmt_antoneg_on fail, output:%s" % output)
            return False, "set_mgmt_antoneg_on fail, output:%s" % output

        log_debug("set_mgmt_antoneg_on success")
        return True, output

    def get_kr_port_status(self, eth):
        '''get kr port up/down status'''

        # get bcm_port
        cmd = get_sdk_cmd("ps %s" % self.get_mgmt_bcmport(eth))
        ret, output = port_getstatusoutput(cmd)

        if ret == 0:
            return PortHsdkUtil.ReUtil.getre_port_status(output)
        return False, output

    def get_kr_unit_port_by_bcm(self, eth, bcm_port):
        '''get unit_port'''

        unit_port = None
        cmd = get_sdk_cmd("ps %s" % bcm_port)
        ret, output = port_getstatusoutput(cmd)

        lines = output.split("\n")
        if ret == 0:
            for line in lines:
                if (re.search('(.*?)\((.*?)$', line.strip())):
                    unit_port = PortHsdkUtil.ReUtil.getre_output_unit_port(line)
            log_debug("port:%s bcm_port:%s unit_port:%d, get_kr_unit_port_by_bcm success" % (eth, bcm_port, unit_port))
            return True, unit_port

        log_error("port:%s bcm_port:%s, get_unit_port_by_bcm fail, output:%s" % (eth, bcm_port, output))
        return False, 0

    def check_mgmt_speed_is_10G(self, eth, bcm_port):
        '''check Internal management port speed whether is 10G'''

        cmd = get_sdk_cmd("ps %s" % bcm_port)
        ret, output = port_getstatusoutput(cmd)
        lines = output.split("\n")
        mgmt_speed = None
        if ret == 0:
            for line in lines:
                if (re.search('(.*?)\((.*?)$', line.strip())):
                    mgmt_speed = PortHsdkUtil.ReUtil.getre_output_speed(line)
        if mgmt_speed == "10G":
            log_debug("port:%s bcm_port:%s speed:%s, check_mgmt_speed_is_10G success" % (eth, bcm_port, mgmt_speed))
            return True, "port:%s bcm_port:%s speed:%s, check_mgmt_speed_is_10G success" % (eth, bcm_port, mgmt_speed)
        else:
            log_error("port:%s bcm_port:%s speed:%s, check_mgmt_speed_is_10G fail, output:%s" % (eth, bcm_port, mgmt_speed, output))
            return False, "port:%s bcm_port:%s speed:%s, check_mgmt_speed_is_10G fail, output:%s" % (eth, bcm_port, mgmt_speed, output)

    def check_port_packets(self, mgmt_eth, count=PACKETS_COUNT):
        '''get Internal management port test result'''

        kr_count_pkt = 0
        pktgen_count_pkt = 0
        result_str = ""
        # get pktgen send packets result
        cmd = "cat /proc/net/pktgen/%s" % mgmt_eth
        ret, output = port_getstatusoutput(cmd)
        log_debug(output)
        lines = output.split("\n")
        for line in lines:
            if (re.search('Result(.*?)$', line.strip())):
                pktgen_count_pkt = int((line.split("usec,"))[1].split("(")[0])
                log_debug("pktgen_count_pkt:%d" % pktgen_count_pkt)
        if (pktgen_count_pkt != 0):
            result_str += "pktgen_count_pkt:%d\n" % pktgen_count_pkt
        else:
            result_str += (output + "\n")
        # get show c result
        cmd = get_sdk_cmd("show c %s" % self.get_mgmt_bcmport(mgmt_eth))
        ret, output = port_getstatusoutput(cmd)
        lines = output.split("\n")
        for line in lines:
            if (re.search('XLMIB_RPOK(.*?)$', line.strip())):
                kr_count_pkt = PortHsdkUtil.ReUtil.getre_output_packets_count(line)
                log_debug("kr_count_pkt:%d" % kr_count_pkt)
                result_str += "kr_count_pkt:%d\n" % kr_count_pkt
                if (pktgen_count_pkt == kr_count_pkt):
                    return True, result_str
                else:
                    result_str += "pktgen_count_pkt != kr_count_pkt\n"
                    return False, result_str
        result_str += "kr_count_pkt:%d\n" % kr_count_pkt
        result_str += "%s, output:\n%s" % (cmd, output)
        return False, result_str

    def clear_all_mgmt_packets(self):
        '''claer Internal management port port_packets'''

        cmd = get_sdk_cmd("clear c %s" % (",".join(self.get_mgmt_bcmport(item)
                                                    for item
                                                    in global_port_config["mgmt_kt_ports"])))
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            log_warning("clear_all_mgmt_packets fail, output:%s" % output)
            return False, "clear_all_mgmt_packets fail, output:%s" % output

        log_debug("clear_all_mgmt_packets success")
        return True, "clear_all_mgmt_packets success"

    @classmethod
    def install_pktgen_mode(cls):
        '''Check whether the pktgen module is loaded. If not, load the pktgen module'''

        cmd = "lsmod | grep pktgen"
        ret, output = port_getstatusoutput(cmd)
        if not output or ret != 0:
            log_debug("载入pktgen模块")
            cmd = "modprobe pktgen"
            ret, output = port_getstatusoutput(cmd)
        eth_list = list(global_port_config["mgmt_kt_ports"].keys())
        eth_list.sort()
        for eth in eth_list:
            cmd = "ls /proc/net/pktgen/%s" % eth
            ret, output = port_getstatusoutput(cmd)
            if "cannot" in output:
                cmd = "ifconfig %s up" % eth
                ret, output = port_getstatusoutput(cmd, time_sleep=1)
                cmd = "echo \"add_device %s\" > /proc/net/pktgen/kpktgend_0" % eth
                ret, output = port_getstatusoutput(cmd)
        time.sleep(3)

    @classmethod
    def kr_vlan_config(cls, vlan, mgmt_bcmport):
        '''Internal management port send packets set vlan'''

        time.sleep(1)
        cmd = get_sdk_cmd("vlan destroy %d" % vlan)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        cmd = get_sdk_cmd("vlan create %d PortBitMap=%s UntagBitMap=%s" % (vlan,
                                                                           mgmt_bcmport,
                                                                           mgmt_bcmport))
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        cmd = get_sdk_cmd("pvlan set %s %d" % (mgmt_bcmport, vlan))
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output

        return True, "kr_vlan_config success"

    @classmethod
    def kr_pktgen_config(cls, **kwargs):
        '''Internal management port send packets set pktgen config'''

        mgmt_eth = kwargs["mgmt_eth"]
        size = kwargs["size"]
        count = kwargs["count"]
        dst_mac = kwargs["dst_mac"]
        vlan = kwargs["vlan"]
        mgmt_bcmport = kwargs["mgmt_bcmport"]

        cmd = "echo \"pkt_size %d\" > /proc/net/pktgen/%s" % (size, mgmt_eth)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        cmd = "echo \"count %d\" > /proc/net/pktgen/%s" % (count, mgmt_eth)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        cmd = "echo \"dst_mac %s\" > /proc/net/pktgen/%s" % (dst_mac, mgmt_eth)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output
        cmd = "echo \"vlan_id %s\" > /proc/net/pktgen/%s" % (vlan, mgmt_eth)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output

        cmd = get_sdk_cmd("clear c %s" % mgmt_bcmport)
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output

        return True, "kr_pktgen_config success"

    @classmethod
    def kr_pktgen_start(cls, mgmt_eth, vlan, mgmt_bcmport):
        '''Internal management port use pktgen satrt send packets'''

        # start pktgen send packets,sleep 5s
        cmd = "echo \"start\" > /proc/net/pktgen/pgctrl"
        ret, output = port_getstatusoutput(cmd, time_sleep=5)
        if ret != 0:
            return False, output

        # stop pktgen send packets
        cmd = "echo \"stop\" > /proc/net/pktgen/pgctrl"
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output

        # After packets are sent, the internal management port is removed from the VLAN
        cmd = get_sdk_cmd("vlan remove %d PortBitMap=%s" % (vlan, mgmt_bcmport))
        ret, output = port_getstatusoutput(cmd)
        if ret != 0:
            return False, output

        return True, "start_send_port_packets_t success"

class PortScene():
    '''port class'''

    @staticmethod
    def port_frame_test(port_list=[], redirect=True):
        '''Port frame test'''

        log_debug("开始端口收发帧测试")
        pft = PortHsdkFrameTest()
        psf = PortScnFn()
        frmnm = PACKETS_COUNT
        port_list = copy.deepcopy(port_list)# Prevents an operation on an incoming object when it is an object
        cycle_num = global_port_config["port_frame_test_retrynum"]# cycles
        del_sleep_time = global_port_config["port_frame_del_time"]# Restore the test environment waiting time
        psf.sdk_cmd_redirect_judge(redirect)
        log_debug("端口收发帧重试次数为%d次" % cycle_num)

        for c_i in range(cycle_num):
            log_debug("端口收发帧第%d次测试" % (c_i + 1))
            global global_port_log_info
            global_port_log_info = "port_log_info:\n"

            upports = []
            successports = []
            updownerrorports = []
            errorports = []
            result_dict = {}
            ret_t = 0
            try:
                ret_t, result_dict, upports, updownerrorports = psf.get_port_status_f(f_obj=pft, port_list=port_list)
                log_debug("up_port:" + ", ".join(str(index) for index in upports))
                if ret_t < 0 or len(upports) == 0:
                    if (ret_t < 0):
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f ret_t < 0\n"
                        log_error("get_port_status_f ret_t < 0")
                    else:
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f len(upports) == 0\n"
                        log_error("get_port_status_f len(upports) == 0")
                else:
                    ret, result = pft.init_test()
                    if ret is False:
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "init_test fail, result:%s\n" % result
                        log_error("init_test fail, result:%s" % result)
                        continue # Start the entire test item retry
                    ret_t, result_dict = psf.frame_start_f(f_obj=pft,
                                                           ret_t=ret_t,
                                                           uprt=upports,
                                                           frmnm=frmnm,
                                                           r_dict=result_dict)
                    time.sleep(5)
                    ret_t, result_dict, successports, errorports = psf.frame_check_f(f_obj=pft,
                                                                                     ret_t=ret_t,
                                                                                     uprt=upports,
                                                                                     frmnm=frmnm,
                                                                                     r_dict=result_dict)
            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)
                ret_t = -999
                continue
            finally:
                ret, result = pft.del_test()
                if ret is False:
                    log_error("del_test fail, result:%s" % result)
                time.sleep(del_sleep_time)
                ret_t, result_dict = psf.compare_start_end_ports(f_obj=pft,
                                                                 ret_t=ret_t,
                                                                 uprt=upports,
                                                                 r_dict=result_dict,
                                                                 port_list=port_list)
            result_dict["successports"] = successports
            result_dict["updownerrorports"] = updownerrorports
            result_dict["errorports"] = errorports
            if len(updownerrorports) > 0:
                ret_t -= 1
            if ret_t < 0:
                continue
            break

        return psf.test_return(ret_t=ret_t, result_dict=result_dict, test_type="frame")

    @staticmethod
    def port_brcst_test(port_list=[], redirect=True):
        '''Port broadcast test'''

        log_debug("开始端口广播测试")
        pbt = PortHsdkBrcstTest()
        psf = PortScnFn()
        psf.sdk_cmd_redirect_judge(redirect)
        port_list = copy.deepcopy(port_list)# Prevents an operation on an incoming object when it is an object
        cycle_num = global_port_config["port_brcst_test_retrynum"]# cycle
        del_sleep_time = global_port_config["port_brcst_del_time"]# Restore the test environment waiting time
        log_debug("端口广播重试次数为%d次" % cycle_num)

        for c_i in range(cycle_num):
            log_debug("端口广播帧第%d次测试" % (c_i + 1))
            global global_port_log_info
            global_port_log_info = "port_log_info:\n"

            upports = []
            successports = []
            updownerrorports = []
            errorports = []
            result_dict = {}
            ret_t = 0
            try:
                ret_t, result_dict, upports, updownerrorports = psf.get_port_status_f(f_obj=pbt, port_list=port_list)
                log_debug("up_port:" + ", ".join(str(index) for index in upports))
                if ret_t < 0 or len(upports) == 0:
                    if (ret_t < 0):
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f ret_t < 0\n"
                        log_error("get_port_status_f ret_t < 0")
                    else:
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f len(upports) == 0\n"
                        log_error("get_port_status_f len(upports) == 0")
                else:
                    ret, result = pbt.init_test()
                    if ret is False:
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "init_test fail, result:%s\n" % result
                        log_error("init_test fail, result:%s" % result)
                        continue
                    # Broadcast packets are sent through the first up port
                    port=upports[0]
                    ret, output = pbt.start_test(port=port, count=PACKETS_COUNT)
                    if ret is True:
                        time.sleep(10)# Port broadcast test Wait for flooding 10 seconds
                        ret_t, result_dict, successports, errorports = psf.brcst_check_f(f_obj=pbt,
                                                                                         ret_t=ret_t,
                                                                                         uprt=upports,
                                                                                         r_dict=result_dict)
                    else:
                        ret_t -= 1
                        log_error("port %d:sending packet , output:%s" % (port, output))
                        output_info = result_dict["port_info_dict"][port]["output"]
                        result_dict["port_info_dict"][port]["output"] = output_info + "port %d:sending packet , output:%s" % (port, output)

            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)
                ret_t = -999
                continue
            finally:
                # Disable the broadcast and restore the environment
                ret, result = pbt.del_test()
                if ret is False:
                    log_error("del_test fail, result:%s" % result)
                time.sleep(del_sleep_time)
                ret_t, result_dict = psf.compare_start_end_ports(f_obj=pbt,
                                                                 ret_t=ret_t,
                                                                 uprt=upports,
                                                                 r_dict=result_dict,
                                                                 port_list=port_list)
            result_dict["successports"] = successports
            result_dict["updownerrorports"] = updownerrorports
            result_dict["errorports"] = errorports
            if len(updownerrorports) > 0:
                ret_t -= 1
            if ret_t < 0:
                continue
            break

        return psf.test_return(ret_t=ret_t, result_dict=result_dict, test_type="brcst")

    def port_prbs_test(self, port_list=[], test_type="", redirect=True):
        '''port PRBS test'''

        # Initialize the production test configuration,Prevent external PHY devices
        # When the first test item is PRBS, the production configuration is not initialized and the internal PHY PRBS interface is invoked
        ppipt = PortHsdkPrbsIntPhyTest()
        if global_port_config.get("extphy_device", 0) == 1:# have external phy
            log_debug("PortHsdkPrbsExtPhyTest")
            return self.test_port_prbs_extphy(port_list=port_list, test_type=test_type, redirect=redirect)
        # no external  phy
        log_debug("PortHsdkPrbsIntPhyTest")
        return self.test_port_prbs_intphy(port_list=port_list, test_type=test_type, redirect=redirect)

    @staticmethod
    def port_kr_test(port_list=[], redirect=True):
        '''Internal management port receiving and sending test'''

        log_debug("开始内部管理口收发包测试")
        pkt = PortHsdkKrTest()
        psf = PortScnFn()
        packetcount = PACKETS_COUNT
        port_list = copy.deepcopy(port_list)# Prevents an operation on an incoming object when it is an object
        cycle_num = global_port_config["port_kr_test_retrynum"]# cycles
        del_sleep_time = global_port_config["port_kr_del_time"]# Restore the test environment waiting time
        psf.sdk_cmd_redirect_judge(redirect)
        log_debug("内部管理口收发包重试次数为%d次" % cycle_num)

        for c_i in range(cycle_num):
            log_debug("内部管理口收发包第%d次测试" % (c_i + 1))
            global global_port_log_info
            global_port_log_info = "port_log_info:\n"

            upports = []
            successports = []
            updownerrorports = []
            errorports = []
            result_dict = {}
            ret_t = 0
            try:
                ret, result = pkt.init_test()
                if ret is False:
                    ret_t = -1
                    other_info = result_dict.get("other_info", "")
                    result_dict["other_info"] = other_info + "init_test fail, result:%s\n" % result
                    log_error("init_test fail, result:%s" % result)
                ret_t, result_dict, upports, updownerrorports = psf.get_port_status_f(f_obj=pkt, kr_test=True, port_list=port_list)
                log_debug("up_port:" + ", ".join(str(index) for index in upports))
                if ret_t < 0 or len(upports) == 0:
                    if (ret_t < 0):
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f ret_t < 0\n"
                        log_error("get_port_status_f ret_t < 0")
                    else:
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f len(upports) == 0\n"
                        log_error("get_port_status_f len(upports) == 0")
                else:
                    for eth in upports:
                        log_debug("内部管理口:%s 正在发包" % eth)
                        ret, output = pkt.start_test(mgmt_eth=eth, count=packetcount, vlan=2000)
                        if ret is False:
                            errorports.append(eth)
                            output_info = result_dict["port_info_dict"][eth]["log"]
                            result_dict["port_info_dict"][eth]["log"] = output_info + "port_kr_test start_test fail, output:%s" % output
                            log_warning("port_kr_test start_test fail, output:%s" % output)
                        else:
                            time.sleep(4)
                            ret, output = pkt.check_test(mgmt_eth=eth, count=packetcount)
                            if ret:
                                successports.append(eth)
                            else:
                                ret_t = -1
                                errorports.append(eth)
                                output_info = result_dict["port_info_dict"][eth]["log"]
                                result_dict["port_info_dict"][eth]["log"] = output_info + "port_kr_test check_test fail, output:%s" % output
                                log_error("%s check_test fail, output:%s" % (eth, output))
            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)
                ret_t = -999
                continue
            finally:
                ret_t, result_dict = psf.compare_start_end_ports(f_obj=pkt,
                                                                 ret_t=ret_t,
                                                                 uprt=upports,
                                                                 r_dict=result_dict,
                                                                 kr_test=True,
                                                                 port_list=port_list)
                ret, result = pkt.del_test()
                if ret is False:
                    log_error("del_test fail, result:%s" % result)
                time.sleep(del_sleep_time)
            result_dict["successports"] = successports
            result_dict["updownerrorports"] = updownerrorports
            result_dict["errorports"] = errorports
            if len(updownerrorports) > 0:
                ret_t -= 1
            if ret_t < 0:
                continue
            break

        return psf.test_return(ret_t=ret_t, result_dict=result_dict, test_type="kr")

    @staticmethod
    def test_port_prbs_extphy(port_list=[], test_type="", redirect=True):
        '''ExtPhy prbs test'''

        log_debug("开始ExtPhy prbs测试")
        if (test_type != ""):
            log_debug("test_type: %s" % test_type)
        else:
            log_debug("test_type: prbs_mac、prbs_sys、prbs_line")

        psf = PortScnFn()
        psf.sdk_cmd_redirect_judge(redirect)
        ppept = PortHsdkPrbsExtPhyTest()
        port_list = copy.deepcopy(port_list)# Prevents an operation on an incoming object when it is an object
        cycle_num = global_port_config["port_prbs_test_retrynum"]# cycles
        del_sleep_time = global_port_config["port_prbs_del_time"]# Restore the test environment waiting time
        log_debug("ExtPhy prbs重试次数为%d次" % cycle_num)

        for c_i in range(cycle_num):
            log_debug("ExtPhy prbs第%d次测试" % (c_i + 1))
            global global_port_log_info
            global_port_log_info = "port_log_info:\n"

            upports = []
            updownerrorports = []
            result_dict = {}
            # Keep pointing to the same object
            prbs_mac_result_dict = result_dict
            prbs_sys_result_dict = result_dict
            prbs_line_result_dict = result_dict
            prbs_all_result_dict = {
                    "prbs_mac_result_dict":prbs_mac_result_dict,
                    "prbs_sys_result_dict":prbs_sys_result_dict,
                    "prbs_line_result_dict":prbs_line_result_dict
            }
            ret_t = 0
            try:
                ret_t, result_dict, upports, updownerrorports = psf.get_port_status_f(f_obj=ppept, port_list=port_list)
                result_dict["updownerrorports"] = updownerrorports
                log_debug("up_port:" + ", ".join(str(index) for index in upports))
                if ret_t < 0 or len(upports) == 0:
                    if (ret_t < 0):
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f ret_t < 0\n"
                        log_error("get_port_status_f ret_t < 0")
                    else:
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f len(upports) == 0\n"
                        log_error("get_port_status_f len(upports) == 0")
                else:
                    ret_t, prbs_all_result_dict = psf.prbs_mac_sys_line_start_check(f_obj=ppept,
                                                                                    ret_t=ret_t,
                                                                                    uprt=upports,
                                                                                    udeprt=updownerrorports,
                                                                                    test_type=test_type,
                                                                                    r_dict=result_dict)
            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)
                ret_t = -999
                continue
            finally:
                ret, result = ppept.del_test()
                if ret is False:
                    log_error("del_test fail, result:%s" % result)
                time.sleep(del_sleep_time)
                ret_t, result_dict = psf.compare_start_end_ports(f_obj=ppept,
                                                                 ret_t=ret_t,
                                                                 uprt=upports,
                                                                 r_dict=result_dict,
                                                                 port_list=port_list)
                prbs_all_result_dict = psf.prbs_ext_result_dict_dispose(r_dict=result_dict,
                                                                        test_type=test_type,
                                                                        prbs_all_r_dict=prbs_all_result_dict)
            if len(updownerrorports) > 0:
                ret_t -= 1
            if ret_t < 0:
                continue
            break
        return PortScnFn.test_return(ret_t=ret_t, prbs_all_result_dict=prbs_all_result_dict, test_type=test_type)

    @staticmethod
    def test_port_prbs_intphy(port_list=[], test_type="", redirect=True):
        '''IntPhy prbs test'''

        log_debug("开始IntPhy prbs测试")
        ppipt = PortHsdkPrbsIntPhyTest()
        psf = PortScnFn()
        psf.sdk_cmd_redirect_judge(redirect)
        port_list = copy.deepcopy(port_list)# Prevents an operation on an incoming object when it is an object
        cycle_num = global_port_config["port_prbs_test_retrynum"]# cycles
        del_sleep_time = global_port_config["port_prbs_del_time"]# Restore the test environment waiting time
        log_debug("IntPhy prbs重试次数为%d次" % cycle_num)

        for c_i in range(cycle_num):
            log_debug("IntPhy prbs第%d次测试" % (c_i + 1))
            global global_port_log_info
            global_port_log_info = "port_log_info:\n"
            prbs_info_gather_fun("prbs_mac_test", clear=True)

            upports = []
            successports = []
            updownerrorports = []
            errorports = []
            result_dict = {}
            prbs_all_result_dict = {}
            ret_t = 0
            try:
                ret_t, result_dict, upports, updownerrorports = psf.get_port_status_f(f_obj=ppipt, port_list=port_list)
                log_debug("up_port:" + ", ".join(str(index) for index in upports))
                if ret_t < 0 or len(upports) == 0:
                    if (ret_t < 0):
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f ret_t < 0\n"
                        log_error("get_port_status_f ret_t < 0")
                    else:
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status_f len(upports) == 0\n"
                        log_error("get_port_status_f len(upports) == 0")
                else:
                    ret_t, result_dict = psf.prbs_int_start_f(f_obj=ppipt, ret_t=ret_t, uprt=upports, r_dict=result_dict)
                    ret_t, result_dict, successports, errorports = psf.prbs_int_check_f(f_obj=ppipt,
                                                                                        ret_t=ret_t,
                                                                                        uprt=upports,
                                                                                        r_dict=result_dict)
            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)
                ret_t = -999
                continue
            finally:
                ret, result = ppipt.del_test()
                if ret is False:
                    log_error("del_test fail, result:%s" % result)
                time.sleep(del_sleep_time)
                ret_t, result_dict = psf.compare_start_end_ports(f_obj=ppipt,
                                                                 ret_t=ret_t,
                                                                 uprt=upports,
                                                                 r_dict=result_dict,
                                                                 port_list=port_list)
            result_dict["successports"] = successports
            result_dict["updownerrorports"] = updownerrorports
            result_dict["errorports"] = errorports
            if len(updownerrorports) > 0:
                ret_t -= 1
            if ret_t < 0:
                continue
            break
        prbs_all_result_dict["prbs_mac_result_dict"] = copy.deepcopy(result_dict)
        prbs_all_result_dict["prbs_mac_result_dict"]["prbs_info"] = global_prbs_info
        prbs_all_result_dict["prbs_sys_result_dict"] = {}
        prbs_all_result_dict["prbs_line_result_dict"] = {}
        prbs_all_result_dict["prbs_mac_result_dict"]["test_type"] = "prbs_mac"
        if ret_t < 0:
            prbs_all_result_dict["prbs_mac_result_dict"]["test_result"] = False
        else:
            prbs_all_result_dict["prbs_mac_result_dict"]["test_result"] = True
        return psf.test_return(ret_t=ret_t, prbs_all_result_dict=prbs_all_result_dict, test_type="prbs_mac")

class PortScnFn():
    '''PortScene function'''

    @staticmethod
    def get_port_status_f(**kwargs):
        '''get port status'''

        ret_t = 0
        upports = []
        updownerrorports = []
        result_dict = {"port_info_dict":{}, "other_info":"", "test_result": False,
                        "updownerrorports":[], "errorports":[], "successports":[]}
        f_obj = kwargs["f_obj"]
        kr_test_flag = kwargs.get("kr_test", False)
        port_list = kwargs.get("port_list", [])

        log_debug("开始获取端口状态")
        try:
            if kr_test_flag is False:
                # introduction port_list=[] or not introduction port_list, test all ports
                # introduction port_list=[7,8,9,10], test panel port 7, 8, 9, 10
                log_debug("bcm_port数量:%d" % len(f_obj.device_port_list))
                if len(port_list) == 0:
                    for i in range(len(f_obj.device_port_list)):
                        port_list.append(i + 1)

                if type(port_list[0]) is int:
                    log_debug("port_list %s" % port_list)
                else:
                    other_info = result_dict.get("other_info", "")
                    result_dict["other_info"] = other_info + "not find port in port_list:%s\n" % port_list
                    log_error("not find port in port_list:%s " % port_list)
                    ret_t -= 1
                    port_list = []

                # for port_list init result_dict
                for port in port_list:
                    result_dict["port_info_dict"][port] = {
                        "port_info":"",
                        "status":"",
                        "log":""}
                for port in port_list:
                    # get port_info,add result_dict["port_info_dict"][port]["port_info"]
                    bcm_port = f_obj.device_port_list[port - 1].bcm_port
                    unit_port = f_obj.device_port_list[port - 1].unit_port
                    port_info = "port:%-3d %s(%d)" % (port, bcm_port, unit_port)
                    result_dict["port_info_dict"][port]["port_info"] = port_info

                    # get port status,add result_dict["port_info_dict"][port]["status"],add the port status to the list
                    ret, output = f_obj.get_port_status(port)
                    if ret is True:
                        if output == "up":
                            upports.append(port)
                            result_dict["port_info_dict"][port]["status"] = "up"
                            log_debug("%-18s:up" % port_info)
                        elif output == "down":
                            updownerrorports.append(port)
                            result_dict["port_info_dict"][port]["status"] = "down"
                            log_warning("%-18s:down" % port_info)
                        elif output == "!ena":
                            updownerrorports.append(port)
                            result_dict["port_info_dict"][port]["status"] = "!ena"
                            log_warning("%-18s:!ena" % port_info)
                        else:
                            updownerrorports.append(port)
                            result_dict["port_info_dict"][port]["status"] = "NA"
                            log_warning("%-18s:NA, output:%s" % (port_info, output))
                    else:
                        ret_t -= 1
                        result_dict["port_info_dict"][port]["status"] = "NA"
                        result_dict["port_info_dict"][port]["log"] = "get_port_status abnormal, output:%s\n" % output
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status abnormal, output:%s\n" % output
                        log_error("%-18s:get_port_status abnormal, output:%s" % (port_info, output))
                        break
            else: # kr test: get is eth of bcm_port
                # introduction port_list=[] or not introduction port_list, test all internal management ports
                # introduction port_list=['eth1'], test internal management ports eth1
                # Internal management port Additional check whether the rate is 10G
                if len(port_list) == 0:
                    eth_list = list(global_port_config["mgmt_kt_ports"].keys())
                    eth_list.sort()
                else:
                    eth_list = port_list
                    eth_list.sort()

                if type(eth_list[0]) is int:
                    other_info = result_dict.get("other_info", "")
                    result_dict["other_info"] = other_info + "not find ethX in eth_list:%s\n" % eth_list
                    log_error("not find ethX in eth_list:%s " % eth_list)
                    ret_t -= 1
                    eth_list = []
                else:
                    log_debug("eth_list %s" % eth_list)

                # for eth_list init result_dict
                for eth in eth_list:
                    result_dict["port_info_dict"][eth] = {
                        "port_info":"",
                        "status":"",
                        "log":""}
                for eth in eth_list:
                    # get port_info,add result_dict["port_info_dict"][eth]["port_info"]
                    bcm_port = f_obj.get_mgmt_bcmport(eth)
                    ret, unit_port = f_obj.get_kr_unit_port_by_bcm(eth, bcm_port)
                    port_info = "port:%s %s(%s)" % (eth, bcm_port, str(unit_port))
                    result_dict["port_info_dict"][eth]["port_info"] = port_info

                    # obtain the port rate and check whether it is 10G
                    ret, output = f_obj.check_mgmt_speed_is_10G(eth, bcm_port)
                    if ret is False:
                        ret_t -= 1
                        result_dict["port_info_dict"][eth]["log"] = "%s\n" % output
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "%s\n" % output
                        break
                    # Obtaining port Status,add result_dict["port_info_dict"][eth]["status"],add the port status to the list
                    ret, output = f_obj.get_kr_port_status(eth)# Obtain the bcm_port status of the management port
                    if ret is True:
                        if output == "up":
                            upports.append(eth)
                            result_dict["port_info_dict"][eth]["status"] = "up"
                            log_debug("%-18s:up" % port_info)
                        elif output == "down":
                            updownerrorports.append(eth)
                            result_dict["port_info_dict"][eth]["status"] = "down"
                            log_warning("%-18s:down" % port_info)
                        elif output == "!ena":
                            updownerrorports.append(eth)
                            result_dict["port_info_dict"][eth]["status"] = "!ena"
                            log_warning("%-18s:!ena" % port_info)
                        else:
                            updownerrorports.append(eth)
                            result_dict["port_info_dict"][eth]["status"] = "NA"
                            log_warning("%-18s:NA, output:%s" % (port_info, output))
                    else:
                        ret_t -= 1
                        result_dict["port_info_dict"][eth]["status"] = "NA"
                        result_dict["port_info_dict"][eth]["log"] = "get_port_status abnormal, output:%s\n" % output
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + "get_port_status abnormal, output:%s\n" % output
                        log_error("%-18s:get_port_status abnormal" % port_info)
                        break
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict, upports, updownerrorports
        return ret_t, result_dict, upports, updownerrorports

    @staticmethod
    def compare_start_end_ports(**kwargs):
        '''Compare the port up status at the start and end of the test item'''

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        kr_test_flag = kwargs.get("kr_test", False)
        port_list = kwargs.get("port_list", [])
        result_dict = kwargs["r_dict"]

        try:
            # When all the above tests are successful, the port up status at the start and end of the test item will be compared
            if ret_t == 0:
                if kr_test_flag is False:
                    s_ret_t, _, s_upports, _ = PortScnFn.get_port_status_f(f_obj=f_obj, port_list=port_list)
                else:
                    # During the KR test, the ETH interface is obtained
                    s_ret_t, _, s_upports, _ = PortScnFn.get_port_status_f(f_obj=f_obj, port_list=port_list, kr_test=kr_test_flag)
                if s_ret_t == 0:
                    if upports != s_upports:
                        ret_t -= 1
                        temp_log = "first_uplist != second_uplist\nfirst_uplist:%s\nsecond_uplist:%s\n" % (upports, s_upports)
                        other_info = result_dict.get("other_info", "")
                        result_dict["other_info"] = other_info + temp_log
                        log_error(temp_log)
                    else:
                        log_debug("两次端口up状态相同")
                else:
                    ret_t -= 1
                    other_info = result_dict.get("other_info", "")
                    result_dict["other_info"] = other_info + "test end:get_port_status abnormal"
                    log_warning("test end:get_port_status abnormal")
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict
        return ret_t, result_dict

    @staticmethod
    def frame_start_f(**kwargs):
        '''Port frame send packets'''

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        framenum = kwargs["frmnm"]
        result_dict = kwargs["r_dict"]

        try:
            for port in upports:
                bcm_port = f_obj.device_port_list[port - 1].bcm_port
                unit_port = f_obj.device_port_list[port - 1].unit_port
                port_info = "port:%d %s(%d)" % (port, bcm_port, unit_port)
                log_debug("%-18s:sending packet" % port_info)

                ret, output = f_obj.start_test(port=port, count=framenum, size=1024)
                if ret is False:
                    ret_t -= 1
                    output_info = result_dict["port_info_dict"][port]["log"]
                    result_dict["port_info_dict"][port]["log"] = output_info + "sending packet fail, output:%s\n" % output
                    other_info = result_dict.get("other_info", "")
                    result_dict["other_info"] = other_info + "sending packet fail, output:%s\n" % output
                    log_warning("%-18s:sending packet fail, output:%s" % (port_info, output))
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict
        return ret_t, result_dict

    @staticmethod
    def frame_check_f(**kwargs):
        '''Port frame results check'''

        successport = []
        errorport = []

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        framenum = kwargs["frmnm"]
        result_dict = kwargs["r_dict"]

        try:
            # Verify the upports
            for port in upports:
                bcm_port = f_obj.device_port_list[port - 1].bcm_port
                unit_port = f_obj.device_port_list[port - 1].unit_port
                port_info = "port:%d %s(%d)" % (port, bcm_port, unit_port)

                ret, output = f_obj.check_test(port=port, count=framenum, direc="rx")
                if ret is True:
                    successport.append(port)
                    log_debug("%-18s:test success" % port_info)
                else:
                    ret_t -= 1
                    errorport.append(port)
                    output_info = result_dict["port_info_dict"][port]["log"]
                    result_dict["port_info_dict"][port]["log"] = output_info + "frame_check_f fail, output:%s" % output
                    log_warning("%-18s:test fail, output:%s" % (port_info, output))
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict, successport, errorport
        return ret_t, result_dict, successport, errorport

    @staticmethod
    def brcst_check_f(**kwargs):
        '''Port broadcast result detection'''

        successport = []
        errorport = []

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        result_dict = kwargs["r_dict"]

        try:
            for port in upports:
                bcm_port = f_obj.device_port_list[port - 1].bcm_port
                unit_port = f_obj.device_port_list[port - 1].unit_port
                port_info = "port:%d %s(%d)" % (port, bcm_port, unit_port)

                ret, output = f_obj.check_test(port=port)
                if ret is True:
                    successport.append(port)
                    log_debug("%-18s:test success" % port_info)
                else:
                    ret_t -= 1
                    errorport.append(port)
                    output_info = result_dict["port_info_dict"][port]["log"]
                    result_dict["port_info_dict"][port]["log"] = output_info + "brcst_check_f fail, output:%s\n" % output
                    log_warning("%-18s:test fail, output:%s" % (port_info, output))
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict, successport, errorport
        return ret_t, result_dict, successport, errorport

    @staticmethod
    def prbs_prepare_test(**kwargs):
        '''ExtPhy prbs prepare test'''

        f_obj = kwargs["f_obj"]
        upports = kwargs["uprt"]
        try:
            # Because the upports imported may be different each time,need to obtain the upports again
            f_obj.get_unit_port_list(upports)
            f_obj.get_prbs_port_range()
            # test is for 3 sides, so prbs need to be cleared again before each side is tested
            ret, output = f_obj.init_test()
            if ret is False:
                log_warning("prbs_prepare_test fail, output:%s" % output)
                return False, "prbs_prepare_test fail, output:%s\n" % output

        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            return False, "Exception_info:\n%s" % msg
        return True, "prbs_prepare_test success"

    @staticmethod
    def prbs_mac_sys_line_start_check(**kwargs):
        '''ExtPhy prbs mac、sys、line check'''

        psf = PortScnFn()

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        test_type = kwargs["test_type"]
        result_dict = kwargs["r_dict"]
        prbs_all_result_dict = {
                "prbs_mac_result_dict":{},
                "prbs_sys_result_dict":{},
                "prbs_line_result_dict":{}
        }
        mac_flag = False
        sys_flag = False
        line_flag = False
        all_flag = False
        try:
            if test_type == "prbs_mac":
                mac_flag = True
            elif test_type == "prbs_sys":
                sys_flag = True
            elif test_type == "prbs_line":
                line_flag = True
            else:
                all_flag = True
            # MAC port
            if mac_flag or all_flag:
                prbs_info_gather_fun("prbs_mac_test", clear=True)
                log_debug("====================prbs_mac_test")
                prbs_mac_result_dict = copy.deepcopy(result_dict)
                ret_t, prbs_mac_result_dict = psf.prbs_mac_sys_line_result(f_obj=f_obj,
                                                                           ret_t=ret_t,
                                                                           uprt=upports,
                                                                           r_dict=prbs_mac_result_dict,
                                                                           test_type="prbs_mac")

                prbs_all_result_dict["prbs_mac_result_dict"] = copy.deepcopy(prbs_mac_result_dict)
                prbs_all_result_dict["prbs_mac_result_dict"]["prbs_info"] = global_prbs_info
            # SYS port
            if sys_flag or all_flag:
                prbs_info_gather_fun("prbs_sys_test", clear=True)
                log_debug("====================prbs_sys_test")
                prbs_sys_result_dict = copy.deepcopy(result_dict)
                ret_t, prbs_sys_result_dict = psf.prbs_mac_sys_line_result(f_obj=f_obj,
                                                                           ret_t=ret_t,
                                                                           uprt=upports,
                                                                           r_dict=prbs_sys_result_dict,
                                                                           test_type="prbs_sys")
                prbs_all_result_dict["prbs_sys_result_dict"] = copy.deepcopy(prbs_sys_result_dict)
                prbs_all_result_dict["prbs_sys_result_dict"]["prbs_info"] = global_prbs_info
            # Line port
            if line_flag or all_flag:
                prbs_info_gather_fun("prbs_line_test", clear=True)
                log_debug("====================prbs_line_test")
                prbs_line_result_dict = copy.deepcopy(result_dict)
                ret_t, prbs_line_result_dict = psf.prbs_mac_sys_line_result(f_obj=f_obj,
                                                                            ret_t=ret_t,
                                                                            uprt=upports,
                                                                            r_dict=prbs_line_result_dict,
                                                                            test_type="prbs_line")

                prbs_all_result_dict["prbs_line_result_dict"] = copy.deepcopy(prbs_line_result_dict)
                prbs_all_result_dict["prbs_line_result_dict"]["prbs_info"] = global_prbs_info
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, prbs_all_result_dict
        return ret_t, prbs_all_result_dict

    @staticmethod
    def prbs_mac_sys_line_result(**kwargs):
        '''ExtPhy prbs mac、sys、line start test, and check test result'''

        psf = PortScnFn()

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        result_dict = kwargs["r_dict"]
        test_type = kwargs["test_type"]

        try:
            ret, output = psf.prbs_prepare_test(f_obj=f_obj, uprt=upports)
            if ret is False:
                ret_t -= 1
                other_info = result_dict.get("other_info", "")
                result_dict["other_info"] = other_info + "output:%s\n" % output
                log_error("prbs_mac_sys_line_result fail, output:%s\n")
                return ret_t, result_dict
            ret, output = f_obj.start_port_prbs(test_type)
            if ret is False:
                ret_t -= 1
                other_info = result_dict.get("other_info", "")
                result_dict["other_info"] = other_info + "output:%s\n" % output
                log_error("prbs_mac_sys_line_result fail, output:%s\n")
                return ret_t, result_dict
            ret_t, result_dict = psf.prbs_mac_sys_line_check(f_obj=f_obj,
                                                             ret_t=ret_t,
                                                             uprt=upports,
                                                             r_dict=result_dict,
                                                             test_type=test_type)
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict
        return ret_t, result_dict

    @staticmethod
    def prbs_mac_sys_line_check(**kwargs):
        '''ExtPhy prbs mac、sys、line check'''

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        result_dict = kwargs["r_dict"]
        test_type = kwargs["test_type"]

        try:
            ret, result_dict = f_obj.check_test(test_type=test_type,
                                                uprt=upports,
                                                r_dict=result_dict)
            result_dict["test_type"] = test_type
            if ret:
                result_dict["test_result"] = True
                log_debug("======================%s_test check success\n" % test_type)
            else:
                ret_t -= 1
                result_dict["test_result"] = False
                log_warning("======================%s_test check fail\n" % test_type)
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict
        return ret_t, result_dict

    @staticmethod
    def prbs_ext_result_dict_dispose(**kwargs):
        '''ExtPhy return result dictionary processing'''

        result_dict = kwargs["r_dict"]
        test_type = kwargs["test_type"]
        prbs_all_result_dict = kwargs["prbs_all_r_dict"]

        try:
            # During the test, the dictionary key is not assigned due to a sudden exception
            if (test_type == "prbs_mac"):
                if prbs_all_result_dict["prbs_mac_result_dict"] == {}:
                    prbs_all_result_dict["prbs_mac_result_dict"] = copy.deepcopy(result_dict)
                prbs_all_result_dict["prbs_mac_result_dict"]["test_type"] = "prbs_mac"
                result_dict_other_info = result_dict.get("other_info", "")
                prbs_all_result_dict_other_info = prbs_all_result_dict["prbs_mac_result_dict"].get("other_info", "")
                prbs_all_result_dict["prbs_mac_result_dict"]["other_info"] = result_dict_other_info + prbs_all_result_dict_other_info
            elif (test_type == "prbs_sys"):
                if prbs_all_result_dict["prbs_sys_result_dict"] == {}:
                    prbs_all_result_dict["prbs_sys_result_dict"] = copy.deepcopy(result_dict)
                prbs_all_result_dict["prbs_sys_result_dict"]["test_type"] = "prbs_sys"
                result_dict_other_info = result_dict.get("other_info", "")
                prbs_all_result_dict_other_info = prbs_all_result_dict["prbs_sys_result_dict"].get("other_info", "")
                prbs_all_result_dict["prbs_sys_result_dict"]["other_info"] = result_dict_other_info + prbs_all_result_dict_other_info
            elif (test_type == "prbs_line"):
                if prbs_all_result_dict["prbs_line_result_dict"] == {}:
                    prbs_all_result_dict["prbs_line_result_dict"] = copy.deepcopy(result_dict)
                prbs_all_result_dict["prbs_line_result_dict"]["test_type"] = "prbs_line"
                result_dict_other_info = result_dict.get("other_info", "")
                prbs_all_result_dict_other_info = prbs_all_result_dict["prbs_line_result_dict"].get("other_info", "")
                prbs_all_result_dict["prbs_line_result_dict"]["other_info"] = result_dict_other_info + prbs_all_result_dict_other_info
            else:
                if prbs_all_result_dict["prbs_mac_result_dict"] == {}:
                    prbs_all_result_dict["prbs_mac_result_dict"] = copy.deepcopy(result_dict)
                if prbs_all_result_dict["prbs_sys_result_dict"] == {}:
                    prbs_all_result_dict["prbs_sys_result_dict"] = copy.deepcopy(result_dict)
                if prbs_all_result_dict["prbs_line_result_dict"] == {}:
                    prbs_all_result_dict["prbs_line_result_dict"] = copy.deepcopy(result_dict)

                prbs_all_result_dict["prbs_mac_result_dict"]["test_type"] = "prbs_mac"
                prbs_all_result_dict["prbs_sys_result_dict"]["test_type"] = "prbs_sys"
                prbs_all_result_dict["prbs_line_result_dict"]["test_type"] = "prbs_line"

                result_dict_other_info = result_dict.get("other_info", "")
                prbs_all_result_dict_other_info = prbs_all_result_dict["prbs_mac_result_dict"].get("other_info", "")
                prbs_all_result_dict["prbs_mac_result_dict"]["other_info"] = result_dict_other_info + prbs_all_result_dict_other_info

                result_dict_other_info = result_dict.get("other_info", "")
                prbs_all_result_dict_other_info = prbs_all_result_dict["prbs_sys_result_dict"].get("other_info", "")
                prbs_all_result_dict["prbs_sys_result_dict"]["other_info"] = result_dict_other_info + prbs_all_result_dict_other_info

                result_dict_other_info = result_dict.get("other_info", "")
                prbs_all_result_dict_other_info = prbs_all_result_dict["prbs_line_result_dict"].get("other_info", "")
                prbs_all_result_dict["prbs_line_result_dict"]["other_info"] = result_dict_other_info + prbs_all_result_dict_other_info
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            return prbs_all_result_dict
        return prbs_all_result_dict

    @staticmethod
    def prbs_int_start_f(**kwargs):
        '''IntPhy prbs test'''

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        result_dict = kwargs["r_dict"]

        try:
            # Because the upports imported may be different each time, need to obtain the upports again
            f_obj.get_unit_port_list(upports)
            f_obj.get_prbs_port_range()
            ret, output = f_obj.start_test()
            if ret is False:
                other_info = result_dict.get("other_info", "")
                result_dict["other_info"] = other_info + "prbs_int_start_f fail, output:%s\n" % output
                log_error("prbs_int_start_f fail, output:%s" % output)
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict
        return ret_t, result_dict

    @staticmethod
    def prbs_int_check_f(**kwargs):
        '''IntPhy prbs results check'''

        successport = []
        errorport = []

        f_obj = kwargs["f_obj"]
        ret_t = kwargs["ret_t"]
        upports = kwargs["uprt"]
        result_dict = kwargs["r_dict"]

        try:
            for port in upports:
                bcm_port = f_obj.device_port_list[port - 1].bcm_port
                unit_port = f_obj.device_port_list[port - 1].unit_port
                port_info = "port:%d %s(%d)" % (port, bcm_port, unit_port)
                ret, output = f_obj.check_test(port=port)
                if ret is True:
                    successport.append(port)
                    log_debug("%-18s:prbs check success" % port_info)
                else:
                    ret_t -= 1
                    errorport.append(port)
                    output_info = result_dict["port_info_dict"][port]["log"]
                    result_dict["port_info_dict"][port]["log"] = output_info + "prbs_int_check_f fail\noutput:%s" % output
                    log_error("%-18s:prbs check fail\noutput:%s" % (port_info, output))
        except Exception as except_result:
            msg = traceback.format_exc()
            print("Exception_info:\n%s" % msg)
            ret_t = -999
            return ret_t, result_dict, successport, errorport
        return ret_t, result_dict, successport, errorport

    @staticmethod
    def sdk_cmd_redirect_judge(redirect):
        '''determine whether input redirection is enabled and set the redirect based on the incoming redirect'''

        if redirect == False and sdk_cmd_redirect_console == True:
            PortLog.set_sdk_cmd_redirect_console(False)
        elif redirect == True and sdk_cmd_redirect_console == False:
            PortLog.set_sdk_cmd_redirect_console(True)

    @staticmethod
    def test_return(**kwargs):
        '''test case return result judgment'''
        ret_t = kwargs["ret_t"]
        test_type = kwargs.get("test_type", "")
        result_dict = kwargs.get("result_dict", {})
        prbs_all_result_dict = kwargs.get("prbs_all_result_dict", {})
        return_dict = {}
        errorports_flag = False # errorports > 0 is True

        if prbs_all_result_dict:
            # prbs tests with external PHY return dictionaries with 3 side results, so separate judgments are made
            # test_type、test_result assignment, when testing results on one side or the other
            return_dict = copy.deepcopy(prbs_all_result_dict)
            if "errorports" in return_dict["prbs_mac_result_dict"]:
                if (len(return_dict["prbs_mac_result_dict"]["errorports"])) > 0:
                    errorports_flag = True
            elif "errorports" in return_dict["prbs_sys_result_dict"]:
                if (len(return_dict["prbs_sys_result_dict"]["errorports"])) > 0:
                    errorports_flag = True
            elif "errorports" in return_dict["prbs_line_result_dict"]:
                if (len(return_dict["prbs_line_result_dict"]["errorports"])) > 0:
                    errorports_flag = True
            else:
                errorports_flag = False
        else:
            return_dict = copy.deepcopy(result_dict)
            return_dict["test_type"] = test_type
            if ret_t < 0:
                return_dict["test_result"] = False
            else:
                return_dict["test_result"] = True

            if "errorports" in return_dict:
                if (len(return_dict["errorports"])) > 0:
                    errorports_flag = True
        if ret_t < 0:
            if port_log_info_print_to_console and errorports_flag:
                # Control macros enabled: prints the log of the entire test flow to the console when the test fails and errorports > 0
                print(global_port_log_info)
            return return_dict
        return return_dict

class PortLog():
    '''port log macro control class'''

    @classmethod
    def get_log_also_print_to_console(cls):
        '''set control macros: print out the log at the same time'''

        log_debug("get_log_also_print_to_console: %r" % log_also_print_to_console)
        return log_also_print_to_console

    @staticmethod
    def set_log_also_print_to_console(console_val):
        '''set control macros: print out the log at the same time'''

        global log_also_print_to_console
        log_also_print_to_console = console_val
        log_debug("set_log_also_print_to_console: %r" % log_also_print_to_console)

    @classmethod
    def get_cmd_also_print_to_console(cls):
        '''set control macros: print out the log at the same time'''

        log_debug("get_cmd_also_print_to_console: %r" % cmd_also_print_to_console)
        return cmd_also_print_to_console

    @staticmethod
    def set_cmd_also_print_to_console(console_val):
        '''set control macros: print out the results of execute cmd at the same time'''

        global cmd_also_print_to_console
        cmd_also_print_to_console = console_val
        log_debug("set_cmd_also_print_to_console: %r" % cmd_also_print_to_console)

    @classmethod
    def get_cmd_output_also_print_to_console(cls):
        '''set control macros: print out the results of execute cmd at the same time'''

        log_debug("get_cmd_output_also_print_to_console: %r" % cmd_output_also_print_to_console)
        return cmd_output_also_print_to_console

    @staticmethod
    def set_cmd_output_also_print_to_console(console_val):
        '''set control macros: print out the results of execute cmd at the same time'''

        global cmd_output_also_print_to_console
        cmd_output_also_print_to_console = console_val
        log_debug("set_cmd_output_also_print_to_console: %r" % cmd_output_also_print_to_console)

    @classmethod
    def get_port_log_info_print_to_console(cls):
        '''set control macros: prints the log of the entire test flow to the console when the test fails'''

        log_debug("get_port_log_info_print_to_console: %r" % port_log_info_print_to_console)
        return port_log_info_print_to_console

    @staticmethod
    def set_port_log_info_print_to_console(console_val):
        '''set control macros: prints the log of the entire test flow to the console when the test fails'''

        global port_log_info_print_to_console
        port_log_info_print_to_console = console_val
        log_debug("set_port_log_info_print_to_console: %r" % port_log_info_print_to_console)

    @classmethod
    def get_sdk_cmd_redirect_console(cls):
        '''set control macros: enable input redirection  cmd + < /dev/null'''

        log_debug("get_sdk_cmd_redirect_console: %r" % sdk_cmd_redirect_console)
        return sdk_cmd_redirect_console

    @staticmethod
    def set_sdk_cmd_redirect_console(console_val):
        '''set control macros: enable input redirection  cmd + < /dev/null'''

        global sdk_cmd_redirect_console
        sdk_cmd_redirect_console = console_val
        log_debug("set_sdk_cmd_redirect_console: %r" % sdk_cmd_redirect_console)

def hsdk_check():
    if global_port_config.get("flag", False) is False:
        pt = PortHsdkTest()
    if global_port_config.get("hsdk_device", 0) == 1:
        return True
    else:
        return False

@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''device operator'''
    pass

@main.command()
def test():
    pr = PortPrbsTest()
    pr.clear_port_prbs()
    pr.init_port_prbs()
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("mac", i + 1)
        print (ret)
        print (result)
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("sys", i + 1)
        print (ret)
        print (result)
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("line", i + 1)
        print (ret)
        print (result)
    pr.clear_port_prbs()


if __name__ == '__main__':
    main()


'''
portts = PortTest()


portts.init_port_prbs()
for i in range(64):
    portts.set_port_prbs((i+1),1)
    # portts.set_port_prbs(2,1)

time.sleep(5)

for i in range(64):
    print portts.get_port_prbs_result((i+1))
    # print portts.get_port_prbs_result(2)
    
for i in range(64):
    portts.set_port_prbs((i+1),0)


#status = get_port_status(i + 1)
'''
