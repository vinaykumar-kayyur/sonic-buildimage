#######################################################
#
# interface.py
# Python implementation of the Class interface
# Original author: support@ragilenetworks.com
#
#######################################################
from chassisbase import chassisbase
import collections
from baseutil import baseutil
from osutil import osutil

def Singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton

@Singleton
class interface(object):
    __chas = None
    __error_ret = None

    def __init__(self):
        self.chas = chassisbase()
        self.__error_ret = -99999
        self.__na_ret = 'N/A'

    @property
    def na_ret(self):
        return self.__na_ret

    @na_ret.setter
    def na_ret(self, val):
        self.__na_ret = val

    @property
    def error_ret(self):
        return self.__error_ret

    @error_ret.setter
    def error_ret(self, val):
        self.__error_ret = val

    @property
    def chas(self):
        return self.__chas

    @chas.setter
    def chas(self, val):
        self.__chas = val

    # temp
    def get_temp_total_number(self):
        templist = self.chas.temp_list
        return len(templist)

    def get_temp_location(self, temp_name):
        temp = self.chas.get_temp_byname(temp_name)
        return temp.get_location()

    def set_temp_location(self, temp_name, location):
        temp = self.chas.get_temp_byname(temp_name)
        return temp.set_location(location)

    def set_temp_name(self, temp_name, name):
        temp = self.chas.get_temp_byname(temp_name)
        return temp.set_name(name)

    def get_appoint_temp(self, temp_name):
        temp = self.chas.get_led_byname(temp_name)
        return temp.get_temp()

    def set_appoint_temp(self, temp_name, val):
        temp = self.chas.get_temp_byname(temp_name)
        return temp.set_temp(val)

    def get_temp_mintemp(self, temp_name):
        temp = self.chas.get_temp_byname(temp_name)
        return temp.get_mintemp()

    def set_temp_mintemp(self, temp_name, val):
        temp = self.chas.get_temp_byname(temp_name)
        return temp.set_mintemp(val)

    # led
    def get_led_total_number(self):
        ledlist = self.chas.led_list
        return len(ledlist)

    def get_led_color(self, led_name):
        led = self.chas.get_led_byname(led_name)
        return led.get_color()

    def set_led_color(self, led_name, color, blink):
        led = self.chas.get_led_byname(led_name)
        return led.set_color(color, blink)

    # psu
    def get_psu_total_number(self):
        psulist = self.chas.psu_list
        return len(psulist)

    def get_psus(self):
        psulist = self.chas.psu_list
        return psulist

    def get_psu_presence(self, psu_name):
        psu = self.chas.get_psu_byname(psu_name)
        return psu.present

    def get_psu_fru_info(self, psu_name):
        '''
                    {
                    "Name": "PSU1",
                    "SN": "serial_number_example",    # 'N/A'
                    "PN": "part_number_example",      # 'N/A'
                    "AirFlow": "B2F"                  # 'N/A'
                }
        '''
        psu = self.chas.get_psu_byname(psu_name)
        psu.get_fru_info()
        psu.get_AirFlow()

        dic = collections.OrderedDict()
        dic["Name"] = psu.name
        dic["SN"] = psu.productSerialNumber if (psu.productSerialNumber is not None) else self.na_ret
        dic["PN"] = psu.productPartModelName if (psu.productPartModelName is not None) else self.na_ret
        dic["AirFlow"] = psu.AirFlow if (psu.AirFlow is not None) else self.na_ret
        return dic

    def get_psu_input_output_status(self, psu_name):
        psu = self.chas.get_psu_byname(psu_name)
        if (psu.InputStatus == True) and (psu.OutputStatus == True):
            status = True
        else:
            status = False
        return status

    def get_psu_status(self, psu_name):
        """
        Get status of a specific PSU
        @return dict of the specific PSU's status, None for failure
                Example return value(all keys are mandatory)
                {
                    "Name": "PSU1",
                    "InputType": "DC",    # "AC" or 'N/A'
                    "InputStatus": True,  # H/W status bit
                    "OutputStatus": True  # H/W status bit
                    "FanSpeed": {
                        "Value": 4000,    # -99999
                        "Min": 2000,      # -99999
                        "Max": 10000      # -99999
                    },
                    "Temperature": {
                        "Value": 40.0,    # -99999.0
                        "Min": -30.0,     # -99999.0
                        "Max": 50.0       # -99999.0
                    }
                }
        """
        psu = self.chas.get_psu_byname(psu_name)

        dic = collections.OrderedDict()
        # psu.get_Temperature()
        temp_dict = collections.OrderedDict()
        temp_dict['Min'] = psu.Temperature.Min
        temp_dict['Max'] = psu.Temperature.Max
        temp_dict['Value'] = psu.Temperature.Value
        dic["Temperature"] = temp_dict

        # psu.get_FanSpeed()
        fan_speed_dict = collections.OrderedDict()
        fan_speed_dict['Min'] = psu.FanSpeed.Min
        fan_speed_dict['Max'] = psu.FanSpeed.Max
        fan_speed_dict['Value'] = psu.FanSpeed.Value
        dic["FanSpeed"] = fan_speed_dict

        dic["Name"] = psu.name
        dic["InputType"] = psu.InputsType
        dic["InputStatus"] = psu.InputStatus
        dic["OutputStatus"] = psu.OutputStatus
        return dic

    def get_psu_power_status(self, psu_name):
        """
        Get power status of a specific PSU
        @return dict of the specific PSU's power status, None for failure
                Example return value
                {
                    "Name": "PSU1",
                    "Inputs": {
                        "Status": True, # H/W status bit
                        "Type": "DC",   # or "AC" or "N/A"
                        "Voltage": {
                            "Value": 220,       # -1
                            "LowAlarm": 200,    # -1
                            "HighAlarm": 240,   # -1
                            "Unit": "V"
                        },
                        "Current": {
                            "Value": 6.0,       # -99999.0
                            "LowAlarm": 0.2,    # -99999.0
                            "HighAlarm": 7.0,   # -99999.0
                            "Unit": "A"
                        },
                        "Power": {
                            "Value": 1000,      # -99999
                            "LowAlarm": -1,     # -99999
                            "HighAlarm": 1400,  # -99999
                            "Unit": "W"
                       }
                    },
                    "Outputs": {
                        "Status": True,
                        "Voltage": {
                            "Value": 220,
                            "LowAlarm": 200,
                            "HighAlarm": 240,
                            "Unit": "V"
                        },
                        "Current": {
                            "Value": 6.0,
                            "LowAlarm": 0.2,
                            "HighAlarm": 7.0,
                            "Unit": "A"
                        },
                        "Power": {
                            "Value": 1000,
                            "LowAlarm": -1,  # Don't care
                            "HighAlarm": 1400,
                            "Unit": "W"
                        }
                    }
                }
        """
        psu = self.chas.get_psu_byname(psu_name)

        dic = collections.OrderedDict()
        inputdic =collections.OrderedDict()
        Outputsdic = collections.OrderedDict()
        dic["Name"] = psu.name
        inputdic["Status"] = psu.InputStatus
        inputdic["Type"] = psu.InputsType

        # psu.get_InputsVoltage()
        inputdic_voltage = collections.OrderedDict()

        inputdic_voltage["Value"] = psu.InputsVoltage.Value
        inputdic_voltage["LowAlarm"] = psu.InputsVoltage.Min
        inputdic_voltage["HighAlarm"] = psu.InputsVoltage.Max
        inputdic_voltage["Unit"] = psu.InputsVoltage.Unit


        inputdic["Voltage"] = inputdic_voltage
        inputdic_current = collections.OrderedDict()
        inputdic_current["Value"] = psu.InputsCurrent.Value
        inputdic_current["LowAlarm"] = psu.InputsCurrent.Min
        inputdic_current["HighAlarm"] = psu.InputsCurrent.Max
        inputdic_current["Unit"] = psu.InputsCurrent.Unit
        inputdic["Current"] = inputdic_current

        inputdic_power = collections.OrderedDict()
        inputdic_power["Value"] = psu.InputsPower.Value
        inputdic_power["LowAlarm"] = psu.InputsPower.Min
        inputdic_power["HighAlarm"] = psu.InputsPower.Max
        inputdic_power["Unit"] = psu.InputsPower.Unit
        inputdic["Power"] = inputdic_power
        Outputsdic["Status"] = psu.InputStatus

        outputdic_voltage =collections.OrderedDict()
        outputdic_current = collections.OrderedDict()
        outputdic_power = collections.OrderedDict()

        outputdic_voltage["Value"] = psu.OutputsVoltage.Value
        outputdic_voltage["LowAlarm"] = psu.OutputsVoltage.Min
        outputdic_voltage["HighAlarm"] = psu.OutputsVoltage.Max
        outputdic_voltage["Unit"] = psu.OutputsVoltage.Unit

        outputdic_current["Value"] = psu.OutputsCurrent.Value
        outputdic_current["LowAlarm"] = psu.OutputsCurrent.Min
        outputdic_current["HighAlarm"] = psu.OutputsCurrent.Max
        outputdic_current["Unit"] = psu.OutputsCurrent.Unit

        outputdic_power["Value"] = psu.OutputsPower.Value
        outputdic_power["LowAlarm"] = psu.OutputsPower.Min
        outputdic_power["HighAlarm"] = psu.OutputsPower.Max
        outputdic_power["Unit"] = psu.OutputsPower.Unit



        Outputsdic["Voltage"]  = outputdic_voltage
        Outputsdic["Current"]  = outputdic_current
        Outputsdic["Power"]  = outputdic_power


        dic["Inputs"] = inputdic
        dic["Outputs"] = Outputsdic

        return dic

    def set_psu_fan_speed_pwm(self, psu_name, pwm):
        psu = self.chas.get_psu_byname(psu_name)
        return psu.set_fan_speed_pwm(pwm)

    def get_psu_fan_speed_pwm(self, psu_name):
        psu = self.chas.get_psu_byname(psu_name)
        return psu.get_fan_speed_pwm()

    def get_psu_info_all(self):
        """
                        {
                    "Number": 2,
                    "PSU1": {
                        "SN": "serial_number_example",  # 'N/A'
                        "PN": "part_number_example",    # 'N/A'
                        "AirFlow": "F2B",               # 'N/A'

                        "FanSpeed": {
                            "Value": 4000,
                            "Min": 2000,
                            "Max": 30000
                        },
                        "Temperature": {
                            "Value": 35.0,
                            "Min": -20.0,
                            "Max": 45.0
                        },
                        "Inputs": {
                            "Status": True, # H/W status bit
                            "Type": "DC",   # or "AC"
                            "Voltage": {
                                "Value": 220,
                                "LowAlarm": 200,
                                "HighAlarm": 240,
                                "Unit": "V"
                            },
                            "Current": {
                                "Value": 6.0,
                                "LowAlarm": 0.2,
                                "HighAlarm": 7.0,
                                "Unit": "A"
                            },
                            "Power": {
                                "Value": 1000,
                                "LowAlarm": -1,
                                "HighAlarm": 1400,
                                "Unit": "W"
                           }
                        },
                        "Outputs": {
                            "Status": True,
                            "Voltage": {
                                "Value": 220,
                                "LowAlarm": 200,
                                "HighAlarm": 240,
                                "Unit": "V"
                            },
                            "Current": {
                                "Value": 6.0,
                                "LowAlarm": 0.2,
                                "HighAlarm": 7.0,
                                "Unit": "A"
                            },
                            "Power": {
                                "Value": 1000,
                                "LowAlarm": -1,  # Don't care
                                "HighAlarm": 1400,
                                "Unit": "W"
                            }
                        }
                    }
                }
        """

        psus = self.get_psus()
        dict = collections.OrderedDict()
        dict['Number'] = len(psus)
        for psu in psus:
            dicttmp = self.get_psu_fru_info(psu.name)
            dicttmp.update(self.get_psu_status(psu.name))
            dicttmp.update(self.get_psu_power_status(psu.name))
            if self.get_psu_presence(psu.name) is True:
                dicttmp['Present'] = 'yes'
            else:
                dicttmp['Present'] = 'no'
            dict[psu.name] = dicttmp
        return dict

    def get_fans(self):
        fanlist = self.chas.fan_list
        return fanlist

    # fan
    def get_fan_total_number(self):
        fanlist = self.chas.fan_list
        if fanlist is None:
            return -1
        return len(fanlist)

    def get_fan_rotor_number(self, fan_name):
        fan = self.chas.get_fan_byname(fan_name)
        ret = fan.rotors
        if ret is None:
            return -1
        return ret

    def get_fan_speed(self, fan_name, rotor_index):
        fan = self.chas.get_fan_byname(fan_name)
        ret = fan.get_speed(rotor_index)
        if ret is None:
            return -1
        return ret

    def set_fan_speed(self, fan_name, rotor_index, speed):
        return -1

    def fan_speed_set_level(self, fan_name, rotor_index, level):
        fan = self.chas.get_fan_byname(fan_name)
        ret = fan.set_speed(rotor_index, level)
        if ret is True:
            return 0
        else:
            return -1

    def get_fan_speed_pwm(self, fan_name, rotor_index):
        fan = self.chas.get_fan_byname(fan_name)
        val = fan.get_speed_pwm(rotor_index)
        if val is None:
            return -1
        return val

    def set_fan_speed_pwm(self, fan_name, rotor_index, pwm):
        fan = self.chas.get_fan_byname(fan_name)
        if isinstance(pwm, str):
            rate = float(pwm.strip('%s'))
            speed = round(rate * 255 / 100)
        elif isinstance(pwm, int):
            speed = round(pwm * 255 / 100)
        elif isinstance(pwm, float):
            speed = round(pwm * 255 / 100)
        else:
            return -1
        ret = self.fan_speed_set_level(fan.name, rotor_index, speed)
        if ret == 0:
            return 0
        return -1

    def get_fan_watchdog_status(self):
        fan = self.chas.fan_list[0]
        dic = fan.get_watchdog_status()
        if dic is None or dic["support"] == False:
            return "N/A"
        elif dic["open"] is False or dic["work_allow_set"] is True:
            return "Normal"
        elif dic["work_full"] is True:
            return "Abnormal"
        else:
            return "Abnormal"


    def enable_fan_watchdog(self, enable=True, timeout_sec=10):
        fan = self.chas.fan_list[0]
        ret = fan.enable_watchdog(enable, timeout_sec)
        if ret is True:
            return 0
        else:
            return -1

    def feed_fan_watchdog(self, pwm):
        fan_list = self.chas.fan_list
        if fan_list is None:
            return -1
        for fan in fan_list:
            ret = fan.feed_watchdog(pwm)
            if ret is False:
                return -1
        return 0

    def set_fan_led(self, fan_name, color, blink = False):
        fan = self.chas.get_fan_byname(fan_name)
        ret = fan.set_led(color, blink)
        if ret is True:
            return 0
        else:
            return -1

    def get_fan_presence(self, fan_name):
        fan = self.chas.get_fan_byname(fan_name)
        return fan.get_presence()

    def get_fan_fru_info(self, fan_name):
        """
        Get specific fan's information
                    # Properties
                    "Name": "FAN1",
                    "SN": "serial_number_example",  # 'N/A'
                    "PN": "part_number_exampple",   # 'N/A'
                    "Rotors": 2,                    # -1
                    "AirFlow": "F2B",               # 'N/A'
                    "SpeedMin": 2000,               # -1
                    "SpeedMax": 30000               # -1
        """
        fan = self.chas.get_fan_byname(fan_name)
        fan.get_fru_info()
        fan.get_AirFlow()
        dic = collections.OrderedDict()
        dic["Name"] = fan.name
        dic["SN"] = fan.productSerialNumber
        if dic["SN"] is None:
            dic["SN"] = "N/A"
        dic["PN"] = fan.productPartModelName
        if dic["PN"] is None:
            dic["PN"] = "N/A"
        dic["Rotors"] = fan.rotors
        dic["AirFlow"] = fan.AirFlow
        if dic["AirFlow"] is None:
            dic["AirFlow"] = "N/A"
        dic["SpeedMin"] = fan.SpeedMin
        dic["SpeedMax"] = fan.SpeedMax
        return dic

    def get_product_fullname(self):
        return baseutil.get_product_fullname()

    def get_fan_status(self, fan_name):
        fan = self.chas.get_fan_byname(fan_name)
        if fan is None:
            return -1
        rotorlist = fan.rotor_list
        dir = collections.OrderedDict()
        for rotor in rotorlist:
            dir_val = collections.OrderedDict()
            if rotor.rotor_Running == True:
                dir_val['Running'] = 'yes'
            else:
                dir_val['Running'] = 'no'
            if rotor.rotor_HwAlarm == True:
                dir_val['HwAlarm'] = 'yes'
            else:
                dir_val['HwAlarm'] = 'no'
            dir_val['Speed'] = int(rotor.rotor_Speed.Value)
            dir[rotor.name] = dir_val
        return dir

    def get_fan_rotor_status(self, fan_name, rotor_name):
        fan = self.chas.get_fan_byname(fan_name)
        if fan is None:
            return -1
        rotorlist = fan.rotor_list
        for i in range(len(rotorlist)):
            if rotor_name == rotorlist[i].name:
                rotor = rotorlist[i]
                if rotor.rotor_Running == True:
                    return True
                else:
                    return False
        return -1

    def get_fan_info_fru(self, fan_name):
        fan = self.chas.get_fan_byname(fan_name)
        fan.get_fru_info()
        fan.get_AirFlow()
        dic = collections.OrderedDict()
        dic["Name"] = fan.name
        dic["SN"] = fan.productSerialNumber
        if dic["SN"] is None:
            dic["SN"] = "N/A"
        dic["PN"] = fan.productPartModelName
        if dic["PN"] is None:
            dic["PN"] = "N/A"
        flag = self.get_fan_presence(fan_name)
        if flag is True:
            dic["Present"] = "yes"
        elif flag is False:
            dic["Present"] = "no"
        else:
            dic["Present"] = "N/A"
        dic["Rotors"] = fan.rotors
        dic["AirFlow"] = fan.AirFlow
        if dic["AirFlow"] is None:
            dic["AirFlow"] = "N/A"
        return dic

    def get_fan_info_rotor(self, fan_name):
        fan = self.chas.get_fan_byname(fan_name)
        if fan is None:
            return -1
        rotorlist = fan.rotor_list
        dir = collections.OrderedDict()
        for rotor in rotorlist:
            dir_val = collections.OrderedDict()
            if rotor.rotor_Running == True:
                dir_val['Running'] = 'yes'
            else:
                dir_val['Running'] = 'no'
            if rotor.rotor_HwAlarm == True:
                dir_val['HwAlarm'] = 'yes'
            else:
                dir_val['HwAlarm'] = 'no'
            speed_value = rotor.rotor_Speed.Value
            if speed_value is None:
                dir_val['Speed'] = self.error_ret
            else:
                dir_val['Speed'] = int(speed_value)
            if rotor.SpeedMin is None:
                dir_val['SpeedMin'] = self.error_ret
            else:
                dir_val['SpeedMin'] = rotor.SpeedMin
            if rotor.SpeedMax is None:
                dir_val['SpeedMax'] = self.error_ret
            else:
                dir_val['SpeedMax'] = rotor.SpeedMax

            dir[rotor.name] = dir_val
        return dir

    def get_fan_info_all(self):
        fanlist = self.chas.fan_list
        dic = collections.OrderedDict()
        dic['Number'] = len(fanlist)
        dic['WatchdogStatus'] = self.get_fan_watchdog_status()
        for fan in fanlist:
            dic[fan.name] = self.get_fan_info_fru(fan.name)
            dic[fan.name].update(self.get_fan_info_rotor(fan.name))
        return dic

    def temp_test(self):
        templist = self.chas.temp_list
        dicret = collections.OrderedDict()

        for temp in templist:
            dic = collections.OrderedDict()
            dic["Value"] = temp.Value if (temp.Value is not None) else self.error_ret
            dic["LowAlarm"] = temp.Min
            dic["HighAlarm"] = temp.Max
            dicret[temp.name] = dic
        return dicret

    # sensors
    def get_dcdc_all_info(self):
        val_list = collections.OrderedDict()
        dcdclist = self.chas.dcdc_list
        for dcdc in dcdclist:
            for name,sensor in dcdc.dcdc_ordict.items():
                dicttmp = collections.OrderedDict()
                sensorname = "%s%s" % (dcdc.name, name)
                dicttmp['Min'] = sensor.Min
                dicttmp['Max'] = sensor.Max
                dicttmp['Value'] = sensor.Value if (sensor.Value is not None) else self.error_ret
                dicttmp['Unit'] = sensor.Unit
                val_list[sensorname] = dicttmp
        return val_list
    def get_monitor_temp(self, name):
        templist = self.chas.temp_list
        temptmp = None
        for temp in templist:
            if temp.name == name:
                temptmp = temp

        dic = collections.OrderedDict()
        if temptmp is None:
            dic["Min"] = self.error_ret
            dic["Max"] = self.error_ret
            dic["Value"] = self.error_ret
            dic["Unit"] = self.error_ret
        else:
            dic["Min"] = temptmp.Min
            dic["Max"] = temptmp.Max
            dic["Value"] = temptmp.Value if (temptmp.Value is not None) else self.error_ret
            dic["Unit"] = temptmp.Unit
        return dic

    def get_temp_info(self):
        val_list = collections.OrderedDict()
        # temp
        templist = self.chas.temp_list
        for temp in templist:
            dic = collections.OrderedDict()
            dic["Min"] = temp.Min
            dic["Max"] = temp.Max
            dic["Value"] = temp.Value if (temp.Value is not None) else self.error_ret
            dic["Unit"] = temp.Unit
            val_list[temp.name] = dic
        return val_list

    def get_sensor_info(self):
        val_list = collections.OrderedDict()
        # temp
        templist = self.chas.temp_list
        for temp in templist:
            dic = collections.OrderedDict()
            dic["Min"] = temp.Min
            dic["Max"] = temp.Max
            dic["Value"] = temp.Value if (temp.Value is not None) else self.error_ret
            dic["Unit"] = temp.Unit
            val_list[temp.name] = dic
        # fan
        fanlist = self.chas.fan_list
        for fan in fanlist:
            for rotor in fan.rotor_list:
                sensorname = "%s%s"%(fan.name, rotor.name)
                speed = collections.OrderedDict()
                speed['Min'] = rotor.rotor_Speed.Min
                speed['Max'] = rotor.rotor_Speed.Max
                speed['Value'] = rotor.rotor_Speed.Value if (rotor.rotor_Speed.Value is not None) else self.error_ret
                speed['Unit'] = rotor.rotor_Speed.Unit
                val_list[sensorname] = speed

        # dcdc
        dcdclist = self.chas.dcdc_list
        for dcdc in dcdclist:
            for name,sensor in dcdc.dcdc_ordict.items():
                dicttmp = collections.OrderedDict()
                sensorname = "%s%s" % (dcdc.name, name)
                dicttmp['Min'] = sensor.Min
                dicttmp['Max'] = sensor.Max
                dicttmp['Value'] = sensor.Value if (sensor.Value is not None) else self.error_ret
                dicttmp['Unit'] = sensor.Unit
                val_list[sensorname] = dicttmp

        # psu
        psulist = self.chas.psu_list
        for psu in psulist:
            inputdic_voltage = collections.OrderedDict()
            inputdic_current = collections.OrderedDict()
            inputdic_power = collections.OrderedDict()
            outputdic_voltage =collections.OrderedDict()
            outputdic_current = collections.OrderedDict()
            outputdic_power = collections.OrderedDict()
            temperature = collections.OrderedDict()
            fanspeed = collections.OrderedDict()

            temperature["Value"] = psu.Temperature.Value if (psu.Temperature.Value is not None) else self.error_ret
            temperature["Min"] = psu.Temperature.Min
            temperature["Max"] = psu.Temperature.Max
            temperature["Unit"] = psu.Temperature.Unit

            fanspeed["Value"] = psu.FanSpeed.Value
            fanspeed["Min"] = psu.FanSpeed.Min
            fanspeed["Max"] = psu.FanSpeed.Max
            fanspeed["Unit"] = psu.FanSpeed.Unit

            inputdic_voltage["Value"] = psu.InputsVoltage.Value if (psu.InputsVoltage.Value is not None) else self.error_ret
            inputdic_voltage["Min"] = psu.InputsVoltage.Min
            inputdic_voltage["Max"] = psu.InputsVoltage.Max
            inputdic_voltage["Unit"] = psu.InputsVoltage.Unit

            inputdic_current["Value"] = psu.InputsCurrent.Value if (psu.InputsCurrent.Value is not None) else self.error_ret
            inputdic_current["Min"] = psu.InputsCurrent.Min
            inputdic_current["Max"] = psu.InputsCurrent.Max
            inputdic_current["Unit"] = psu.InputsCurrent.Unit

            inputdic_power["Value"] = psu.InputsPower.Value if (psu.InputsPower.Value is not None) else self.error_ret
            inputdic_power["Min"] = psu.InputsPower.Min
            inputdic_power["Max"] = psu.InputsPower.Max
            inputdic_power["Unit"] = psu.InputsPower.Unit

            outputdic_voltage["Value"] = psu.OutputsVoltage.Value if (psu.OutputsVoltage.Value is not None) else self.error_ret
            outputdic_voltage["Min"] = psu.OutputsVoltage.Min
            outputdic_voltage["Max"] = psu.OutputsVoltage.Max
            outputdic_voltage["Unit"] = psu.OutputsVoltage.Unit

            outputdic_current["Value"] = psu.OutputsCurrent.Value if (psu.OutputsCurrent.Value is not None) else self.error_ret
            outputdic_current["Min"] = psu.OutputsCurrent.Min
            outputdic_current["Max"] = psu.OutputsCurrent.Max
            outputdic_current["Unit"] = psu.OutputsCurrent.Unit

            outputdic_power["Value"] = psu.OutputsPower.Value if (psu.OutputsPower.Value is not None) else self.error_ret
            outputdic_power["Min"] = psu.OutputsPower.Min
            outputdic_power["Max"] = psu.OutputsPower.Max
            outputdic_power["Unit"] = psu.OutputsPower.Unit

            val_list["%s%s"%(psu.name,"Vol_I" )] = inputdic_voltage
            val_list["%s%s"%(psu.name,"Curr_I" )] = inputdic_current
            val_list["%s%s"%(psu.name,"Power_I" )] = inputdic_power
            val_list["%s%s"%(psu.name,"Vol_O" )] = outputdic_voltage
            val_list["%s%s"%(psu.name,"Curr_O" )] = outputdic_current
            val_list["%s%s"%(psu.name,"Power_O" )] = outputdic_power
            val_list["%s%s" % (psu.name, "Fan")] = fanspeed
            val_list["%s%s" % (psu.name, "Temp")] = temperature

        return val_list

    # cpld
    def get_cpld_user_reg(self):
        cpld = self.chas.get_cpld_byname("BASE_CPLD")
        if cpld == None :
            return None
        else:
            return cpld.get_user_reg()

    def set_cpld_user_reg(self, value):
        if (isinstance (value, int) == False) :
            baseutil.logger_debug("value must int %s"%type(value))
            return -1
        if (int(value) < 0 or int(value) > 255) :
            baseutil.logger_debug("value must [0 - 255]")
            return -1
        cpld = self.chas.get_cpld_byname("BASE_CPLD")
        if cpld == None :
            baseutil.logger_debug("name BASE_CPLD not find")
            return -1
        if cpld.set_user_reg(value) == True:
            return 0
        else:
            return -1

    def set_cpld_console_owner(self, owner):
        """
        Set console I/O owner

        @param owner I/O owner of the console, either "cpu" or "bmc"

        @return 0 for success, -1 for failure
        """
        if (owner == None):
            baseutil.logger_debug("owner is None")
            return -1
        if (owner != "cpu" and owner != "bmc") :
            baseutil.logger_debug("owner is %s, must cpu or bmc"%owner)
            return -1
        cpld = self.chas.get_cpld_byname("BASE_CPLD")
        if cpld == None :
            baseutil.logger_debug("name BASE_CPLD not find")
            return -1
        if cpld.set_console_owner(owner) == True:
            return 0
        else:
            return -1

    def get_cpld_all_version(self):
        """
        Get version of all CPLDs' that can be read from BMC

        @return dict of CPLDs' version or None for failure.
                example outputs:
                {
                    "BASE_CPLD": "0.1",     # or "N/A" for read failure
                    "FAN_CPLD": "0.2"
                }
        """
        cpld_version = {
            "BASE_CPLD": "N/A",
            "FAN_CPLD": "N/A"
        }
        for cpld_name in cpld_version.keys():
            cpld = self.chas.get_cpld_byname(cpld_name)
            if cpld == None :
                baseutil.logger_debug("name %s not find"%cpld_name)
                continue
            cpld_version[cpld_name] = cpld.get_version()
        return cpld_version

    def get_bmc_productname(self):
        """
        Get product name

        @return product name string, e.g. AS13-32H-F-$(VENDOR_NAME), if error return "N/A"
        """
        bmc = self.chas.get_bmc_byname("master")
        if (bmc == None):
            baseutil.logger_debug("name bmc(master) not find")
            return "N/A"
        return bmc.get_productname()

    def call_bmc_diagcmd(self, cmdstr):
        """
        Call BMC diag comman func

        @return ret: 0 sucess , -1 fail
                outmsg: if success is out msg, or fail is err msg
        """
        if (cmdstr == None or cmdstr == ""):
            outmsg = "cmdstr is empty"
            baseutil.logger_debug(outmsg)
            return -1, outmsg
        bmc = self.chas.get_bmc_byname("master")
        if (bmc == None):
            outmsg = "name bmc(master) not find"
            baseutil.logger_debug(outmsg)
            return -1, outmsg
        baseutil.logger_debug("call cmdstr %s"%cmdstr)
        return bmc.call_diagcmd(cmdstr)

    def write_bios_version(self, flash, version):
        bios = self.chas.get_bios_byname("master")
        if bios == None :
            baseutil.logger_debug("name bios(master) not find")
            return -1
        return bios.set_bios_version(flash, version)

    def get_bios_version(self):
        bios = self.chas.get_bios_byname("master")
        if bios == None :
            baseutil.logger_debug("name bios(master) not find")
            return -1
        return bios.get_bios_version()

    def get_bios_status(self):
        bios = self.chas.get_bios_byname("master")
        if bios == None :
            baseutil.logger_debug("name bios(master) not find")
            return -1
        return bios.get_bios_boot_status()

    def monitor_cpu_host_watchdog(self, value):
        cpu = self.chas.get_cpu_byname("cpu")
        if cpu == None:
            baseutil.logger_debug("name cpu not find")
            return -1
        return cpu.set_cpu_host_watchdog(value)

    def get_bmc_mac_rov(self):
        """
        Get BMC mac rov

        @return ret: 0 sucess , -1 fail
                outmsg: if success is out msg, or fail is err msg
        """
        bmc = self.chas.get_bmc_byname("master")
        if bmc == None:
            msg = "name master not find"
            baseutil.logger_debug(msg)
            return -1, msg
        return bmc.get_mac_rov()

    def get_bmc_next_boot(self):
        """
        Get next booting flash of BMC

        @return 'master'/'slave' on success, "N/A" for failure
        """
        bmc = self.chas.get_bmc_byname("master")
        if bmc == None:
            baseutil.logger_debug("name master not find")
            return "N/A"
        return bmc.get_next_boot()

    def set_bmc_next_boot(self, flash):
        """
        Set flash from which next BMC boot

        @param flash Booting flash of BMC, "master" or "slave"

        @return 0 on success, -1 for failure
        """
        if flash == None or (flash != "master" and flash != "slave"):
            baseutil.logger_debug("parameter flash illegal, should be [master|slave]")
            return -1
        bmc = self.chas.get_bmc_byname("master")
        if bmc == None:
            baseutil.logger_debug("name master not find")
            return -1
        return bmc.set_next_boot(flash)

    def reboot_bmc(self):
        """
        Reboot running BMC
        """
        bmc = self.chas.get_bmc_byname("master")
        if bmc == None:
            baseutil.logger_debug("name master not find")
            return -1
        return bmc.reboot()

    def get_bmc_info(self):
        """
        Get BMC info

        @return dict of BMC info or None for failure
                    "Version": "1.1.1", # "N/A"
                    "Flash": "master",  # "N/A"
                    "Next": "master"    # "N/A"
        """
        bmc = self.chas.get_bmc_byname("master")
        if bmc == None:
            baseutil.logger_debug("name master not find")
            return "N/A"
        return bmc.get_info()

    def get_bmc_version_all(self):
        """
        @return dict of BMCs
                {
                    "MasterVersion": "1.1.1",   # "N/A"
                    "SlaveVersion": "1.1.1"     # "N/A"
                }
        """
        bmc = self.chas.get_bmc_byname("master")
        if bmc == None:
            baseutil.logger_debug("name master not find")
            return "N/A"
        return bmc.get_version_all()

    def bmc_execute_command(self, cmd_str):
        ret, output = osutil.command(cmd_str)
        if ret:
            baseutil.logger_debug("execute %s command failed" %(cmd_str))
        return ret, output

    def get_cpu_status(self):
        """
        Get CPU current status.

        @return 'S0', ..., 'S5', or 'N/A' for failure
        """
        cpu = self.chas.get_cpu_byname("cpu")
        if cpu == None:
            baseutil.logger_debug("name cpu not find")
            return 'N/A'
        return cpu.get_state()





