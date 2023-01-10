from devicebase import devicebase
from eepromutil.fru import *
from sensor import sensor
import collections

class dcdc(devicebase):
    __attr = None
    __dcdc_ordict = None
    def __init__(self, conf = None):
        self.dcdc_ordict = collections.OrderedDict()
        if conf is not  None:
            self.name = conf.get('name', None)
            self.attr = conf.get('attr', None)
            tmp = {}
            for key in self.attr:
                tmpdict= sensor(self.attr[key])
                tmp[key] = tmpdict
            tmp_list = sorted(tmp.items(), key=lambda item: item[0])
            for member in tmp_list:
                self.dcdc_ordict[member[0]] = member[1]

    @property
    def dcdc_ordict(self):
        return self.__dcdc_ordict

    @dcdc_ordict.setter
    def dcdc_ordict(self, val):
        self.__dcdc_ordict = val

    @property
    def attr(self):
        return self.__attr

    @attr.setter
    def attr (self, val):
        self.__attr = val

