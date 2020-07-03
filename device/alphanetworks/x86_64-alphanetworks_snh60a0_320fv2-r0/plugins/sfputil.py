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
class SfpUtil(SfpUtilBase):
    """Platform specific SfpUtill class"""

    first_port = 0
    last_port = 31
    port_num = 32

    sfp_status = 0

    port_to_eeprom = {}
    port_to_i2cbus_0 = {
         1 : 14,
         2 : 15,
         3 : 16,
         4 : 17,
    }

    port_to_i2cbus_1 = {
         1 : 15,
         2 : 16,
         3 : 17,
         4 : 18,
    }

    port_to_i2cbus_mapping = {}

    eeprom_path = "/sys/bus/i2c/devices/{0}-005f/sfp{1}_eeprom"
    port_reset_path = "/sys/bus/i2c/devices/{0}-005f/sfp{1}_port_reset"
    present_path = "/sys/bus/i2c/devices/{0}-005f/sfp{1}_is_present"
    lpmode_path = "/sys/bus/i2c/devices/{0}-005f/sfp{1}_lpmode"

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
        port = self.port_start
        bitmap = ""

        while (port >= self.port_start) and (port <= self.port_end):
            i2c_index = (port / CPLD_PORT_NUM) + 1
            index = (port % CPLD_PORT_NUM) + 1
            path = self.present_path
            port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))

            try:
                reg_file = open(port_path)
            except IOError as e:
                print "Error: unable to open file: %s" % str(e)
                return False

            reg_value = reg_file.readline().rstrip()
            reg_file.close()

            if reg_value == '1':
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

        path = self.eeprom_path
        for x in range(self.first_port, self.last_port + 1):
            index = (x % CPLD_PORT_NUM) + 1
            i2c_index = (x / CPLD_PORT_NUM) + 1
            self.port_to_eeprom[x] = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))
        SfpUtilBase.__init__(self)

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num < self.first_port or port_num > self.last_port:
            return False

        index = (port_num % CPLD_PORT_NUM) + 1
        i2c_index = (port_num / CPLD_PORT_NUM) + 1
        path = self.port_reset_path
        port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))
          
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

        index = (port_num % CPLD_PORT_NUM)
        i2c_index = (port_num / CPLD_PORT_NUM) + 1
        path = self.lpmode_path
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

        index = (port_num % CPLD_PORT_NUM)
        i2c_index = (port_num / CPLD_PORT_NUM) + 1
        path = self.lpmode_path
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
        if port_num < self.port_start or port_num > self.port_end:
            return False

        i2c_index = (port_num / CPLD_PORT_NUM) + 1
        index = (port_num % CPLD_PORT_NUM) + 1
        path = self.present_path
        port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))

          
        try:
            reg_file = open(port_path)

        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        reg_value = int(reg_file.readline().rstrip(), 16)
        reg_file.close()

        if reg_value == '1':
            return True

        return False

