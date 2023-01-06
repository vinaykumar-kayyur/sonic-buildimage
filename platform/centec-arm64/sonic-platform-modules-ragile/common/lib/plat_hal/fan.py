#######################################################
#
# fan.py
# Python implementation of the Class fan
# Original author: support@ragilenetworks.com
#
#######################################################
from devicebase import devicebase
from eepromutil.fru import *
from sensor import sensor
from rotor import rotor

class fan(devicebase):
    __rotor_list = []
    __pn               = None
    __raweeprom        = None
    __sn               = None
    __present          = None
    __e2loc            = None
    __rotors           = None
    __AirFlow          = None
    __SpeedMin         = None
    __SpeedMax         = None
    __productName      = None
    __productSerialNumber =None
    __productPartModelName = None
    __WatchdogStatus = None
    __led_attrs_config = None
    __led_config =None
    __WatchdogStatus_config  = None
    __AirFlowconifg    = None
    __EnableWatchdogConf = None
    __Rotor_config = None

    def __init__(self, conf = None):
        if conf is not  None:
            self.name = conf.get('name', None)
            self.sn = conf.get('sn', None)
            self.present = conf.get('present', None)
            self.e2loc = conf.get('e2loc', None)
            self.SpeedMin = conf.get('SpeedMin', None)
            self.SpeedMax = conf.get('SpeedMax', None)
            self.AirFlowconifg = conf.get("airflow", None)
            self.AirFlowconfig = conf.get('airflow', None)
            self.WatchdogStatus_config = conf.get('WatchdogStatus', None)
            self.EnableWatchdogConf = conf.get('EnableWatchdogConf', None)
            self.led_attrs_config = conf.get('led_attrs', None)
            self.led_config = conf.get('led', None)
            self.Rotor_config = conf.get('Rotor', None)
            rotor_tmp = []
            for key,value in (self.Rotor_config).items():
                rotor_tmp.append(rotor(value))
            rotor_tmp.sort(key=lambda x: x.name, reverse=False)
            self.rotor_list = rotor_tmp
            self.rotors = len(self.rotor_list)
    @property
    def EnableWatchdogConf(self):
        return self.__EnableWatchdogConf

    @EnableWatchdogConf.setter
    def EnableWatchdogConf(self, val):
        self.__EnableWatchdogConf  = val

    @property
    def rotor_list(self):
        return self.__rotor_list

    @rotor_list.setter
    def rotor_list(self, val):
        self.__rotor_list  = val

    @property
    def Rotor_config(self):
        return self.__Rotor_config

    @Rotor_config.setter
    def Rotor_config(self, val):
        self.__Rotor_config = val

    @property
    def productName(self):
        return self.__productName

    @productName.setter
    def productName(self, val):
        self.__productName = val

    @property
    def productSerialNumber(self):
        return self.__productSerialNumber

    @productSerialNumber.setter
    def productSerialNumber(self, val):
        self.__productSerialNumber = val

    @property
    def productPartModelName(self):
        return self.__productPartModelName

    @productPartModelName.setter
    def productPartModelName(self, val):
        self.__productPartModelName = val

    @property
    def sn(self):
        return self.__sn

    @sn.setter
    def sn(self, val):
        self.__sn = val

    @property
    def pn(self):
        return self.__pn

    @pn.setter
    def pn(self, val):
        self.__pn = val

    @property
    def raweeprom(self):
        return self.__raweeprom

    @raweeprom.setter
    def raweeprom(self, val):
        self.__raweeprom = val

    @property
    def SpeedMax(self):
        return self.__SpeedMax

    @SpeedMax.setter
    def SpeedMax(self, val):
        self.__SpeedMax = val

    @property
    def SpeedMin(self):
        return self.__SpeedMin

    @SpeedMin.setter
    def SpeedMin(self, val):
        self.__SpeedMin = val

    @property
    def rotors(self):
        return self.__rotors

    @property
    def AirFlow(self):
        return self.__AirFlow

    @AirFlow.setter
    def AirFlow(self, val):
        self.__AirFlow = val

    @rotors.setter
    def rotors(self, val):
        self.__rotors = val

    def getspeed(self, conf):
        tmp = None
        if conf == None:
            return -1
        ret, val = self.get_value(conf)
        if ret == True:
            tmp = int(str(val), 10)
        else:
            val = None
        if val is not None:
            return int(15000000 / tmp)
        return -1

    def get_speed(self, rotor_index):
        rotor = self.get_rotor_index(rotor_index)
        return int(rotor.rotor_Speed.Value)

    def set_led(self, color, blink):
        status = self.led_attrs_config.get(color, None)
        if status == None:
            return False
        if blink == True:
            blink_status = self.led_attrs_config.get('flash', None)
        elif blink == False:
            blink_status = self.led_attrs_config.get('light', None)
        if blink_status == None:
            return False
        byte = status & blink_status
        ret, val = self.set_value(self.led_config, byte)
        return ret

    def set_speed(self, rotor_index, level):
        if level > 255 or level < 0 :
            return False
        rotor = self.get_rotor_index(rotor_index)
        if rotor is None:
            return False
        ret, val = self.set_value(rotor.Speedconfig, int(level))
        return ret

    def get_rotor_index(self, rotor_index):
        if rotor_index > len(self.rotor_list):
            raise Exception("%s: rotor_index value is wrong" % self.name)
        rotor = self.rotor_list[rotor_index - 1]
        return rotor

    def get_rotor_byname(self, rotor_index):
        for rotor in self.rotor_list:
            if rotor.name == rotor_index:
                return rotor
        return None

    def get_presence(self):
        ret , val = self.get_value(self.present)
        mask = self.present.get("mask")
        if (ret == False) or (val is None):
            return False
        flag = val & mask
        if flag == 0:
            return True
        else:
            return False

    def get_speed_pwm(self, rotor_index):
        rotor = self.get_rotor_index(rotor_index)
        if rotor is None:
            return False
        if rotor.i2c_speed is None:
            return False
        val = round(rotor.i2c_speed * 100 / 255)
        return val

    def feed_watchdog(self, pwm):
        ret = False
        for rotor in self.rotor_list:
            ret, val= rotor.feed_watchdog()
            if ret is False:
                return ret
        return ret

    def get_fru_info(self):
        try:
            if self.get_presence() is False:
                raise Exception("%s: not present" % self.name)
            eeprom = self.get_eeprom_info(self.e2loc)
            if eeprom is None:
                raise Exception("%s: value is none" % self.name)
            fru = ipmifru()
            fru.decodeBin(eeprom)
            self.productName = fru.productInfoArea.productName.strip()
            self.productSerialNumber = fru.productInfoArea.productSerialNumber.strip()  #SN
            self.productPartModelName = fru.productInfoArea.productPartModelName.strip() #PN
        except Exception as e:
            self.productName = None
            self.productSerialNumber = None
            self.productPartModelName = None
            return False
        return True

    def get_AirFlow(self):
        if self.productPartModelName  == None:
            ret = self.get_fru_info()
            if ret is False:
                self.AirFlow = None
                return False
        if self.AirFlowconifg == None:
            self.AirFlow = None
            return False
        else:
            for i in self.AirFlowconifg:
                if self.productPartModelName in self.AirFlowconifg[i]:
                    self.AirFlow = i
                    return True
        self.AirFlow = None
        return False

    def enable_watchdog(self, enable, timeout_sec):
        if enable == True:
            byte = self.EnableWatchdogConf.get("enable_byte", None)
            ret, val = self.set_value(self.EnableWatchdogConf, byte)
        elif enable == False:
            byte = self.EnableWatchdogConf.get("disable_byte", None)
            ret, val = self.set_value(self.EnableWatchdogConf, byte)
        return ret

    def get_watchdog_status(self):
        dic = {"support": None , "open": None, "work_full":None, "work_allow_set":None}
        if self.WatchdogStatus_config == None:
            return None
        ret , val = self.get_value(self.WatchdogStatus_config)
        if (ret == False) or (val is None):
            return None
        support_watchdog_off = self.WatchdogStatus_config.get("support_watchdog_off", None)
        is_open_off = self.WatchdogStatus_config.get("is_open_off", None)
        full_running_off = self.WatchdogStatus_config.get("full_running_off", None)
        running_setting_off = self.WatchdogStatus_config.get("running_setting_off", None)
        if support_watchdog_off is not None:
            if support_watchdog_off & val == self.WatchdogStatus_config.get("support_watchdog_mask", None):
                dic["support"] = True
            else:
                dic["support"] = False
                return dic
        if is_open_off is not None:
            if is_open_off & val == self.WatchdogStatus_config.get("is_open_mask", None):
                dic["open"] = True
            else:
                dic["open"] = False
        if full_running_off is not None:
            if full_running_off & val == self.WatchdogStatus_config.get("full_running_mask", None):
                dic["work_full"] = True
            else:
                dic["work_full"] = False
        if running_setting_off is not None:
            if running_setting_off & val == self.WatchdogStatus_config.get("running_setting_mask", None):
                dic["work_allow_set"] = True
            else:
                dic["work_allow_set"] = False
        return dic