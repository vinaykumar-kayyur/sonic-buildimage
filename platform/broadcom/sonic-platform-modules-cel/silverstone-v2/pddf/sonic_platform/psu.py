#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/3/10 10:11
# @Mail    : J_Talong@163.com yajiang@celestica.com
# @Author  : jiang tao
try:
    from sonic_platform_pddf_base.pddf_psu import PddfPsu
    import re
    from . import helper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

Change_Channel_Cmd = "0x3a 0x3e 6 0xe0 0 {}"


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

    def get_status(self):
        """
        Get PSU1/2 Status by bmc command
        return: True or False
        """
        status_cmd = "ipmitool sdr get PSU%d_Status" % self.psu_index
        res_status, result = self.helper.run_command(status_cmd)
        if res_status:
            return True if "[Presence detected]" in result.split(":")[6] else False
        else:
            return False

    def get_revision(self):
        """
        Get PSU HW Revision by read psu eeprom data.
        data address(hex) 46-49.The response is the ascii value of hex
        return: HW Revision or 'N/A'
        """
        channel_data = "0x01" if self.psu_index == 1 else "0x02"
        change_channel_status, result_channel = self.helper.ipmi_raw(Change_Channel_Cmd.format(channel_data))
        if not change_channel_status:
            print("Fail! Change channel to ch%d fail" % (self.psu_index - 1))
            return "N/A"
        rev = ""
        for address in range(46, 50):
            data_status, data = self.helper.ipmi_raw("0x3a 0x3e 6 0xa0 1 0x%d" % address)
            if not data_status:
                print("Fail! Get Ch%d PSU eeprom address %d fail" % (self.psu_index - 1, address))
                return "N/A"
            rev = rev + chr(int(data, 16))
        return rev.strip()

