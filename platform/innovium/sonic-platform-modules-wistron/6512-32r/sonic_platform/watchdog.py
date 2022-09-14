#!/usr/bin/env python

########################################################################
#
# Abstract base class for implementing a platform-specific class with
# which to interact with a hardware watchdog module in SONiC
#
########################################################################

try:
    import subprocess
    from sonic_platform_base.watchdog_base import WatchdogBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

WDT_COMMON_ERROR = -1
IPMI_WDT_EN_KICK_CMD = "ipmitool mc watchdog reset"
IPMI_WDT_OFF_CMD = "ipmitool mc watchdog off"
IPMI_WDT_SET_TIMEOUT_CMD = "ipmitool raw 0x6 0x24 0x4 0x0 0x0 0x0 {0} {1}"
IPMI_WDT_GET_TIMEOUT_CMD = "ipmitool mc watchdog get | grep Present | awk '{print $3}'"
IPMI_WDT_GET_STATUS_CMD = "ipmitool mc watchdog get | grep 'Timer Is' | awk '{printf $4}'"

class Watchdog(WatchdogBase):
    """
    Abstract base class for interfacing with a hardware watchdog module
    """

    def __init__(self):
        # Set default value
        self.armed = self._get_status()
        self.timeout = self._gettimeout()

    def _get_status(self):
        p = subprocess.Popen(IPMI_WDT_GET_STATUS_CMD, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        status_str = out.decode().rstrip('\n')

        if "Running" in status_str:
            return True

        return False

    def _enable(self):
        """
        Turn on the watchdog timer
        """
        p = subprocess.Popen(IPMI_WDT_EN_KICK_CMD, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return 0

    def _disable(self):
        """
        Turn off the watchdog timer
        """
        p = subprocess.Popen(IPMI_WDT_OFF_CMD, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return 0

    def _keepalive(self):
        """
        Keep alive watchdog timer
        """
        p = subprocess.Popen(IPMI_WDT_EN_KICK_CMD, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return 0

    def _settimeout(self, seconds):
        """
        Set watchdog timer timeout
        @param seconds - timeout in seconds
        @return is the actual set timeout
        """
        ipmi_timeout = seconds * 10;
        cmd = IPMI_WDT_SET_TIMEOUT_CMD.format(ipmi_timeout % 256, int(ipmi_timeout / 256))
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()

        return seconds

    def _gettimeout(self):
        p = subprocess.Popen(IPMI_WDT_GET_TIMEOUT_CMD, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return int(out.decode().rstrip('\n'), 10)

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
        ret = WDT_COMMON_ERROR

        if seconds < 0 or seconds > 500:
            return ret

        try:
            if self.timeout != seconds:
                self.timeout = self._settimeout(seconds)

            if self.armed:
                self._keepalive()
            else:
                self._enable()

            ret = self.timeout
        except IOError as e:
            print("Error: unable to enable wdt due to : {}".format(e))

        return ret

    def disarm(self):
        """
        Disarm the hardware watchdog
        Returns:
            A boolean, True if watchdog is disarmed successfully, False if not
        """
        disarmed = False
        try:
            self._disable()
            self.armed = False
            disarmed = True
        except IOError as e:
            print("Error: unable to disable wdt due to : {}".format(e))
        return disarmed

    def is_armed(self):
        """
        Retrieves the armed state of the hardware watchdog.
        Returns:
            A boolean, True if watchdog is armed, False if not
        """
        return self.armed

    def get_remaining_time(self):
        """
        If the watchdog is armed, retrieve the number of seconds remaining on
        the watchdog timer
        Returns:
            An integer specifying the number of seconds remaining on thei
            watchdog timer. If the watchdog is not armed, returns -1.
        """

        timeleft = WDT_COMMON_ERROR

        if self.armed:
            return self._gettimeout()

        return timeleft
