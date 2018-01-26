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

    PORT_START = 0
    PORT_END = 71
    PORTS_IN_BLOCK = 72
    QSFP_PORT_START = 48
    QSFP_PORT_END = 72

    BASE_VAL_PATH = "/sys/class/i2c-adapter/i2c-{0}/{1}-0050/"

    _port_to_is_present = {}
    _port_to_lp_mode = {}

    _port_to_eeprom_mapping = {}
    _port_to_i2c_mapping = {
           0:  18, 
           1:  19, 
           2:  20, 
           3:  21, 
           4:  22, 
           5:  23, 
           6:  24, 
           7:  25, 
           8:  26,
           9:  27,
           10: 28,
           11: 29,
           12: 30,
           13: 31,
           14: 32,
           15: 33,
           16: 34,
           17: 35,
           18: 36,
           19: 37,
           20: 38,
           21: 39,
           22: 40,
           23: 41,
           24: 42,
           25: 43,
           26: 44,
           27: 45,
           28: 46,
           29: 47,
           30: 48,
           31: 49,
           32: 50,
           33: 51,
           34: 52,
           35: 53,
           36: 54,
           37: 55,
           38: 56,
           39: 57,
           40: 58,
           41: 59,
           42: 60,
           43: 61,
           44: 62,
           45: 63,
           46: 64,
           47: 65,
           48: 66, #QSFP49
           49: 66,
           50: 66,
           51: 66,
           52: 67, #QSFP50
           53: 67,
           54: 67,
           55: 67,
           56: 68, #QSFP51
           57: 68,
           58: 68,
           59: 68,
           60: 69, #QSFP52
           61: 69,
           62: 69,
           63: 69,
           64: 70, #QSFP53
           65: 70,
           66: 70,
           67: 70,
           68: 71, #QSFP54
           69: 71,
           70: 71,
           71: 71,
           }

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_port_start(self):
        return self.QSFP_PORT_START

    @property
    def qsfp_port_end(self):
        return self.QSFP_PORT_END
    
    @property
    def qsfp_ports(self):
        return range(self.QSFP_PORT_START, self.PORTS_IN_BLOCK + 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def __init__(self):
        eeprom_path = self.BASE_VAL_PATH + "sfp_eeprom"

        for x in range(0, self.port_end+1):
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                self._port_to_i2c_mapping[x],
                self._port_to_i2c_mapping[x])

        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False
	print port_num
        present_path = self.BASE_VAL_PATH + "sfp_is_present"
        self.__port_to_is_present = present_path.format(self._port_to_i2c_mapping[port_num], self._port_to_i2c_mapping[port_num])
        try:
            val_file = open(self.__port_to_is_present)
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)          
            return False

        content = val_file.readline().rstrip()
        val_file.close()

        # content is a string, either "0" or "1"
        if content == "1":
            return True

        return False

    def get_low_power_mode(self, port_num):             
        raise NotImplementedError

    def set_low_power_mode(self, port_num, lpmode):                
        raise NotImplementedError

    def reset(self, port_num):
        if port_num < self.qsfp_port_start or port_num > self.qsfp_port_end:
            return False
         
        mod_rst_path = self.BASE_VAL_PATH + "sfp_mod_rst"
        self.__port_to_mod_rst = mod_rst_path.format(self._port_to_i2c_mapping[port_num], self._port_to_i2c_mapping[port_num])
        try:
            reg_file = open(self.__port_to_mod_rst, 'r+')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)          
            return False

        reg_value = '1'

        reg_file.write(reg_value)
        reg_file.close()
        
        return True
