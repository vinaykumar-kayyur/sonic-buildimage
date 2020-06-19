#!/usr/bin/env python

import os.path
import time

try:
    from sonic_sfp.sfputilbase import SfpUtilBase 
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")

#from xcvrd
SFP_STATUS_INSERTED = '1'
SFP_STATUS_REMOVED = '0'

CPLD_PORT_NUM = 8
SFP_PATH = "/sys/bus/i2c/devices/{0}-005f"
SFPPLUS_PATH = "/sys/bus/i2c/devices/{0}-005e"
SFPPLUS_EEPROM_PATH = "/sys/bus/i2c/devices/{0}-0050"

class SfpUtil(SfpUtilBase):
    """Platform specific SfpUtill class"""

    first_port = 0
    last_port = 33
    port_num = 31

    sfp_status = 0

    port_to_eeprom = {}

    port_to_i2cbus_0 = {
         1 : 13,
         2 : 14,
         3 : 15,
         4 : 16,
         5 : 12,
         6 : 11,
    }

    port_to_i2cbus_1 = {
         1 : 14,
         2 : 15,
         3 : 16,
         4 : 17,
         5 : 13,
         6 : 12,
    }

    port_to_i2cbus_mapping = {}

    sfpplus_eeprom_path = SFPPLUS_EEPROM_PATH+"/sfp_eeprom"
    eeprom_path = SFP_PATH+"/sfp{1}_eeprom"
    port_reset_path = SFP_PATH+"/sfp{1}_port_reset"
    present_path = SFP_PATH+"/sfp{1}_is_present"
    sfpplus_present_path = SFPPLUS_PATH+"/sfp_present"
    lpmode_path = SFP_PATH+"/sfp{1}_lpmode"

    _qsfp_ports = range(first_port, port_num + 1)

    @property
    def port_start(self):
        return self.first_port

    @property
    def port_end(self):
        return self.last_port

    @property
    def qsfp_ports(self):
        return range(self.first_port, self.port_num + 1)

    @property 
    def port_to_eeprom_mapping(self):
         return self.port_to_eeprom

    @property 
    def get_presence_all(self):
        bitmap = ""
        port = self.port_start

        while (port >= self.first_port) and (port <= self.last_port):
            i2c_index = (port / CPLD_PORT_NUM) + 1
            index = (port % CPLD_PORT_NUM) + 1
            if i2c_index == 5:
                path = self.sfpplus_present_path
                port_path = path.format(0)
            else:
                path = self.present_path
                port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], index)

            try:
                reg_file = open(port_path, 'r')
                reg_value = int(reg_file.readline().rstrip(), 16)
                reg_file.close()
            except IOError as e:
                print "Error: unable to open file: %s" % str(e)
                return False


            if i2c_index == 5:
                if index == 1:
                    reg_value = reg_value & 0x1
                else:
                    reg_value = reg_value & 0x2

            if reg_value:
                bitmap += '1' + " "
            else:
                bitmap += '0' + " "

            port += 1

        content = bitmap.split(" ")
        content = "".join(content[::-1])

        return int(content, 2)

    def get_transceiver_change_event(self, timeout=0):
        while True:
            port_dict = {}
            port = self.port_start

            # Check for OIR events and return updated port_dict
            reg_value = self.get_presence_all
            if reg_value != self.sfp_status:
                changed_ports = self.sfp_status ^ reg_value
                while (port >= self.port_start) and (port <= self.port_end):

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

            time.sleep(0.5)

    def __init__(self):
        path = self.present_path
        port_path = path.format(self.port_to_i2cbus_0[1], 1)
        if not os.path.exists(port_path):
            self.port_to_i2cbus_mapping = self.port_to_i2cbus_1
        else:
            self.port_to_i2cbus_mapping = self.port_to_i2cbus_0

        for x in range(self.first_port, self.last_port + 1):
            index = (x % CPLD_PORT_NUM) + 1
            cpld_index = (x / CPLD_PORT_NUM) + 1
            if cpld_index == 5:
                path = self.sfpplus_eeprom_path
                if index == 1:
                    self.port_to_eeprom[x] = path.format(self.port_to_i2cbus_mapping[cpld_index])
                else:
                    self.port_to_eeprom[x] = path.format(self.port_to_i2cbus_mapping[cpld_index+1])
            else:
                path = self.eeprom_path
                self.port_to_eeprom[x] = path.format(self.port_to_i2cbus_mapping[cpld_index], index)
        SfpUtilBase.__init__(self)

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num < self.first_port or port_num > self.last_port:
            return False

        cpld_index = (port_num / CPLD_PORT_NUM) + 1
        index = (port_num % CPLD_PORT_NUM) + 1
        if cpld_index == 5:
           # Not support reset for SFP+
           return True
        else:
            path = self.port_reset_path
        port_path = path.format(self.port_to_i2cbus_mapping[cpld_index], index)
          
        try:
            reg_file = open(port_path, 'w')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        # reset
        reg_file.write('1')

        time.sleep(1)

        reg_file.write('0')

        reg_file.close()
        return True

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num < self.first_port or port_num > self.last_port:
            return False

        index = (port_num % 8)
        i2c_index = (port_num / 8) + 1
        path = self.lpmode_path
        if i2c_index == 5:
            raise NotImplementedError
        else:
            port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))

        try:
            reg_file = open(port_path, 'w')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        if lpmode == True:
            reg_file.write('1')
        else:
            reg_file.write('0')

        reg_file.close()
        return True

    def get_low_power_mode(self, port_num):
        # Check for invalid port_num
        if port_num < self.first_port or port_num > self.last_port:
            return False

        index = (port_num % 8)
        i2c_index = (port_num / 8) + 1
        path = self.lpmode_path
        if i2c_index == 5:
            return False
        else:
            port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))

        try:
            reg_file = open(port_path)
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        reg_value = reg_file.readline().rstrip()

        reg_file.close()

        if reg_value == '1':
            return True

        return False
        
    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.first_port or port_num > self.last_port:
            return False

        cpld_index = (port_num / CPLD_PORT_NUM) + 1
        index = (port_num % CPLD_PORT_NUM) + 1
        if cpld_index == 5:
            path = self.sfpplus_present_path
            port_path = path.format(0)
        else:
            path = self.present_path
            port_path = path.format(self.port_to_i2cbus_mapping[cpld_index], index)

        try:
            reg_file = open(port_path, 'r')
            reg_value = int(reg_file.readline().rstrip(), 16)
            reg_file.close()
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        if cpld_index == 5:
            if reg_value == 3:
                # SFP+ 1 and 0 is not present, 0 is present
                reg_value = 0
            else:
                if index == 1:
                    reg_value = (reg_value < 2)
                else:
                    reg_value = ((reg_value % 2) == 0)
        return reg_value

