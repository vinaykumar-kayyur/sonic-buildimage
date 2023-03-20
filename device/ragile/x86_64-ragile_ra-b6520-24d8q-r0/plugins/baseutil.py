#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
import commands
import time
import platform
import os.path
import syslog
import traceback
import json
import subprocess
import glob
import collections

PLUGINS_DOCKER_STARTED_FLAG = "/etc/sonic/.plugins_docker_started_flag"
DOING_WARM_UPGRADE = "/etc/sonic/.doing_warm_upg"
PLUGINS_DEBUG_FILE = "/etc/.plugins_debug_flag"
PLUGINSDEBUG = 1
debuglevel = 0

def debug_init():
    global debuglevel
    if os.path.exists(PLUGINS_DEBUG_FILE):
        debuglevel = debuglevel | PLUGINSDEBUG
    else:
        debuglevel = debuglevel & ~(PLUGINSDEBUG)

def pluginserror(s):
    #s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("PLUGINS",syslog.LOG_PID)
    syslog.syslog(syslog.LOG_ERR,s)

def pluginsdebuglog(s):
    #s = s.decode('utf-8').encode('gb2312')
    if PLUGINSDEBUG & debuglevel:
        syslog.openlog("PLUGINS",syslog.LOG_PID)
        syslog.syslog(syslog.LOG_DEBUG,s)

def exec_os_cmd(cmd):
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        return proc.returncode, stdout
    except Exception as e:
        pluginserror('%%PLUGINS-3-FAILED: exec_os_cmd happen exception, log:%s' % str(e))
        return -1, str(e)

def readsysfs(location):
    try:
        locations = glob.glob(location)
        with open(locations[0], 'rb') as fd1:
            retval = fd1.read()
        retval = retval.rstrip('\r\n')
        retval = retval.lstrip(" ")
    except Exception as e:
        pluginserror('%%PLUGINS-3-FAILED: readsysfs happen exception, location:%s, log:%s' % (location, str(e)))
        return False, (str(e)+" location[%s]" % location)
    return True, retval

def i2cget(bus, devno, address, word=None):
    try:
        if word == None:
            command_line = "i2cget -f -y %d 0x%02x 0x%02x " % (bus, devno, address)
        else:
            command_line = "i2cget -f -y %d 0x%02x 0x%02x %s" % (bus, devno, address, word)
        ret, ret_t = exec_os_cmd(command_line)
        if ret:
            return False, ("cmd %s failed, log: %s" % (command_line, ret_t))
        return True, ret_t
    except Exception as e:
        pluginserror('%%PLUGINS-3-FAILED: i2cget happen exception, log:%s' % str(e))
        return False, str(e)

def io_rd(reg_addr, len =1):
    try:
        regaddr = 0
        if type(reg_addr) == int:
            regaddr = reg_addr
        else:
            regaddr = int(reg_addr, 16)
        devfile = "/dev/port"
        fd = os.open(devfile, os.O_RDWR|os.O_CREAT)
        os.lseek(fd, regaddr, os.SEEK_SET)
        str = os.read(fd, len)
        return "".join(["%02x"% ord(item) for item in str])
    except ValueError:
        pluginserror('%%PLUGINS-3-FAILED: io_rd happen ValueError')
        return None
    except Exception as e:
        pluginserror('%%PLUGINS-3-FAILED: io_rd happen exception, log:%s' % str(e))
        return None
    finally:
        os.close(fd)
    return None

def dev_file_read(path, offset, len, bit_width):
    ret = ""
    joinstr = ''
    val_str = '0x'
    val_list = []
    fd = -1
    if not os.path.exists(path):
        return False, ("%s not found !" % path)
    if len % bit_width != 0:
        return False, "only support read by bit_width"
    if len < bit_width:
        return False, "len needs to greater than or equal to bit_width"

    try:
        fd = os.open(path, os.O_RDONLY)
        os.lseek(fd, offset, os.SEEK_SET)
        ret = os.read(fd, len)
        for item in ret:
            value = ord(item)  # data ASCII transformation
            val_list.append(value)

        for j in range(0, bit_width):
            val_str += "%02x" % val_list[bit_width - j - 1]

    except Exception as e:
        pluginserror('%%PLUGINS-3-FAILED: dev_file_read happen exception, log:%s' % str(e))
        return False, str(e)
    finally:
        if fd > 0:
            os.close(fd)
    return True, val_str

def get_value_one_time(config):
    try:
        way = config.get("gettype")
        if way == 'sysfs':
            loc = config.get("loc")
            ret, val = readsysfs(loc)
            if ret == True:
                val = val.replace("\x00","").strip()
                return True, val
            else:
                return False, ("sysfs read %s failed. log:%s" % (loc, val))
        elif way == "i2c":
            bus = config.get("bus")
            addr = config.get("loc")
            offset = config.get("offset")
            ret, val = i2cget(bus, addr, offset)
            if ret == True:
                val = val.replace("\x00","").strip()
                return True, val
            else:
                return False, ("i2c read bus:%d, addr:0x%x, offset:0x%x failed." % (bus, addr, offset))
        elif way == "io":
            io_addr = config.get('io_addr')
            val = io_rd(io_addr)
            if len(val) != 0:
                val = val.replace("\x00","").strip()
                return True, val
            else:
                return False, ("io_addr read failed. 0x%x failed" % io_addr)
        elif way == "i2cword":
            bus = config.get("bus")
            addr = config.get("loc")
            offset = config.get("offset")
            ret, val = i2cget(bus, addr, offset, 1)
            if ret == True:
                val = val.replace("\x00","").strip()
                return True, val
            else:
                return False, ("i2cword read bus:%d, addr:0x%x, offset:0x%x failed." % (bus, addr, offset))
        elif way == "devfile":
            path = config.get("path")
            offset = config.get("offset")
            read_len = config.get("read_len")
            bit_width = config.get("bit_width")
            ret, val = dev_file_read(path, offset, read_len, bit_width)
            if ret == True:
                val = val.replace("\x00","").strip()
                return True, val
            else:
                return False, ("devfile read path:%s, offset:0x%x, read_len:%d, bit_width:%d failed." % (path, offset, read_len, bit_width))
        elif way == 'cmd':
            cmd = config.get("cmd")
            ret, val = exec_os_cmd(cmd)
            if ret:
                return False, ("cmd read exec %s failed, log:%s" % (cmd, val))
            else:
                val = val.replace("\x00","").strip()
                return True, val
        elif way == 'direct_config':
            data = config.get("data")
            data = data.replace("\x00","").strip()
            return True, data
        else:
            return False, "not support read type"
    except Exception as e:
        pluginserror('%%PLUGINS-3-FAILED: get_value_one_time happen exception, log:%s' % str(e))
        return False, str(e)

def get_value(config):
    retrytime = 3
    for i in range(retrytime):
        ret, val = get_value_one_time(config)
        if ret == True:
            return True, val
        if (i + 1) < retrytime:
            time.sleep(0.1)
    return False, val

class BaseDev(object):
    def __init__(self, _list):
        self.each_dev_list = _list
        self.dev_dict = collections.OrderedDict()

    def get_attr(self):
        na_display_flag = 0
        for attr_config in self.each_dev_list:
            try:
                arrt_name = attr_config.get("attr", None)
                check_val = attr_config.get("ok_val", None)
                attr_decimal_precision = attr_config.get("decimal_precision", None)
                attr_unit = attr_config.get("unit", None)
                na_display_determinant = attr_config.get("na_display_determinant", 0)
                display_na_affected = attr_config.get("display_na_affected", 0)
                decode_val = attr_config.get("decode", None)
                formula = attr_config.get("formula", None)

                #arrt return NA when doing warm upgrade.
                if os.path.exists(DOING_WARM_UPGRADE):
                    pluginsdebuglog('PLUGINS-6-DEBUG: doing warm upgrade, arrt_name:%s return NA' % (arrt_name))
                    self.dev_dict[arrt_name] = "NA"
                    continue

                #wait plugins_init process finish and docker start complete.otherwise return NA directly.
                if not os.path.exists(PLUGINS_DOCKER_STARTED_FLAG):
                    pluginsdebuglog('PLUGINS-6-DEBUG: waiting plugins_init finish, arrt_name:%s return NA' % (arrt_name))
                    self.dev_dict[arrt_name] = "NA"
                    continue

                if display_na_affected == 1 and na_display_flag == 1:
                    self.dev_dict[arrt_name] = "NA"
                    pluginsdebuglog('PLUGINS-6-DEBUG: arrt_name:%s affected and display NA'% (arrt_name))
                    continue

                pluginsdebuglog('PLUGINS-6-DEBUG: arrt_name:%s, check_val:%s, attr_decimal_precision:%s, attr_unit:%s'
                    % (arrt_name, check_val, attr_decimal_precision, attr_unit))

                ret, val = get_value(attr_config)
                pluginsdebuglog('PLUGINS-6-DEBUG: %s get attr value:%s' %(arrt_name, val))

                if ret == False:
                    pluginserror('%%PLUGINS-3-FAILED: get attr %s failed. attr_config:%s'
                        % (arrt_name, attr_config))
                    pluginserror('%%PLUGINS-3-FAILED: %s failed log: %s' % (arrt_name, val))
                    self.dev_dict[arrt_name] = "NA"
                elif val == "NA" or val == "":
                    self.dev_dict[arrt_name] = "NA"
                else:
                    if check_val is not None:
                        pluginsdebuglog('PLUGINS-6-DEBUG: check_val:%s' % check_val)
                        if isinstance(check_val, list):
                            if int(val) in check_val:
                                self.dev_dict[arrt_name] = '1'
                            else:
                                self.dev_dict[arrt_name] = '0'
                                #check_val is not ok. judge whether this attribute is the determinant
                                if na_display_determinant == 1:
                                    na_display_flag = 1
                        elif isinstance(check_val, int):
                            if int(val) == check_val:
                                self.dev_dict[arrt_name] = '1'
                            else:
                                self.dev_dict[arrt_name] = '0'
                                #check_val is not ok. judge whether this attribute is the determinant
                                if na_display_determinant == 1:
                                    na_display_flag = 1
                        else:
                            pluginserror('%%PLUGINS-3-FAILED: %s is no support check_val type.' % check_val)
                            self.dev_dict[arrt_name] = 'NA'
                    else:
                        self.dev_dict[arrt_name] = val
                    if decode_val is not None:
                        if isinstance(decode_val, dict):
                            self.dev_dict[arrt_name] = decode_val.get(self.dev_dict[arrt_name], "NA")
                    if formula is not None:
                        val = str(eval(formula % (float(val))))
                        self.dev_dict[arrt_name] = val
                    if attr_decimal_precision is not None:
                        format = "%%.%df" % attr_decimal_precision
                        val = str(format % (float(val)))
                        self.dev_dict[arrt_name] = val
                    if attr_unit is not None:
                        self.dev_dict[arrt_name] += " %s" % attr_unit
                    pluginsdebuglog('PLUGINS-6-DEBUG: :final %s attr value:%s' % (arrt_name, self.dev_dict[arrt_name]))
            except Exception as e:
                pluginserror('%%PLUGINS-3-FAILED: get_attr happen exception, log:%s' % str(e))
                self.dev_dict[arrt_name] = "ERROR"
        return self.dev_dict

class Plugins(BaseDev):
    def __init__(self):
        debug_init()
        self.final_info = collections.OrderedDict()
        self.each_dev_list = []
        self.devs_list = []

    def get_data(self, config, type):
        self.initial_conifg = config

        # type == 1 is multiple devices attribute, has 'num' attribute
        if type == 1:
            self.final_info['num'] = self.initial_conifg.get("num", None)
            self.attr_list = self.initial_conifg.get("attr_list", [])

            #each dev list as a Class
            for attr in self.attr_list:
                attr_instance = BaseDev(attr)
                self.each_dev_list.append(attr_instance)

            #get each dev attribute Combined into devs_list
            for dev in self.each_dev_list:
                each_dev_dict = dev.get_attr()
                self.devs_list.append(each_dev_dict)
            self.final_info['objs'] = self.devs_list

        # type == 2 is single devices attribute
        elif type == 2:
            dev_instance = BaseDev(self.initial_conifg)
            self.final_info = dev_instance.get_attr()
        else:
            pluginserror('%%PLUGINS-3-FAILED: type:%s is unsupport type.' % type)
        return self.final_info