#!/usr/bin/env python

try:
    from sfputilbase import sfputilbase
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")


class sfputil(sfputilbase):
    """Platform specific sfputil class"""

    port_start = 0
    port_end = 32
    ports_in_block = 32

    port_to_eeprom_mapping = {}
    port_to_i2c_mapping = {
        0: 18,
        1: 18,
        2: 19,
        3: 20,
        4: 21,
        5: 22,
        6: 23,
        7: 24,
        8: 25,
        9: 26,
        10: 27,
        11: 28,
        12: 29,
        13: 31,
        14: 30,
        15: 33,
        16: 32,
        17: 34,
        18: 35,
        19: 36,
        20: 37,
        21: 38,
        22: 39,
        23: 40,
        24: 41,
        25: 42,
        26: 43,
        27: 44,
        28: 45,
        29: 46,
        30: 47,
        31: 48,
        32: 49
    }

    _qsfp_ports = range(0, ports_in_block + 1)

    def __init__(self, port_num):
        # Override port_to_eeprom_mapping for class initialization
        eeprom_path = '/sys/class/i2c-adapter/i2c-{0}/{0}-0050/eeprom'
        for x in range(0, self.port_end + 1):
            port_eeprom_path = eeprom_path.format(self.port_to_i2c_mapping[x])
            self.port_to_eeprom_mapping[x] = port_eeprom_path
        sfputilbase.__init__(self, port_num)
