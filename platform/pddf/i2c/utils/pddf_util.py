#!/usr/bin/env python


"""
Usage: %(scriptName)s [options] command object

options:
    -h | --help     : this help message
    -d | --debug    : run with debug mode
    -f | --force    : ignore error during installation or clean
command:
    install     : install drivers and generate related sysfs nodes
    clean       : uninstall drivers and remove related sysfs nodes
    switch-pddf     : switch to pddf mode, installing pddf drivers and generating sysfs nodes
    switch-nonpddf  : switch to per platform, non-pddf mode
"""

import os
import commands
import sys, getopt
import logging
import re
import subprocess
import shutil
import time
import json
import pddfparse
from collections import namedtuple

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'

PROJECT_NAME = 'PDDF'
version = '1.1'
verbose = False
DEBUG = False
args = []
ALL_DEVICE = {}               
FORCE = 0

# Instantiate the class pddf_obj 
pddf_obj = pddfparse.PddfParse()
try:
    import pddf_switch_svc
except ImportError:
    print "Unable to find pddf_switch_svc.py. PDDF might not be supported on this platform"
    sys.exit()



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
        elif arg == 'switch-pddf':
            do_switch_pddf()
        elif arg == 'switch-nonpddf':
            do_switch_nonpddf()
        else:
            show_help()
            
    return 0              
        
def show_help():
    print __doc__ % {'scriptName' : sys.argv[0].split("/")[-1]}
    sys.exit(0)

def my_log(txt):
    if DEBUG == True:
        print "[PDDF]"+txt    
    return
    
def log_os_system(cmd, show):
    logging.info('Run :'+cmd)  
    status, output = commands.getstatusoutput(cmd)    
    my_log (cmd +"with result:" + str(status))
    my_log ("      output:"+output)    
    if status:
        logging.info('Failed :'+cmd)
        if show:
            print('Failed :'+cmd)
    return  status, output
            
def driver_check():
    ret, lsmod = log_os_system("lsmod| grep pddf", 0)
    logging.info('mods:'+lsmod)
    if len(lsmod) ==0:
        return False   
    return True

kos = [
'modprobe i2c-ismt',
'modprobe i2c-i801',
'modprobe i2c_dev',
'modprobe i2c_mux_pca954x force_deselect_on_exit=1',
'modprobe pddf_client_module'  ,
'modprobe optoe'      ,
'modprobe pddf_cpld_module'  ,
'modprobe pddf_xcvr_module',
'modprobe pddf_mux_module'  ,
'modprobe pddf_cpld_driver' ,
'modprobe pddf_xcvr_driver_module' ,
'modprobe pddf_psu_driver_module' ,
'modprobe pddf_psu_module' ,
'modprobe pddf_fan_driver_module' ,
#'modprobe -f platform_pddf_fan' ,
'modprobe pddf_fan_module' ,
'modprobe pddf_led_module' ,
'modprobe pddf_sysstatus_module'
]

devs = []

# Returns platform and HW SKU
def get_platform_and_hwsku():
    try:
        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-H', '-v', PLATFORM_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        platform = stdout.rstrip('\n')

        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-d', '-v', HWSKU_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        hwsku = stdout.rstrip('\n')
    except OSError, e:
        raise OSError("Cannot detect platform")

    return (platform, hwsku)

def get_path_to_device():
    # Get platform and hwsku
    (platform, hwsku) = get_platform_and_hwsku()

    # Load platform module from source
    platform_path = "/".join([PLATFORM_ROOT_PATH, platform])
    hwsku_path = "/".join([platform_path, hwsku])

    return platform_path

def get_path_to_pddf_plugin():
    pddf_path = "/".join([PLATFORM_ROOT_PATH, "pddf/plugins"])
    return pddf_path

def config_pddf_utils():
    device_path = get_path_to_device()
    device_plugin_path = "/".join([device_path, "plugins"])
    pddf_path = get_path_to_pddf_plugin()
    backup_path = "/".join([device_plugin_path, "orig"])

    if os.path.exists(backup_path) is False:
        os.mkdir(backup_path)
        log_os_system("mv "+device_plugin_path+"/*.*"+" "+backup_path, 0)
    
    for item in os.listdir(pddf_path):
        shutil.copy(pddf_path+"/"+item, device_plugin_path+"/"+item)
    
    shutil.copy('/usr/local/bin/pddfparse.py', device_plugin_path+"/pddfparse.py")
    # Take a backup of orig fancontrol
    if os.path.exists(device_path+"/fancontrol"):
        log_os_system("mv "+device_path+"/fancontrol"+" "+device_path+"/fancontrol.bak", 0)
        #print "***Created fancotnrol.bak"
    
    # Create a link to fancontrol of PDDF
    if os.path.exists(device_path+"/pddf/fancontrol") and not os.path.exists(device_path+"/fancontrol"):
        shutil.copy(device_path+"/pddf/fancontrol",device_path+"/fancontrol")
        #print "*** Copied the pddf fancontrol file "

    return 0

def cleanup_pddf_utils():
    device_path = get_path_to_device()
    device_plugin_path = "/".join([device_path, "plugins"])

    backup_path = "/".join([device_plugin_path, "orig"])
    if os.path.exists(backup_path) is True:
        for item in os.listdir(device_plugin_path):
            if os.path.isdir(device_plugin_path+"/"+item) is False:
                os.remove(device_plugin_path+"/"+item)

        status = log_os_system("mv "+backup_path+"/*"+" "+device_plugin_path, 1)
        os.rmdir(backup_path)
    else:
        print "\nERR: Unable to locate original device files...\n"

    if os.path.exists(device_path+"/fancontrol"):
        os.remove(device_path+"/fancontrol")
        #print "Removed the fancontrol"

    if os.path.exists(device_path+"/fancontrol.bak"):
        log_os_system("mv "+device_path+"/fancontrol.bak"+" "+device_path+"/fancontrol", 0)
        #print "***Moved fancotnrol.bak to fancontrol"

    return 0

def create_pddf_log_files():
    if not os.path.exists('/var/log/pddf'):
    	log_os_system("sudo mkdir /var/log/pddf", 1)

    log_os_system("sudo touch /var/log/pddf/led.txt", 1)
    log_os_system("sudo touch /var/log/pddf/psu.txt", 1)
    log_os_system("sudo touch /var/log/pddf/fan.txt", 1)
    log_os_system("sudo touch /var/log/pddf/xcvr.txt", 1)
    log_os_system("sudo touch /var/log/pddf/sysstatus.txt", 1)
    log_os_system("sudo touch /var/log/pddf/cpld.txt", 1)
    log_os_system("sudo touch /var/log/pddf/client.txt", 1)
    log_os_system("sudo touch /var/log/pddf/mux.txt", 1)

def driver_install():
    global FORCE
    status, output = log_os_system("depmod", 1)
    for i in range(0,len(kos)):
        status, output = log_os_system(kos[i], 1)
        if status:
            if FORCE == 0:        
                return status       

    output = config_pddf_utils()

    return 0
    
def driver_uninstall():
    global FORCE

    status = cleanup_pddf_utils()

    for i in range(0,len(kos)):
        rm = kos[-(i+1)].replace("modprobe", "modprobe -rq")
        rm = rm.replace("insmod", "rmmod")        
        status, output = log_os_system(rm, 1)
        if status:
            if FORCE == 0:        
                return status              
    return 0

def device_install():
    global FORCE
    # trigger the pddf_obj script for FAN, PSU, CPLD, MUX, etc
    status = pddf_obj.create_pddf_devices()
    if status:
        if FORCE == 0:
            return status
    return

def device_uninstall():
    global FORCE
    # Trigger the paloparse script for deletion of FAN, PSU, OPTICS, CPLD clients
    status = pddf_obj.delete_pddf_devices()
    if status:
        if FORCE == 0:
            return status
    return 
        
def do_install():
    print "Checking system...."
    if not os.path.exists('/usr/share/sonic/platform/pddf_support'):
        print PROJECT_NAME.upper() +" mode is not enabled"
        return

    if driver_check()== False :
        print PROJECT_NAME.upper() +" has no PDDF driver installed...."
    	create_pddf_log_files()
        print "Installing...."    
        status = driver_install()
        if status:
            return  status
    else:
        print PROJECT_NAME.upper() +" drivers detected...."

    print "Creating devices ..." 
    status = device_install()
    if status:
        return status

    return
    
def do_uninstall():
    print "Checking system...."
    if not os.path.exists('/usr/share/sonic/platform/pddf_support'):
        print PROJECT_NAME.upper() +" mode is not enabled"
        return


    if os.path.exists('/var/log/pddf'):
	print "Remove pddf log files....."
    	log_os_system("sudo rm -rf /var/log/pddf", 1)

    print "Remove all the devices..."
    status = device_uninstall()
    if status:
        return status


    if driver_check()== False :
        print PROJECT_NAME.upper() +" has no PDDF driver installed...."
    else:
        print "Removing installed driver...."
        status = driver_uninstall()
        if status:
            if FORCE == 0:        
                return  status                          
    return       

def do_switch_pddf():
    print "Check the pddf support..."
    status = pddf_switch_svc.check_pddf_support()
    if not status:
        print "PDDF is not supported on this platform"
        return status


    print "Checking system...."
    if os.path.exists('/usr/share/sonic/platform/pddf_support'):
        print PROJECT_NAME.upper() +" system is already in pddf mode...."
    else:
        print "Stopping the pmon service ..."
        status, output = log_os_system("systemctl stop pmon.service", 1)
        if status:
            if FORCE==0:
                return status

        print "Stopping the platform services.."
        status = pddf_switch_svc.stop_platform_svc()
        if not status:
            if FORCE==0:
                return status

        print "Creating the pddf_support file..."
        if os.path.exists('/usr/share/sonic/platform'):
            status, output = log_os_system("touch /usr/share/sonic/platform/pddf_support", 1)
        else:
            print "/usr/share/sonic/platform path doesnt exist. Unable to set pddf mode"
            return -1

        print "Starting the PDDF platform service..."
        status = pddf_switch_svc.start_platform_pddf()
        if not status:
            if FORCE==0:
                return status

        print "Disabling the 'skip_fand' from pmon daemon control script..."
        if os.path.exists('/usr/share/sonic/platform/pmon_daemon_control.json'):
            with open('/usr/share/sonic/platform/pmon_daemon_control.json','r') as fr:
                data = json.load(fr)
            if 'skip_fand' in data.keys():
                old_val = data['skip_fand']
                if old_val:
                    data['skip_fand'] = False
                    with open('/usr/share/sonic/platform/pmon_daemon_control.json','w') as fw:
                        json.dump(data,fw)

        print "Restart the pmon service ..."
        status, output = log_os_system("systemctl start pmon.service", 1)
        if status:
            if FORCE==0:
                return status

        return

def do_switch_nonpddf():
    print "Checking system...."
    if not os.path.exists('/usr/share/sonic/platform/pddf_support'):
        print PROJECT_NAME.upper() +" system is already in non-pddf mode...."
    else:
        print "Stopping the pmon service ..."
        status, output = log_os_system("systemctl stop pmon.service", 1)
        if status:
            if FORCE==0:
                return status

        print "Stopping the PDDF platform service..."
        status = pddf_switch_svc.stop_platform_pddf()
        if not status:
            if FORCE==0:
                return status

        print "Removing the pddf_support file..."
        if os.path.exists('/usr/share/sonic/platform'):
            status, output = log_os_system("rm -f /usr/share/sonic/platform/pddf_support", 1)
        else:
            print "/usr/share/sonic/platform path doesnt exist. Unable to set non-pddf mode"
            return -1

        print "Starting the platform services..."
        status = pddf_switch_svc.start_platform_svc()
        if not status:
            if FORCE==0:
                return status

        print "Enabeling the 'skip_fand' from pmon startup script..."
        if os.path.exists('/usr/share/sonic/platform/pmon_daemon_control.json'):
            with open('/usr/share/sonic/platform/pmon_daemon_control.json','r') as fr:
                data = json.load(fr)
            if 'skip_fand' in data.keys():
                old_val = data['skip_fand']
                if not old_val:
                    data['skip_fand'] = True
                    with open('/usr/share/sonic/platform/pmon_daemon_control.json','w') as fw:
                        json.dump(data,fw)

        print "Restart the pmon service ..."
        status, output = log_os_system("systemctl start pmon.service", 1)
        if status:
            if FORCE==0:
                return status

        return

if __name__ == "__main__":
    main()
