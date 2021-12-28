#!/usr/bin/env python3
#
# Copyright (C) 2016 Accton Networks, Inc.
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
"""
import subprocess
import getopt
import sys
import logging
import time
import os

PROJECT_NAME = 'minipack'
version = '0.2.0'
verbose = False
DEBUG = False
args = []
ALL_DEVICE = {}

i2c_prefix = '/sys/bus/i2c/devices/'
i2c_bus = {
           'psu': ['35-0038','36-003b'],
           'sfp': ['-0050']}

NO_QSFP = 128

#For sideband signals of SFP/QSFP modules.
cpld_of_module = {'-0062': list(range(0,16)),
                  '-0064': list(range(16,32)) }


mknod =[
'echo pca9548 0x70 > /sys/bus/i2c/devices/i2c-1/new_device',
'echo 24c64 0x57 > /sys/bus/i2c/devices/i2c-1/new_device',
]

FORCE = 0



if DEBUG == True:
    print(sys.argv[0])
    print('ARGV      :', sys.argv[1:])


def main():
    global DEBUG
    global args
    global FORCE

    if len(sys.argv)<2:
        show_help()

    options, args = getopt.getopt(sys.argv[1:], 'hdf', ['help',
                                                       'debug',
                                                       'force',
                                                          ])
    if DEBUG == True:
        print(options)
        print(args)
        print(len(sys.argv))

    for opt, arg in options:
        if opt in ('-h', '--help'):
            show_help()
        elif opt in ('-d', '--debug'):
            DEBUG = True
            logging.basicConfig(filename= PROJECT_NAME+'.log', filemode='w',level=logging.DEBUG)
            logging.basicConfig(level=logging.INFO)
        elif opt in ('-f', '--force'):
            FORCE = 1
        else:
            logging.info('no option')
    for arg in args:
        if arg == 'install':
           do_install()
        elif arg == 'clean':
           do_uninstall()
        elif arg == 'api':
           do_minipack_fpga_install()
        elif arg == 'api_clean':
           do_minipack_fpga_clean()
        elif arg == 'show':
           device_traversal()
        elif arg == 'sff':
            if len(args)!=2:
                show_eeprom_help()
            elif int(args[1]) ==0 or int(args[1]) > DEVICE_NO['sfp']:
                show_eeprom_help()
            else:
                show_eeprom(args[1])
            return
        elif arg == 'set':
            if len(args)<3:
                show_set_help()
            else:
                set_device(args[1:])
            return
        else:
            show_help()


    return 0

def show_help():
    print(__doc__ % {'scriptName' : sys.argv[0].split("/")[-1]})
    sys.exit(0)

def my_log(txt):
    if DEBUG == True:
        print("[ACCTON DBG]: "+txt)
    return

def log_os_system(cmd, show):
    logging.info('Run :'+cmd)
    status = 1
    output = ""
    status, output = subprocess.getstatusoutput(cmd)
    my_log (cmd +"with result:" + str(status))
    my_log ("cmd:" + cmd)
    my_log ("      output:"+output)
    if status:
        logging.info('Failed :'+cmd)
        if show:
            print(('Failed :'+cmd))
    return  status, output

def driver_inserted():
    ret, lsmod = log_os_system("ls /sys/module/*accton*", 0)
    logging.info('mods:'+lsmod)
    if ret :
        return False
    else :
        return True



kos = [
'depmod -ae',
'modprobe i2c_dev',
'modprobe i2c_mux_pca954x force_deselect_on_exit=1',
'modprobe optoe',
'modprobe minipack_psensor']

def driver_install():
    for i in range(0,len(kos)):
        status, output = log_os_system(kos[i], 1)
        if status:
            if FORCE == 0:
                return status
    return 0

def driver_uninstall():
    for i in range(0,len(kos)):
        #remove parameter if any
        rm = kos[-(i+1)]
        lst = rm.split(" ")
        if len(lst) > 2:
            del(lst[2:])
        rm = " ".join(lst)

        #Change to removing commands
        rm = rm.replace("modprobe", "modprobe -rq")
        rm = rm.replace("insmod", "rmmod")
        status, output = log_os_system(rm, 1)
        if status:
            if FORCE == 0:
                return status
    return 0

def sfp_map(index):
    port = index + 1
    base = ((port-1)//8*8) + 10
    index = (port - 1) % 8
    index = 7 - index
    if (index%2):
        index = index -1
    else:
        index = index +1
    bus = base + index
    return bus

def device_install():
    for i in range(0,len(mknod)):
        #for pca932x need times to built new i2c buses
        if mknod[i].find('pca954') != -1:
           time.sleep(2)

        status, output = log_os_system(mknod[i], 1)
        if status:
            print(output)
            if FORCE == 0:
                return status

    rm_cmd="rm -rf /usr/local/bin/minipack_qsfp > /dev/null 2>&1"
    log_os_system(rm_cmd, 1)
    mk_cmd= "mkdir /usr/local/bin/minipack_qsfp"
    log_os_system(mk_cmd, 1)
   
    return

def device_uninstall():
    nodelist = mknod
    for i in range(len(nodelist)):
        target = nodelist[-(i+1)]
        temp = target.split()
        del temp[1]
        temp[-1] = temp[-1].replace('new_device', 'delete_device')
        status, output = log_os_system(" ".join(temp), 1)
        if status:
            print(output)
            if FORCE == 0:
                return status

    return

def system_ready():
    if driver_inserted() == False:
        return False
    if not device_exist():
        return False
    return True

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
MINIPACK_FPGA_WHL_FILE_PY3 ='minipack_platform_fpga-1.0-py3-none-any.whl'
def do_minipack_fpga_install():
    device_path = "{}{}{}{}".format(PLATFORM_ROOT_PATH, '/x86_64-accton_', PROJECT_NAME, '-r0')
    MINIPACK_FPGA_BSP_WHL_PKG_PY3 = "/".join([device_path, MINIPACK_FPGA_WHL_FILE_PY3])

    status, output = log_os_system("pip3 show minipack-platform-fpga > /dev/null 2>&1", 0)
    if status:
        if os.path.exists(MINIPACK_FPGA_BSP_WHL_PKG_PY3):
            status, output = log_os_system("pip3 install "+ MINIPACK_FPGA_BSP_WHL_PKG_PY3, 1)
            if status:
                print("Error: Failed to install {}".format(MINIPACK_FPGA_WHL_FILE_PY3))
                return status
            else:
                print("Successfully installed {} package".format(MINIPACK_FPGA_WHL_FILE_PY3))
        else:
            print('{} is not found'.format(MINIPACK_FPGA_WHL_FILE_PY3))
    else:
        print('{} has installed'.format(MINIPACK_FPGA_WHL_FILE_PY3))

    return

def do_minipack_fpga_clean():
    status, output = log_os_system("pip3 show minipack-platform-fpga > /dev/null 2>&1", 0)
    if status:
        print('{} does not install, not need to uninstall'.format(MINIPACK_FPGA_WHL_FILE_PY3))

    else:
        status, output = log_os_system("pip3 uninstall minipack-platform-fpga -y", 0)
        if status:
            print('Error: Failed to uninstall {}'.format(MINIPACK_FPGA_WHL_FILE_PY3))
            return status
        else:
            print('{} is uninstalled'.format(MINIPACK_FPGA_WHL_FILE_PY3))

    return

def do_install():
    print("Checking system....")
    if driver_inserted() == False:
        print("No driver, installing....")
        status = driver_install()
        if status:
            if FORCE == 0:
                return  status
    else:
        print(PROJECT_NAME.upper()+" drivers detected....")
    if not device_exist():
        print("No device, installing....")
        status = device_install()
        if status:
            if FORCE == 0:
                return  status
    else:
        print( PROJECT_NAME.upper()+" devices detected....")

    do_minipack_fpga_install()
    return

def do_uninstall():
    print("Checking system....")
    if not device_exist():
        print(PROJECT_NAME.upper() +" has no device installed....")
    else:
        print("Removing device....")
        status = device_uninstall()
        if status:
            if FORCE == 0:
                return  status

    if driver_inserted()== False :
        print(PROJECT_NAME.upper() +" has no driver installed....")
    else:
        print("Removing installed driver....")
        status = driver_uninstall()
        if status:
            if FORCE == 0:
                return  status

    do_minipack_fpga_clean()
    return


def device_exist():
    ret1, log = log_os_system("ls "+i2c_prefix+"*0070", 0)
    ret2, log = log_os_system("ls "+i2c_prefix+"i2c-2", 0)
    return not(ret1 or ret2)

if __name__ == "__main__":
    main()
