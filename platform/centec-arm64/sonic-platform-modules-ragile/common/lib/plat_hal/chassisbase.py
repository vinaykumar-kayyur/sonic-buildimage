#######################################################
#
# chassisbase.py
# Python implementation of the Class chassisbase
# Original author: support@ragilenetworks.com
#
#######################################################
from dcdc import dcdc
from psu import psu
from led import led
from temp import temp
from fan import fan
from card import card
from sensor import sensor
# from cpld import cpld
# from bios import bios
# from bmc import bmc
# from cpu import cpu
from baseutil import baseutil


class chassisbase:
    __psu_list  = []
    __led_list  = []
    __temp_list = []
    __fan_list  = []
    __card_list = []
    __sensor_list = []
    __dcdc_list = []
    __cpld_list = []
    __bios_list = []
    __bmc_list  = []
    __cpu = None

    def __init__(self, conftype = 0, conf = None):
        # type: (object, object, object) -> object
        """
        init chassisbase as order

        type  = 0  use default conf, maybe auto find by platform
        type  = 1  use given conf,  conf is not None

        BITMAP
              bit 16
                      bit 0    PSU
                      bit 1    LED
                      bit 2    TEMP
                      bit 3    fan
                      bit 4    card
                      bit 5    sensor
        """
        __confTemp = None

        if conftype == 0:
            # user
            __confTemp = baseutil.get_config()
        elif conftype == 1:
            __confTemp = conf


        # psu
        psutemp = []
        psuconfig = __confTemp.get('psus')
        for i in range(len((psuconfig))):
            psu1  = psu(psuconfig[i])
            psutemp.append(psu1)
        self.psu_list = psutemp

        # led
        ledtemp = []
        ledconfig = __confTemp.get('leds')
        for i in range(len((ledconfig))):
            led1  = led(ledconfig[i])
            ledtemp.append(led1)
        self.led_list = ledtemp
        # temp
        temptemp = []
        tempconfig = __confTemp.get('temps')
        for i in range(len((tempconfig))):
            temp1  = temp(tempconfig[i])
            temptemp.append(temp1)
        self.temp_list = temptemp
        # fan
        fantemp = []
        fanconfig = __confTemp.get('fans')
        for i in range(len((fanconfig))):
            fan1  = fan(fanconfig[i])
            fantemp.append(fan1)
        self.fan_list = fantemp
        # card
        cardtemp = []
        cardconfig = __confTemp.get('cards')
        for i in range(len((cardconfig))):
            card1  = card(cardconfig[i])
            cardtemp.append(card1)
        self.card_list = cardtemp

        '''
        #dcdc
        dcdctemp = []
        dcdcconfig = __confTemp.get('dcdc')
        for i in range(len((dcdcconfig))):
            dcdc1 = dcdc(dcdcconfig[i])
            dcdctemp.append(dcdc1)
        self.dcdc_list = dcdctemp
        '''

    # dcdc
    @property
    def dcdc_list(self):
        return self.__dcdc_list

    @dcdc_list.setter
    def dcdc_list(self, val):
        self.__dcdc_list = val

    # sensor
    @property
    def sensor_list(self):
        return self.__sensor_list

    @sensor_list.setter
    def sensor_list(self, val):
        self.__sensor_list = val

    def get_sensor_byname(self, name):
        tmp = self.sensor_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None

    # psu
    @property
    def psu_list(self):
        return self.__psu_list


    @psu_list.setter
    def psu_list(self, val):
        self.__psu_list  = val

    def get_psu_byname(self, name):
        tmp = self.psu_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None

    # fan
    @property
    def fan_list(self):
        return self.__fan_list

    @fan_list.setter
    def fan_list(self, val):
        self.__fan_list = val

    def get_fan_byname(self, name):
        tmp = self.fan_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None


    # led
    @property
    def led_list(self):
        return self.__led_list

    @led_list.setter
    def led_list(self, val):
        self.__led_list = val

    def get_ledlist_config(self):
        pass

    def get_led_byname(self, name):
        tmp = self.led_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None

    # temp
    @property
    def temp_list(self):
        return self.__temp_list

    @temp_list.setter
    def temp_list(self, val):
        self.__temp_list = val

    def get_temp_byname(self, name):
        tmp = self.temp_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None

    # cpld
    @property
    def cpld_list(self):
        return self.__cpld_list

    @cpld_list.setter
    def cpld_list(self, val):
        self.__cpld_list = val

    def get_cpld_byname(self, name):
        tmp = self.cpld_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None

    # bios
    @property
    def bios_list(self):
        return self.__bios_list

    @bios_list.setter
    def bios_list(self, val):
        self.__bios_list = val

    def get_bios_byname(self, name):
        tmp = self.bios_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None

    # bmc
    @property
    def bmc_list(self):
        return self.__bmc_list

    @bmc_list.setter
    def bmc_list(self, val):
        self.__bmc_list = val

    def get_bmc_byname(self, name):
        tmp = self.bmc_list
        for i in range(len(tmp)):
            if name == tmp[i].name:
                return tmp[i]
        return None

    # cpu
    @property
    def cpu(self):
        return self.__cpu

    @cpu.setter
    def cpu(self, val):
        self.__cpu = val

    def get_cpu_byname(self, name):
        return self.cpu
