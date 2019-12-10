# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#
# For S5248F-ON, hardware version X01

try:
    import struct
    import sys
    import getopt
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase
    from os import *
    from mmap import *

except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 0 
    PORT_END = 55
    PORTS_IN_BLOCK = 56

    BASE_RES_PATH = "/sys/bus/pci/devices/0000:04:00.0/resource0"

    _port_to_i2c_mapping = {
                0:  2,
                1:  3,
                2:  4,
                3:  5,
                4:  6,
                5:  7,
                6:  8,
                7:  9,
                8:  10, 
                9: 11, 
                10: 12,
                11: 13,
                12: 14,
                13: 15,
                14: 16,
                15: 17,
                16: 18,
                17: 19,
                18: 20,
                19: 21,
                20: 22,
                21: 23,
                22: 24,
                23: 25,
                24: 26,
                25: 27,
                26: 28,
                27: 29,
                28: 30,
                29: 31,
                30: 32,
                31: 33,
                32: 34,
                33: 35,
                34: 36,
                35: 37,
                36: 38,
                37: 39,
                38: 40,
                39: 41,
                40: 42,
                41: 43,
                42: 44,
                43: 45,
                44: 46,
                45: 47,
                46: 48,
                47: 49,
                # DD + QSFP28 
                48: 50,
                49: 50,
                50: 51,
                51: 51,
                52: 52,
                53: 53,
                54: 54,
		55: 55,
                }

    _port_to_eeprom_mapping = {}


    _global_port_pres_dict = {}

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return range(48, self.PORTS_IN_BLOCK + 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def pci_mem_read(self, mm, offset):
        mm.seek(offset)
        read_data_stream=mm.read(4)
        reg_val=struct.unpack('I',read_data_stream)
        mem_val = str(reg_val)[1:-2]
        # print "reg_val read:%x"%reg_val
        return mem_val

    def pci_mem_write(self, mm, offset, data):
        mm.seek(offset)
        # print "data to write:%x"%data
        mm.write(struct.pack('I',data))

    def pci_set_value(self, resource, val, offset):
        fd = open(resource, O_RDWR)
        mm = mmap(fd, 0)
        val = self.pci_mem_write(mm, offset, val)
        mm.close()
        close(fd)
        return val

    def pci_get_value(self, resource, offset):
        fd = open(resource, O_RDWR)
        mm = mmap(fd, 0)
        val = self.pci_mem_read(mm, offset)
        mm.close()
        close(fd)
        return val
	
    def init_global_port_presence(self):
        for port_num in range(self.port_start, (self.port_end + 1)):
            presence = self.get_presence(port_num)
            if(presence):
                self._global_port_pres_dict[port_num] = '1'
            else:
                self._global_port_pres_dict[port_num] = '0'
 
    def __init__(self):
        eeprom_path = "/sys/class/i2c-adapter/i2c-{0}/{0}-0050/eeprom"

        for x in range(self.port_start, self.port_end + 1):
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                    self._port_to_i2c_mapping[x])
        self.init_global_port_presence()
        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        # Port offset starts with 0x4004
	port_offset = 16388 + ((port_num) * 16)

	status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
	reg_value = int(status)
        
        # Absence of status throws error
        if (reg_value == "" ):
            return False

        # Mask off bit for presence
        mask = (1 << 1)
        if (port_num > 47):
            mask = (1 << 4)


        # ModPrsL is active low
        if reg_value & mask == 0:
            return True

        return False

    def get_low_power_mode(self, port_num):

        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

	# Port offset starts with 0x4000
	port_offset = 16384 + ((port_num) * 16)

	status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
	reg_value = int(status)

        # Absence of status throws error
        if (reg_value == "" ):
            return False

        # Mask off 4th bit for presence
        mask = (1 << 6)

        # LPMode is active high
        if reg_value & mask == 0:
            return False

        return True

    def set_low_power_mode(self, port_num, lpmode):

        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

	# Port offset starts with 0x4000
	port_offset = 16384 + ((port_num) * 16)

	status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
	reg_value = int(status)

        # Absence of status throws error
        if (reg_value == "" ):
            return False

        # Mask off 4th bit for presence
        mask = (1 << 6)
		
	# LPMode is active high; set or clear the bit accordingly
        if lpmode is True:
            reg_value = reg_value | mask
        else:
            reg_value = reg_value & ~mask

        # Convert our register value back to a hex string and write back
	status = self.pci_set_value(self.BASE_RES_PATH, reg_value, port_offset)

        return True

    def reset(self, port_num):

	# Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

	# Port offset starts with 0x4000
	port_offset = 16384 + ((port_num) * 16)

	status = self.pci_get_value(self.BASE_RES_PATH, port_offset)
	reg_value = int(status)

        # Absence of status throws error
        if (reg_value == "" ):
            return False

        # Mask off 4th bit for presence
        mask = (1 << 6)

        # ResetL is active low
        reg_value = reg_value & ~mask

	# Convert our register value back to a hex string and write back
	status = self.pci_set_value(self.BASE_RES_PATH, reg_value, port_offset)

        # Sleep 1 second to allow it to settle
        time.sleep(1)

        reg_value = reg_value | mask

	# Convert our register value back to a hex string and write back
	status = self.pci_set_value(self.BASE_RES_PATH, reg_value, port_offset)

        return True

    def get_transceiver_change_event(self, timeout=0):
        port_dict = {}
        while True:
            for port_num in range(self.port_start, (self.port_end + 1)):
                presence = self.get_presence(port_num)
                if(presence and self._global_port_pres_dict[port_num] == '0'):
                    self._global_port_pres_dict[port_num] = '1'
                    port_dict[port_num] = '1'
                elif(not presence and
                     self._global_port_pres_dict[port_num] == '1'):
                    self._global_port_pres_dict[port_num] = '0'
                    port_dict[port_num] = '0'

                if(len(port_dict) > 0):
                    return True, port_dict

            time.sleep(0.5)
