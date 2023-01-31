#######################################################
#
# devicebase.py
# Python implementation of the Class devicebase
# Original author: support@ragilenetworks.com
#
#######################################################
from osutil import osutil
from baseutil import baseutil

class devicebase(object):
    _name = None
    __error_ret = -99999

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

    def dumpValueByI2c(self, bus, loc):
        str = ""
        for i in range(256):
            ret,val = self.get_i2c(bus, loc, i)
            str += chr(val)
        return str

    def get_eeprom_info(self, conf):
        if conf.get('way') == 'sysfs':
            ret, eeprom = self.get_value(conf)
            if ret is False:
                return None
        else:
            eeprom = self.dumpValueByI2c(conf.get('bus'), conf.get('addr'))
        return eeprom

    def get_value(self, config):
        '''
            get value by config way
            way  i2c/sysfs/lpc
        '''
        way = config.get("way")
        if way == 'sysfs':
            return self.get_sysfs(config.get("loc"))
        elif way == "i2c":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.get_i2c(bus, addr, offset)
        elif way == "i2cword":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.get_i2cword(bus, addr, offset)
        elif way == "devmem":
            addr = config.get("addr")
            digit = config.get("digit")
            mask = config.get("mask", None)
            return self.get_devmem(addr, digit, mask)
        elif way == "sdk":
            type = config.get("type")
            if type == "bcm_temp":
                return self.getbcmtemp()
            elif type == "bcm_reg":
                reg = config.get("reg")
                return self.getbcmreg(reg)
            else:
                raise Exception("cannot found sdk type deal")
        else:
            raise Exception("cannot found way deal")

    def get_sysfs(self, loc):
        return self.getsysfs(loc)

    def getsysfs(self, loc):
        ret,val = osutil.readsysfs(loc)
        return ret , val

    def get_devmem(self, addr, digit, mask):
        return osutil.getdevmem(addr, digit, mask)

    def get_i2cword(self, bus, addr, offset):
        return self.geti2cword(bus, addr, offset)

    def geti2cword(self,bus,addr, offset):
        ret,val = osutil.geti2cword(bus, addr, offset)
        return ret, val

    def get_i2c(self, bus, addr, offset):
        return self.geti2c(bus, addr, offset)

    def geti2c(self, bus, addr, offset):
        ret,val = osutil.rji2cget(bus, addr, offset)
        return ret , val

    def set_value(self, config, val):
        '''
            get value by config way
            way  i2c/sysfs/lpc
        '''
        way = config.get("way")
        if way == 'sysfs':
            return self.set_sysfs(config.get("loc"), "0x%02x" % val)
        elif way == "i2c":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.set_i2c(bus, addr, offset, val)
        elif way == "i2cpec":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.seti2c_byte_pec(bus, addr, offset, val)
        elif way =='i2cword':
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.set_i2cword(bus, addr, offset, val)
        elif way == "i2cwordpec":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.set_i2cwordpec(bus, addr, offset, val)

    def set_sysfs(self, loc, value):
        return self.setsysfs(loc, value)

    def setsysfs(self, loc, value):
        return osutil.writesysfs(loc, value)

    def set_i2cword(self, bus, addr, offset, byte):
        return self.seti2cword(bus, addr, offset, byte)

    def seti2cword(self, bus, addr, offset, byte):
        return osutil.seti2cword(bus, addr, offset, byte)

    def set_i2cwordpec(self, bus, addr, offset, val):
        return osutil.seti2cwordpec(bus, addr, offset, val)

    def seti2c_byte_pec(self, bus, addr, offset, val):
        return osutil.seti2c_byte_pec(bus, addr, offset, val)

    def set_i2c(self, bus, addr, offset, byte):
        return self.seti2c(bus, addr, offset, byte)

    def seti2c(self, bus, addr, offset, byte):
        ret, val = osutil.rji2cset(bus, addr, offset, byte)
        return ret, val

    def getbcmtemp(self):
        try:
            sta, ret = osutil.getmactemp()
            if sta == True:
                mac_aver = float(ret.get("average", self.__error_ret))
                mac_max = float(ret.get("maximum", self.__error_ret))
                mac_aver = mac_aver * 1000
                mac_max = mac_max * 1000
            else:
                return False, ret
        except AttributeError as e:
            return False, str(e)
        return True, mac_aver

    def getbcmreg(self, reg):
        ret, val = osutil.getsdkreg(reg)
        return ret, val

    def logger_debug(self, msg):
        baseutil.logger_debug(msg)

    def command(self, cmd):
        ret, output = osutil.command(cmd)
        return ret, output
