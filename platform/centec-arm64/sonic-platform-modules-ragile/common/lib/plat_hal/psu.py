#######################################################
#
# psu.py
# Python implementation of the Class psu
# Original author: support@ragilenetworks.com
#
#######################################################
from devicebase import devicebase
from eepromutil.fru import *
from sensor import sensor

class psu(devicebase):
    __pmbus = None
    __e2loc = None
    __present = None
    __productManufacturer = None # ARTESYN
    __productName         = None # CRPS550W
    __productPartModelName= None # CSU550AP-3-300
    __productVersion      = None # AB
    __productSerialNumber = None # M623UZ00JYABL
    __AirFlow             = None # 'N/A'
    __AirFlowconifg       = None
    __InputStatus_config   = None
    __OutputStatus_config  = None
    __FanSpeed_config      = None
    __Temperature_config   = None
    __InputStatus   = None
    __OutputStatus  = None
    __FanSpeed      = None
    __Temperature   = None
    __FanSpeedMin   = None
    __FanSpeedMax   = None
    __InputsVoltage_config    = None
    __InputsCurrent_config     = None
    __InputsPower_config       = None
    __OutputsVoltage_config   = None
    __OutputsCurrent_config   = None
    __OutputsPower_config     = None
    __InputsVoltage   = {}
    __InputsCurrent    = None
    __InputsPower      = None
    __OutputsVoltage  = None
    __OutputsCurrent  = None
    __OutputsPower    = None
    __InputsType_config = None
    __InputsType = None

    def __init__(self, conf = None):
        self.pmbus = conf.get("pmbusloc", None)
        self.e2loc = conf.get("e2loc", None)
        self.__presentconfig = conf.get("present", None)
        self.name =  conf.get("name", None)
        self.AirFlowconifg =  conf.get("airflow", None)
        self.Temperature_config = conf.get("Temperature", None)
        self.Temperature   = sensor(self.Temperature_config)

        self.FanSpeed_config = conf.get("FanSpeed", None)
        self.FanSpeed   = sensor(self.FanSpeed_config)

        self.__InputsVoltage_config  = conf.get("InputsVoltage",None)
        self.generate_psu_input_vol(self.__InputsVoltage_config)
        self.__InputsCurrent_config   = conf.get("InputsCurrent",None)
        self.InputsCurrent = sensor(self.__InputsCurrent_config)
        self.__InputsPower_config     = conf.get("InputsPower",None)
        self.InputsPower = sensor(self.__InputsPower_config)
        self.__OutputsVoltage_config = conf.get("OutputsVoltage",None)
        self.OutputsVoltage = sensor(self.__OutputsVoltage_config)
        self.__OutputsCurrent_config = conf.get("OutputsCurrent",None)
        self.OutputsCurrent = sensor(self.__OutputsCurrent_config)
        self.__OutputsPower_config   = conf.get("OutputsPower",None)
        self.OutputsPower = sensor(self.__OutputsPower_config)

        self.__InputStatus_config = conf.get("InputsStatus", None)
        self.__OutputStatus_config = conf.get("OutputsStatus", None)
        self.__InputsType_config = conf.get('InputsType', None)

    def generate_psu_input_vol(self, config):
        tmp = {}
        for (key, item) in config.items():
            tmp.setdefault(key, sensor(item))
        self.__InputsVoltage  = tmp

    def get_psu_sensor_by_name(self, psutype):
        return self.__InputsVoltage.get(psutype) or self.__InputsVoltage.get('other')

    @property
    def InputsVoltage(self):
        psutype = self.InputsType
        input_sensor = self.get_psu_sensor_by_name(psutype)
        if input_sensor  is None:
            return None
        else:
            return input_sensor

    @InputsVoltage.setter
    def InputsVoltage(self, val):
        self.__InputsVoltage  = val

    @property
    def InputsCurrent(self):
        return self.__InputsCurrent

    @InputsCurrent.setter
    def InputsCurrent(self, val):
        self.__InputsCurrent  = val

    @property
    def InputsPower(self):
        return self.__InputsPower

    @InputsPower.setter
    def InputsPower(self, val):
        self.__InputsPower  = val

    @property
    def OutputsVoltage(self):
        return self.__OutputsVoltage

    @OutputsVoltage.setter
    def OutputsVoltage(self, val):
        self.__OutputsVoltage  = val

    @property
    def OutputsCurrent(self):
        return self.__OutputsCurrent

    @OutputsCurrent.setter
    def OutputsCurrent(self, val):
        self.__OutputsCurrent  = val

    @property
    def OutputsPower(self):
        return self.__OutputsPower

    @OutputsPower.setter
    def OutputsPower(self, val):
        self.__OutputsPower  = val

    @property
    def InputStatus(self):
        if self.present == False:
            self.__InputStatus = False
        else:
            ret, val = self.get_value(self.__InputStatus_config)
            mask = self.__InputStatus_config.get("mask")
            if ret == True:
                ttt = val & mask
                if ttt == 0:
                    self.__InputStatus = True
                else:
                    self.__InputStatus = False
            else:
                self.__InputStatus = False
        return self.__InputStatus

    @InputStatus.setter
    def InputStatus(self, val):
        self.__InputStatus  = val


    @property
    def InputsType(self):
        psutypedecode = self.__InputsType_config.get('psutypedecode', None)
        if self.present == False:
            self.__InputsType = psutypedecode.get(0x00)
        else:
            ret, val = self.get_value(self.__InputsType_config)
            self.__InputsType = self.__InputsType_config.get(val,None)
            if self.__InputsType is not None:
                return self.__InputsType
            if ret == True and val in psutypedecode:
                self.__InputsType = psutypedecode.get(val)
            else:
                self.__InputsType = psutypedecode.get(0x00)
        return self.__InputsType

    @InputsType.setter
    def InputsType(self, val):
        self.__InputsType  = val

    @property
    def FanSpeedMin(self):
        return self.__FanSpeedMin

    @FanSpeedMin.setter
    def FanSpeedMin(self, val):
        self.__FanSpeedMin  = val

    @property
    def FanSpeedMax(self):
        return self.__FanSpeedMax

    @FanSpeedMax.setter
    def FanSpeedMax(self, val):
        self.__FanSpeedMax  = val

    @property
    def OutputStatus(self):
        if self.present == False:
            self.__OutputStatus = False
        else:
            ret, val = self.get_value(self.__OutputStatus_config)
            mask = self.__OutputStatus_config.get("mask")
            if ret == True:
                ttt = val & mask
                if ttt == 0:
                    self.__OutputStatus = True
                else:
                    self.__OutputStatus = False
            else:
                self.__OutputStatus = False
        return self.__OutputStatus

    @OutputStatus.setter
    def OutputStatus(self, val):
        self.__OutputStatus  = val

    @property
    def FanSpeed(self):
        return self.__FanSpeed

    @FanSpeed.setter
    def FanSpeed(self, val):
        self.__FanSpeed  = val

    @property
    def Temperature(self):
        return self.__Temperature

    @Temperature.setter
    def Temperature(self, val):
        self.__Temperature  = val

    @property
    def Temperature_config(self):
        return self.__Temperature_config

    @Temperature_config.setter
    def Temperature_config(self, val):
        self.__Temperature_config = val

    @property
    def AirFlowconifg(self):
        return self.__AirFlowconifg

    @AirFlowconifg.setter
    def AirFlowconifg(self, val):
        self.__AirFlowconifg = val

    @property
    def pmbus(self):
        return self.__pmbus

    @pmbus.setter
    def pmbus(self, val):
        self.__pmbus = val

    @property
    def e2loc(self):
        return self.__e2loc

    @e2loc.setter
    def e2loc(self, val):
        self.__e2loc = val

    @property
    def AirFlow(self):
        return self.__AirFlow

    @AirFlow.setter
    def AirFlow(self, val):
        self.__AirFlow = val

    @property
    def present(self):
        ret , val = self.get_value(self.__presentconfig)
        if (ret == False) or (val is None):
            return False
        mask = self.__presentconfig.get("mask")
        ttt = (int(val, 16)) & mask
        if ttt == 0:
            return True
        else:
            return False

    @present.setter
    def present(self, val):
        self.__present = val

    @property
    def productManufacturer(self):
        return self.__productManufacturer

    @productManufacturer.setter
    def productManufacturer(self, val):
        self.__productManufacturer = val

    @property
    def productName(self):
        return self.__productName

    @productName.setter
    def productName(self, val):
        self.__productName = val

    @property
    def productPartModelName(self):
        return self.__productPartModelName

    @productPartModelName.setter
    def productPartModelName(self, val):
        self.__productPartModelName = val

    @property
    def productVersion(self):
        return self.__productVersion

    @productVersion.setter
    def productVersion(self, val):
        self.__productVersion = val

    @property
    def productSerialNumber(self):
        return self.__productSerialNumber

    @productSerialNumber.setter
    def productSerialNumber(self, val):
        self.__productSerialNumber = val

    def __str__(self):
        formatstr =  \
                "name                : %s \n" \
                "productManufacturer : %s \n" \
                "productName         : %s \n" \
                "productPartModelName: %s \n" \
                "productVersion      : %s \n" \
                "productSerialNumber : %s \n" \
                "AirFlow             : %s \n" \

        tmpstr = formatstr % (self.name, self.productManufacturer,
                                self.productName, self.productPartModelName,
                                self.productVersion, self.productSerialNumber, self.AirFlow)
        return tmpstr

    def get_fan_speed_pwm(self):
        if self.present == False:
            return None
        selfconfig = {}
        selfconfig['bus'] = self.pmbus['bus']
        selfconfig['addr'] = self.pmbus['addr']
        selfconfig['way'] = 'i2cword'
        selfconfig['offset'] = 0x3b
        ret, val = self.get_value(selfconfig)
        if ret == True:
            return val
        else:
            return None

    def set_fan_speed_pwm(self, pwm):
        '''
            pmbus
                if duty:
                 i2cset -f -y 0x3b 0x0064  wp
        '''
        if self.present == False:
            return None
        if 0 <= pwm <= 100:
            '''enable duty first '''
            selfconfig = {}

            selfconfig['bus'] = self.pmbus['bus']
            selfconfig['addr'] = self.pmbus['addr']
            selfconfig['way'] = 'i2cpec'
            selfconfig['offset'] = 0x3a
            ret , val = self.set_value(selfconfig, 0x80)

            selfconfig['way'] = 'i2cwordpec'
            selfconfig['offset'] = 0x3b
            bytetmp = pwm
            ret , val = self.set_value(selfconfig, int(bytetmp))
            if ret == True:
                return True
            else:
                return None
        else:
            raise Exception("pwm not in range [0,100]")

    def get_fru_info(self):
        try:
            if self.present == False:
                raise Exception("%s: not present" % self.name)
            eeprom = self.get_eeprom_info(self.e2loc)
            if eeprom is None:
                raise Exception("%s:value is none" % self.name)
            fru = ipmifru()
            fru.decodeBin(eeprom)
            if fru.productInfoArea is not None:
                self.productManufacturer = fru.productInfoArea.productManufacturer.strip()
                self.productName         = fru.productInfoArea.productName.strip()
                self.productPartModelName= fru.productInfoArea.productPartModelName.strip()
                self.productVersion      = fru.productInfoArea.productVersion.strip()
                self.productSerialNumber = fru.productInfoArea.productSerialNumber.strip().replace(chr(0),"")
        except Exception as e:
            self.productManufacturer = None
            self.productName         = None
            self.productPartModelName= None
            self.productVersion      = None
            self.productSerialNumber = None
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

