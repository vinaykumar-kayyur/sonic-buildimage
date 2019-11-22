# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import struct
    import sys
    import getopt
    import time
    import select
    from sonic_sfp.sfputilbase import SfpUtilBase
    from os import *
    from mmap import *

except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

#from xcvrd
SFP_STATUS_REMOVED = '0'
SFP_STATUS_INSERTED = '1'





class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 0
    PORT_END = 33
    PORTS_IN_BLOCK = 33

    BASE_RES_PATH = "/sys/bus/pci/devices/0000:09:00.0/resource0"

    _port_to_i2c_mapping = {
            0:  10,
            1:  11,
            2:  12,
            3:  13,
            4:  14,
            5:  15,
            6:  16,
            7:  17,
            8:  18,
            9: 19,
            10: 20,
            11: 21,
            12: 22,
            13: 23,
            14: 24,
            15: 25,
            16: 26,
            17: 27,
            18: 28,
            19: 29,
            20: 30,
            21: 31,
            22: 32,
            23: 33,
            24: 34,
            25: 35,
            26: 36,
            27: 37,
            28: 38,
            29: 39,
            30: 40,
            31: 41,
            32: 1,
            33: 2,
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
        return range(self.PORT_START, self.PORTS_IN_BLOCK + 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def pci_mem_read(self, mm, offset):
        mm.seek(offset)
        read_data_stream = mm.read(4)
        reg_val = struct.unpack('I', read_data_stream)
        mem_val = str(reg_val)[1:-2]
        # print "reg_val read:%x"%reg_val
        return mem_val

    def pci_mem_write(self, mm, offset, data):
        mm.seek(offset)
        # print "data to write:%x"%data
        mm.write(struct.pack('I', data))

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

    def mod_pres(self):
        port_pres_mask =0
        for port_num in range(self.port_start, (self.port_end + 1)):
            presence = self.get_presence(port_num)
            if(presence):
                self._global_port_pres_dict[port_num] = '1'
                port_val = (1 << (port_num ))
                port_pres_mask = (port_pres_mask | port_val)
            else:
                self._global_port_pres_dict[port_num] = '0'
                port_val = ~(1 << (port_num ))
                port_pres_mask = (port_pres_mask & port_val)

        return port_pres_mask


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
        if (reg_value == ""):
            return False

        # Mask off 4th bit for presence
        mask = (1 << 4)

        # Mask off 1st bit for presence 33,34
        if (port_num > 32):
            mask =  (1 << 0)

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
        if (reg_value == ""):
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
        if (reg_value == ""):
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
        if (reg_value == ""):
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

    def get_register(self, reg_file):
            retval = 'ERR'
            if (not path.isfile(reg_file)):
                print reg_file,  'not found !'
                return retval

            try:
                with fdopen(open(reg_file, O_RDONLY)) as fd:
                    retval = fd.read()
            except Exception as error:
                logging.error("Unable to open ", reg_file, "file !")

            retval = retval.rstrip('\r\n')
            retval = retval.lstrip(" ")
            return retval

    def get_transceiver_change_event(self,timeout=0):
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


