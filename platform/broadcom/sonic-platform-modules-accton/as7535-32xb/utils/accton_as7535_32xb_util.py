#!/usr/bin/env python3
#
# Copyright (C) 2019 Accton Networks, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Usage: %(scriptName)s [options] command object

options:
    -h | --help     : this help message
    -d | --debug    : run with debug mode
    -f | --force    : ignore error during installation or clean
command:
    install     : install drivers and generate related sysfs nodes
    clean       : uninstall drivers and remove related sysfs nodes
    show        : show all systen status
    sff         : dump SFP eeprom
    set         : change board setting with fan|led|sfp
"""

import subprocess
import getopt
import sys
import logging
import time
import os

PROJECT_NAME = 'as7535_32xb'
DEBUG = False
ARGS = []
FORCE = 0

def main():
    global DEBUG
    global ARGS
    global FORCE

    if len(sys.argv) < 2:
        return 0

    (options, ARGS) = getopt.getopt(sys.argv[1:], 'hdf',
                                ['help','debug', 'force'])
    if DEBUG == True:
        print(options)
        print(ARGS)
        print(len(sys.argv))

    for arg in ARGS:
        if arg == 'install':
            do_install()
        elif arg == 'clean':
            do_uninstall()
        elif arg == 'api':
           do_sonic_platform_install()
        elif arg == 'api_clean':
           do_sonic_platform_clean()
    return 0


def log_os_system(cmd, show):
    logging.info('Run :' + cmd)
    status, output = subprocess.getstatusoutput(cmd)
    if status:
        logging.info('Failed :' + cmd)
        if show:
            print('Failed :' + cmd)
    return (status, output)


def driver_check():
    ret, lsmod = log_os_system("ls /sys/module/*accton*", 0)
    logging.info('mods:'+lsmod)
    if ret :
        return False
    else :
        return True

ipmi_ko = [
'modprobe ipmi_msghandler',
'modprobe ipmi_ssif',
'modprobe ipmi_si',
'modprobe ipmi_devintf',
]

ATTEMPTS = 5

def init_ipmi_dev_intf():
    attempts = ATTEMPTS
    interval = 3

    while attempts:
        for i in range(0, len(ipmi_ko)):
            subprocess.getstatusoutput(ipmi_ko[i])

        if os.path.exists('/dev/ipmi0') or os.path.exists('/dev/ipmidev/0'):
            return (0, (ATTEMPTS - attempts) * interval)

        for i in reversed(range(0, len(ipmi_ko))):
            rm = ipmi_ko[i].replace("modprobe", "modprobe -rq")
            subprocess.getstatusoutput(rm)

        attempts -= 1
        time.sleep(interval)

    return (1, ATTEMPTS * interval)

def init_ipmi_oem_cmd():
    attempts = ATTEMPTS
    interval = 3

    while attempts:
        status, output = subprocess.getstatusoutput('ipmitool raw 0x34 0x95')
        if status:
            attempts -= 1
            time.sleep(interval)
            continue

        return (0, (ATTEMPTS - attempts) * interval)

    return (1, ATTEMPTS * interval)

def init_ipmi():
    attempts = ATTEMPTS
    interval = 60

    while attempts:
        attempts -= 1

        (status, elapsed_dev) = init_ipmi_dev_intf()
        if status:
            time.sleep(interval - elapsed_dev)
            continue

        (status, elapsed_oem) = init_ipmi_oem_cmd()
        if status:
            time.sleep(interval - elapsed_dev - elapsed_oem)
            continue

        print('IPMI dev interface is ready.')
        return 0

    print('Failed to initialize IPMI dev interface')
    return 1

kos = [
'depmod -ae',
'modprobe i2c_dev',
'modprobe i2c_mux_pca954x force_deselect_on_exit=1',
'modprobe x86-64-accton-as7535-32xb-cpld',
'modprobe x86-64-accton-as7535-32xb-fan',
'modprobe x86-64-accton-as7535-32xb-thermal',
'modprobe x86-64-accton-as7535-32xb-leds',
'modprobe x86-64-accton-as7535-32xb-psu',
'modprobe optoe']

def driver_install():
    global FORCE

    status = init_ipmi()
    if status:
        if FORCE == 0:
            return status

    for i in range(0,len(kos)):
        status, output = log_os_system(kos[i], 1)
        if status:
            if FORCE == 0:
                return status
    return 0

def driver_uninstall():
    global FORCE
    for i in reversed(range(0,len(kos))):
        rm = kos[i].replace("modprobe", "modprobe -rq")
        rm = rm.replace("insmod", "rmmod")
        lst = rm.split(" ")
        if len(lst) > 3:
            del(lst[3])
        rm = " ".join(lst)
        status, output = log_os_system(rm, 1)
        if status:
            if FORCE == 0:
                return status
    return 0

i2c_prefix = '/sys/bus/i2c/devices/'
sfp_map =  [25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
            35, 36, 37, 38, 39, 40, 41, 42, 43, 44,
            45, 46, 47, 48, 49, 50, 23, 21, 24, 22]

mknod =[
'echo 24c02 0x57 > /sys/bus/i2c/devices/i2c-0/new_device',
'echo pca9548 0x77 > /sys/bus/i2c/devices/i2c-0/new_device',
'echo pca9548 0x76 > /sys/bus/i2c/devices/i2c-1/new_device',
'echo pca9548 0x73 > /sys/bus/i2c/devices/i2c-9/new_device',
'echo pca9548 0x74 > /sys/bus/i2c/devices/i2c-17/new_device',
'echo pca9548 0x74 > /sys/bus/i2c/devices/i2c-18/new_device',
'echo pca9548 0x74 > /sys/bus/i2c/devices/i2c-19/new_device',
'echo pca9548 0x74 > /sys/bus/i2c/devices/i2c-20/new_device',
'echo as7535_32xb_fpga 0x60 > /sys/bus/i2c/devices/i2c-11/new_device',
'echo as7535_32xb_cpld1 0x61 > /sys/bus/i2c/devices/i2c-12/new_device',
]

def device_install():
    global FORCE

    for i in range(0, len(mknod)):
        (status, output) = log_os_system(mknod[i], 1)
        if status:
            print(output)
            if FORCE == 0:
                return status

        # for pca954x need times to built new i2c buses
        if mknod[i].find('pca954') != -1:
            time.sleep(2)

    for i in range(27, 31):
        status, output =log_os_system("echo 0 > /sys/bus/i2c/devices/12-0061/module_reset_"+str(i), 1)
        if status:
            print(output)
            if FORCE == 0:
                return status

    for i in range(0,len(sfp_map)):
        status
        output

        if (i <= 25):
            status, output =log_os_system("echo optoe2 0x50 > /sys/bus/i2c/devices/i2c-"+str(sfp_map[i])+"/new_device", 1)
        else:
            status, output =log_os_system("echo optoe1 0x50 > /sys/bus/i2c/devices/i2c-"+str(sfp_map[i])+"/new_device", 1)

        if status:
            print(output)
            if FORCE == 0:
                return status

        path = "/sys/bus/i2c/devices/{0}-0050/port_name"
        status, output =log_os_system("echo port{0} > ".format(i+1)+path.format(sfp_map[i]), 1)
        if status:
            print(output)
            if FORCE == 0:
                return status
    return

def device_uninstall():
    global FORCE

    for i in range(0, len(sfp_map)):
        target = '/sys/bus/i2c/devices/i2c-' + str(sfp_map[i]) \
            + '/delete_device'
        (status, output) = log_os_system('echo 0x50 > ' + target, 1)
        if status:
            print(output)
            if FORCE == 0:
                return status
    nodelist = mknod

    for i in range(len(nodelist)):
        target = nodelist[-(i + 1)]
        temp = target.split()
        del temp[1]
        temp[-1] = temp[-1].replace('new_device', 'delete_device')
        (status, output) = log_os_system(' '.join(temp), 1)
        if status:
            print(output)
            if FORCE == 0:
                return status

    return

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_API2_WHL_FILE_PY3 ='sonic_platform-1.0-py3-none-any.whl'
def do_sonic_platform_install():
    device_path = "{}{}{}{}".format(PLATFORM_ROOT_PATH, '/x86_64-accton_', PROJECT_NAME, '-r0')
    SONIC_PLATFORM_BSP_WHL_PKG_PY3 = "/".join([device_path, PLATFORM_API2_WHL_FILE_PY3])

    #Check API2.0 on py whl file
    status, output = log_os_system("pip3 show sonic-platform > /dev/null 2>&1", 0)
    if status:
        if os.path.exists(SONIC_PLATFORM_BSP_WHL_PKG_PY3):
            status, output = log_os_system("pip3 install "+ SONIC_PLATFORM_BSP_WHL_PKG_PY3, 1)
            if status:
                print("Error: Failed to install {}".format(PLATFORM_API2_WHL_FILE_PY3))
                return status
            else:
                print("Successfully installed {} package".format(PLATFORM_API2_WHL_FILE_PY3))
        else:
            print('{} is not found'.format(PLATFORM_API2_WHL_FILE_PY3))
    else:
        print('{} has installed'.format(PLATFORM_API2_WHL_FILE_PY3))

def do_sonic_platform_clean():
    status, output = log_os_system("pip3 show sonic-platform > /dev/null 2>&1", 0)
    if status:
        print('{} does not install, not need to uninstall'.format(PLATFORM_API2_WHL_FILE_PY3))

    else:
        status, output = log_os_system("pip3 uninstall sonic-platform -y", 0)
        if status:
            print('Error: Failed to uninstall {}'.format(PLATFORM_API2_WHL_FILE_PY3))
            return status
        else:
            print('{} is uninstalled'.format(PLATFORM_API2_WHL_FILE_PY3))

    return

def do_install():
    print('Checking system....')
    if driver_check() is False:
        print('No driver, installing....')
        status = driver_install()
        if status:
            if FORCE == 0:
                return status
    else:
        print(PROJECT_NAME.upper() + ' drivers detected....')

    if not device_exist():
        print('No device, installing....')
        status = device_install()
        if status:
            if FORCE == 0:
                return status
    else:
        print(PROJECT_NAME.upper() + ' devices detected....')

    do_sonic_platform_install()

    return

def do_uninstall():
    print('Checking system....')
    if not device_exist():
        print(PROJECT_NAME.upper() + ' has no device installed....')
    else:
        print('Removing device....')
        status = device_uninstall()
        if status and FORCE == 0:
            return status

    if driver_check() is False:
        print(PROJECT_NAME.upper() + ' has no driver installed....')
    else:
        print('Removing installed driver....')
        status = driver_uninstall()
        if status and FORCE == 0:
            return status

    do_sonic_platform_clean()

    return None

def device_exist():
    ret1 = log_os_system('ls ' + i2c_prefix + '*0077', 0)
    ret2 = log_os_system('ls ' + i2c_prefix + 'i2c-2', 0)
    return not (ret1[0] or ret2[0])


if __name__ == '__main__':
    main()
