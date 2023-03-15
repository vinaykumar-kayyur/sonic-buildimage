#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/3/9 16:19
# @Mail    : J_Talong@163.com yajiang@celestica.com
# @Author  : jiang tao

import fcntl
import os
import array

try:
    from sonic_platform_base.watchdog_base import WatchdogBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

""" ioctl constants """
IO_WRITE = 0x40000000
IO_READ = 0x80000000
IO_READ_WRITE = 0xC0000000
IO_SIZE_INT = 0x00040000
IO_SIZE_40 = 0x00280000
IO_TYPE_WATCHDOG = ord('W') << 8

WDR_INT = IO_READ | IO_SIZE_INT | IO_TYPE_WATCHDOG
WDR_40 = IO_READ | IO_SIZE_40 | IO_TYPE_WATCHDOG
WDWR_INT = IO_READ_WRITE | IO_SIZE_INT | IO_TYPE_WATCHDOG

""" Watchdog ioctl commands """
WDIOC_GETSUPPORT = 0 | WDR_40
WDIOC_GETSTATUS = 1 | WDR_INT
WDIOC_GETBOOTSTATUS = 2 | WDR_INT
WDIOC_GETTEMP = 3 | WDR_INT
WDIOC_SETOPTIONS = 4 | WDR_INT
WDIOC_KEEPALIVE = 5 | WDR_INT
WDIOC_SETTIMEOUT = 6 | WDWR_INT
WDIOC_GETTIMEOUT = 7 | WDR_INT
WDIOC_SETPRETIMEOUT = 8 | WDWR_INT
WDIOC_GETPRETIMEOUT = 9 | WDR_INT
WDIOC_GETTIMELEFT = 10 | WDR_INT

""" Watchdog status constants """
WDIOS_DISABLECARD = 0x0001
WDIOS_ENABLECARD = 0x0002

WDT_COMMON_ERROR = -1
WD_MAIN_IDENTITY = "iTCO_wdt"
WDT_SYSFS_PATH = "/sys/class/watchdog/"

DEFAULT_TIMEOUT = 180
watchdog = 0


class Watchdog(WatchdogBase):
    def __init__(self):
        self.watchdog = None
        self.wdt_main_dev_name = self._get_wdt()
        if self.wdt_main_dev_name is None:
            raise Exception("Watchdog device is not instantiated")

        self.time_left = "/sys/class/watchdog/%s/timeleft" % self.wdt_main_dev_name
        self.state_path = "/sys/class/watchdog/%s/state" % self.wdt_main_dev_name
        self.timeout_path = "/sys/class/watchdog/%s/timeout" % self.wdt_main_dev_name

        self.armed = False if self._read_file(self.state_path) == "inactive" else True
        self.watchdog_device_path = "/dev/{}".format(self.wdt_main_dev_name)

        self.timeout = DEFAULT_TIMEOUT

    def _is_wd_main(self, dev):
        """
        Checks watchdog identity
        """
        identity = self._read_file("{}/{}/identity".format(WDT_SYSFS_PATH, dev))
        return identity == WD_MAIN_IDENTITY or identity == 'wdat_wdt'

    def _get_wdt(self):
        """
        Retrieves watchdog device
        """

        wdt_main_dev_list = [dev for dev in os.listdir("/dev/") if dev.startswith("watchdog") and self._is_wd_main(dev)]
        if not wdt_main_dev_list:
            return None
        wdt_main_dev_name = wdt_main_dev_list[0]
        return wdt_main_dev_name

    @staticmethod
    def _read_file(file_path):
        """
        Read text file
        """
        try:
            with open(file_path, "r") as fd:
                txt = fd.read()
        except IOError:
            return WDT_COMMON_ERROR
        return txt.strip()

    def _enable(self):
        """
        Turn on the watchdog timer
        """
        if self.watchdog is None:
            self.watchdog = os.open(self.watchdog_device_path, os.O_RDWR)
        req = array.array('h', [WDIOS_ENABLECARD])
        fcntl.ioctl(self.watchdog, WDIOC_SETOPTIONS, req, False)

    def _disable(self):
        """
        Turn off the watchdog timer
        """
        if self.watchdog is None:
            self.watchdog = os.open(self.watchdog_device_path, os.O_RDWR)
        req = array.array('h', [WDIOS_DISABLECARD])
        fcntl.ioctl(self.watchdog, WDIOC_SETOPTIONS, req, False)

    def _keep_alive(self):
        """
        Keep alive watchdog timer
        """
        if self.watchdog is None:
            self.watchdog = os.open(self.watchdog_device_path, os.O_RDWR)
        fcntl.ioctl(self.watchdog, WDIOC_KEEPALIVE)

    def _set_timeout(self, seconds):
        """
        Set watchdog timer timeout
        @param seconds - timeout in seconds
        @return is the actual set timeout
        """
        if self.watchdog is None:
            self.watchdog = os.open(self.watchdog_device_path, os.O_RDWR)
        req = array.array('I', [seconds])
        fcntl.ioctl(self.watchdog, WDIOC_SETTIMEOUT, req, True)
        return int(req[0])

    def _get_timeout(self):
        """
        Get watchdog timeout
        @return watchdog timeout
        """
        return int(self._read_file(self.timeout_path))

    def _get_time_left(self):
        """
        Get time left before watchdog timer expires
        @return time left in seconds
        """
        return int(self._read_file(self.time_left))

    # Watchdog Base API #

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
        if seconds < 0:
            return ret

        try:
            if self.timeout != seconds:
                self.timeout = self._set_timeout(seconds)

            if self.armed:
                self._keep_alive()
            else:
                self._enable()
                self.armed = True
            ret = self.timeout
        except IOError:
            pass

        return ret

    def disarm(self):
        """
        Disarm the hardware watchdog
        Returns:
            A boolean, True if watchdog is disarmed successfully, False if not
        """
        disarmed = False
        if self.is_armed():
            try:
                self._disable()
                self.armed = False
                disarmed = True
            except IOError:
                pass

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

        time_left = WDT_COMMON_ERROR

        if self.armed:
            try:
                time_left = self._get_time_left()
            except IOError:
                pass

        return time_left

    def __del__(self):
        """
        Close watchdog
        """

        if self.watchdog is not None:
            os.close(self.watchdog)
