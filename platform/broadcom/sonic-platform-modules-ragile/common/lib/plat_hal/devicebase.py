#!/usr/bin/env python3
#######################################################
#
# devicebase.py
# Python implementation of the Class devicebase
#
#######################################################
import subprocess
from plat_hal.osutil import osutil
from plat_hal.baseutil import baseutil


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
        value = ""
        for i in range(256):
            ret, val = self.get_i2c(bus, loc, i)
            value += chr(val)
        return value

    def byteTostr(self, val):
        strtmp = ''
        for value in val:
            strtmp += chr(value)
        return strtmp

    def get_eeprom_info(self, conf):
        eeprom = ""
        if conf.get('way') == 'sysfs':
            ret, eeprom = self.get_value(conf)
            if ret is False:
                return None
        elif conf.get('way') == 'devfile':
            ret, eeprom_list = self.get_value(conf)
            if ret is False:
                return None
            for item in eeprom_list:
                eeprom += chr(item)
        else:
            eeprom = self.dumpValueByI2c(conf.get('bus'), conf.get('addr'))
        return eeprom

    def exec_os_cmd(self, cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        return proc.returncode, stdout

    def get_value(self, config):
        '''
            get value by config way
            way  i2c/sysfs/lpc
        '''
        way = config.get("way")
        if way == 'sysfs':
            return self.get_sysfs(config.get("loc"), config.get("flock_path"))
        if way == "i2c":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.get_i2c(bus, addr, offset)
        if way == "io":
            io_addr = config.get('io_addr')
            read_len = config.get('read_len', 1)
            return self.get_io(io_addr, read_len)
        if way == "i2cword":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.get_i2cword(bus, addr, offset)
        if way == "devmem":
            addr = config.get("addr")
            digit = config.get("digit")
            mask = config.get("mask", None)
            return self.get_devmem(addr, digit, mask)
        if way == "sdk":
            get_type = config.get("type")
            if get_type == "bcm_temp":
                return self.getbcmtemp()
            if get_type == "bcm_reg":
                reg = config.get("reg")
                return self.getbcmreg(reg)
            raise Exception("cannot found sdk type deal")
        if way == "devfile":
            loc = config.get("loc")
            offset = config.get("offset")
            length = config.get("len")
            ret, val_list = self.devfile_read(loc, offset, length)
            if ret is True:
                if length == 1:
                    val = val_list[0]
                    return True, val
                return True, val_list
            return False, ("devfile read failed. path:%s, offset:0x%x, read_len:%d" % (loc, offset, length))
        if way == "devfile_ascii":
            loc = config.get("loc")
            offset = config.get("offset")
            length = config.get("len")
            return self.devfile_read_ascii(loc, offset, length)
        if way == 'cmd':
            cmd = config.get("cmd")
            ret, log = self.exec_os_cmd(cmd)
            if ret:
                return False, ("cmd write exec %s failed, log: %s" % (cmd, log))
            return True, log
        raise Exception("cannot found way deal")

    def devfile_read(self, loc, offset, length):
        return osutil.readdevfile(loc, offset, length)

    def devfile_read_ascii(self, loc, offset, length):
        return osutil.readdevfile_ascii(loc, offset, length)

    def get_sysfs(self, loc, flock_path=None):
        return self.getsysfs(loc, flock_path)

    def getsysfs(self, loc, flock_path=None):
        ret, val = osutil.readsysfs(loc, flock_path)
        return ret, val

    def get_devmem(self, addr, digit, mask):
        return osutil.getdevmem(addr, digit, mask)

    def get_i2cword(self, bus, addr, offset):
        return self.geti2cword(bus, addr, offset)

    def geti2cword(self, bus, addr, offset):
        ret, val = osutil.geti2cword(bus, addr, offset)
        return ret, val

    def get_io(self, reg_addr, read_len):
        return self.getio(reg_addr, read_len)

    def getio(self, reg_addr, read_len):
        ret, val = osutil.io_rd(reg_addr, read_len)
        return ret, val

    def get_i2c(self, bus, addr, offset):
        return self.geti2c(bus, addr, offset)

    def geti2c(self, bus, addr, offset):
        ret, val = osutil.wbi2cget(bus, addr, offset)
        return ret, val

    def set_value(self, config, val):
        '''
            get value by config way
            way  i2c/sysfs/lpc
        '''
        way = config.get("way")
        if way == 'sysfs':
            return self.set_sysfs(config.get("loc"), "0x%02x" % val)
        if way == "i2c":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.set_i2c(bus, addr, offset, val)
        if way == "i2cpec":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.seti2c_byte_pec(bus, addr, offset, val)
        if way == 'i2cword':
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.set_i2cword(bus, addr, offset, val)
        if way == "i2cwordpec":
            bus = config.get("bus")
            addr = config.get("addr")
            offset = config.get("offset")
            return self.set_i2cwordpec(bus, addr, offset, val)
        if way == "devfile":
            loc = config.get("loc")
            offset = config.get("offset")
            return self.devfile_write(loc, offset, val)
        return False, "unsupport way: %s" % way

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
        ret, val = osutil.wbi2cset(bus, addr, offset, byte)
        return ret, val

    def devfile_write(self, loc, offset, val):
        ret, val = osutil.writedevfile(loc, offset, val)
        return ret, val

    def getbcmtemp(self):
        try:
            sta, ret = osutil.getmactemp()
            if sta is True:
                mac_aver = float(ret.get("average", self.__error_ret))
                mac_aver = mac_aver * 1000
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
