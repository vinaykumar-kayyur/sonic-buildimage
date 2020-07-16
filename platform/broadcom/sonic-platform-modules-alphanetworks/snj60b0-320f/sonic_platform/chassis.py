#!/usr/bin/env python

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

import sys
import json

try:
    from sonic_platform_base.chassis_base import ChassisBase
    from .fan import Alpha_Fan as Fan
    from .psu import Alpha_Psu as Psu
    from .sfp import Alpha_Sfp as Sfp
    from .thermal import Alpha_Thermal as Thermal
    from .component import Alpha_Component as Component
    from .fan_drawer import Alpha_FanDrawer as FanDrawer
    from .led import Alpha_FanLed as FanLed
    from .led import Alpha_PsuLed as PsuLed
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

#from xcvrd
SFP_STATUS_INSERTED = '1'
SFP_STATUS_REMOVED = '0'

NUM_THERMAL = 3
NUM_FANDRAWER = 6
NUM_FANSPERDRAWER = 2
NUM_FAN = NUM_FANDRAWER * NUM_FANSPERDRAWER
NUM_PSU = 2
NUM_SFP = 34
NUM_COMPONENT = 3
CONFIG_DB_PATH = "/etc/sonic/config_db.json"

class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    # List of SfpBase-derived objects representing all sfps
    # available on the chassis
    _sfp_list = None

    # Leds
    PSULED = None
    FANLED = None

    def __init__(self):
        self._sfp_list = []

        ChassisBase.__init__(self)
        # initialize thermals
        for index in range(0, NUM_THERMAL):
            thermal = Thermal(index)
            self._thermal_list.append(thermal)

        # initialize fans, fanled
        Chassis.FANLED = FanLed()
        for index in range(0, NUM_FANDRAWER):
            fan_drawer = FanDrawer(index)
            for i in range(0, NUM_FANSPERDRAWER):
                fan_index = NUM_FANSPERDRAWER * index + i
                fan = Fan(fan_index)
                Chassis.FANLED.add_fan(fan)
                fan_drawer._fan_list.append(fan)
                self._fan_list.append(fan)
            self._fan_drawer_list.append(fan_drawer)
        Chassis.FANLED.update_status()

        # initialize psus, psuled
        Chassis.PSULED = PsuLed()
        for index in range(0, NUM_PSU):
            psu = Psu(index)
            self._psu_list.append(psu)
            Chassis.PSULED.add_psu(psu)
        Chassis.PSULED.update_status()

        # initialize sfps
        for index in range(0, NUM_SFP):
            if (index < 32):
                sfp = Sfp(index, 'QSFP')
            else:
                sfp = Sfp(index, 'SFP')
            self._sfp_list.append(sfp)

        # initialize component
        for index in range(0, NUM_COMPONENT):
            component = Component(index)
            self._component_list.append(component)

    def __read_config_db(self):
        try:
            with open(CONFIG_DB_PATH, 'r') as fd:
                data = json.load(fd)
                return data
        except IOError:
            raise IOError("Unable to open config_db file !")

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis
        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        try:
            self.config_data = self.__read_config_db()
            base_mac = self.config_data["DEVICE_METADATA"]["localhost"]["mac"]
            return str(base_mac)
        except KeyError:
            raise KeyError("Base MAC not found")

    ##############################################
    # SFP methods
    ##############################################

    def get_num_sfps(self):
        """
        Retrieves the number of sfps available on this chassis

        Returns:
            An integer, the number of sfps available on this chassis
        """
        return len(self._sfp_list)

    def get_all_sfps(self):
        """
        Retrieves all sfps available on this chassis

        Returns:
            A list of objects derived from SfpBase representing all sfps 
            available on this chassis
        """
        return self._sfp_list

    def get_sfp(self, index):
        """
        Retrieves sfp represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the sfp to retrieve.
                   The index should be the sequence of a physical port in a chassis,
                   starting from 0.
                   For example, 0 for Ethernet0, 1 for Ethernet4 and so on.

        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None

        try:
            sfp = self._sfp_list[index]
        except IndexError:
            sys.stderr.write("SFP index {} out of range (0-{})\n".format(
                             index, len(self._sfp_list)-1))

        return sfp

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
                  value is a dictionary with key:value pairs in the format of
                  {'device_id':'device_event'}, 
                  where device_id is the device ID for this device and
                        device_event,
                             status='1' represents device inserted,
                             status='0' represents device removed.
                  Ex. {'fan':{'0':'0', '2':'1'}, 'sfp':{'11':'0'}}
                      indicates that fan 0 has been removed, fan 2
                      has been inserted and sfp 11 has been removed.
        """
        port_dict = {}
        port = Sfp._port_start

        # Check for OIR events and return updated port_dict
        reg_value = Sfp.get_presence_all()
        if reg_value != Sfp.sfp_status:
            changed_ports = Sfp.sfp_status ^ reg_value
            while (port >= Sfp._port_start) and (port <= Sfp._port_end):

                # Mask off the bit corresponding to our port
                mask = (1 << port)

                if changed_ports & mask:
                    # port presence is high
                    if (reg_value & mask) == mask:
                        port_dict[port] = SFP_STATUS_INSERTED
                    else:
                        port_dict[port] = SFP_STATUS_REMOVED

                port += 1

            # Update reg value
            self.sfp_status = reg_value
        return True, port_dict

    def get_thermal_manager(self):
        from .thermal_manager import ThermalManager
        return ThermalManager

    @classmethod
    def get_psuled(cls):
        return cls.PSULED

    @classmethod
    def get_fanled(cls):
        return cls.FANLED
