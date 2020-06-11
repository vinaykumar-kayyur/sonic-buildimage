#!/usr/bin/env python

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
#
#############################################################################

try:
    import os
    import sys
    import subprocess
    import glob
    import sonic_device_util
    from sonic_platform_base.platform_base import PlatformBase
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.sfp import Sfp
    from sonic_platform.psu import Psu
    from sonic_platform.fan import Fan
    from sonic_platform.thermal import Thermal
    from sonic_platform.eeprom import Eeprom
    import json
    #sys.path.append('/usr/share/sonic/platform/sonic_platform')
    import pddfparse
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class PddfChassis(ChassisBase):
    """
    PDDF Generic Chassis class
    """
    pddf_obj = {}

    def __init__(self):

        ChassisBase.__init__(self)

        self.pddf_obj = pddfparse.PddfParse()
        self.platform_inventory = self.pddf_obj.get_platform()

        # Initialize EEPROM
        self.sys_eeprom = Eeprom()

        # FANs
        for i in range(self.platform_inventory['num_fantrays']):
            for j in range(self.platform_inventory['num_fans_pertray']):
                fan = Fan(i, j)
                self._fan_list.append(fan)
                #color=""
                #fan.get_status_led(color)
                #print "%s"%color
                #fan.set_status_led("STATUS_LED_COLOR_GREEN")
                #fan.get_status_led(color)
                #print "%s"%color

        # PSUs
        for i in range(self.platform_inventory['num_psus']):
            psu = Psu(i)
            self._psu_list.append(psu)
            # for testing, remove the below lines later on 
            #print "%s"%psu.get_name()
            #print "Status: %d"%psu.get_status()
            #print "Model: %s"%psu.get_model()
            #print "FanName: %s"%psu._fan_list[0].get_name()
            #print "FanSpeed: %d%%"%psu._fan_list[0].get_speed()
            #color=""
            #psu.get_status_led(color)
            #print "%s"%color
            #psu.set_status_led("STATUS_LED_COLOR_GREEN")
            #psu.get_status_led(color)
            #print "%s"%color

        # OPTICs
        for index in range(self.platform_inventory['num_ports']):
            sfp = Sfp(index)
            self._sfp_list.append(sfp)

        # THERMALs
        for i in range(self.platform_inventory['num_temps']):
            thermal = Thermal(i)
            self._thermal_list.append(thermal)
	    # Thermal Test Cases
            #temp=thermal.get_temperature()
            #high=thermal.get_high_threshold()
            #hyst=thermal.get_low_threshold()
            #value="TEMP%d\t %+.1f C (high = %+.1f C, hyst = %+.1f C)" % (i, temp, high, hyst)
            #print value
            #thermal.set_high_threshold(80.0)
            #thermal.set_low_threshold(75.0)
            #value="TEMP%d\t %+.1f C (high = %+.1f C, hyst = %+.1f C)" % (i, thermal.get_temperature(), thermal.get_high_threshold(), thermal.get_low_threshold())
            #print value
            #thermal.set_high_threshold(high)
            #thermal.set_low_threshold(hyst)
            #value="TEMP%d\t %+.1f C (high = %+.1f C, hyst = %+.1f C)" % (i, thermal.get_temperature(), thermal.get_high_threshold(), thermal.get_low_threshold())
            #print value


	# SYSTEM LED Test Cases 
	"""
	#comment out test cases
	sys_led_list= { "LOC":0,
			"DIAG":0, 
			"FAN":0,
			"SYS":0, 
			"PSU1":0,
			"PSU2":1
		      }  

	for led in sys_led_list:
		color=self.get_system_led(led, sys_led_list[led])
		print color

	self.set_system_led("LOC_LED","STATUS_LED_COLOR_GREEN")
	color=self.get_system_led("LOC_LED")
	print "Set Green: " + color
	self.set_system_led("LOC_LED", "STATUS_LED_COLOR_OFF")
	color=self.get_system_led("LOC_LED")
	print "Set off: " + color
	"""

    def get_name(self):
        """
        Retrieves the name of the chassis
        Returns:
            string: The name of the chassis
        """
        return self.sys_eeprom.modelstr()

    def get_presence(self):
        """
        Retrieves the presence of the chassis
        Returns:
            bool: True if chassis is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the chassis
        Returns:
            string: Model/part number of chassis
        """
        return self.sys_eeprom.part_number_str()

    def get_serial(self):
        """
        Retrieves the serial number of the chassis (Service tag)
        Returns:
            string: Serial number of chassis
        """
        return self.sys_eeprom.serial_str()

    def get_status(self):
        """
        Retrieves the operational status of the chassis
        Returns:
            bool: A boolean value, True if chassis is operating properly
            False if not
        """
        return True

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self.sys_eeprom.base_mac_addr()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis

        Returns:
            A string containing the hardware serial number for this
            chassis.
        """
        return self.sys_eeprom.serial_number_str()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis
        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        return self.sys_eeprom.system_eeprom_info()

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot

        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
        raise NotImplementedError

    def get_component_name_list(self):
        """
        Retrieves a list of the names of components available on the chassis (e.g., BIOS, CPLD, FPGA, etc.)

        Returns:
            A list containing the names of components available on the chassis
        """
        return self._component_name_list

    def get_firmware_version(self, component_name):
        """
        Retrieves platform-specific hardware/firmware versions for chassis
        componenets such as BIOS, CPLD, FPGA, etc.
        Args:
            component_name: A string, the component name.

        Returns:
            A string containing platform-specific component versions
        """
        raise NotImplementedError

    def install_component_firmware(self, component_name, image_path):
        """
        Install firmware to component
        Args:
            component_name: A string, the component name.
            image_path: A string, path to firmware image.

        Returns:
            A boolean, True if install was successful, False if not
        """
        raise NotImplementedError

    ##############################################
    # Module methods
    ##############################################

    def get_num_modules(self):
        """
        Retrieves the number of modules available on this chassis

        Returns:
            An integer, the number of modules available on this chassis
        """
        return len(self._module_list)

    def get_all_modules(self):
        """
        Retrieves all modules available on this chassis

        Returns:
            A list of objects derived from ModuleBase representing all
            modules available on this chassis
        """
        return self._module_list

    def get_module(self, index):
        """
        Retrieves module represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the module to
            retrieve

        Returns:
            An object dervied from ModuleBase representing the specified
            module
        """
        module = None

        try:
            module = self._module_list[index]
        except IndexError:
            sys.stderr.write("Module index {} out of range (0-{})\n".format(
                             index, len(self._module_list)-1))

        return module
    ##############################################
    # Fan methods
    ##############################################

    def get_num_fans(self):
        """
        Retrieves the number of fans available on this chassis

        Returns:
            An integer, the number of fan modules available on this chassis
        """
        return len(self._fan_list)

    def get_all_fans(self):
        """
        Retrieves all fan modules available on this chassis

        Returns:
            A list of objects derived from FanBase representing all fan
            modules available on this chassis
        """
        return self._fan_list

    def get_fan(self, index):
        """
        Retrieves fan module represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the fan module to
            retrieve

        Returns:
            An object dervied from FanBase representing the specified fan
            module
        """
        fan = None

        try:
            fan = self._fan_list[index]
        except IndexError:
            sys.stderr.write("Fan index {} out of range (0-{})\n".format(
                             index, len(self._fan_list)-1))

        return fan

    ##############################################
    # PSU methods
    ##############################################

    def get_num_psus(self):
        """
        Retrieves the number of power supply units available on this chassis

        Returns:
            An integer, the number of power supply units available on this
            chassis
        """
        return len(self._psu_list)

    def get_all_psus(self):
        """
        Retrieves all power supply units available on this chassis

        Returns:
            A list of objects derived from PsuBase representing all power
            supply units available on this chassis
        """
        return self._psu_list

    def get_psu(self, index):
        """
        Retrieves power supply unit represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the power supply unit to
            retrieve

        Returns:
            An object dervied from PsuBase representing the specified power
            supply unit
        """
        psu = None

        try:
            psu = self._psu_list[index]
        except IndexError:
            sys.stderr.write("PSU index {} out of range (0-{})\n".format(
                             index, len(self._psu_list)-1))

        return psu

    ##############################################
    # THERMAL methods
    ##############################################

    def get_num_thermals(self):
        """
        Retrieves the number of thermals available on this chassis

        Returns:
            An integer, the number of thermals available on this chassis
        """
        return len(self._thermal_list)

    def get_all_thermals(self):
        """
        Retrieves all thermals available on this chassis

        Returns:
            A list of objects derived from ThermalBase representing all thermals
            available on this chassis
        """
        return self._thermal_list

    def get_thermal(self, index):
        """
        Retrieves thermal unit represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the thermal to
            retrieve

        Returns:
            An object dervied from ThermalBase representing the specified thermal
        """
        thermal = None

        try:
            thermal = self._thermal_list[index]
        except IndexError:
            sys.stderr.write("THERMAL index {} out of range (0-{})\n".format(
                             index, len(self._thermal_list)-1))

        return thermal

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

    ##############################################
    # System LED  methods
    ##############################################
    color_map = {
         "STATUS_LED_COLOR_GREEN" : "on",
         "STATUS_LED_COLOR_RED" : "faulty",
         "STATUS_LED_COLOR_OFF" : "off"
    }

    def set_system_led(self, led_device_name, color):
        color_state="SOLID"
        if (not led_device_name in self.pddf_obj.data.keys()):
                print  led_device_name + " is not configured"
                return (False)


        if (not color in self.color_map.keys()):
                print "ERROR: Invalid color"
                return (False)


        if(not self.pddf_obj.is_led_device_configured(led_device_name, self.color_map[color])):
                print "ERROR :" + led_device_name + ' ' + color + " is not supported in the platform"
                return (False)

        index=self.pddf_obj.data[led_device_name]['dev_attr']['index']
        device_name=self.pddf_obj.data[led_device_name]['dev_info']['device_name']
        self.pddf_obj.create_attr('device_name', device_name,  self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('index', index, self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('color', self.color_map[color], self.pddf_obj.get_led_cur_state_path())
        self.pddf_obj.create_attr('color_state', color_state, self.pddf_obj.get_led_cur_state_path())
        self.pddf_obj.create_attr('dev_ops', 'set_status',  self.pddf_obj.get_led_path())
        return (True)


    def get_system_led(self, led_device_name):
        if (not led_device_name in self.pddf_obj.data.keys()):
                status= led_device_name + " is not configured"
                return (status)

        index=self.pddf_obj.data[led_device_name]['dev_attr']['index']
        device_name=self.pddf_obj.data[led_device_name]['dev_info']['device_name']
        self.pddf_obj.create_attr('device_name', device_name,  self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('index', index, self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('dev_ops', 'get_status',  self.pddf_obj.get_led_path())
        color=self.pddf_obj.get_led_color()
        return (color)


    ##############################################
    # Other methods
    ##############################################

    def get_watchdog(self):
        """
        Retreives hardware watchdog device on this chassis

        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device
        """
        return self._watchdog

    def get_eeprom(self):
        """
        Retreives eeprom device on this chassis

        Returns:
            An object derived from WatchdogBase representing the hardware
            eeprom device
        """
        return self.sys_eeprom

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
        raise NotImplementedError

