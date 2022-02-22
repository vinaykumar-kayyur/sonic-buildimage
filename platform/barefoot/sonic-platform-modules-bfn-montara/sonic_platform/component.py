#!/usr/bin/env python

########################################################################
# BAREFOOT MONTARA
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Components' (e.g., BIOS, CPLD, FPGA, BMC etc.) available in
# the platform
#
########################################################################

try:
    import subprocess
    from sonic_platform_base.component_base import ComponentBase
    from platform_thrift_client import thrift_try
    import json
    from collections import OrderedDict

except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

def get_bios_version():
    try:
        return subprocess.check_output(['dmidecode', '-s', 'bios-version']).strip().decode()
    except:
        print("Error: bios_version N/A, dmidecode not found")

def get_bmc_version():
    ver="N/A"
    def bmc_get(client):
        return client.pltfm_mgr.pltfm_mgr_chss_mgmt_bmc_get()
    try:    
        ver = thrift_try(bmc_get)
    except Exception:
        raise RuntimeError("bmc.py: Initialization failed")
    return ver

def get_platform():
    import os
    stream = os.popen('show version  | grep Platform | awk \'{print $2}\'')
    return stream.read()
    #return subprocess.check_output(['show', 'version', '|', 'grep', 'Platform', '|', 'awk', '\'{print $2}\'']).strip()


class BFPlatformComponentsParser(object):
    """
    BFPlatformComponentsParser
    """

    PLATFORM_COMPONENTS_PATH_TEMPLATE = "{}/usr/share/sonic/device/{}/{}"
    PLATFORM_COMPONENTS_FILE_PATH = None

    CHASSIS_KEY = "chassis"
    MODULE_KEY = "module"
    COMPONENT_KEY = "component"
    FIRMWARE_KEY = "firmware"
    UTILITY_KEY = "utility"
    VERSION_KEY = "version"

    UTF8_ENCODING = "utf-8"

    def __init__(self, is_modular_chassis, bf_model="Wedge100BF-32X-O-AC-F-BF"):
        self.__is_modular_chassis = is_modular_chassis
        self.__chassis_component_map = OrderedDict()
        self.__module_component_map = OrderedDict()
        self.__component_list = []
        self.__bf_model = bf_model
    """
    def __get_platform_components_path(self, root_path):
        if "{}".format(root_path).startswith(FWUPDATE_FWPACKAGE_DIR):
            self.PLATFORM_COMPONENTS_FILE_PATH = os.path.join(root_path, PLATFORM_COMPONENTS_FILE)
        else:
            self.PLATFORM_COMPONENTS_FILE_PATH = self.PLATFORM_COMPONENTS_PATH_TEMPLATE.format(
                root_path,
                device_info.get_platform(),
                PLATFORM_COMPONENTS_FILE
            )
        return self.PLATFORM_COMPONENTS_FILE_PATH
    """

    def __is_str(self, obj):
        return isinstance(obj, str)

    def __is_dict(self, obj):
        return isinstance(obj, dict)

    def __parser_fail(self, msg):
        raise RuntimeError("Failed to parse \"{}\": {}".format(PLATFORM_COMPONENTS_FILE, msg))

    def __parser_platform_fail(self, msg):
        self.__parser_fail("invalid platform schema: {}".format(msg))

    def __parser_chassis_fail(self, msg):
        self.__parser_fail("invalid chassis schema: {}".format(msg))

    def __parser_module_fail(self, msg):
        self.__parser_fail("invalid module schema: {}".format(msg))

    def __parser_component_fail(self, msg):
        self.__parser_fail("invalid component schema: {}".format(msg))

    def __parse_component_section(self, section, component, is_module_component=False):
        if not self.__is_dict(component):
            self.__parser_component_fail("dictionary is expected: key={}".format(self.COMPONENT_KEY))

        if not component:
            return

        missing_key = None

        for key1, value1 in component.items():
            if not self.__is_dict(value1):
                self.__parser_component_fail("dictionary is expected: key={}".format(key1))

            if not is_module_component:
                self.__chassis_component_map[section][key1] = OrderedDict()
            else:
                self.__module_component_map[section][key1] = OrderedDict()

            if value1:
                if len(value1) < 1 or len(value1) > 3:
                    self.__parser_component_fail("unexpected number of records: key={}".format(key1))

                if self.FIRMWARE_KEY not in value1:
                    missing_key = self.FIRMWARE_KEY
                    break

                for key2, value2 in value1.items():
                    if not self.__is_str(value2):
                        self.__parser_component_fail("string is expected: key={}".format(key2))

                if not is_module_component:
                    self.__chassis_component_map[section][key1] = value1
                else:
                    self.__module_component_map[section][key1] = value1

        if missing_key is not None:
            self.__parser_component_fail("\"{}\" key hasn't been found".format(missing_key))

    def __parse_chassis_section(self, chassis):
        self.__chassis_component_map = OrderedDict()

        if not self.__is_dict(chassis):
            self.__parser_chassis_fail("dictionary is expected: key={}".format(self.CHASSIS_KEY))

        if not chassis:
            self.__parser_chassis_fail("dictionary is empty: key={}".format(self.CHASSIS_KEY))

        if len(chassis) != 1:
            self.__parser_chassis_fail("unexpected number of records: key={}".format(self.CHASSIS_KEY))

        for key, value in chassis.items():
            if not self.__is_dict(value):
                self.__parser_chassis_fail("dictionary is expected: key={}".format(key))

            if not value:
                self.__parser_chassis_fail("dictionary is empty: key={}".format(key))

            if self.COMPONENT_KEY not in value:
                self.__parser_chassis_fail("\"{}\" key hasn't been found".format(self.COMPONENT_KEY))

            if len(value) != 1:
                self.__parser_chassis_fail("unexpected number of records: key={}".format(key))

            self.__chassis_component_map[key] = OrderedDict()
            self.__parse_component_section(key, value[self.COMPONENT_KEY])

    def __parse_module_section(self, module):
        self.__module_component_map = OrderedDict()

        if not self.__is_dict(module):
            self.__parser_module_fail("dictionary is expected: key={}".format(self.MODULE_KEY))

        if not module:
            self.__parser_module_fail("dictionary is empty: key={}".format(self.MODULE_KEY))

        for key, value in module.items():
            if not self.__is_dict(value):
                self.__parser_module_fail("dictionary is expected: key={}".format(key))

            if not value:
                self.__parser_module_fail("dictionary is empty: key={}".format(key))

            if self.COMPONENT_KEY not in value:
                self.__parser_module_fail("\"{}\" key hasn't been found".format(self.COMPONENT_KEY))

            if len(value) != 1:
                self.__parser_module_fail("unexpected number of records: key={}".format(key))

            self.__module_component_map[key] = OrderedDict()
            self.__parse_component_section(key, value[self.COMPONENT_KEY], True)

    def get_components_list(self):
        self.__component_list = []
        for key, value in self.__chassis_component_map[self.__bf_model].items():
            self.__component_list.append(key)
        
        return self.__component_list

    def get_chassis_component_map(self):
        return self.__chassis_component_map

    def get_module_component_map(self):
        return self.__module_component_map

    def parse_platform_components(self,  platform_components_path):
        with open(platform_components_path) as platform_components:
            data = json.load(platform_components)

            if not self.__is_dict(data):
                self.__parser_platform_fail("dictionary is expected: key=root")

            if not data:
                self.__parser_platform_fail("dictionary is empty: key=root")

            if self.CHASSIS_KEY not in data:
                self.__parser_platform_fail("\"{}\" key hasn't been found".format(self.CHASSIS_KEY))

            if not self.__is_modular_chassis:
                if len(data) != 1:
                    self.__parser_platform_fail("unexpected number of records: key=root")

            self.__parse_chassis_section(data[self.CHASSIS_KEY])

            if self.__is_modular_chassis:
                if self.MODULE_KEY not in data:
                    self.__parser_platform_fail("\"{}\" key hasn't been found".format(self.MODULE_KEY))

                if len(data) != 2:
                    self.__parser_platform_fail("unexpected number of records: key=root")

                self.__parse_module_section(data[self.MODULE_KEY])

    chassis_component_map = property(fget=get_chassis_component_map)
    module_component_map = property(fget=get_module_component_map)

class Components(ComponentBase):
    """BFN Montara Platform-specific Component class"""

    #bf_model = get_model()
    bpcp = BFPlatformComponentsParser(is_modular_chassis=False,  bf_model="Wedge100BF-32X-O-AC-F-BF")
    #bf_platform = get_platform()
    bf_platform = "x86_64-accton_wedge100bf_32x-r0"
    bf_platform_json =  "/usr/share/sonic/device/{}/platform_components.json".format(bf_platform.strip())

    def __init__(self, component_index=0):
        self.bpcp.parse_platform_components(self.bf_platform_json)
        try:
            self.index = component_index
            self.name = self.bpcp.get_components_list()[self.index]
            self.description = "N/A"
        except IndexError as e:
            raise IndexError(str(e) + " - Error: No components found in plaform_components.json")
        
        if(self.name=="BMC"):
            self.version = get_bmc_version()
            self.description = "Chassis BMC"
        elif(self.name=="BIOS"):
            self.version = get_bios_version()
            self.description = "Chassis BIOS"
        else:
            self.version =  "N/A"
        
        self.__bmc = None

    def get_name(self):
        """
        Retrieves the name of the component
        Returns:
        A string containing the name of the component
        """
        return self.name

    def get_description(self):
        """
        Retrieves the description of the component
        Returns:
        A string containing the description of the component
        """
        return self.description

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component
        Returns:
            A string containing the firmware version of the component
        """
        return self.version

    def install_firmware(self, image_path):
        """
        Installs firmware to the component
        Args:
        image_path: A string, path to firmware image
        Returns:
        A boolean, True if install was successful, False if not
        """
        return False

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        return 'N/A'

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        return 'N/A'

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True

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
        return -1

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return False
    
    def get_available_firmware_version(self, image_path):
            return 'N/A'

    def get_firmware_update_notification(self, image_path):
        """
        Retrieves a notification on what should be done in order to complete
        the component firmware update

        Args:
            image_path: A string, path to firmware image

        Returns:
            A string containing the component firmware update notification if required.
            By default 'None' value will be used, which indicates that no actions are required
        """
        return 'N/A'

    def install_firmware(self, image_path):
        """
        Installs firmware to the component
        Args:
        image_path: A string, path to firmware image
        Returns:
        A boolean, True if install was successful, False if not
        """
        return False

    def update_firmware(self, image_path):
        """
        Updates firmware of the component

        This API performs firmware update: it assumes firmware installation and loading in a single call.
        In case platform component requires some extra steps (apart from calling Low Level Utility)
        to load the installed firmware (e.g, reboot, power cycle, etc.) - this will be done automatically by API

        Args:
            image_path: A string, path to firmware image

        Raises:
            RuntimeError: update failed
        """
        return None

