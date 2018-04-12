#!/usr/bin/env python

try:
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase 
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")


class SfpUtil(SfpUtilBase):
    """Platform specific SfpUtill class"""

    _port_start = 0
    _port_end = 65
    ports_in_block = 63

    _port_to_eeprom_mapping = {}
    port_to_i2c_mapping = {
         1 : 13,
         2 : 14,
         3 : 15,
         4 : 16,
         5 : 23,
    }

    _qsfp_ports = range(0, ports_in_block)

    def __init__(self):
        for x in range(0, self._port_end + 1):
            cpld_index = (x / 16) + 1
            index = (x % 16) + 1
            if cpld_index == 5:
                eeprom_path = '/sys/bus/i2c/devices/{0}-0020/sfp{1}_eeprom'
            else:
                eeprom_path = '/sys/bus/i2c/devices/{0}-005f/sfp{1}_eeprom'
            port_eeprom_path = eeprom_path.format(self.port_to_i2c_mapping[cpld_index], index)
            self._port_to_eeprom_mapping[x] = port_eeprom_path
        SfpUtilBase.__init__(self)

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False

        cpld_index = (port_num / 16) + 1
        index = (port_num % 16) + 1
        if cpld_index == 5:
            path = "/sys/bus/i2c/devices/{0}-0020/sfp{1}_port_reset"
        else:
            path = "/sys/bus/i2c/devices/{0}-005f/sfp{1}_port_reset"
        port_ps = path.format(self.port_to_i2c_mapping[cpld_index], index)
          
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            if cpld_index < 5:
                print "Error: unable to open file: %s" % str(e)
            return False

        #toggle reset
        reg_file.seek(0)
        reg_file.write('1')
        time.sleep(1)
        reg_file.seek(0)
        reg_file.write('0')
        reg_file.close()
        return True

    def set_low_power_mode(self, port_nuM, lpmode):
        raise NotImplementedError

    def get_low_power_mode(self, port_num):
        raise NotImplementedError
        
    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False

        cpld_index = (port_num / 16) + 1
        index = (port_num % 16) + 1
        if cpld_index == 5:
            path = "/sys/bus/i2c/devices/{0}-0020/sfp{1}_is_present"
        else:
            path = "/sys/bus/i2c/devices/{0}-005f/sfp{1}_is_present"
        port_ps = path.format(self.port_to_i2c_mapping[cpld_index], index)

          
        try:
            reg_file = open(port_ps)
        except IOError as e:
            if cpld_index < 5:
                print "Error: unable to open file: %s" % str(e)
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False

    @property
    def port_start(self):
        return self._port_start

    @property
    def port_end(self):
        return self._port_end
	
    @property
    def qsfp_ports(self):
        return range(0, self.ports_in_block + 1)

    @property 
    def port_to_eeprom_mapping(self):
         return self._port_to_eeprom_mapping



