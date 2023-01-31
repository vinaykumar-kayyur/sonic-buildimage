#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import inspect
import os
import sys
import json
import time
from  plat_hal.interface import interface

class Basecommand():
    def __init__(self, doc = '', name = None):
        self.name  = name
        self.doc = doc

class Command(Basecommand):
    def __init__(self, name, f):
        self.name =name
        self.f = f
        self.paramcount =self.f.__code__.co_argcount

    def dofun(self, args):
        fn = self.f.__call__
        fn(*args)

class Group(Basecommand):
    def __init__(self, name, f):
        self.groups= []
        self.commands = []
        self.name =name
        self.f = f
        pass

    def add_groups(self, command):
        self.groups.append(command)
        pass

    def add_commands(self, commnad):
        x = Command(commnad.__name__, commnad)
        self.subprocess.append(x)

    def find_valuebyname(self, name):
        for item in self.groups:
            if name == item.name:
                return item
        for item in self.commands:
            if name == item.name:
                return item
        return None

    def deal(self, args):
        if len(args) <= 0:
            return self.print_help()
        funclevel = args[0]
        val = self.find_valuebyname(funclevel)
        if val is None:
            return self.print_help()
        if isinstance(val, Command):
            if len(args) < (val.paramcount + 1):
                return self.print_help()
            else:
                inputargs = args[1: (1 + val.paramcount)]
            return val.dofun(inputargs)
        if isinstance(val , Group):
            args = args[1:]
            return val.deal(args)
        else:
            self.print_help()

    def get_max(self, arr):
        lentmp = 0
        for ar in arr:
            lentmp = len(ar) if (len(ar) > lentmp) else lentmp
        return lentmp

    def print_help(self,*attrs):

        namesize = []
        for item in self.groups:
            namesize.append(item.name)
        for item in self.commands:
            namesize.append(item.name)
        maxvalue  = self.get_max(namesize)

        if len(self.groups) > 0:
            print("Groups:")
            for item in self.groups:
                print("   %-*s    %s" % (maxvalue, item.name, item.f.__doc__ or ''))
        if len(self.commands) > 0:
            print("Commands:")
            for item in self.commands:
                print("   %-*s   %s" % (maxvalue,item.name, item.f.__doc__ or ''))

class clival():
    @staticmethod
    def Fire(val = None):
        group = Group("top",'mainlevel')
        clival.iterGroup(val, group)
        # context = {}
        # caller = inspect.stack()[1]
        # caller_frame = caller[0]
        # caller_globals = caller_frame.f_globals
        # caller_locals = caller_frame.f_locals
        # context.update(caller_globals)
        # context.update(caller_locals)
        args = sys.argv[1:]
        group.deal(args)

    @staticmethod
    def iterGroup(val, group):
        for key, item in val.items():
            if item is None:  # first level
                if (inspect.isfunction(key)):
                    group.add_commands(key)
            else:
                group1 = Group(key.__name__, key)
                clival.iterGroup(item, group1)
                group.add_groups(group1)

def psu():
    '''test psu '''
    pass

def fan():
    '''test fan '''
    pass

def sensor():
    '''test sensor '''
    pass

int_case = interface()

def get_total_number():
    '''psu  get_total_number '''
    print("=================get_total_number======================")
    print(int_case.get_psu_total_number())

def get_presence():
    '''psu  get_presence '''
    print("=================get_presence======================")
    psus = int_case.get_psus()
    for psu in psus:
        print(psu.name, end=' ')
        print(int_case.get_psu_presence(psu.name))

def get_fru_info():
    '''psu  get_fru_info '''
    print("=================get_fru_info======================")
    psus = int_case.get_psus()
    for psu in psus:
        print(psu.name, end=' ')
        print(json.dumps(int_case.get_psu_fru_info(psu.name), ensure_ascii = False,indent=4))

def get_status():
    '''psu  get_status '''
    print("=================get_status======================")
    psus = int_case.get_psus()
    for psu in psus:
        print(psu.name, end=' ')
        print(json.dumps(int_case.get_psu_status(psu.name), ensure_ascii = False,indent=4))

def set_psu_fan_speed_pwm(realspeed):
    '''set_psu_fan_speed_pwm'''
    print("=================set_psu_fan_speed_pwm======================")
    psus = int_case.get_psus()
    for psu in  psus:
        print(psu.name, end=' ')
        print(int_case.set_psu_fan_speed_pwm(psu.name, int(realspeed)))
    pass

def get_psu_fan_speed_pwm():
    '''get_psu_fan_speed_pwm'''
    print("=================get_psu_fan_speed_pwm======================")
    psus = int_case.get_psus()
    for psu in  psus:
        print(psu.name, end=' ')
        print(json.dumps(int_case.get_psu_fan_speed_pwm(psu.name)))
    pass

def get_psu_power_status():
    '''psu  get_psu_power_status '''
    print("=================get_psu_power_status======================")
    psus = int_case.get_psus()
    for psu in psus:
        print(psu.name, end=' ')
        print(json.dumps(int_case.get_psu_power_status(psu.name), ensure_ascii = False,indent=4))

def get_info_all():
    '''psu  get_info_all '''
    print("=================get_info_all======================")
    print(json.dumps(int_case.get_psu_info_all(), ensure_ascii = False,indent=4))

def fan_get_total_number():
    print("=================get_info_all======================")
    print(json.dumps(int_case.get_fan_total_number(), ensure_ascii = False, indent=4))


def fan_get_rotor_number():
    '''fan_get_rotor_numbe'''
    print("=================fan_get_rotor_number======================")
    fans = int_case.get_fans()
    for fan in  fans:
        print(fan.name, end=' ')
        print(int_case.get_fan_rotor_number(fan.name))

    pass

def fan_get_speed():
    '''fan_get_speed'''
    print("=================fan_get_speed======================")
    fans = int_case.get_fans()
    for fan in  fans:
        rotors = fan.rotor_list
        for rotor in rotors:
            index  =  rotors.index(rotor)
            print("%s rotor%d"%(fan.name, index + 1) , end ='  ' )
            print(int_case.get_fan_speed(fan.name, index + 1))
    pass

def fan_set_speed(realspeed):
    '''fan_set_speed'''
    speed = int(realspeed)
    xspeed = round(speed /255 * 100)
    print("=================fan_set_speed======================")
    fans = int_case.get_fans()
    for fan in  fans:
        rotors = fan.rotor_list
        for rotor in rotors:
            index  =  rotors.index(rotor)
            print("%s %s" % (fan.name, rotor.name) , end ='  ' )
            print(int_case.get_fan_speed(fan.name, index + 1), end ='  ')
            print(int_case.set_fan_speed(fan.name, index + 1, xspeed))
            time.sleep(5)
            print("%s %s" % (fan.name, rotor.name) , end ='  ' )
            print(int_case.get_fan_speed(fan.name, index + 1))

def fan_get_speed_pwm():
    '''fan_get_speed_pwm'''
    print("=================fan_get_speed_pwm======================")
    fans = int_case.get_fans()
    for fan in  fans:
        rotors = fan.rotor_list
        for rotor in rotors:
            index  =  rotors.index(rotor)
            print("%s rotor%d" % (fan.name, index + 1), end='  ' )
            print (int_case.get_fan_speed_pwm(fan.name, index + 1))

def fan_set_speed_pwm(pwm):
    '''fan_set_speed_pwm'''
    print("=================fan_set_speed_pwm======================")
    fans = int_case.get_fans()
    for fan in fans:
        rotors = fan.rotor_list
        for rotor in rotors:
            index  =  rotors.index(rotor)
            print("%s %s"% (fan.name, rotor.name), end ='  ')
            val = int_case.set_fan_speed_pwm(fan.name, index + 1, pwm)
            print (val)

def fan_get_watchdog_status():
    '''fan_get_watchdog_status'''
    print("=================fan_get_watchdog_status======================")
    print(int_case.get_fan_watchdog_status())
    pass

def fan_enable_watchdog():
    '''fan_enable_watchdog'''
    print("=================fan_enable_watchdog======================")
    print('enable',int_case.enable_fan_watchdog())

def fan_disable_watchdog():
    '''fan_disable_watchdog'''
    print("=================fan_disable_watchdog======================")
    print('disable', int_case.enable_fan_watchdog(enable = False))

def fan_get_speed1():
    '''fan_get_speed'''
    print("=================fan_get_speed======================")
    fans = int_case.get_fans()
    for fan in  fans:
        total = int_case.get_fan_rotor_number(fan.name)
        rotors = fan.rotor_list
        for rotor in rotors:
            print("%s %s"%(fan.name, rotor.name) , end ='  ' )
            print(int_case.get_fan_speed(fan.name, rotor.name))
    pass

def fan_feed_watchdog():
    '''fan_feed_watchdog'''
    print("=================fan_feed_watchdog======================")
    fan_get_speed()
    print (int_case.feed_fan_watchdog(None))
    time.sleep(2)
    fan_get_speed()

def fan_set_led(color):
    '''fan_set_led'''
    print("=================fan_set_led======================")
    fans = int_case.get_fans()
    for fan in fans:
        print("%s" % fan.name)
        for i in range(2):
            if i == 0:
                flag = True
            elif i == 1:
                flag = False
            print(color, int_case.set_fan_led(fan.name, color, flag))

def fan_get_presence():
    '''fan_get_presence'''
    print("=================fan_get_presence======================")
    fans = int_case.get_fans()
    for fan in fans:
        print("%s" % fan.name)
        print(int_case.get_fan_presence(fan.name))

def fan_get_fru_info():
    '''fan_get_fru_info'''
    print("=================fan_get_fru_info======================")
    fans = int_case.get_fans()
    for fan in fans:
        print("%s" % fan.name)
        print(json.dumps(int_case.get_fan_fru_info(fan.name), ensure_ascii=False, indent=4))

def fan_get_status():
    '''fan_get_status'''
    print("=================fan_get_status======================")
    fans = int_case.get_fans()
    for fan in fans:
        print("%s" % fan.name)
        print(json.dumps(int_case.get_fan_status(fan.name), ensure_ascii=False, indent=4))

def fan_get_info_all():
    '''fan_get_info_all'''
    print("=================fan_get_info_all======================")
    print(json.dumps(int_case.get_fan_info_all(), ensure_ascii=False, indent=4))
    pass

def get_sensor_info():
    '''get_sensor_info'''
    print("=================get_sensor_info======================")
    print(json.dumps(int_case.get_sensor_info(), ensure_ascii = False, indent=4))

if __name__ == '__main__':
    clival.Fire(
        {
            psu:{
                    get_total_number       : None,
                    get_presence           : None,
                    get_fru_info           : None,
                    set_psu_fan_speed_pwm  : None,
                    get_psu_fan_speed_pwm  : None,
                    get_status             : None,
                    get_psu_power_status   : None,
                    get_info_all           : None
                 },
            fan:{
                    fan_get_total_number    : None,
                    fan_get_rotor_number    : None,
                    fan_get_speed           : None,
                    fan_set_speed           : None,
                    fan_get_speed_pwm       : None,
                    fan_set_speed_pwm       : None,
                    fan_get_watchdog_status : None,
                    fan_enable_watchdog     : None,
                    fan_disable_watchdog    : None,
                    fan_feed_watchdog       : None,
                    fan_set_led             : None,
                    fan_get_presence        : None,
                    fan_get_fru_info        : None,
                    fan_get_status          : None,
                    fan_get_info_all        : None
                 },
            sensor:{
                    get_sensor_info : None
                 }
        }

    )
