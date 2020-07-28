#!/usr/bin/env python
########################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs' information which are available in the platform
#
########################################################################
try:
    import os
    from sonic_platform_base.psu_base import PsuBase
    from sonic_platform.eeprom import Eeprom
    from sonic_platform.fan import Fan
    from sonic_daemon_base.daemon_base import Logger
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")
smbus_present = 1
try:
   import smbus
except ImportError as e:
   smbus_present = 0
logger = Logger('psu')
class Psu(PsuBase):
    """Marvell platform-specific PSU class for et6448m """
    def __init__(self, psu_index):
        # PSU is 1-based in et6448m  platforms
        self.index = psu_index + 1
        # Instantiate PSU eeprom
        #self.eeprom = Eeprom(is_psu=True, psu_index=self.index)
        # Overriding _fan_list class variable defined in PsuBase, to
        # make it unique per Psu object
        self._fan_list = []
        # FIX-ME: PSU fans not yet supported
        #self._fan_list.append(Fan(self.index, psu_fan=True, dependency=self))
    def get_name(self):
        """
        Retrieves the name of the device
        Returns:
            string: The name of the device
        """
        return "PSU{}".format(self.index)
    def get_presence(self):
        """
        Retrieves the presence of the Power Supply Unit (PSU)
        Returns:
            bool: True if PSU is present, False if not
        """
        if smbus_present == 0:
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 0 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(0)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
        if self.index == 1:
             psustatus = psustatus&1
             if psustatus == 1 :
                 return True
        if self.index == 2:
            psustatus = psustatus&2
            if psustatus == 2 :
                return True
        return False
    def get_model(self):
        """
        Retrieves the part number of the PSU
        Returns:
            string: Part number of PSU
        """
        return self.eeprom.modelstr()
    def get_serial(self):
        """
        Retrieves the serial number of the PSU
        Returns:
            string: Serial number of PSU
        """
        return self.eeprom.serial_number_str()
    def get_status(self):
        """
        Retrieves the operational status of the PSU
        Returns:
            bool: True if PSU is operating properly, False if not
        """
        if smbus_present == 0:
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 0 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(0)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
        if self.index == 1:
            psustatus = psustatus&4
            if psustatus == 4:
                return True
        if self.index == 2:
            psustatus = psustatus&8
            if psustatus == 8 :
                return True
        return False
    def get_voltage(self):
        """
        Retrieves current PSU voltage output
        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        if smbus_present == 0:
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 0 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(0)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
        if self.index == 1:
            psustatus = psustatus&4
            if psustatus == 4:
                psu_voltage = 12.0
                return psu_voltage
        if self.index == 2:
            psustatus = psustatus&8
            if psustatus == 8 :
                psu_voltage = 12.0
                return True
        psu_voltage = 0.0
        return psu_voltage
    def get_current(self):
        """
        Retrieves present electric current supplied by PSU
        Returns:
            A float number, electric current in amperes,
            e.g. 15.4
        """
        psu_current = 0.0
        return psu_current
    def get_power(self):
        """
        Retrieves current energy supplied by PSU
        Returns:
            A float number, the power in watts,
            e.g. 302.6
        """
        psu_power = 0.0
        return psu_power
    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and
            passed all its internal self-tests, False if not.
        """
        if smbus_present == 0:
             cmdstatus, psustatus = cmd.getstatusoutput('i2cget -y 0 0x41 0xa') #need to verify the cpld register logic
             psustatus = int(psustatus, 16)
        else :
             bus = smbus.SMBus(0)
             DEVICE_ADDRESS = 0x41
             DEVICE_REG = 0xa
             psustatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
        if self.index == 1:
            psustatus = psustatus&4
            if psustatus == 4:
                return True
        if self.index == 2:
            psustatus = psustatus&8
            if psustatus == 8 :
                return True
        return False
    def get_status_led(self):
        """
        Gets the state of the PSU status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
        if self.get_powergood_status():
            return self.STATUS_LED_COLOR_GREEN
        else:
            return self.STATUS_LED_COLOR_OFF
    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED
        Args:
            color: A string representing the color with which to set the
                   PSU status LED
        Returns:
            bool: True if status LED state is set successfully, False if
                  not
        """
        # In IXR7220_D1, the firmware running in the PSU controls the LED
        # and the PSU LED state cannot be changed from CPU.
        return False
