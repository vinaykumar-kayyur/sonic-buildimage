#
# watchdog_base.py
#
# Abstract base class for implementing a platform-specific class with which
# to interact with a hardware watchdog module in SONiC
#
try:
    import os
    import sys
    import subprocess
    import logging
    import time
    from sonic_platform_base.watchdog_base import WatchdogBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Watchdog(WatchdogBase):
    """
    Abstract base class for interfacing with a hardware watchdog module
    """
    WATCHDOG_DEFAULT_FILE = "/etc/default/watchdog"
    WATCHDOG_CONFIG_FILE = "/etc/watchdog.conf"

    WATCHDOG_START = "systemctl start watchdog.service"
    WATCHDOG_STATUS = "systemctl status watchdog.service"
    WATCHDOG_STOP = "systemctl stop watchdog.service"
    WATCHDOG_RESTART = "systemctl restart watchdog.service"

    def run_command(self, command):

        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        (out, err) = proc.communicate()

        if proc.returncode != 0:
            sys.exit(proc.returncode)

    def write_config(self, filename, search, replace):

        retval = -1

        if (not os.path.isfile(filename)):
            print filename,  'not found !'
            return retval

        with open(filename, "r") as file:
            filedata = file.read()

        if filedata:
            filedata = filedata.replace(search, replace)

        with open(filename, 'w') as file:
            file.write(filedata)

    def check_config(self, filename, param):

        filedata = open(filename).read()
        for item in filedata.split("\n"):
            if param in item:
                return item

        return None

    def get_wd_register(self, reg_name):

        retval = 'ERR'
        WATCHDOG_SYS_DIR = "/sys/class/watchdog/watchdog0"

        wd_reg_file = WATCHDOG_SYS_DIR+'/'+reg_name

        if (not os.path.isfile(wd_reg_file)):
            print wd_reg_file,  'not found !'
            return retval

        try:
            with open(wd_reg_file, 'r') as fd:
                retval = fd.read()
        except Exception as error:
            logging.error("Unable to open ", wd_reg_file, "file !")

        retval = retval.rstrip('\r\n')
        retval = retval.lstrip(" ")
        return retval

    def arm(self, seconds):
        """
        Arm the hardware watchdog with a timeout of <seconds> seconds.
        If the watchdog is currently armed, calling this function will
        simply reset the timer to the provided value. If the underlying
        hardware does not support the value provided in <seconds>, this
        method should arm the watchdog with the *next greater* available
        value.

        Returns:
            An integer specifying the *actual* number of seconds the watchdog
            was armed with. On failure returns -1.
        """

        # Max timeout is 30 seconds
        if seconds > 30:
            seconds = 30

        # Enable watchdog in boot-up
        watchdog_enable = self.check_config(
                                self.WATCHDOG_DEFAULT_FILE,
                                "run_watchdog=1")
        if watchdog_enable is None:
            self.write_config(
                self.WATCHDOG_DEFAULT_FILE,
                "run_watchdog=0",
                "run_watchdog=1")

        # configure watchdog-timeout
        new_timeout = 'watchdog-timeout        = ' + str(seconds)
        old_timeout = self.check_config(
                            self.WATCHDOG_CONFIG_FILE,
                            "watchdog-timeout")

        if old_timeout is not None:
            self.write_config(
                self.WATCHDOG_CONFIG_FILE,
                old_timeout,
                new_timeout)
        else:
            with open(self.WATCHDOG_CONFIG_FILE, "a") as wd_file:
                wd_file.write(new_timeout)
            self.run_command(self.WATCHDOG_START)

        # Restart watchdog service
        self.run_command(self.WATCHDOG_RESTART)

        if self.get_wd_register("timeout") == str(seconds):
            return seconds

        return -1

    def disarm(self):
        """
        Disarm 'watchdog-timeout' in open(self.WATCHDOG_CONFIG_FILE).read():
         the hardware watchdog

        Returns:
            A boolean, True if watchdog is disarmed successfully, False if not
        """
        if self.get_wd_register("state") == "active":

            # Disable watchdog in boot-up
            self.write_config(
                self.WATCHDOG_DEFAULT_FILE,
                "run_watchdog=1",
                "run_watchdog=0")

            return True

        return False

    def is_armed(self):
        """
        Retrieves the armed state of the hardware watchdog.

        Returns:
            A boolean, True if watchdog is armed, False if not
        """

        if self.get_wd_register("state") == "active":
            return True

        return False

    def get_remaining_time(self):
        """
        If the watchdog is armed, retrieve the number of seconds remaining on
        the watchdog timer

        Returns:
            An integer specifying the number of seconds remaining on thei
            watchdog timer. If the watchdog is not armed, returns -1.
        """
        if self.get_wd_register("state") == "active":
            return self.get_wd_register("timeleft")

        return -1

