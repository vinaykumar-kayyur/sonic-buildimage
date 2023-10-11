#!/usr/bin/env python

#############################################################################
# Huaqin
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################

from __future__ import division
import math
import urllib3
import json
import os.path

try:
    from sonic_platform_base.fan_base import FanBase
    from sonic_platform.helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

ROTOR_PER_FAN = 2
FAN_SPEED_TOLERANCE = 10

class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, fan_tray_index=0,fan_index=0, is_psu_fan=False, psu_index=0):
        FanBase.__init__(self)
        self.rawcmd = "http://240.1.1.1:8080/api/sys/raw"
        self.http = urllib3.PoolManager()
        self._api_helper = APIHelper()
        self.psu_fan = is_psu_fan
        self.fan_tray_index = fan_tray_index
        self.fan_index = fan_index
        if self.psu_fan:
            self.psu_index = psu_index
            self.bmc_psu = "http://240.1.1.1:8080/api/psu/psu{}".format((self.psu_index + 1))
            self.psu_info = None
        else:
            self.bmc_fan = "http://240.1.1.1:8080/api/fan/fan{}".format((self.fan_tray_index + 1))
            self.fan_info = None
        
        FanBase.__init__(self)

    def get_data(self):
        if self.psu_fan:
            resp = self.http.request('GET', self.bmc_psu)
            if 200 != resp.status:
                self.psu_info = None
                return
        else:
            resp = self.http.request('GET', self.bmc_fan)
            if 200 != resp.status:
                self.fan_info = None
                return
        data_info = resp.data.decode('utf-8')
        data_json = json.loads(data_info)
        if not data_json or 'data' not in data_json:
            self.psu_info = None
            self.fan_info = None
            return
        if self.psu_fan:    
            self.psu_info = data_json.get('data')
        else:
            self.fan_info = data_json.get('data')

        return

    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        fan_dir = self.FAN_DIRECTION_EXHAUST
        self.get_data()
        if self.psu_fan:
            return fan_dir
        else:
            if self.fan_info is None:
                return fan_dir
            if "yes" == self.fan_info["Present"]:
                fan_dir = self.FAN_DIRECTION_EXHAUST if "F2B" == self.fan_info["AirFlow"] \
                        else self.FAN_DIRECTION_INTAKE

        return fan_dir

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        fan_speed = 0
        self.get_data()
        if self.psu_fan:
            if self.psu_info is None:
                return fan_speed
            if "yes" == self.psu_info["Present"]:
                speed = self.psu_info["FanSpeed"]["Value"]
                max_speed = self.psu_info["FanSpeed"]["Max"]
                fan_speed = 100 * speed / max_speed
        else:
            if self.fan_info is None:
                return fan_speed
            if "yes" == self.fan_info["Present"]:
                rotor = "Rotor{}".format((self.fan_index + 1))
                speed = self.fan_info[rotor]["Speed"]
                max_speed = self.fan_info[rotor]["SpeedMax"]
                fan_speed = 100 * speed / max_speed 

        return int(fan_speed)

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)

        """
        fan_target = 0
        self.get_data()
        if self.psu_fan:
            return 'N/A'
        else:
            if self.fan_info is None:
                return fan_target
            if "yes" == self.fan_info["Present"]:
                rotor = "Rotor{}".format((self.fan_index + 1))
                if "yes" == self.fan_info[rotor]["status"]:
                    speed = self.fan_info[rotor]["speed_target"]
                    max_speed = self.fan_info[rotor]["SpeedMax"]
                    fan_target = 100 * speed / max_speed

        return int(fan_target)

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan
        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        return FAN_SPEED_TOLERANCE

    def set_speed(self, speed):
        """
        Sets the fan speed
        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)
        Returns:
            A boolean, True if speed is set successfully, False if not
        """
        succ = False
        if self.psu_fan:
            return succ
        if self.fan_info is not None:
            if "yes" == self.fan_info["Present"]:
                cmd = "/usr/local/bin/set_fan_speed.sh {} {}".format(speed, (self.fan_tray_index + 1))
                data = {"command": cmd}
                data = json.dumps(data)
                ret = self.http.request('POST', self.rawcmd, data)
                if 200 == ret.status:
                    succ = True
                
        return succ

    def set_status_led(self, color):
        """
        Sets the state of the fan module status LED
        Args:
            color: A string representing the color with which to set the
                   fan module status LED
        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        succ = False
        typ = ""
        col = ""
        sta = ""
        if self.psu_fan:
            typ = "psu"
        else:
            typ = "fan"

        if color == self.STATUS_LED_COLOR_GREEN:
            col = "green"
            sta = "on"
        elif color == self.STATUS_LED_COLOR_AMBER or color == self.STATUS_LED_COLOR_RED:
            col = "yellow"
            sta = "on"
        elif color == self.STATUS_LED_COLOR_OFF:
            col = "green"
            sta = "off"
        else:
            return succ

        cmd = "/usr/local/bin/set_sled.sh -t {} -s {} -c {} -f 1".format(typ,sta,col)
        data = {"command": cmd}
        data = json.dumps(data)
        ret = self.http.request('POST', self.rawcmd, data)
        if 200 == ret.status:
            succ = True
        
        return succ

    def get_status_led(self):
        """
        Gets the state of the fan status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        return True
############################# Device methods ############################

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        fan_n = "N/A"
        self.get_data()
        if self.psu_fan:
            if self.psu_info is None:
                return fan_n
            fan_n = "PSU{}-FAN{}".format(self.psu_index + 1, self.fan_index + 1)
        else:
            if self.fan_info is None:
                return fan_n
            fan_n = "{}-Rotors{}".format(self.fan_info["Name"],(self.fan_index + 1))

        return fan_n

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        fan_pres = False
        self.get_data()
        if self.psu_fan:
            if self.psu_info is None:
                return fan_pres
            if "yes" == self.psu_info["Present"] and 0 < self.psu_info["FanSpeed"]["Value"]:
                fan_pres = True
        else:
            if self.fan_info is None:
                return fan_pres
            rotor = "Rotor{}".format((self.fan_index + 1))
            if "yes" == self.fan_info["Present"] and "yes" == self.fan_info[rotor]["status"]:
                fan_pres = True

        return fan_pres

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        fan_model = "N/A"
        self.get_data()
        if self.psu_fan:
            return fan_model
        else:
            if self.fan_info is None:
                return fan_model
            if "yes" == self.fan_info["Present"]:
                fan_model = self.fan_info["ModelId"]

        return fan_model

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        fan_sn = "N/A"
        self.get_data()
        if self.psu_fan:
            if self.psu_info is None:
                return fan_sn
            if "yes" == self.psu_info["Present"]:
                fan_sn = self.psu_info["SN"]
        else: 
            if self.fan_info is None:
                return fan_sn
            if "yes" == self.fan_info["Present"]:
                fan_sn = self.fan_info["SN"]

        return fan_sn

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        fan_sta = False
        self.get_data()
        if self.psu_fan:
            if self.psu_info is None:
                return fan_sta
            if "yes" == self.psu_info["Present"] and self.psu_info["FanSpeed"]["Value"]:
                fan_sta = True
        else:
            if self.fan_info is None:
                return fan_sta
            rotor = "Rotor{}".format((self.fan_index + 1))
            if "yes" == self.fan_info[rotor]["status"]:
                toler = math.fabs((self.fan_info[rotor]["speed_target"] - self.fan_info[rotor]["Speed"]))
                toler_target = self.fan_info[rotor]["speed_tolerance"]
                if toler < toler_target:
                    fan_sta = True
        return fan_sta

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        If the agent cannot determine the parent-relative position
        for some reason, or if the associated value of
        entPhysicalContainedIn is'0', then the value '-1' is returned
        Returns:
            integer: The 1-based relative physical position in parent device
            or -1 if cannot determine the position
        """
        return (self.fan_index + 1)

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True if not self.psu_fan else False
