#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/3/10 10:plugins
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao
try:
    from sonic_platform_pddf_base.pddf_psu import PddfPsu
    import re
    import os
    from . import helper
    from . import sensor_list_config
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
        Get PSU1/2 Status by sensor list information
        return: True or False
        """
        if not os.path.exists(sensor_list_config.Sensor_List_Info):
            cmd = "ipmitool sensor list > %s" % sensor_list_config.Sensor_List_Info
            cmd_status, sensor_info = self.helper.run_command(cmd)
        cmd = "cat %s | grep PSU%d_Status" % (sensor_list_config.Sensor_List_Info, self.psu_index)
        cmd_status, sensor_info = self.helper.run_command(cmd)
        if cmd_status:
            return True if sensor_info.split("|")[3].strip() == "0x0180" else False
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

