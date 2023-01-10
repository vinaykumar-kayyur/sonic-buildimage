#######################################################
#
# temp.py
# Python implementation of the Class temp
# Original author: support@ragilenetworks.com
#
#######################################################
from devicebase import devicebase
from sensor import sensor

class temp(sensor):
    def __init__(self, conf = None):
        super(temp, self).__init__(conf.get('Temperature', None))
        self.name =  conf.get("name", None)

    def __str__(self):
        super(temp, self).__str__()

    def get_max_value(self, conf):
        try:
            ret, val = self.get_value(conf)
            if ret == True:
                return val
            else:
                return None
        except:
            return None

    def check_flag(self):
        try:
            okbit = self.Flag.get('okbit')
            okval = self.Flag.get('okval')
            ret, val = self.get_value(self.Flag)
            if (ret == False) or (val is None):
                return False
            val_t = (int(val) & (1<< okbit)) >> okbit
            if val_t != okval:
                return False
        except Exception as e:
            return False
        return True

    @property
    def Value(self):
        try:
            if self.Flag != None:
                if self.check_flag() == False:
                    return None
            if isinstance(self.ValueConfig, list):
                max = None
                for i in self.ValueConfig:
                    tmp = self.get_max_value(i)
                    if tmp is None:
                        continue
                    if max is None or max < tmp:
                        max = tmp
                if max is None:
                    return None
                if self.format is None:
                    self.__Value = int(max)
                else:
                    self.__Value = eval(self.format % max)
            else:
                ret, val = self.get_value(self.ValueConfig)
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
