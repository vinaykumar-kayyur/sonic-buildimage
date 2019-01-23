#!/usr/bin/env python

try:
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase 
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")


class SfpUtil(SfpUtilBase):
    """Platform specific SfpUtill class"""

    _port_start = 0
    _port_end = 55
    _qsfp_port_start = 48
    _ports_in_block = 55

    _port_to_eeprom_mapping = {}
    _port_to_i2c_mapping = {
        0 : 7,
        1 : 8,
        2 : 9,
        3 : 10,
        4 : 11,
        5 : 12,
        6 : 13,
        7 : 14,
        8 : 15,
        9 : 16,
        10 : 17,
        11 : 18,
        12 : 19,
        13 : 20,
        14 : 21,
        15 : 22,
        16 : 23,
        17 : 24,
        18 : 25,
        19 : 26,
        20 : 27,
        21 : 28,
        22 : 29,
        23 : 30,
        24 : 31,
        25 : 32,
        26 : 33,
        27 : 34,
        28 : 35,
        29 : 36,
        30 : 37,
        31 : 38,
        32 : 39,
        33 : 40,
        34 : 41,
        35 : 42,
        36 : 43,
        37 : 44,
        38 : 45,
        39 : 46,
        40 : 47,
        41 : 48,
        42 : 49,
        43 : 50,
        44 : 51,
        45 : 52,
        46 : 53,
        47 : 54,
        48 : 55,
        49 : 56,
        50 : 57,
        51 : 58,
        52 : 59,
        53 : 60,
        54 : 61,
        55 : 62,         
    }

    _qsfp_ports = range(_qsfp_port_start, _ports_in_block + 1)

    def __init__(self):
        eeprom_path = '/sys/bus/i2c/devices/{0}-0050/sfp_eeprom'
        for x in range(self._port_start, self._port_end + 1):
            port_eeprom_path = eeprom_path.format(self._port_to_i2c_mapping[x])
            self._port_to_eeprom_mapping[x] = port_eeprom_path
                
            SfpUtilBase.__init__(self)

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False

        path = "/sys/bus/i2c/devices/{0}-0050/sfp_port_reset"
        port_ps = path.format(self._port_to_i2c_mapping[port_num])
          
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
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

        path = "/sys/bus/i2c/devices/{0}-0050/sfp_is_present"
        port_ps = path.format(self._port_to_i2c_mapping[port_num])

          
        try:
            reg_file = open(port_ps)
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False

    def get_transceiver_change_event(self):
        """
        TODO: This function need to be implemented
        when decide to support monitoring SFP(Xcvrd)
        on this platform.
        """
        raise NotImplementedError

    @property
    def port_start(self):
        return self._port_start

    @property
    def port_end(self):
        return self._port_end

    @property
    def qsfp_ports(self):
        return self._qsfp_ports

    @property 
    def port_to_eeprom_mapping(self):
         return self._port_to_eeprom_mapping
