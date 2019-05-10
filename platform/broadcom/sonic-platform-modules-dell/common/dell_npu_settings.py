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
import dell_deemphasis

SYSLOG_IDENTIFIER = "dell_npu_set"

HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_SPECIFIC_CLASS_NAME = "SfpUtil"
PLATFORM_SPECIFIC_MODULE_NAME = "sfputil"

# Global platform-specific sfputil class instance
platform_sfputil = None

# Timer Value
DEFAULT_WAIT_FOR_SWSS_SYNCD = 45
MINIMUM_WAIT_FOR_BCM_SHELL = 3
MINIMUM_WAIT_FOR_SWSS_SYNCD = 5
MINIMUM_RETRY_FOR_SWSS_DB = 30


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


# Wait for bcmshell to be running
def check_bcm_shell_status():
    while (1):
        # Check if bcmshell is ready.
        # Execute ps command,
        # If bcmShell is not ready it raises exception
        # Wait till bcmcmd returns success
        cmd = "bcmcmd ps"
        try:
            result = subprocess.check_output(cmd, shell=True)
            return 0
        except subprocess.CalledProcessError as e:
            log_info("Waiting for bcmShell to get ready !!!")
            time.sleep(MINIMUM_WAIT_FOR_BCM_SHELL)
            continue
    return 0


# Wait for syncd to be running
def check_swss_sycnd_status():
    redis_db_cnt = 0
    while (1):
        # Check if syncd starts and redisDb populated
        # Wait till redis Db return valid output
        cmd_p1 = "docker exec -i swss bash -c "
        cmd_p2 = cmd_p1 + "\"echo -en \\\"SELECT 1\\\\nHLEN HIDDEN\\\" | "
        cmd = cmd_p2 + "redis-cli | sed -n 2p\""
        try:
            result = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            # Wait till swss is spawned
            log_info("Waiting for swss to spawn !!!")
            time.sleep(MINIMUM_WAIT_FOR_SWSS_SYNCD)
            continue
        if (result.rstrip() == "5"):
            # Check if bcm_shell server,client is ready
            ret = check_bcm_shell_status()
            return ret
        else:
            if (redis_db_cnt == MINIMUM_RETRY_FOR_SWSS_DB):
                log_error("Fail : RedisDb in swss not populated")
                sys.exit(2)

            # Wait till redisDb is populated
            log_info("Waiting for redisDb to be populated !!!")
            time.sleep(MINIMUM_WAIT_FOR_SWSS_SYNCD)
            redis_db_cnt = redis_db_cnt + 1
    return 0


def main():
    log_info("Starting up...")

    if not os.geteuid() == 0:
        log_error("Must be root to run this daemon")
        print "Error: Must be root to run this daemon"
        sys.exit(1)

    # Register our signal handlers
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Default Wait Time till SWSS spawns
    time.sleep(DEFAULT_WAIT_FOR_SWSS_SYNCD)

    err = check_swss_sycnd_status()
    if (err != 0):
        log_error("Error timeout for swss service spawn")
        sys.exit(3)

    # Instantiate Dell DeEmphasis object
    log_info("Dell DeEmphasis NPU<->CPU Settings Started...")
    dell_deemphasisd = dell_deemphasis.dell_deemphasis_set()
    dell_deemphasisd.run()

    log_info("Dell DeEmphasis NPU<->CPU Settings Completed Successfully...")


if __name__ == "__main__":
    main()
