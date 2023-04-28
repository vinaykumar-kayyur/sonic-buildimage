#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/4/26 15:43
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao

try:
    from sonic_platform_pddf_base.pddf_sfp import PddfSfp
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

I2C_EEPROM_PATH = '/sys/bus/i2c/devices/i2c-{0}/{0}-0050/eeprom'
BUS_PORT_DICT = {'1': '16', '2': '13', '3': '12', '4': '10', '5': '9', '6': '14', '7': '11', '8': '7', '9': '20',
                 '10': '17', '11': '22', '12': '25', '13': '19', '14': '21', '15': '24', '16': '18', '17': '3',
                 '18': '4', '19': '1', '20': '2', '21': '8', '22': '6', '23': '5', '24': '15', '25': '27', '26': '32',
                 '27': '29', '28': '31', '29': '30', '30': '23', '31': '26', '32': '28'}


class Sfp(PddfSfp):
    """
    PDDF Platform-Specific Sfp class
    """

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None):
        PddfSfp.__init__(self, index, pddf_data, pddf_plugin_data)

    # Provide the functions/variables below for which implementation is to be overwritten
    def get_eeprom_path(self):
        """
        Overwrite this function cause BUS-Port isn't Ordered
        """
        for bus, port in BUS_PORT_DICT.items():
            if port == str(self.port_index):
                eeprom_path = I2C_EEPROM_PATH.format(bus, port)
                return eeprom_path
