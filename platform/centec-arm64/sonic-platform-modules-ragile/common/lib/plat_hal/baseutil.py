#######################################################
#
# baseutil.py
# Python implementation of the Class baseutil
# Original author: support@ragilenetworks.com
#
#######################################################

import json
import subprocess
import imp
import re
import os
import syslog
from osutil import osutil

SYSLOG_IDENTIFIER = "BMC"

def getonieplatform():
    if not os.path.isfile('/host/machine.conf'):
        return ""
    machine_vars = {}
    with open('/host/machine.conf') as machine_file:
        for line in machine_file:
            tokens = line.split('=')
            if len(tokens) < 2:
                continue
            machine_vars[tokens[0]] = tokens[1].strip()
    return machine_vars.get("onie_platform")

configfile_path = "/usr/lib/python2.7/dist-packages/"
platform = (getonieplatform()).replace("-","_")

devicefile = (configfile_path + platform + "_device.py")
monitorfile = (configfile_path + platform + "_monitor.py")

class baseutil:

    CONFIG_NAME =  'devices'
    MONITOR_CONFIG_NAME =  'monitor'
    UBOOT_ENV_URL = '/etc/device/uboot_env'

    @staticmethod
    def get_config():
        real_path = devicefile
        devices = imp.load_source(baseutil.CONFIG_NAME, real_path)
        return devices.devices

    @staticmethod
    def get_monitor_config():
        real_path = monitorfile
        monitor = imp.load_source(baseutil.MONITOR_CONFIG_NAME, real_path)
        return monitor.monitor

    @staticmethod
    def get_productname():
        ret, val = osutil.command("cat %s |grep productname | awk -F\"=\" '{print $2;}'" % baseutil.UBOOT_ENV_URL)
        tmp = val.lower().replace('-', '_')
        if ret != 0 or len(val) <= 0:
            raise Exception("get productname error")
        else:
            return tmp

    @staticmethod
    def get_platform():
        ret, val = osutil.command("cat %s |grep conffitname | awk -F\"=\" '{print $2;}'" % baseutil.UBOOT_ENV_URL)
        if ret != 0 or len(val) <= 0:
            raise Exception("get platform error")
        else:
            return val

    @staticmethod
    def get_product_fullname():
        ret, val = osutil.command("cat %s |grep productname | awk -F\"=\" '{print $2;}'" % baseutil.UBOOT_ENV_URL)
        if ret != 0 or len(val) <= 0:
            raise Exception("get productname error")
        else:
            return val

    @staticmethod
    def logger_debug(msg):
        syslog.openlog(SYSLOG_IDENTIFIER)
        syslog.syslog(syslog.LOG_DEBUG, msg)
        syslog.closelog()