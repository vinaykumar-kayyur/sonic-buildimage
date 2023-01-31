#######################################################
#
# sensor.py
# Python implementation of the Class sensor
# Original author: support@ragilenetworks.com
#
#######################################################
from devicebase import devicebase

class sensor(devicebase):

    __Value = None
    __Min = None
    __Max = None
    __ValueConfig = None
    __Flag = None
    __Unit = None
    __format = None

    __Min_config = None
    __Max_config = None



    @property
    def Min_config(self):
        return self.__Min_config

    @Min_config.setter
    def Min_config(self, val):
        self.__Min_config  = val

    @property
    def Max_config(self):
        return self.__Max_config

    @Max_config.setter
    def Max_config(self, val):
        self.__Max_config  = val

    @property
    def Unit(self):
        return self.__Unit

    @Unit.setter
    def Unit(self, val):
        self.__Unit  = val

    @property
    def format(self):
        return self.__format

    @format.setter
    def format(self, val):
        self.__format  = val


    @property
    def ValueConfig(self):
        return self.__ValueConfig

    @ValueConfig.setter
    def ValueConfig(self, val):
        self.__ValueConfig  = val

    @property
    def Flag(self):
        return self.__Flag

    @Flag.setter
    def Flag(self, val):
        self.__Flag  = val

    @property
    def Value(self):
        try:
            ret, val  = self.get_value(self.ValueConfig)
            if (ret == False) or (val is None):
                return None
            if self.format is None:
                self.__Value = int(val)
            else:
                self.__Value = eval(self.format % val)
        except:
            return None
        return self.__Value

    @Value.setter
    def Value(self, val):
        self.__Value  = val

    @property
    def Min(self):
        try:
            if self.format is None:
                self.__Min = self.Min_config
            else:
                self.__Min = eval(self.format % self.Min_config)
        except:
            return None
        return self.__Min

    @Min.setter
    def Min(self, val):
        self.__Min  = val

    @property
    def Max(self):
        try:
            if self.format is None:
                self.__Max = self.Max_config
            else:
                self.__Max = eval(self.format % self.Max_config)
        except:
            return None
        return self.__Max

    @Max.setter
    def Max(self, val):
        self.__Max  = val

    def __init__(self, conf=None):
        self.ValueConfig = conf.get("value", None)
        self.Flag = conf.get("flag", None)
        self.Min_config = conf.get("Min", None)
        self.Max_config = conf.get("Max", None)
        self.Unit = conf.get('Unit', None)
        self.format = conf.get('format', None)

    def __str__(self):
        formatstr =  \
            "ValueConfig:                : %s \n" \
            "Min :          %s \n" \
            "Max : %s \n" \
            "Unit  : %s \n" \
            "format:       : %s \n"

        tmpstr = formatstr % (self.ValueConfig, self.Min,
                                self.Max, self.Unit,
                                self.format)
        return tmpstr

