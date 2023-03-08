try:
    from sonic_platform_pddf_base.pddf_thermal import PddfThermal
    from . import helper
    import os
    import time

except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

Sensor_List_Info = "/tmp/sensor_info.log"
Sensor_Info_Update_Period_Secs = 5


class Thermal(PddfThermal):
    """PDDF Platform-Specific Thermal class"""

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None, is_psu_thermal=False, psu_index=0):
        self.helper = helper.APIHelper()
        self.__refresh_sensor_list_info()
        PddfThermal.__init__(self, index, pddf_data, pddf_plugin_data, is_psu_thermal=is_psu_thermal,
                             psu_index=psu_index)

    def __refresh_sensor_list_info(self):
        """
        refresh the sensor list informal in sensor_info.log.
        The refresh interval is 5 seconds
        """
        if not os.path.exists(Sensor_List_Info):
            self.__write_sensor_list_info()

        with open(Sensor_List_Info, "r") as f:
            log_time = f.readline()
        if time.time() - float(log_time.strip()) > Sensor_Info_Update_Period_Secs:
            self.__write_sensor_list_info()

    def __write_sensor_list_info(self):
        """
        Write the log of the command 'ipmitool sensor list' in sensor_info.log
        """
        status, info = self.helper.run_command("ipmitool sensor list")
        if not status:
            print("Fail! Can't get sensor list info by command: ipmitool sensor list")
            return False
        with open(Sensor_List_Info, "w") as f:
            f.write("%s\n%s" % (str(time.time()), info))
        return True

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
            with open(Sensor_List_Info, "r") as f:
                info = f.readlines()
            for line in info:
                if "PSU%d_Temp1" % self.thermals_psu_index in line:
                    return float(line.split("|")[8])

