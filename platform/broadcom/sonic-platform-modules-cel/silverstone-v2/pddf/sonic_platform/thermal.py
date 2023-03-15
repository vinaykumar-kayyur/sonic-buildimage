#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/3/6 09:32
# @Mail    : J_Talong@163.com yajiang@celestica.com
# @Author  : jiang tao

try:
    from sonic_platform_pddf_base.pddf_thermal import PddfThermal
    from . import helper

except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Thermal(PddfThermal):
    """PDDF Platform-Specific Thermal class"""

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None, is_psu_thermal=False, psu_index=0):
        self.helper = helper.APIHelper()
        PddfThermal.__init__(self, index, pddf_data, pddf_plugin_data, is_psu_thermal=is_psu_thermal,
                             psu_index=psu_index)

    def get_high_critical_threshold(self):
        """
        Rewrite the method of obtaining PSU high critical in pddf_thermal

        Returns:
            A float number, the high critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        if not self.is_psu_thermal:
            output = self.pddf_obj.get_attr_name_output(self.thermal_obj_name, "temp1_high_crit_threshold")
            if not output:
                return None

            if output['status'].isalpha():
                attr_value = None
            else:
                attr_value = float(output['status'])

            if output['mode'] == 'bmc':
                return attr_value
            else:
                return float(attr_value / 1000)
        else:
            with open("/tmp/sensor_info.log", "r") as f:
                info = f.readlines()
            for line in info:
                if "PSU%d_Temp1" % self.thermals_psu_index in line:
                    return float(line.split("|")[8])
