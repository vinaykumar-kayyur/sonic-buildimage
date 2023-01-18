#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import click
import os
import time
from  ragileutil import *
import syslog
from rest.rest import BMCMessage
import subprocess
import signal
from logutil.logutil import *

SYSLOG_IDENTIFIER = "sfpTempToBmc"

def subprocess_os_system(cmd, timeout=1):
    slice = 0.1   # 100ms for the unit
    retry_total_cnt  = timeout / slice
    retry_cnt = 0
    try:
        child_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False,preexec_fn=os.setsid)
    except Exception as e:
        print(e)
        return child_process.returncode, ""

    while child_process.poll() is None and retry_cnt < retry_total_cnt:
        time.sleep(slice)
        retry_cnt += 1

    if retry_cnt >= retry_total_cnt:
        os.killpg(os.getpgid(child_process.pid), signal.SIGTERM)
        log_error("time out:[%d]" % timeout,SYSLOG_IDENTIFIER)
        return False, ""
    out, err = child_process.communicate()
    return child_process.returncode, out

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

def getSfpMaxTemp():
    import sfputil.main
    load_platform_sfputil = sfputil.main.load_platform_sfputil()
    platform_sfputil  = sfputil.main.platform_sfputil

    temps = []

    for index in range(platform_sfputil.port_start, platform_sfputil.port_end + 1):
        if index in platform_sfputil.qsfp_ports:
            offset = 22
            eeprom_data = platform_sfputil.get_eeprom_raw(index)
        else :
            offset = 96
            eeprom_data = platform_sfputil.get_eeprom_dom_raw(index)
        if eeprom_data == None:
            continue
        msb = int(eeprom_data[offset], 16)
        lsb = int(eeprom_data[offset + 1], 16)
        result = (msb << 8) | (lsb & 0xff)
        result = float(result / 256.0)
        temps.append(result)
    maxtemp = 0
    if len(temps) > 0:
        maxtemp = max(temps)
    return  int(maxtemp * 1000)

def putDataToBmc():
    # log_info("putDataToBmc")
    maxtemp = getSfpMaxTemp()
    ret = BMCMessage().postSffTemp(maxtemp)
    # print ret
    if ret == False:
        log_warning("put sfp max temp fail",SYSLOG_IDENTIFIER)

def run(interval):
    index = 0
    while True:
        try:
            putDataToBmc()
            time.sleep(interval)
        except Exception as e:
            print(e)

def strtoint(str):
    value = 0
    rest_v = str.replace("0X", "").replace("0x", "")
    for index in range(len(rest_v)):
        value |= int(rest_v[index], 16) << ((len(rest_v) - index - 1) * 4)
    return value

def macreset(macledconfig):
    if  macledconfig == None:
        log_error("get param error",SYSLOG_IDENTIFIER)
    value = macledconfig.get("reset", 0)
    if value == 0:
        log_error("get reset value error",SYSLOG_IDENTIFIER)
        return False
    # try reset 6 times total
    for i in range(6):
        resetcmd = macledconfig.get("cmdwrformat","")
        if resetcmd == "":
            log_error("get resetcmd value error",SYSLOG_IDENTIFIER)
            continue
        ret , status = subprocess_os_system(resetcmd % value)
        if ret == 0:
            readRDcmd  = macledconfig.get("cmdrdformat","")
            ret_rd, status_rd = subprocess_os_system(readRDcmd)
            status_rd = status_rd.replace("\n", "")
            if ret_rd ==0:
                status_value = strtoint(status_rd)
                if strtoint(status_rd) == value:
                    # this getter == setter so return
                    return True
        continue
    return False

def runmacLed(interval):
    while True:
        try:
            ret, status = subprocess_os_system("docker ps |wc -l", 3)
            status = status.replace("\n", "")
            if ret == 0 and int(status) >= 9:
                macLedLocation = STARTMODULE.get("macledset_param", None)
                if macLedLocation == None:
                    log_error("macreset error get param none",SYSLOG_IDENTIFIER)
                else:
                    for item in macLedLocation:
                        if macreset(item) == False:
                            log_error("macreset error",SYSLOG_IDENTIFIER)
                break
            time.sleep(interval)
        except Exception as e:
            print (str(e))

@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''device operator'''
    pass

@main.command()
def start():
    interval = STARTMODULE.get("sfptempmodule_interval", 2)
    run(interval)


@main.command()
def startmacreset():
    interval = STARTMODULE.get("macledreset_interval", 2)
    # time.sleep(1)
    runmacLed(interval)

@main.command()
def stop():
    pass

if __name__ == '__main__':
    main()
