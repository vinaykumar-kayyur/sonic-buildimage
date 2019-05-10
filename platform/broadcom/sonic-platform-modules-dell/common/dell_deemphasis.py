import os
import re
import signal
import subprocess
import sys
import imp
import syslog
import time
import os.path
from sonic_sfp.bcmshell import bcmshell

SYSLOG_IDENTIFIER = "dell_deemphasis_set"

HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_DEEMPHASIS_CONF = 'deemphasis.config'
PLATFORM_SPECIFIC_CLASS_NAME = "SfpUtil"
PLATFORM_SPECIFIC_MODULE_NAME = "sfputil"

# Global platform-specific sfputil class instance
platform_sfputil = None


# ========================== Syslog wrappers ==========================
def log_debug(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_DEBUG, msg)
    syslog.closelog()


def log_info(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()


def log_warning(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_WARNING, msg)
    syslog.closelog()


def log_error(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()


# ========================== Signal Handling ==========================
def signal_handler(sig, frame):
    if sig == signal.SIGHUP:
        log_info("Caught SIGHUP - ignoring...")
        return
    elif sig == signal.SIGINT:
        log_info("Caught SIGINT - exiting...")
        sys.exit(128 + sig)
    elif sig == signal.SIGTERM:
        log_info("Caught SIGTERM - exiting...")
        sys.exit(128 + sig)
    else:
        log_warning("Caught unhandled signal '" + sig + "'")


class BcmShell(bcmshell):

    def execute_command(self, cmd):
        self.cmd(cmd)


class dell_deemphasis_set(object):
    """
    Class which configures the CPU-NPU DeEmphasis Settings.
    This script will run only once after reload.
    Attributes:
    """

    # Instantiate BCM Shell
    def __init__(self):
        self.bcm_shell = BcmShell()

    # Form the CPU-NPU DeEmphasis command string
    def form_deemphasis_cmd(self):
        (platform, hwsku) = get_platform_and_hwsku()
        deemp_cmd = list()
        deemp_config = (PLATFORM_ROOT_PATH + "/" + platform +
                        "/" + PLATFORM_DEEMPHASIS_CONF)

        if not os.path.isfile(deemp_config):
            log_error("Fail : %s file not found !!!" % deemp_config)
            sys.exit(2)

        with open(deemp_config) as fp:
            for line in fp:
                deemp_cmd.append(line.strip())

        return deemp_cmd

    # For the Given port and eeprom_dict, configure
    # the preemphasis settings. This invokes the bcmcmd and configures
    # the preemphasis settings for each lane in all the ports
    def deemphasis_set(self):
        cmd_id = 0

        deemp_cmd = self.form_deemphasis_cmd()
        for cmd_id in deemp_cmd:
            self.bcm_shell.execute_command(cmd_id)

        return 0

    # Loop through all the ports, read the eeprom and configure
    # PreEmphasis Values based on eeprom data
    def run(self):
        ret_val = self.deemphasis_set()
        return ret_val


# Returns platform and HW SKU
def get_platform_and_hwsku():
    try:
        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-H', '-v', PLATFORM_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        platform = stdout.rstrip('\n')

        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-d', '-v', HWSKU_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        hwsku = stdout.rstrip('\n')
    except OSError, e:
        raise OSError("Cannot detect platform")

    return (platform, hwsku)
