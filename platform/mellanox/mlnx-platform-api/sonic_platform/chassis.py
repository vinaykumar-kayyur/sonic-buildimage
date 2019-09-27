#!/usr/bin/env python

#############################################################################
# Mellanox
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

try:
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_daemon_base.daemon_base import Logger
    from os import listdir
    from os.path import isfile, join
    import sys
    import io
    import re
    import subprocess
    import syslog
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

MAX_SELECT_DELAY = 3600

MLNX_NUM_PSU = 2

GET_HWSKU_CMD = "sonic-cfggen -d -v DEVICE_METADATA.localhost.hwsku"

EEPROM_CACHE_ROOT = '/var/cache/sonic/decode-syseeprom'
EEPROM_CACHE_FILE = 'syseeprom_cache'

HWMGMT_SYSTEM_ROOT = '/var/run/hw-management/system/'

#reboot cause related definitions
REBOOT_CAUSE_ROOT = HWMGMT_SYSTEM_ROOT

REBOOT_CAUSE_FILE_LENGTH = 1

#version retrieving related definitions
CPLD_VERSION_ROOT = HWMGMT_SYSTEM_ROOT

CPLD1_VERSION_FILE = 'cpld1_version'
CPLD2_VERSION_FILE = 'cpld2_version'
CPLD_VERSION_MAX_LENGTH = 4

FW_QUERY_VERSION_COMMAND = 'mlxfwmanager --query'
BIOS_QUERY_VERSION_COMMAND = 'dmidecode -t 11'

#components definitions
COMPONENT_BIOS = "BIOS"
COMPONENT_FIRMWARE = "ASIC-FIRMWARE"
COMPONENT_CPLD1 = "CPLD1"
COMPONENT_CPLD2 = "CPLD2"

# Global logger class instance
SYSLOG_IDENTIFIER = "mlnx-chassis-api"
logger = Logger(SYSLOG_IDENTIFIER)

# magic code defnition for port number, qsfp port position of each hwsku
# port_position_tuple = (PORT_START, QSFP_PORT_START, PORT_END, PORT_IN_BLOCK, EEPROM_OFFSET)
hwsku_dict_port = {'ACS-MSN2700': 0, "LS-SN2700":0, 'ACS-MSN2740': 0, 'ACS-MSN2100': 1, 'ACS-MSN2410': 2, 'ACS-MSN2010': 3, 'ACS-MSN3700': 0, 'ACS-MSN3700C': 0, 'Mellanox-SN2700': 0, 'Mellanox-SN2700-D48C8': 0}
port_position_tuple_list = [(0, 0, 31, 32, 1), (0, 0, 15, 16, 1), (0, 48, 55, 56, 1),(0, 18, 21, 22, 1)]

class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    def __init__(self):
        super(Chassis, self).__init__()

        # Initialize SKU name
        self.sku_name = self._get_sku_name()

        # move the initialization of each components to their dedicated initializer
        # which will be called from platform
        self.sfp_module_initialized = False
        self.sfp_event_initialized = False
        self.reboot_cause_initialized = False
        logger.log_info("Chassis loaded successfully")

    def __del__(self):
        if self.sfp_event_initialized:
            self.sfp_event.deinitialize()

    def initialize_psu(self):
        from sonic_platform.psu import Psu
        # Initialize PSU list
        self.psu_module = Psu
        for index in range(MLNX_NUM_PSU):
            psu = Psu(index, self.sku_name)
            self._psu_list.append(psu)

    def initialize_fan(self):
        from sonic_platform.fan import Fan
        from sonic_platform.fan import FAN_PATH
        self.fan_module = Fan
        self.fan_path = FAN_PATH
        # Initialize FAN list
        multi_rotor_in_drawer = False
        num_of_fan, num_of_drawer = self._extract_num_of_fans_and_fan_drawers()
        multi_rotor_in_drawer = num_of_fan > num_of_drawer

        for index in range(num_of_fan):
            if multi_rotor_in_drawer:
                fan = Fan(index, index/2)
            else:
                fan = Fan(index, index)
            self._fan_list.append(fan)

    def initialize_sfp(self):
        from sonic_platform.sfp import SFP

        self.sfp_module = SFP

        # Initialize SFP list
        port_position_tuple = self._get_port_position_tuple_by_sku_name()
        self.PORT_START = port_position_tuple[0]
        self.QSFP_PORT_START = port_position_tuple[1]
        self.PORT_END = port_position_tuple[2]
        self.PORTS_IN_BLOCK = port_position_tuple[3]

        for index in range(self.PORT_START, self.PORT_END + 1):
            if index in range(self.QSFP_PORT_START, self.PORTS_IN_BLOCK + 1):
                sfp_module = SFP(index, 'QSFP')
            else:
                sfp_module = SFP(index, 'SFP')
            self._sfp_list.append(sfp_module)

        self.sfp_module_initialized = True

    def initialize_thermals(self):
        from sonic_platform.thermal import initialize_thermals
        # Initialize thermals
        initialize_thermals(self.sku_name, self._thermal_list, self._psu_list)

    def initialize_eeprom(self):
        from eeprom import Eeprom
        # Initialize EEPROM
        self._eeprom = Eeprom()

    def initialize_components_list(self):
        # Initialize component list
        self._component_name_list.append(COMPONENT_BIOS)
        self._component_name_list.append(COMPONENT_FIRMWARE)
        self._component_name_list.append(COMPONENT_CPLD1)
        self._component_name_list.append(COMPONENT_CPLD2)

    ##############################################
    # SFP methods
    ##############################################
    def get_num_sfps(self):
        """
        Retrieves the number of sfps available on this chassis

        Returns:
            An integer, the number of sfps available on this chassis
        """
        if not self.sfp_module_initialized:
            self.initialize_sfp()
        return len(self._sfp_list)

    def get_all_sfps(self):
        """
        Retrieves all sfps available on this chassis

        Returns:
            A list of objects derived from SfpBase representing all sfps 
            available on this chassis
        """
        if not self.sfp_module_initialized:
            self.initialize_sfp()
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
        if not self.sfp_module_initialized:
            self.initialize_sfp()

        sfp = None

        try:
            sfp = self._sfp_list[index]
        except IndexError:
            sys.stderr.write("SFP index {} out of range (0-{})\n".format(
                             index, len(self._sfp_list)-1))

        return sfp

    def _extract_num_of_fans_and_fan_drawers(self):
        num_of_fan = 0
        num_of_drawer = 0
        for f in listdir(self.fan_path):
            if isfile(join(self.fan_path, f)):
                match_obj = re.match('fan(\d+)_speed_get', f)
                if match_obj != None:
                    if int(match_obj.group(1)) > num_of_fan:
                        num_of_fan = int(match_obj.group(1))
                else:
                    match_obj = re.match('fan(\d+)_status', f)
                    if match_obj != None and int(match_obj.group(1)) > num_of_drawer:
                        num_of_drawer = int(match_obj.group(1))

        return num_of_fan, num_of_drawer

    def _get_sku_name(self):
        p = subprocess.Popen(GET_HWSKU_CMD, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out.rstrip('\n')

    def _get_port_position_tuple_by_sku_name(self):
        position_tuple = port_position_tuple_list[hwsku_dict_port[self.sku_name]]
        return position_tuple

    def get_watchdog(self):
        """
        Retrieves hardware watchdog device on this chassis

        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device

        Note:
            We overload this method to ensure that watchdog is only initialized
            when it is referenced. Currently, only one daemon can open the watchdog.
            To initialize watchdog in the constructor causes multiple daemon 
            try opening watchdog when loading and constructing a chassis object
            and fail. By doing so we can eliminate that risk.
        """
        try:
            if self._watchdog is None:
                from sonic_platform.watchdog import get_watchdog
                self._watchdog = get_watchdog()
        except Exception as e:
            logger.log_info("Fail to load watchdog due to {}".format(repr(e)))

        return self._watchdog

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.get_base_mac()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis

        Returns:
            A string containing the hardware serial number for this chassis.
        """
        return self._eeprom.get_serial_number()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis

        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        return self._eeprom.get_system_eeprom_info()

    def _read_generic_file(self, filename, len):
        """
        Read a generic file, returns the contents of the file
        """
        result = ''
        try:
            fileobj = io.open(filename)
            result = fileobj.read(len)
            fileobj.close()
            return result
        except Exception as e:
            logger.log_info("Fail to read file {} due to {}".format(filename, repr(e)))
            return '0'

    def _verify_reboot_cause(self, filename):
        '''
        Open and read the reboot cause file in 
        /var/run/hwmanagement/system (which is defined as REBOOT_CAUSE_ROOT)
        If a reboot cause file doesn't exists, returns '0'.
        '''
        return bool(int(self._read_generic_file(join(REBOOT_CAUSE_ROOT, filename), REBOOT_CAUSE_FILE_LENGTH).rstrip('\n')))

    def initialize_reboot_cause(self):
        self.reboot_major_cause_dict = {
            'reset_main_pwr_fail'       :   self.REBOOT_CAUSE_POWER_LOSS,
            'reset_aux_pwr_or_ref'      :   self.REBOOT_CAUSE_POWER_LOSS,
            'reset_asic_thermal'        :   self.REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC,
            'reset_hotswap_or_wd'       :   self.REBOOT_CAUSE_WATCHDOG,
            'reset_swb_wd'              :   self.REBOOT_CAUSE_WATCHDOG,
            'reset_sff_wd'              :   self.REBOOT_CAUSE_WATCHDOG
        }
        self.reboot_minor_cause_dict = {
            'reset_fw_reset'            :   "Reset by ASIC firmware",
            'reset_long_pb'             :   "Reset by long press on power button",
            'reset_short_pb'            :   "Reset by short press on power button",
            'reset_comex_thermal'       :   "ComEx thermal shutdown",
            'reset_comex_pwr_fail'      :   "ComEx power fail",
            'reset_comex_wd'            :   "Reset requested from ComEx",
            'reset_from_asic'           :   "Reset requested from ASIC",
            'reset_reload_bios'         :   "Reset caused by BIOS reload",
            'reset_sw_reset'            :   "Software reset",
            'reset_hotswap_or_halt'     :   "Reset caused by hotswap or halt",
            'reset_from_comex'          :   "Reset from ComEx",
            'reset_voltmon_upgrade_fail':   "Reset due to voltage monitor devices upgrade failure"
        }
        self.reboot_cause_initialized = True

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
        #read reboot causes files in the following order
        if not self.reboot_cause_initialized:
            self.initialize_reboot_cause()

        for reset_file, reset_cause in self.reboot_major_cause_dict.iteritems():
            if self._verify_reboot_cause(reset_file):
                return reset_cause, ''

        for reset_file, reset_cause in self.reboot_minor_cause_dict.iteritems():
            if self._verify_reboot_cause(reset_file):
                return self.REBOOT_CAUSE_HARDWARE_OTHER, reset_cause

        return self.REBOOT_CAUSE_NON_HARDWARE, ''

    def _get_cpld_version(self, version_file):
        cpld_version = self._read_generic_file(join(CPLD_VERSION_ROOT, version_file), CPLD_VERSION_MAX_LENGTH)
        return cpld_version.rstrip('\n')

    def _get_command_result(self, cmdline):
        try:
            proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            result = stdout.rstrip('\n')

        except OSError, e:
            result = ''

        return result

    def _get_firmware_version(self):
        """
        firmware version is retrieved via command 'mlxfwmanager --query'
        which should return result in the following convention
            admin@mtbc-sonic-01-2410:~$ sudo mlxfwmanager --query
            Querying Mellanox devices firmware ...

            Device #1:
            ----------

            Device Type:      Spectrum
            Part Number:      MSN2410-CxxxO_Ax_Bx
            Description:      Spectrum based 25GbE/100GbE 1U Open Ethernet switch with ONIE; 48 SFP28 ports; 8 QSFP28 ports; x86 dual core; RoHS6
            PSID:             MT_2860111033
            PCI Device Name:  /dev/mst/mt52100_pci_cr0
            Base MAC:         98039bf3f500
            Versions:         Current        Available     
                FW         ***13.2000.1140***N/A           

            Status:           No matching image found

        By using regular expression '(Versions:.*\n[\s]+FW[\s]+)([\S]+)',
        we can extrace the version which is marked with *** in the above context
        """
        fw_ver_str = self._get_command_result(FW_QUERY_VERSION_COMMAND)
        try: 
            m = re.search('(Versions:.*\n[\s]+FW[\s]+)([\S]+)', fw_ver_str)
            result = m.group(2)
        except :
            result = ''

        return result

    def _get_bios_version(self):
        """
        BIOS version is retrieved via command 'dmidecode -t 11'
        which should return result in the following convention
            # dmidecode 3.0
            Getting SMBIOS data from sysfs.
            SMBIOS 2.7 present.

            Handle 0x0022, DMI type 11, 5 bytes
            OEM Strings
                    String 1:*0ABZS017_02.02.002*
                    String 2: To Be Filled By O.E.M.

        By using regular expression 'OEM[\s]*Strings\n[\s]*String[\s]*1:[\s]*([0-9a-zA-Z_\.]*)'
        we can extrace the version string which is marked with * in the above context
        """
        bios_ver_str = self._get_command_result(BIOS_QUERY_VERSION_COMMAND)
        try:
            m = re.search('OEM[\s]*Strings\n[\s]*String[\s]*1:[\s]*([0-9a-zA-Z_\.]*)', bios_ver_str)
            result = m.group(1)
        except:
            result = ''

        return result

    def get_firmware_version(self, component_name):
        """
        Retrieves platform-specific hardware/firmware versions for chassis
        componenets such as BIOS, CPLD, FPGA, etc.
        Args:
            component_name: A string, the component name.

        Returns:
            A string containing platform-specific component versions
        """
        if component_name in self._component_name_list :
            if component_name == COMPONENT_BIOS:
                return self._get_bios_version()
            elif component_name == COMPONENT_CPLD1:
                return self._get_cpld_version(CPLD1_VERSION_FILE)
            elif component_name == COMPONENT_CPLD2:
                return self._get_cpld_version(CPLD2_VERSION_FILE)
            elif component_name == COMPONENT_FIRMWARE:
                return self._get_firmware_version()

        return None

    def _show_capabilities(self):
        """
        This function is for debug purpose
        Some features require a xSFP module to support some capabilities but it's unrealistic to
        check those modules one by one.
        So this function is introduce to show some capabilities of all xSFP modules mounted on the device.
        """
        for s in self._sfp_list:
            try:
                print "index {} tx disable {} dom {} calibration {} temp {} volt {} power (tx {} rx {})".format(s.index,
                    s.dom_tx_disable_supported,
                    s.dom_supported,
                    s.calibration,
                    s.dom_temp_supported,
                    s.dom_volt_supported,
                    s.dom_rx_power_supported,
                    s.dom_tx_power_supported
                    )
            except:
                print "fail to retrieve capabilities for module index {}".format(s.index)

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
        # Initialize SFP event first
        if not self.sfp_event_initialized:
            from sonic_platform.sfp_event import sfp_event
            self.sfp_event = sfp_event()
            self.sfp_event.initialize()
            self.MAX_SELECT_EVENT_RETURNED = self.PORT_END
            self.sfp_event_initialized = True

        wait_for_ever = (timeout == 0)
        port_dict = {}
        if wait_for_ever:
            timeout = MAX_SELECT_DELAY
            while True:
                status = self.sfp_event.check_sfp_status(port_dict, timeout)
                if not port_dict == {}:
                    break
        else:
            status = self.sfp_event.check_sfp_status(port_dict, timeout)

        if status:
            # get_change_event has the meaning of retrieving all the notifications through a single call.
            # Typically this is implemented via a select framework which requires the underlay file-reading 
            # interface able to retrieve all notifications without blocking once the fd has been selected. 
            # However, sdk doesn't provide any interface satisfied the requirement. as a result,
            # check_sfp_status returns only one notification may indicate more notifications in its queue.
            # In this sense, we have to iterate in a loop to get all the notifications in case that
            # the first call returns at least one.
            i = 0
            while i < self.MAX_SELECT_EVENT_RETURNED:
                status = self.sfp_event.check_sfp_status(port_dict, 0)
                if not status:
                    break
                i = i + 1
            return True, {'sfp':port_dict}
        else:
            return True, {}
