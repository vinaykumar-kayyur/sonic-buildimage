#!/usr/bin/env python
"""
#############################################################################
# DELLEMC Z9332F
#
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
#
#############################################################################
"""

try:
    import os
    import time
    import subprocess
    import mmap
    from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase

except ImportError as err:
    raise ImportError(str(err) + "- required module not found")

QSFP_DD_MODULE_ENC_OFFSET = 3
QSFP_DD_MODULE_ENC_WIDTH = 1

SFP_TYPE_LIST = [
    '0x3' # SFP/SFP+/SFP28 and later
]
QSFP_TYPE_LIST = [
    '0xc', # QSFP
    '0xd', # QSFP+ or later
    '0x11'  # QSFP28 or later
]
QSFP_DD_TYPE_LIST = [
    '0x18' #QSFP_DD Type
]

class Sfp(SfpOptoeBase):
    """
    DELLEMC Platform-specific Sfp class
    """
    BASE_RES_PATH = "/sys/bus/pci/devices/0000:09:00.0/resource0"
    _port_to_i2c_mapping = {
        1:  10,
        2:  11,
        3:  12,
        4:  13,
        5:  14,
        6:  15,
        7:  16,
        8:  17,
        9:  18,
        10: 19,
        11: 20,
        12: 21,
        13: 22,
        14: 23,
        15: 24,
        16: 25,
        17: 26,
        18: 27,
        19: 28,
        20: 29,
        21: 30,
        22: 31,
        23: 32,
        24: 33,
        25: 34,
        26: 35,
        27: 36,
        28: 37,
        29: 38,
        30: 39,
        31: 40,
        32: 41,
        33: 1,
        34: 2
    }

    def __init__(self, index, sfp_type, eeprom_path):
        """
        SFP Dunder init
        """
        SfpOptoeBase.__init__(self)
        self.index = index
        self.eeprom_path = eeprom_path
        #port_type is the native port type and sfp_type is the transceiver type
        #sfp_type will be detected in get_transceiver_info
        self.port_type = sfp_type
        self.sfp_type = self.port_type
        self._initialize_media(delay=False)

    def get_eeprom_path(self):
        """
        Returns SFP eeprom path
        """
        return self.eeprom_path

    @staticmethod
    def pci_mem_read(mem, offset):
        """
        Returns the desired byte in PCI memory space
        """
        mem.seek(offset)
        return mem.read_byte()

    @staticmethod
    def pci_mem_write(mem, offset, data):
        """
        Writes the desired byte in PCI memory space
        """
        mem.seek(offset)
        # print "data to write:%x"%data
        mem.write_byte(data)

    def pci_set_value(self, resource, val, offset):
        """
        Sets the value in PCI memory space
        """
        filed = os.open(resource, os.O_RDWR)
        mem = mmap.mmap(filed, 0)
        self.pci_mem_write(mem, offset, val)
        mem.close()
        os.close(filed)
        return val

    def pci_get_value(self, resource, offset):
        """
        Retrieves the value from PCI memory space
        """
        filed = os.open(resource, os.O_RDWR)
        mem = mmap.mmap(filed, 0)
        val = self.pci_mem_read(mem, offset)
        mem.close()
        os.close(filed)
        return val

    def _initialize_media(self, delay=False):
        """
        Initialize the media type and eeprom driver for SFP
        """
        if delay:
            time.sleep(1)
            self._xcvr_api = None
            self.get_xcvr_api()

        self.set_media_type()
        self.reinit_sfp_driver()

    def get_presence(self):
        """
        Retrieves the presence of the sfp
        Returns : True if sfp is present and false if it is absent
        """
        # Check for invalid port_num
        mask = {'QSFP_DD' : (1 << 4), 'SFP' : (1 << 0)}
        # Port offset starts with 0x4004
        port_offset = 16388 + ((self.index-1) * 16)

        try:
            status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
            reg_value = int(status)
            # ModPrsL is active low
            if reg_value & mask[self.port_type] == 0:
                return True
        except ValueError:
            pass

        return False

    def get_reset_status(self):
        """
        Retrives the reset status of SFP
        """
        reset_status = False
        try:
            if self.port_type == 'QSFP_DD':
                # Port offset starts with 0x4000
                port_offset = 16384 + ((self.index-1) * 16)

                status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
                reg_value = int(status)

                # Mask off 4th bit for reset status
                mask = (1 << 4)
                reset_status = not reg_value & mask
        except ValueError:
            pass

        return reset_status

    def get_lpmode(self):
        """
        Retrieves the lpmode(low power mode) of this SFP
        """
        lpmode_state = False
        try:
            if self.sfp_type == 'QSFP_DD':
                lpmode = self._read_eeprom(QSFP_DD_MODULE_ENC_OFFSET, QSFP_DD_MODULE_ENC_WIDTH)
                if lpmode is not None:
                    if int(lpmode[0])>>1 == 1:
                        return True
                return False
            else:
                # Port offset starts with 0x4000
                port_offset = 16384 + ((self.index-1) * 16)

                status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
                reg_value = int(status)

                # Mask off 6th bit for lpmode
                mask = (1 << 6)

                lpmode_state = (reg_value & mask)
        except ValueError:
            pass
        return bool(lpmode_state)

    def reset(self):
        """
        Reset the SFP and returns all user settings to their default state
        """
        try:
            if self.port_type == 'QSFP_DD':
                # Port offset starts with 0x4000
                port_offset = 16384 + ((self.index-1) * 16)

                status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
                reg_value = int(status)

                # Mask off 4th bit for reset
                mask = (1 << 4)

                # ResetL is active low
                reg_value = reg_value & ~mask

                # Convert our register value back to a hex string and write back
                self.pci_set_value(self.BASE_RES_PATH, reg_value, port_offset)

                # Sleep 1 second to allow it to settle
                time.sleep(1)

                reg_value = reg_value | mask

                # Convert our register value back to a hex string and write back
                self.pci_set_value(self.BASE_RES_PATH, reg_value, port_offset)
            else:
                return False
        except ValueError:
            return False
        return True

    def set_lpmode(self, lpmode):
        """
        Sets the lpmode(low power mode) of this SFP
        """
        try:
            if self.sfp_type == 'QSFP_DD':
                if lpmode is True:
                    write_val = 0x10
                else:
                    write_val = 0x0

                self.write_eeprom(26, 1, bytearray([write_val]))
            else:
                # Port offset starts with 0x4000
                port_offset = 16384 + ((self.index-1) * 16)

                status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
                reg_value = int(status)

                # Mask off 6th bit for lowpower mode
                mask = (1 << 6)

                # LPMode is active high; set or clear the bit accordingly
                if lpmode is True:
                    reg_value = reg_value | mask
                else:
                    reg_value = reg_value & ~mask

                # Convert our register value back to a hex string and write back
                self.pci_set_value(self.BASE_RES_PATH, reg_value, port_offset)
        except ValueError:
            return  False
        return True

    def get_intl_state(self):
        """
        Sets the intL (interrupt; active low) pin of this SFP
        """
        intl_state = True
        try:
            if self.port_type == 'QSFP_DD':
                # Port offset starts with 0x4004
                port_offset = 16388 + ((self.index-1) * 16)

                status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
                reg_value = int(status)

                # Mask off 4th bit for intL
                mask = (1 << 4)

                intl_state = (reg_value & mask)
        except ValueError:
            pass
        return intl_state

    def set_media_type(self):
        """
        Reads optic eeprom byte to determine media type inserted
        """
        eeprom_raw = []
        eeprom_raw = self._xcvr_api_factory._get_id()
        if eeprom_raw is not None:
            eeprom_raw = hex(eeprom_raw)
            if eeprom_raw in SFP_TYPE_LIST:
                self.sfp_type = 'SFP'
            elif eeprom_raw in QSFP_TYPE_LIST:
                self.sfp_type = 'QSFP'
            elif eeprom_raw in QSFP_DD_TYPE_LIST:
                self.sfp_type = 'QSFP_DD'
            else:
                #Set native port type if EEPROM type is not recognized/readable
                self.sfp_type = self.port_type
        else:
            self.sfp_type = self.port_type

        return self.sfp_type

    def reinit_sfp_driver(self):
        """
        Changes the driver based on media type detected
        """
        del_sfp_path = "/sys/class/i2c-adapter/i2c-{0}/delete_device".format(
            self._port_to_i2c_mapping[self.index])
        new_sfp_path = "/sys/class/i2c-adapter/i2c-{0}/new_device".format(
            self._port_to_i2c_mapping[self.index])
        driver_path = "/sys/class/i2c-adapter/i2c-{0}/{0}-0050/name".format(
            self._port_to_i2c_mapping[self.index])
        delete_device = "echo 0x50 >" + del_sfp_path

        if not os.path.isfile(driver_path):
            print(driver_path, "does not exist")
            return False

        try:
            with os.fdopen(os.open(driver_path, os.O_RDONLY)) as filed:
                driver_name = filed.read()
                driver_name = driver_name.rstrip('\r\n')
                driver_name = driver_name.lstrip(" ")

            #Avoid re-initialization of the QSFP/SFP optic on QSFP/SFP port.
            if self.sfp_type == 'SFP' and driver_name in ['optoe1', 'optoe3']:
                subprocess.Popen(delete_device, shell=True, stdout=subprocess.PIPE)
                time.sleep(0.2)
                new_device = "echo optoe2 0x50 >" + new_sfp_path
                subprocess.Popen(new_device, shell=True, stdout=subprocess.PIPE)
                time.sleep(2)
            elif self.sfp_type == 'QSFP' and driver_name in ['optoe2', 'optoe3']:
                subprocess.Popen(delete_device, shell=True, stdout=subprocess.PIPE)
                time.sleep(0.2)
                new_device = "echo optoe1 0x50 >" + new_sfp_path
                subprocess.Popen(new_device, shell=True, stdout=subprocess.PIPE)
                time.sleep(2)
            elif self.sfp_type == 'QSFP_DD' and driver_name in ['optoe1', 'optoe2']:
                subprocess.Popen(delete_device, shell=True, stdout=subprocess.PIPE)
                time.sleep(0.2)
                new_device = "echo optoe3 0x50 >" + new_sfp_path
                subprocess.Popen(new_device, shell=True, stdout=subprocess.PIPE)
                time.sleep(2)

        except IOError as err:
            print("Error: Unable to open file: %s" %str(err))
            return False

        return True

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        Returns:
            integer: The 1-based relative physical position in parent
            device or -1 if cannot determine the position
        """
        return self.index

    @staticmethod
    def is_replaceable():
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True
