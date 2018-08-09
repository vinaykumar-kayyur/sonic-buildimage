# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    BASE_PATH = "/sys/bus/i2c/devices/1-0070/port_{:03d}/"

    _port_start = 0
    _port_end = 71
    _qsfp_port_start = 48
    _qsfp_port_end = 71

    _port_to_eeprom_mapping = {}

    _port_to_i2c_mapping = {
           0:   1,
           1:   2,
           2:   3,
           3:   4,
           4:   5,
           5:   6,
           6:   7,
           7:   8,
           8:   9,
           9:  10,
           10: 11,
           11: 12,
           12: 13,
           13: 14,
           14: 15,
           15: 16,
           16: 17,
           17: 18,
           18: 19,
           19: 20,
           20: 21,
           21: 22,
           22: 23,
           23: 24,
           24: 25,
           25: 26,
           26: 27,
           27: 28,
           28: 29,
           29: 30,
           30: 31,
           31: 32,
           32: 33,
           33: 34,
           34: 35,
           35: 36,
           36: 37,
           37: 38,
           38: 39,
           39: 40,
           40: 41,
           41: 42,
           42: 43,
           43: 44,
           44: 45,
           45: 46,
           46: 47,
           47: 48,
           48: 49, #QSFP49
           49: 49,
           50: 49,
           51: 49,
           52: 50, #QSFP50
           53: 50,
           54: 50,
           55: 50,
           56: 51, #QSFP51
           57: 51,
           58: 51,
           59: 51,
           60: 52, #QSFP52
           61: 52,
           62: 52,
           63: 52,
           64: 53, #QSFP53
           65: 53,
           66: 53,
           67: 53,
           68: 54, #QSFP54
           69: 54,
           70: 54,
           71: 54,
    }

    @property
    def port_start(self):
        return self._port_start

    @property
    def port_end(self):
        return self._port_end

    @property
    def qsfp_port_start(self):
        return self._qsfp_port_start

    @property
    def qsfp_port_end(self):
        return self._qsfp_port_end

    @property
    def qsfp_ports(self):
        return range(self._qsfp_port_start, self._qsfp_port_end + 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def __init__(self):
        eeprom_path = self.BASE_PATH + "data_a0"

        for x in range(0, self.port_end + 1):
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                self._port_to_i2c_mapping[x]
            )

        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        present_path = self.BASE_PATH + "abs"

        port_to_is_present = present_path.format(
            self._port_to_i2c_mapping[port_num]
        )

        try:
            val_file = open(port_to_is_present)
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        content = val_file.readline().rstrip()
        val_file.close()

        # content is a string, either "0" or "1"
        return content == "1"

    def get_low_power_mode(self, port_num):
        raise NotImplementedError

    def set_low_power_mode(self, port_num, lpmode):
        raise NotImplementedError

    def reset(self, port_num):
        raise NotImplementedError

    def get_transceiver_change_event(self, timeout=0):
        raise NotImplementedError
