#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/6/16 13:32
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao

try:
    from sonic_platform_pddf_base.pddf_thermal import PddfThermal
    from . import helper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FAN_STATUS_INFO_CMD = "i2cget -y -f 107 0x0d 0x26"


class Thermal(PddfThermal):
    """PDDF Platform-Specific Thermal class"""

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None, is_psu_thermal=False, psu_index=0):
        self.helper = helper.APIHelper()
        PddfThermal.__init__(self, index, pddf_data, pddf_plugin_data, is_psu_thermal=is_psu_thermal,
                             psu_index=psu_index)

    def get_high_threshold(self):
        status, fan_info = self.helper.run_command(FAN_STATUS_INFO_CMD)
        if not status:
            return None
        thermal_name = self.get_name()
        fan_dir = "B2F" if (bin(int(fan_info, 16)))[-2:-1] == "0" else "F2B"
        value = self.plugin_data["THERMAL"]["NONE_BMC"]["temp1_high_threshold"][thermal_name][fan_dir]
        return float(value) if value.isdigit() else None

