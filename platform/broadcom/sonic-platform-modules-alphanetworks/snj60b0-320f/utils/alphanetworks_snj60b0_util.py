#!/usr/bin/env python
#
# Copyright (C) 2019 Alphanetworks Technology Corporation.
# Robin Chen <Robin_chen@Alphanetworks.com>
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# any later version. 
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details. 
# see <http://www.gnu.org/licenses/>
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

import commands
import sys, getopt
import logging
import time


PROJECT_NAME = 'snj60b0-320f'
DRIVER_NAME = 'snj60b0_320f'
device_path = "x86_64-alphanetworks_snj60b0_320f-r0"
version = '0.1.0'
verbose = False
DEBUG = False
args = []
FORCE = 0

devMaxPort = 34
cpldPortNum = 8

FPGAAddr = "005e"
PortCPLD_Addr = "005f"

portFPGAAddr = "0x5e"
portCPLDAddr = "0x5f"
portAddr = "0x50"

if DEBUG == True:
    print sys.argv[0]
    print 'ARGV      :', sys.argv[1:]   


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
        print options
        print args
        print len(sys.argv)
            
    for opt, arg in options:
        if opt in ('-h', '--help'):
            show_help()
        elif opt in ('-d', '--debug'):            
            DEBUG = True
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
        else:
            show_help()
            
            
    return 0              
        
def show_help():
    print __doc__ % {'scriptName' : sys.argv[0].split("/")[-1]}
    sys.exit(0)

def show_log(txt):
    if DEBUG == True:
        print PROJECT_NAME.upper()+": "+txt
    return

def log_os_system(cmd, show):
    logging.info('Run :'+cmd)  
    status, output = commands.getstatusoutput(cmd)    
    show_log (cmd +" with result: " + str(status))
    show_log ("      output:"+output)
    if status:
        logging.info('Failed :'+cmd)
        if show:
            print('Failed :'+cmd)
    return  status, output
            
def driver_check():
    ret, lsmod = log_os_system("lsmod | grep " + DRIVER_NAME, 0)
    logging.info('mods:'+lsmod)
    if len(lsmod) ==0:
        return False   
    return True



kos = [
'modprobe i2c_ismt',
'modprobe i2c_i801',
'modprobe i2c_dev',
'modprobe i2c_mux_pca954x',
'modprobe optoe',
'modprobe yesm1300am',
'modprobe '+PROJECT_NAME+'_fpga'  ,
'modprobe '+PROJECT_NAME+'_onie_eeprom' ,
'modprobe '+PROJECT_NAME+'_sfp' ]

def driver_install():
    global FORCE
    status, output = log_os_system("depmod", 1)
    if status:
        if FORCE == 0:
            return status
    for i in range(0,len(kos)):
        if kos[i].find('pca954') != -1:
            status, output = log_os_system(kos[i]+ " force_deselect_on_exit=1", 1)
        else:
            status, output = log_os_system(kos[i], 1)
        if status:
            if FORCE == 0:
                return status              
    return 0
    
def driver_uninstall():
    global FORCE
    for i in range(0,len(kos)):
        rm = kos[-(i+1)].replace("modprobe", "modprobe -rq")
        rm = rm.replace("insmod", "rmmod")
        status, output = log_os_system(rm, 1)
        if status:
            if FORCE == 0:
                return status              
    return 0

i2c_prefix = '/sys/bus/i2c/devices/'
                   
sfp_map = [13,14,15,16,12,11]
sfp_map2 = [14,15,16,17,13,12]

mknod =[
'echo pca9548 0x70 > /sys/bus/i2c/devices/i2c-0/new_device',
'echo pca9545 0x71 > /sys/bus/i2c/devices/i2c-5/new_device',
'echo pca9548 0x72 > /sys/bus/i2c/devices/i2c-7/new_device',
'echo pca9548 0x73 > /sys/bus/i2c/devices/i2c-20/new_device',
'echo 24c02 0x50 > /sys/bus/i2c/devices/i2c-9/new_device',
'echo 24c02 0x51 > /sys/bus/i2c/devices/i2c-10/new_device',
'echo snj60b0_onie_eeprom 0x56 > /sys/bus/i2c/devices/i2c-0/new_device',
'echo snj60b0_fpga 0x5e > /sys/bus/i2c/devices/i2c-0/new_device',
'echo lm75 0x4D > /sys/bus/i2c/devices/i2c-3/new_device',
'echo lm75 0x4C > /sys/bus/i2c/devices/i2c-4/new_device',
'echo lm75 0x4F > /sys/bus/i2c/devices/i2c-0/new_device',
'echo yesm1300am 0x58 > /sys/bus/i2c/devices/i2c-9/new_device',
'echo yesm1300am 0x59 > /sys/bus/i2c/devices/i2c-10/new_device' ]

mknod2 =[
'echo pca9548 0x70 > /sys/bus/i2c/devices/i2c-1/new_device',
'echo pca9545 0x71 > /sys/bus/i2c/devices/i2c-6/new_device',
'echo pca9548 0x72 > /sys/bus/i2c/devices/i2c-8/new_device',
'echo pca9548 0x73 > /sys/bus/i2c/devices/i2c-21/new_device',
'echo 24c02 0x50 > /sys/bus/i2c/devices/i2c-10/new_device',
'echo 24c02 0x51 > /sys/bus/i2c/devices/i2c-11/new_device',
'echo snj60b0_onie_eeprom 0x56 > /sys/bus/i2c/devices/i2c-1/new_device',
'echo snj60b0_fpga 0x5e > /sys/bus/i2c/devices/i2c-1/new_device',
'echo lm75 0x4D > /sys/bus/i2c/devices/i2c-4/new_device',
'echo lm75 0x4C > /sys/bus/i2c/devices/i2c-5/new_device',
'echo lm75 0x4F > /sys/bus/i2c/devices/i2c-1/new_device',
'echo yesm1300am 0x58 > /sys/bus/i2c/devices/i2c-10/new_device',
'echo yesm1300am 0x59 > /sys/bus/i2c/devices/i2c-11/new_device' ]


       
def i2c_order_check():    
    # i2c bus 0 and 1 might be installed in different order.
    # Here check if 0x76 is exist @ i2c-0

    status, output = log_os_system("i2cdetect -l | grep I801 | grep i2c-0", 0)
    if  not output:
        order = 1
        tmp = "sed -i 's/0-/1-/g' /usr/share/sonic/device/"+device_path+"/plugins/led_control.py"
    else:
        order = 0
        tmp = "sed -i 's/1-/0-/g' /usr/share/sonic/device/"+device_path+"/plugins/led_control.py"
    status, output = log_os_system(tmp, 0)
    if status:
        print output
        if FORCE == 0:
            return status
    return order
                     
def device_install():
    global FORCE
    global devMaxPort
    global cpldPortNum

    order = i2c_order_check()
                
    # if 0x76 is not exist @i2c-0, use reversed bus order    
    if order:       
        for i in range(0,len(mknod2)):
            #for pca954x need times to built new i2c buses            
            if mknod2[i].find('pca954') != -1:
               time.sleep(1)         
               
            if mknod2[i].find('lm75') != -1:
               time.sleep(1)
         
            status, output = log_os_system(mknod2[i], 1)
            if status:
                print output
                if FORCE == 0:
                    return status
        status, output =log_os_system("echo 0 > /sys/bus/i2c/devices/1-"+FPGAAddr+"/sys_reset1", 1)
	if status:
	    print output
	    if FORCE == 0:
	        return status

        status, output =log_os_system("echo 4 > /sys/bus/i2c/devices/1-"+FPGAAddr+"/sys_reset2", 1)
	if status:
	    print output
	    if FORCE == 0:
	        return status			
    else:
        for i in range(0,len(mknod)):
            #for pca954x need times to built new i2c buses            
            if mknod[i].find('pca954') != -1:
               time.sleep(1)         
               
            if mknod[i].find('lm75') != -1:
               time.sleep(1)
         
            status, output = log_os_system(mknod[i], 1)
            if status:
                print output
                if FORCE == 0:
                    return status
        status, output =log_os_system("echo 0 > /sys/bus/i2c/devices/0-"+FPGAAddr+"/sys_reset1", 1)
    	if status:
    	    print output
    	    if FORCE == 0:
    	        return status

        status, output =log_os_system("echo 4 > /sys/bus/i2c/devices/0-"+FPGAAddr+"/sys_reset2", 1)
        if status:
    	    print output
    	    if FORCE == 0:
    	        return status

    for i in range(0, devMaxPort):
        index = i / cpldPortNum
        port = i % cpldPortNum
        reg_sfp = 0
        if port == 0:
            reg_sfp = 1

# Port CPLD and FPGA device add
        if reg_sfp == 1:
            if i < 32:
                if order:
                    status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portCPLDAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map2[index])+"/new_device", 1)
                else:
                    status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portCPLDAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map[index])+"/new_device", 1)
                if status:
                    print output
                    if FORCE == 0:
                        return status
# Front port EEPROM device add
                if order:
                    status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map2[index])+"/new_device", 1)
                else:
                    status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map[index])+"/new_device", 1)
                if status:
                    print output
                    if FORCE == 0:
                        return status

# Port EEPROM device add
        if i == 32:
            if order:
                status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map2[index])+"/new_device", 1)
            else:
                status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map[index])+"/new_device", 1)

            if status:
                print output
                if FORCE == 0:
                    return status
        if i == 33:
            if order:
                status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map2[index+1])+"/new_device", 1)
            else:
                status, output =log_os_system("echo sfpcpld"+str(i+1)+" "+portAddr+" > /sys/bus/i2c/devices/i2c-"+str(sfp_map[index+1])+"/new_device", 1)
            if status:
                print output
                if FORCE == 0:
                    return status
# Front port LED enable
    if order:
        status, output =log_os_system("echo 0 > /sys/bus/i2c/devices/1-"+FPGAAddr+"/port_led_disable", 1)
    else:
        status, output =log_os_system("echo 0 > /sys/bus/i2c/devices/0-"+FPGAAddr+"/port_led_disable", 1)
    if status:
        print output
        if FORCE == 0:
            return status

    if order:
        for i in [0,1,2,3]:
            status, output =log_os_system("echo 0 > /sys/bus/i2c/devices/"+str(sfp_map2[i])+"-"+PortCPLD_Addr+"/sfp_led_disable", 1)
            if status:
                if FORCE == 0:
                    return status
    else:
        for i in [0,1,2,3]:
            status, output =log_os_system("echo 0 > /sys/bus/i2c/devices/"+str(sfp_map[i])+"-"+PortCPLD_Addr+"/sfp_led_disable", 1)
            if status:
                if FORCE == 0:
                    return status
# end of Front port LED enable

    return 
    
def device_uninstall():
    global FORCE
    
    status, output =log_os_system("ls /sys/bus/i2c/devices/1-0070", 0)
    if status==0:
        I2C_ORDER=1
    else:
        I2C_ORDER=0                    

# Front port LED disable
    if I2C_ORDER:
        status, output =log_os_system("echo 1 > /sys/bus/i2c/devices/1-"+FPGAAddr+"/port_led_disable", 1)
    else:
        status, output =log_os_system("echo 1 > /sys/bus/i2c/devices/0-"+FPGAAddr+"/port_led_disable", 1)
    if status:
        print output
        if FORCE == 0:
            return status

    if I2C_ORDER:
        for i in [0,1,2,3]:
            status, output =log_os_system("echo 1 > /sys/bus/i2c/devices/"+str(sfp_map2[i])+"-"+PortCPLD_Addr+"/sfp_led_disable", 1)
            if status:
                if FORCE == 0:
                    return status
    else:
        for i in [0,1,2,3]:
            status, output =log_os_system("echo 1 > /sys/bus/i2c/devices/"+str(sfp_map[i])+"-"+PortCPLD_Addr+"/sfp_led_disable", 1)
            if status:
                if FORCE == 0:
                    return status
# end of Front port LED disable


    for i in range(0, devMaxPort):
        index = i / cpldPortNum
        port = i % cpldPortNum
        reg_sfp = 0
        if port == 0:
            reg_sfp = 1

        if reg_sfp == 1:
            if i < 32:
                if I2C_ORDER:
                    target = "/sys/bus/i2c/devices/i2c-"+str(sfp_map2[index])+"/delete_device"
                else:
                    target = "/sys/bus/i2c/devices/i2c-"+str(sfp_map[index])+"/delete_device"
                status, output =log_os_system("echo "+portCPLDAddr+" > "+ target, 1)
                if status:
                    print output
                    if FORCE == 0:
                        return status

                if I2C_ORDER:
                    target = "/sys/bus/i2c/devices/i2c-"+str(sfp_map2[index])+"/delete_device"
                else:
                    target = "/sys/bus/i2c/devices/i2c-"+str(sfp_map[index])+"/delete_device"
                status, output =log_os_system("echo "+portAddr+" > "+ target, 1)
                if status:
                    print output
                    if FORCE == 0:
                        return status

        if i == 32:
            if I2C_ORDER:
                status, output =log_os_system("echo 0x50 > /sys/bus/i2c/devices/i2c-"+str(sfp_map2[index])+"/delete_device", 1)
            else:
                status, output =log_os_system("echo 0x50 > /sys/bus/i2c/devices/i2c-"+str(sfp_map[index])+"/delete_device", 1)
            if status:
                print output
                if FORCE == 0:
                    return status
        if i == 33:
            if I2C_ORDER:
                status, output =log_os_system("echo 0x50 > /sys/bus/i2c/devices/i2c-"+str(sfp_map2[index+1])+"/delete_device", 1)
            else:
                status, output =log_os_system("echo 0x50 > /sys/bus/i2c/devices/i2c-"+str(sfp_map[index+1])+"/delete_device", 1)
            if status:
                print output
                if FORCE == 0:
                    return status

    if I2C_ORDER:
        nodelist = mknod2
    else:            
        nodelist = mknod

    for i in range(len(nodelist)):
        target = nodelist[-(i+1)]
        temp = target.split()
        del temp[1]
        temp[-1] = temp[-1].replace('new_device', 'delete_device')
        status, output = log_os_system(" ".join(temp), 1)
        if status:
            print output
            if FORCE == 0:
                return status  
                                  
    return 
        
def system_ready():
    if driver_check() == False:
        return False
    if not device_exist(): 
        return False
    return True
               
def do_install():
    print "Checking system...."
    if driver_check() == False:
        print "No driver, installing...."    
        status = driver_install()
        if status:
            if FORCE == 0:
                return  status
    else:
        print PROJECT_NAME.upper()+" drivers detected...."                      
    if not device_exist():
        print "No device, installing...."     
        status = device_install() 
        if status:
            if FORCE == 0:
                return  status        
    else:
        print PROJECT_NAME.upper()+" devices detected...."           
    return
    
def do_uninstall():
    print "Checking system...."
    if not device_exist():
        print PROJECT_NAME.upper() +" has no device installed...."         
    else:
        print "Removing device...."     
        status = device_uninstall() 
        if status:
            if FORCE == 0:
                return  status  
                
    if driver_check()== False :
        print PROJECT_NAME.upper() +" has no driver installed...."
    else:
        print "Removing installed driver...."
        status = driver_uninstall()
        if status:
            if FORCE == 0:
                return  status                          
                    
    return       

def device_exist():
    ret1, log = log_os_system("ls "+i2c_prefix+"*0070", 0)
    ret2, log = log_os_system("ls "+i2c_prefix+"i2c-2", 0)
    return not(ret1 or ret2)

if __name__ == "__main__":
    main()
