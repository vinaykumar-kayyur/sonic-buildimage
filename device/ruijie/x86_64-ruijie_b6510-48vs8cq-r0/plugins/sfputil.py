# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    import commands
    import re
    import os
    import threading
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 0
    PORT_END = 55
    PORTS_IN_BLOCK = 56

    EEPROM_OFFSET = 11
    SFP_DEVICE_TYPE = "optoe2"
    QSFP_DEVICE_TYPE = "optoe1"
    I2C_MAX_ATTEMPT = 3

    _port_to_eeprom_mapping = {}
    port_to_i2cbus_mapping ={}                        

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return range(48, self.PORTS_IN_BLOCK)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def __init__(self):
        for x in range(self.PORT_START, self.PORTS_IN_BLOCK):
            self.port_to_i2cbus_mapping[x] = (x + self.EEPROM_OFFSET)
        SfpUtilBase.__init__(self)
    
    def _sfp_read_file_path(self, file_path, offset, num_bytes):
        attempts = 0
        while attempts < self.I2C_MAX_ATTEMPT:
            try:
                sysfsfile = open(file_path, "rb", buffering=0)
                sysfsfile.seek(offset)
                read_buf = sysfsfile.read(num_bytes)
            except:
                attempts += 1
                sysfsfile.close()
                time.sleep(0.05)
            else:
                sysfsfile.close()
                return True, read_buf
        return False, None

    def _sfp_eeprom_present(self, sysfs_sfp_i2c_client_eeprompath, offset):
        if not os.path.exists(sysfs_sfp_i2c_client_eeprompath):
            return False
        else:
            rv, buf = self._sfp_read_file_path(sysfs_sfp_i2c_client_eeprompath, offset, 1)
            return rv
    
    def _add_new_sfp_device(self, sysfs_sfp_i2c_adapter_path, devaddr, devtype):
        try:
            sysfs_nd_path = "%s/new_device" % sysfs_sfp_i2c_adapter_path

            # Write device address to new_device file
            nd_file = open(sysfs_nd_path, "w")
            nd_str = "%s %s" % (devtype, hex(devaddr))
            nd_file.write(nd_str)
            nd_file.close()

        except Exception, err:
            print "Error writing to new device file: %s" % str(err)
            return 1
        else:
            return 0

    def _read_eeprom_devid(self, port_num, devid, offset):
        sysfs_i2c_adapter_base_path = "/sys/class/i2c-adapter"
        eeprom_raw = []
        num_bytes = 256

        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        if port_num in self.port_to_eeprom_mapping.keys():
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_mapping[port_num]
        else:
            sysfs_i2c_adapter_base_path = "/sys/class/i2c-adapter"

            i2c_adapter_id = self._get_port_i2c_adapter_id(port_num)
            if i2c_adapter_id is None:
                print "Error getting i2c bus num"
                return None

            # Get i2c virtual bus path for the sfp
            sysfs_sfp_i2c_adapter_path = "%s/i2c-%s" % (sysfs_i2c_adapter_base_path,
                                                        str(i2c_adapter_id))

            # If i2c bus for port does not exist
            if not os.path.exists(sysfs_sfp_i2c_adapter_path):
                print "Could not find i2c bus %s. Driver not loaded?" % sysfs_sfp_i2c_adapter_path
                return None

            sysfs_sfp_i2c_client_path = "%s/%s-00%s" % (sysfs_sfp_i2c_adapter_path,
                                                        str(i2c_adapter_id),
                                                        hex(devid)[-2:])

            # If sfp device is not present on bus, Add it
            if not os.path.exists(sysfs_sfp_i2c_client_path):
                if port_num in self.qsfp_ports:
                    ret = self._add_new_sfp_device(
                            sysfs_sfp_i2c_adapter_path, devid, self.QSFP_DEVICE_TYPE)
                else:
                    ret = self._add_new_sfp_device(
                            sysfs_sfp_i2c_adapter_path, devid, self.SFP_DEVICE_TYPE)
                if ret != 0:
                    print "Error adding sfp device"
                    return None

            sysfs_sfp_i2c_client_eeprom_path = "%s/eeprom" % sysfs_sfp_i2c_client_path

        if not self._sfp_eeprom_present(sysfs_sfp_i2c_client_eeprom_path, offset):
            return None

        rv, raw = self._sfp_read_file_path(sysfs_sfp_i2c_client_eeprom_path, offset, num_bytes)
        if rv == False:
            return None

        try:
            for n in range(0, num_bytes):
                eeprom_raw[n] = hex(ord(raw[n]))[2:].zfill(2)
        except:
            return None

        return eeprom_raw
    
    def get_eeprom_dom_raw(self, port_num):
        if port_num in self.qsfp_ports:
            # QSFP DOM EEPROM is also at addr 0x50 and thus also stored in eeprom_ifraw
            return None
        else:
            # Read dom eeprom at addr 0x51
            return self._read_eeprom_devid(port_num, self.IDENTITY_EEPROM_ADDR, 256)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        if port_num <= 7:
            presence_path = "/sys/bus/i2c/devices/1-0034/sfp_presence1"
        elif port_num >= 8 and port_num <= 15:
            presence_path = "/sys/bus/i2c/devices/1-0034/sfp_presence2"
        elif port_num >= 16 and port_num <= 23:
            presence_path = "/sys/bus/i2c/devices/1-0034/sfp_presence3"
        elif port_num >= 24 and port_num <= 31:
            presence_path = "/sys/bus/i2c/devices/1-0036/sfp_presence4"
        elif port_num >= 32 and port_num <= 39:
            presence_path = "/sys/bus/i2c/devices/1-0036/sfp_presence5"
        elif port_num >= 40 and port_num <= 47:
            presence_path = "/sys/bus/i2c/devices/1-0036/sfp_presence6"
        elif port_num >= 48 and port_num <= 55:
            presence_path = "/sys/bus/i2c/devices/1-0036/sfp_presence7"
        else:
            return False

        try:
            data = open(presence_path, "rb")
        except IOError:
            return False

        presence_data = data.read(2)
        if presence_data == "":
            return False
        result = int(presence_data, 16)
        data.close()

        # ModPrsL is active low
        if result & (1 << (port_num % 8)) == 0:
            return True

        return False

    def get_low_power_mode(self, port_num):
        # Check for invalid port_num

        return True

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num

        return True

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        return True
