#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/5/31 13:38
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao
try:
    from sonic_platform_pddf_base.pddf_psu import PddfPsu
    import re
    import os
    from . import helper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Psu(PddfPsu):
    """PDDF Platform-Specific PSU class"""

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None):
        PddfPsu.__init__(self, index, pddf_data, pddf_plugin_data)
        self.helper = helper.APIHelper()

    @staticmethod
    def get_capacity():
        return 550

    @staticmethod
    def get_type():
        return 'AC'

    @staticmethod
    def get_revision():
        """
        Get PSU HW Revision by read psu eeprom data.
        data address(hex) 46-49.The response is the ascii value of hex
        return: HW Revision or 'N/A'
        """

        return "N/A"
