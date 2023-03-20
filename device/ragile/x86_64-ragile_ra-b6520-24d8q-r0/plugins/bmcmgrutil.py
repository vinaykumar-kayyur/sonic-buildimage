#
# bmcmgrutil.py
# Platform-specific BMC config interface for SONiC
#

import os.path
import subprocess
import syslog
import time

try:
    from sonic_bmcmgr.bmcmgr_base import BmcmgrBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class BmcmgrUtil(BmcmgrBase):
    """Platform-specific BMCmgrutil class"""
    USER_ID = "1"
    USER_NAME = "ADMIN"
    DEFAULT_CHANNEL = "1"

    def __init__(self):
        BmcmgrBase.__init__(self)
        DEFAULT_PASSWORD = "tcsSONiC2017"

    def init_unboxing(self):
        rv = self.set_password(self.DEFAULT_PASSWORD)
        return rv[0]

    def run_command(self, command, ignore_error=False, try_times=3):
        """Run bash command and print output to stdout
        """

        if try_times <= 0:
            return -1

        for i in range(try_times):
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            (out, err) = proc.communicate()
            if proc.returncode != 0:
                time.sleep(1)
                continue
            else:
                #print('BMCMGRD: {} return {}. stdout {}. stderr {}'.format(command, proc.returncode, out, err))
                return [proc.returncode, out, err]

        if proc.returncode != 0 and not ignore_error:
            print('BMCMGRD: {} return {}. stdout {}. stderr {}'.format(command, proc.returncode, out, err))

        return [proc.returncode, out, err]

    def add_whitelist(self, wip):
        ip = wip.split(".")
        return self.run_command("ipmitool raw 0x32 0xc1 {} {} {} {}".format(ip[0], ip[1], ip[2], ip[3]))

    def remove_whitelist(self, wip):
        ip = wip.split(".")
        return self.run_command("ipmitool raw 0x32 0xc2 {} {} {} {}".format(ip[0], ip[1], ip[2], ip[3]))

    def remove_all_whitelist(self):
        return [0, "Not support", ""]

    def enable_whitelist(self):
        return self.run_command("ipmitool raw 0x32 0xc3")

    def disable_whitelist(self):
        return self.run_command("ipmitool raw 0x32 0xc4")

    def set_password(self, password):
        return self.run_command("ipmitool user set password {} {}".format(self.USER_ID, password))

    def set_ntpip(self, ntpip):
        ip = ntpip.split(".")
        return self.run_command("ipmitool raw 0x32 0x03 0x03 {} {} {} {}".format(ip[0], ip[1], ip[2], ip[3]))