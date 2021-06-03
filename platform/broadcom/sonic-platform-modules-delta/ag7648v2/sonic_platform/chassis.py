#!/usr/bin/env python
#
# Name: chassis.py, version: 1.0
#
# Description: Module contains the definitions of SONiC platform APIs
#

try:
    import os
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.eeprom import Eeprom
    from sonic_platform.fan import Fan
    from sonic_platform.fan_drawer import FanDrawer
    from sonic_platform.psu import Psu
    from sonic_platform.thermal import Thermal
    from sonic_platform.sfp import Sfp
    import time
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Chassis(ChassisBase):

    def __init__(self):
        ChassisBase.__init__(self)

        self._num_fantray = 5
        self._num_fan = 2
        self._num_psus = 2
        self._num_thermals = 6
        self._num_sfps = 54

        self.POLL_INTERVAL = 1 # Poll interval in seconds
        self.SWPLD_I2C_PATH = "/sys/devices/platform/delta-ag7648v2-swpld.0/"

        # Initialize EEPROM
        self._eeprom = Eeprom()

        # Initialize FAN
        for index in range(0, self._num_fantray):
            fandrawer = FanDrawer(index)
            self._fan_drawer_list.append(fandrawer)
            self._fan_list.extend(fandrawer._fan_list)
        self._num_fans=self._num_fantray * self._num_fan

        # Initialize PSU
        for index in range(1, self._num_psus + 1):
            psu = Psu(index)
            self._psu_list.append(psu)

        # Initialize THERMAL
        for index in range(0, self._num_thermals):
            thermal = Thermal(index)
            self._thermal_list.append(thermal)

        # Initialize SFP
        for index in range(0, self._num_sfps):
            sfp = Sfp(index)
            self._sfp_list.append(sfp)

        self._transceiver_presence = self._get_transceiver_presence()

    def get_num_fans(self):
        return self._num_fans

    def get_num_psus(self):
        return self._num_psus

    def get_num_thermals(self):
        return self._num_thermals

    def get_num_sfps(self):
        return self._num_sfps

    def get_thermal_manager(self):
        from .thermal_manager import ThermalManager
        return ThermalManager

    def get_name(self):
        """
        Retrieves the name of the chassis
        Returns:
            string: The name of the chassis
        """
        return self._eeprom.modelstr()

    def _get_transceiver_presence(self):
        # 1-54 port
        transceiver_presence = 0x3fffffffffffff
        # 1 = absent , 0 = present
        for port_num in range(1,self.get_num_sfps()+1):
            try:
                # SWPLD2 modprs for sfp port 1~32
                # SWPLD3 modprs for sfp port 33~48
                # SWPLD3 modprs for qsfp port 49~54
                port = (str(port_num)).zfill(2)
                if port_num  <= 32:
                    present_path = "SWPLD2/sfp_p{}_modprs".format(port)
                elif port_num  <= 48:
                    present_path = "SWPLD3/sfp_p{}_modprs".format(port)
                else:
                    present_path = "SWPLD3/qsfp_p{}_modprs".format(port)

                with open(self.SWPLD_I2C_PATH + present_path, 'r') as present:
                    if int(present.readline()) == 0:
                        flag = 1 << (port_num-1)
                        transceiver_presence = transceiver_presence ^ flag
            except IOError as e:
                print ("Error: unable to open file: %s" % str(e))
        return transceiver_presence

    def get_change_event(self, timeout=0):
        """
        Returns a nested dictionary containing all devices which have
        experienced a change at chassis level

        Args:
            timeout: Timeout in milliseconds (optional). If timeout == 0,
                this method will block until a change is detected.

        Returns:
            (bool, dict):
                - True if call successful, False if not;
                - A nested dictionary where key is a device type,
                  value is a dictionary with key:value pairs in the
                  format of {'device_id':'device_event'},
                  where device_id is the device ID for this device and
                        device_event,
                             status='1' represents device inserted,
                             status='0' represents device removed.
                  Ex. {'fan':{'0':'0', '2':'1'}, 'sfp':{'11':'0'}}
                      indicates that fan 0 has been removed, fan 2
                      has been inserted and sfp 11 has been removed.
        """
        port_dict = {}
        ret_dict = {'sfp': port_dict}
        forever = False

        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000) # Convert to secs
        else:
            return False, ret_dict # Incorrect timeout

        while True:
            if forever:
                timer = self.POLL_INTERVAL
            else:
                timer = min(timeout, self.POLL_INTERVAL)
                start_time = time.time()

            time.sleep(timer)
            cur_presence = self._get_transceiver_presence()

            # Update dict only if a change has been detected
            if cur_presence != self._transceiver_presence:
                changed_ports = self._transceiver_presence ^ cur_presence
                for port in range(1,self.get_num_sfps()+1):
                    # Mask off the bit corresponding to particular port
                    mask = 1 << (port-1)
                    if changed_ports & mask:
                        # qsfp_modprs 1 => optics is removed
                        if cur_presence & mask:
                            port_dict[port] = '0'
                        # qsfp_modprs 0 => optics is inserted
                        else:
                            port_dict[port] = '1'

                # Update current presence
                self._transceiver_presence = cur_presence
                break

            if not forever:
                elapsed_time = time.time() - start_time
                timeout = round(timeout - elapsed_time, 3)
                if timeout <= 0:
                    break

        return True, ret_dict
