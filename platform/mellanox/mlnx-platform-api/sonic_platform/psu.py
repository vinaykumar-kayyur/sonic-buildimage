#!/usr/bin/env python

#############################################################################
# Mellanox
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs status which are available in the platform
#
#############################################################################

import os.path

try:
    from sonic_platform_base.psu_base import PsuBase
    from sonic_daemon_base.daemon_base import Logger
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

# Global logger class instance
SYSLOG_IDENTIFIER = "mlnx-psu"
logger = Logger(SYSLOG_IDENTIFIER)

psu_list = []

PSU_CURRENT = "current"
PSU_VOLTAGE = "voltage"
PSU_POWER = "power"
# in most SKUs the file psuX_curr, psuX_volt and psuX_power contain current, voltage and power data respectively. 
# but there are exceptions which will be handled by the following dictionary
hwsku_dict_psu = {'ACS-MSN3700': 1, 'ACS-MSN3700C': 1, 'ACS-MSN3800': 1}
psu_profile_list = [
    # default filename convention
    {
        PSU_CURRENT : "power/psu{}_curr",
        PSU_VOLTAGE : "power/psu{}_volt",
        PSU_POWER : "power/psu{}_power"
    },
    # for 3700, 3700c, 3800
    {
        PSU_CURRENT : "power/psu{}_curr",
        PSU_VOLTAGE : "power/psu{}_volt_out2",
        PSU_POWER : "power/psu{}_power"
    }
]

class Psu(PsuBase):
    """Platform-specific Psu class"""
    def __init__(self, psu_index, sku):
        global psu_list
        PsuBase.__init__(self)
        # PSU is 1-based on Mellanox platform
        self.index = psu_index + 1
        psu_list.append(self.index)
        self.psu_path = "/var/run/hw-management/"
        self.psu_oper_status = "thermal/psu{}_pwr_status".format(self.index)

        if sku in hwsku_dict_psu:
            filemap = psu_profile_list[hwsku_dict_psu[sku]]
        else:
            filemap = psu_profile_list[0]

        print "sku {} filemap {}".format(sku, filemap)
        psu_voltage = filemap[PSU_VOLTAGE].format(self.index)
        if os.path.exists(os.path.join(self.psu_path, psu_voltage)):
            self.psu_voltage = psu_voltage
        else:
            self.psu_voltage = None
        psu_curr = filemap[PSU_CURRENT].format(self.index)
        if os.path.exists(os.path.join(self.psu_path, psu_curr)):
            self.psu_current = psu_curr
        else:
            self.psu_current = None
        psu_power = filemap[PSU_POWER].format(self.index)
        if os.path.exists(os.path.join(self.psu_path, psu_power)):
            self.psu_power = psu_power
        else:
            self.psu_power = None
        psu_presence = "thermal/psu{}_status".format(self.index)
        if os.path.exists(os.path.join(self.psu_path, psu_presence)):
            self.psu_presence = psu_presence
        else:
            self.psu_presence = None
        fan = Fan(psu_index, psu_index, True)
        if fan.get_presence():
            self._fan = fan

    def _read_generic_file(self, filename, len):
        """
        Read a generic file, returns the contents of the file
        """
        result = 0
        try:
            with open(filename, 'r') as fileobj:
                result = int(fileobj.read())
        except:
            logger.log_info("Fail to read file {}, maybe it doesn't exist".format(filename))
            result = 0
        return result

    def get_powergood_status(self):
        """
        Retrieves the operational status of power supply unit (PSU) defined

        Returns:
            bool: True if PSU is operating properly, False if not
        """
        status = self._read_generic_file(os.path.join(self.psu_path, self.psu_oper_status), 0)

        return status == 1

    def get_presence(self):
        """
        Retrieves the presence status of power supply unit (PSU) defined

        Returns:
            bool: True if PSU is present, False if not
        """
        if self.psu_presence is not None:
            status = self._read_generic_file(os.path.join(self.psu_path, self.psu_presence), 0)
            return status == 1
        else:
            return True

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts, 
            e.g. 12.1 
        """
        if self.psu_voltage is not None:
            voltage = self._read_generic_file(os.path.join(self.psu_path, self.psu_voltage), 0)
            return float(voltage) / 1000
        else:
            return None

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        if self.psu_current is not None:
            amperes = self._read_generic_file(os.path.join(self.psu_path, self.psu_current), 0)
            return float(amperes) / 1000
        else:
            return None

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        if self.psu_power is not None:
            power = self._read_generic_file(os.path.join(self.psu_path, self.psu_power), 0)
            return float(power) / 1000000
        else:
            return None
