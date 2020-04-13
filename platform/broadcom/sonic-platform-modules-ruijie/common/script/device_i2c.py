#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import click
import os
import commands
import time
from ruijieconfig import *

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# wrap print() to be compatible with python2 and python3
def rprint(*args):
    print(" ".join(map(str, args)))

class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


def log_os_system(cmd):
    """Run a shell command and print its output"""
    status, output = commands.getstatusoutput(cmd)
    if status:
        rprint(output)
    return status, output


def write_sysfs_value(reg_name, value):
    """Write some value to a file on sysfs"""
    retval = 'ERR'
    mb_reg_file = "/sys/bus/i2c/devices/" + reg_name
    if (not os.path.isfile(mb_reg_file)):
        rprint(mb_reg_file, 'not found !')
        return False
    try:
        with open(mb_reg_file, 'w') as fd:
            fd.write(value)
    except Exception as error:
        return False
    return True


def check_driver():
    """Check if the rg-starting driver is exists"""
    status, output = log_os_system("lsmod | grep rg | wc -l")
    if status:
        return False
    if output.isdigit() and int(output) > 0:
        return True
    else:
        return False


def get_pid(name):
    ret = []
    for dirname in os.listdir('/proc'):
        if dirname == 'curproc':
            continue
        try:
            with open('/proc/{}/cmdline'.format(dirname), mode='rb') as fd:
                content = fd.read()
        except Exception:
            continue
        if name in content:
            ret.append(dirname)
    return ret


def start_avscontrol():
    cmd = "nohup avscontrol.py start >/dev/null 2>&1 &"
    rets = get_pid("avscontrol.py")
    if len(rets) == 0:
        os.system(cmd)
    pass


def start_fancontrol():
    if STARTMODULE['fancontrol'] == 1:
        cmd = "nohup fancontrol.py start >/dev/null 2>&1 &"
        rets = get_pid("fancontrol.py")
        if len(rets) == 0:
            os.system(cmd)


def stop_fancontrol():
    if STARTMODULE['fancontrol'] == 1:
        rets = get_pid("fancontrol.py")
        for ret in rets:
            cmd = "kill " + ret
            os.system(cmd)
        return True


def remove_dev(bus, loc):
    cmd = "echo  0x%02x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (loc, bus)
    devpath = "/sys/bus/i2c/devices/%d-%04x" % (bus, loc)
    if os.path.exists(devpath):
        log_os_system(cmd)


def add_dev(name, bus, loc):
    if name == "lm75":
        time.sleep(0.1)
    pdevpath = "/sys/bus/i2c/devices/i2c-%d/" % (bus)
    # wait 10 seconds at most until i2c bus created
    for i in range(1, 100):
        if os.path.exists(pdevpath) == True:
            break
        time.sleep(0.1)
        rprint(pdevpath, 'not found, wait 0.1 second ! i %d ' % (i))

    cmd = "echo  %s 0x%02x > /sys/bus/i2c/devices/i2c-%d/new_device" % (
        name, loc, bus)
    devpath = "/sys/bus/i2c/devices/%d-%04x" % (bus, loc)
    if os.path.exists(devpath) == False:
        os.system(cmd)


def removedevs():
    devs = GLOBALCONFIG["DEVS"]
    for index in range(len(devs) - 1, -1, -1):
        remove_dev(devs[index]["bus"], devs[index]["loc"])


def adddevs():
    devs = GLOBALCONFIG["DEVS"]
    for dev in range(0, devs.__len__()):
        add_dev(devs[dev]["name"], devs[dev]["bus"], devs[dev]["loc"])


def checksignaldriver(name):
    """Check if the driver exists"""
    modisexistcmd = "lsmod | grep %s | wc -l" % name
    status, output = log_os_system(modisexistcmd)
    if status:
        return False
    if output.isdigit() and int(output) > 0:
        return True
    else:
        return False


def adddriver(name, delay):
    cmd = "modprobe %s" % name
    if delay != 0:
        time.sleep(delay)
        rprint(name, 'sleep %d second!' % (delay))
    if checksignaldriver(name) != True:
        log_os_system(cmd)


def removedriver(name, delay):
    realname = name.lstrip().split(" ")[0]
    cmd = "rmmod -f %s" % realname
    if checksignaldriver(realname):
        log_os_system(cmd)


def removedrivers():
    if GLOBALCONFIG == None:
        click.echo("load GLOBALCONFIG error")
        return
    drivers = GLOBALCONFIG.get("DRIVERLISTS", None)
    if drivers == None:
        click.echo("load DRIVERLISTS error")
        return
    for index in range(len(drivers) - 1, -1, -1):
        delay = 0
        name = ""
        if type(drivers[index]) == dict and drivers[index].has_key("delay"):
            name = drivers[index].get("name")
            delay = drivers[index]["delay"]
        else:
            name = drivers[index]
        removedriver(name, delay)


def adddrivers():
    """Add all drivers in driver list"""
    if GLOBALCONFIG == None:
        click.echo("load GLOBALCONFIG error")
        return
    drivers = GLOBALCONFIG.get("DRIVERLISTS", None)
    if drivers == None:
        click.echo("load DRIVERLISTS error")
        return
    for index in range(0, len(drivers)):
        delay = 0
        name = ""
        if type(drivers[index]) == dict and drivers[index].has_key("delay"):
            name = drivers[index].get("name")
            delay = drivers[index]["delay"]
        else:
            name = drivers[index]
        adddriver(name, delay)


def otherinit():
    for index in GLOBALINITPARAM:
        write_sysfs_value(index["loc"], index["value"])

    for index in GLOBALINITCOMMAND:
        log_os_system(index)


def unload_driver():
    """remove everything and back to the initialization state"""
    stop_fancontrol() # fan control service
    removedevs()      # others
    removedrivers()   # drivers


def reload_driver():
    """reload everything"""
    removedevs()
    removedrivers()
    time.sleep(1)
    adddrivers()
    adddevs()


def i2c_check(bus, retrytime=6):
    try:
        i2cpath = "/sys/bus/i2c/devices/" + bus
        while retrytime and not os.path.exists(i2cpath):
            click.echo("%s not found,retrytime:%d," % (i2cpath, retrytime))
            reload_driver()
            retrytime -= 1
            time.sleep(1)
    except Exception as e:
        click.echo(str(e))
    return


def load_driver():
    adddrivers()
    adddevs()
    if STARTMODULE.get("i2ccheck", 0) == 1:  #i2c HA
        busend = i2ccheck_params.get("busend")
        retrytime = i2ccheck_params.get("retrytime")
        i2c_check(busend, retrytime)
    start_fancontrol() # start fan control service
    if STARTMODULE['avscontrol'] == 1:
        start_avscontrol()  # start avs control service
    otherinit()


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    """device operator"""
    pass


@main.command()
def start():
    """load device"""
    if check_driver():
        unload_driver()
    load_driver()
    click.echo("start")


@main.command()
def stop():
    """stop device"""
    unload_driver()
    click.echo("stop")


@main.command()
def restart():
    """restart device"""
    unload_driver()
    load_driver()
    click.echo("restart")


if __name__ == '__main__':
    main()
