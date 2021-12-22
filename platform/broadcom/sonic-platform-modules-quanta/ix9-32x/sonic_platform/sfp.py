#############################################################################
# Quanta
#
# Sfp contains an implementation of SONiC Platform Base API and
# provides the sfp device status which are available in the platform
#
#############################################################################

try:
    from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

class Sfp(SfpOptoeBase):
    """Platform-specific Sfp class"""

    # Port number
    PORT_START = 1
    PORT_END = 32

    def __init__(self, sfp_index, sfp_type):
        # Init index
        self.index = sfp_index
        self.port_num = self.index
        self.sfp_type = sfp_type
        self.reset_path = "/sys/class/cpld-qsfpdd/port-"+str(self.port_num)+"/reset"
        self.lpmode_path = "/sys/class/cpld-qsfpdd/port-"+str(self.port_num)+"/lpmode"
        # Init eeprom path
        sfp_eeprom_path = '/sys/bus/i2c/devices/{0}-0050/eeprom'
        self.port_to_eeprom_mapping = {}
        self.port_to_i2c_mapping = {
             1 : 13,
             2 : 14,
             3 : 15,
             4 : 16,
             5 : 17,
             6 : 18,
             7 : 19,
             8 : 20,
             9 : 21,
            10 : 22,
            11 : 23,
            12 : 24,
            13 : 25,
            14 : 26,
            15 : 27,
            16 : 28,
            17 : 29,
            18 : 30,
            19 : 31,
            20 : 32,
            21 : 33,
            22 : 34,
            23 : 35,
            24 : 36,
            25 : 37,
            26 : 38,
            27 : 39,
            28 : 40,
            29 : 41,
            30 : 42,
            31 : 43,
            32 : 44,
        }

        for x in range(self.PORT_START, self.PORT_END + 1):
            port_eeprom_path = sfp_eeprom_path.format(self.port_to_i2c_mapping[x])
            self.port_to_eeprom_mapping[x] = port_eeprom_path

        SfpOptoeBase.__init__(self)

    def get_eeprom_path(self):
        return self.port_to_eeprom_mapping[self.index]

    def get_presence(self):
        """
        Retrieves the presence of the SFP module
        Returns:
            bool: True if SFP module is present, False if not
        """
        # Check for invalid port_num
        if self.port_num < self.PORT_START or self.port_num > self.PORT_END:
            return False

        try:
            reg_file = open("/sys/class/cpld-qsfpdd/port-"+str(self.port_num)+"/module_present")
        except IOError as e:
            print ("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False
