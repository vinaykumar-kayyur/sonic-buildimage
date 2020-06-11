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
kos = []
perm_kos = []
devs = []

# Instantiate the class pddf_obj
try:
    pddf_obj = pddfparse.PddfParse()
except Exception as e:
    print "%s" % str(e)
    sys.exit()



if DEBUG == True:
    print sys.argv[0]
    print 'ARGV      :', sys.argv[1:]   

def main():
    global DEBUG
    global args
    global FORCE
    global kos
        
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
    
    # generate the KOS list from pddf device JSON file
    if 'std_perm_kos' in pddf_obj.data['PLATFORM'].keys():
       kos.extend(pddf_obj.data['PLATFORM']['std_perm_kos'])
       perm_kos.extend(pddf_obj.data['PLATFORM']['std_perm_kos'])
    kos.extend(pddf_obj.data['PLATFORM']['std_kos'])
    kos.extend(pddf_obj.data['PLATFORM']['pddf_kos'])

    kos = ['modprobe '+i for i in kos]

    if 'custom_kos' in pddf_obj.data['PLATFORM']:
        custom_kos = pddf_obj.data['PLATFORM']['custom_kos']
        kos.extend(['modprobe -f '+i for i in custom_kos])
        # print kos

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
    pddf_path = get_path_to_pddf_plugin()

    # ##########################################################################
    status, output = log_os_system("pip show sonic-platform > /dev/null 2>&1", 1)
    if status:
        # Platform API 2.0 is not supported
        SONIC_PLATFORM_WHL_PKG = device_path+'/pddf/sonic_platform-1.0-py2-none-any.whl'
        
        if os.path.exists(SONIC_PLATFORM_WHL_PKG):
            # whl package exist ... this must be the whl package created from 
            # PDDF 2.0 ref API classes and some changes on top of it ... install it
            SONIC_PLATFORM_WHL_PKG_NEW = device_path+'/sonic_platform-1.0-py2-none-any.whl'
            if not os.path.exists(SONIC_PLATFORM_WHL_PKG_NEW):
                shutil.copy(SONIC_PLATFORM_WHL_PKG, SONIC_PLATFORM_WHL_PKG_NEW)
            print "Attemting to install the sonic_platform wheel package ..."
            status, output = log_os_system("pip install "+ SONIC_PLATFORM_WHL_PKG_NEW, 1)
            if status:
                print "Error: Failed to install {}".format(SONIC_PLATFORM_WHL_PKG_NEW)
                return status
            else:
                print "Successfully installed {} package".format(SONIC_PLATFORM_WHL_PKG_NEW)
        else:
            # PDDF with platform APIs 1.5 must be supported
            device_plugin_path = "/".join([device_path, "plugins"])
            backup_path = "/".join([device_plugin_path, "orig"])
            print "Loading PDDF generic plugins (1.0)"
            if os.path.exists(backup_path) is False:
                os.mkdir(backup_path)
                log_os_system("mv "+device_plugin_path+"/*.*"+" "+backup_path, 0)
            
            for item in os.listdir(pddf_path):
                shutil.copy(pddf_path+"/"+item, device_plugin_path+"/"+item)
            
            shutil.copy('/usr/local/bin/pddfparse.py', device_plugin_path+"/pddfparse.py")

    else:
        # sonic_platform whl pkg is installed
        SONIC_PLATFORM_WHL_PKG_PATH = '/usr/local/lib/python2.7/dist-packages/sonic_platform'
        if os.path.isdir(SONIC_PLATFORM_WHL_PKG_PATH+'/pddf/'):
            # PDDF support is present and ODMs 2.0 platform api implementation exist too
            backup_path = "/".join([SONIC_PLATFORM_WHL_PKG_PATH,'orig'])
            if not os.path.exists(backup_path):
                os.mkdir(backup_path)
                log_os_system("mv "+SONIC_PLATFORM_WHL_PKG_PATH+"/*.*"+" "+backup_path, 0)
                # bringin the PDDF object classes into sonic_platform folder
                for item in os.listdir(SONIC_PLATFORM_WHL_PKG_PATH+'/pddf/'):
                    shutil.copy(SONIC_PLATFORM_WHL_PKG_PATH+'/pddf/'+item, SONIC_PLATFORM_WHL_PKG_PATH+"/"+item)
            else:
                # orig folder contains native 2.0 api implementation and 
                # SONIC_PLATFORM_WHL_PKG_PATH holds PDDF implementation and system is rebooted in PDDF mode
                print "System rebooted in PDDF mode, hence keeping the PDDF 2.0 classes"
        else:
            # PDDF 2.0 implementation is present at SONIC_PLATFORM_WHL_PKG_PATH and system is rebooted
            # in PDDF mode
            print "System rebooted in PDDF mode, hence keeping the PDDF 2.0 classes"
    # ##########################################################################
    # Take a backup of orig fancontrol
    if os.path.exists(device_path+"/fancontrol"):
        log_os_system("mv "+device_path+"/fancontrol"+" "+device_path+"/fancontrol.bak", 0)
        #print "***Created fancontrol.bak"
    
    # Create a link to fancontrol of PDDF
    if os.path.exists(device_path+"/pddf/fancontrol") and not os.path.exists(device_path+"/fancontrol"):
        shutil.copy(device_path+"/pddf/fancontrol",device_path+"/fancontrol")
        #print "*** Copied the pddf fancontrol file "

    # BMC support
    f_sensors="/usr/bin/sensors"
    f_sensors_org="/usr/bin/sensors.org"
    f_pddf_sensors="/usr/local/bin/pddf_sensors"
    if os.path.exists(f_pddf_sensors) is True:
        if os.path.exists(f_sensors_org) is False:
            shutil.copy(f_sensors, f_sensors_org)
        shutil.copy(f_pddf_sensors, f_sensors)


    return 0

def cleanup_pddf_utils():
    device_path = get_path_to_device()
    # ##########################################################################
    status, output = log_os_system("pip show sonic-platform > /dev/null 2>&1", 1)
    if status:
        # PDDF Platform API 2.0 is not supported but system is in PDDF mode, hence PDDF 1.0 plugins are present
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

    else:
        # PDDF 2.0 apis are supported and whl package is installed
        SONIC_PLATFORM_WHL_PKG = device_path+'/pddf/sonic_platform-1.0-py2-none-any.whl'
        if os.path.exists(SONIC_PLATFORM_WHL_PKG):
            # platform doesnt support 2.0 APIs but PDDF is 2.0 based
            if os.path.exists(device_path+'/sonic_platform-1.0-py2-none-any.whl'):
                os.remove(device_path+'/sonic_platform-1.0-py2-none-any.whl')
            status, output = log_os_system("pip uninstall sonic-platform -y &> /dev/null", 1)
            if status:
                print "Error: Unable to uninstall sonic-platform whl package"
                return status
        else:
            # platform supports 2.0 and PDDF is also 2.0 based
            SONIC_PLATFORM_WHL_PKG_PATH = '/usr/local/lib/python2.7/dist-packages/sonic_platform'
            if os.path.isdir(SONIC_PLATFORM_WHL_PKG_PATH+'/pddf/'):
                # PDDF support is present and ODMs 2.0 platform api implementation exist too
                backup_path = "/".join([SONIC_PLATFORM_WHL_PKG_PATH,'orig'])
                if not os.path.exists(backup_path):
                    print "Error: Fatal error as the original object classes are not found"
                else:
                    for item in os.listdir(SONIC_PLATFORM_WHL_PKG_PATH):
                        if os.path.isdir(SONIC_PLATFORM_WHL_PKG_PATH+"/"+item) is False:
                            os.remove(SONIC_PLATFORM_WHL_PKG_PATH+"/"+item)
                    log_os_system("mv "+backup_path+"/*"+" "+SONIC_PLATFORM_WHL_PKG_PATH, 1)
                    os.rmdir(backup_path)
            else:
                # Something seriously wrong as the pddf folder is absent.
                print "Error: Fatal error as the system is in PDDF mode but the original pddf directory is not present"
    # ###################################################################################################################

    if os.path.exists(device_path+"/fancontrol"):
        os.remove(device_path+"/fancontrol")
        #print "Removed the fancontrol"

    if os.path.exists(device_path+"/fancontrol.bak"):
        log_os_system("mv "+device_path+"/fancontrol.bak"+" "+device_path+"/fancontrol", 0)
        #print "***Moved fancotnrol.bak to fancontrol"

    # BMC support
    f_sensors="/usr/bin/sensors"
    f_sensors_org="/usr/bin/sensors.org"
    if os.path.exists(f_sensors_org) is True:
        shutil.copy(f_sensors_org, f_sensors)

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
    log_os_system("sudo touch /var/log/pddf/cpldmux.txt", 1)
    log_os_system("sudo touch /var/log/pddf/client.txt", 1)
    log_os_system("sudo touch /var/log/pddf/mux.txt", 1)

def driver_install():
    global FORCE
    status, output = log_os_system("depmod", 1)
    for i in range(0,len(kos)):
        status, output = log_os_system(kos[i], 1)
        if status:
            print "driver_install() failed with error %d"%status
            if FORCE == 0:        
                return status       

    output = config_pddf_utils()

    return 0
    
def driver_uninstall():
    global FORCE

    status = cleanup_pddf_utils()

    for i in range(0,len(kos)):
        # if it is in perm_kos, do not remove
        if (kos[-(i+1)].split())[-1] in perm_kos or 'i2c-i801' in kos[-(i+1)]:
            continue

        rm = kos[-(i+1)].replace("modprobe", "modprobe -rq")
        rm = rm.replace("insmod", "rmmod")        
        status, output = log_os_system(rm, 1)
        if status:
            print "driver_uninstall() failed with error %d"%status
            if FORCE == 0:        
                return status              
    return 0

def device_install():
    global FORCE
    # trigger the pddf_obj script for FAN, PSU, CPLD, MUX, etc
    status = pddf_obj.create_pddf_devices()
    if status:
        print "Error: create_pddf_devices() failed with error %d"%status
        if FORCE == 0:
            return status
    return

def device_uninstall():
    global FORCE
    # Trigger the paloparse script for deletion of FAN, PSU, OPTICS, CPLD clients
    status = pddf_obj.delete_pddf_devices()
    if status:
        print "Error: delete_pddf_devices() failed with error %d"%status
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
        print "Installing ..."    
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
    try:
        import pddf_switch_svc
    except ImportError:
        print "Unable to find pddf_switch_svc.py. PDDF might not be supported on this platform"
        sys.exit()
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
            print "Pmon stop failed"
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
            print "/usr/share/sonic/platform path doesn't exist. Unable to set pddf mode"
            return -1

        print "Starting the PDDF platform service..."
        status = pddf_switch_svc.start_platform_pddf()
        if not status:
            if FORCE==0:
                return status

        print "Restart the pmon service ..."
        status, output = log_os_system("systemctl start pmon.service", 1)
        if status:
            print "Pmon restart failed"
            if FORCE==0:
                return status

        return

def do_switch_nonpddf():
    try:
        import pddf_switch_svc
    except ImportError:
        print "Unable to find pddf_switch_svc.py. PDDF might not be supported on this platform"
        sys.exit()
    print "Checking system...."
    if not os.path.exists('/usr/share/sonic/platform/pddf_support'):
        print PROJECT_NAME.upper() +" system is already in non-pddf mode...."
    else:
        print "Check if the sonic-platform whl package is installed in the pmon docker"
        status, output = log_os_system("docker exec -it pmon pip show sonic-platform", 1)
        if not status:
            # Need to remove this whl module
            status, output = log_os_system("docker exec -it pmon pip uninstall sonic-platform -y", 1)
            if not status:
                print "Successfully uninstalled the sonic-platform whl pkg from pmon container"
            else:
                print "Error: Unable to uninstall the sonic-platform whl pkg from pmon container. Do it manually before moving to nonpddf mode"
                return status
        print "Stopping the pmon service ..."
        status, output = log_os_system("systemctl stop pmon.service", 1)
        if status:
            print "Stopping pmon service failed"
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

        #print "Enabeling the 'skip_fand' from pmon startup script..."
        #if os.path.exists('/usr/share/sonic/platform/pmon_daemon_control.json'):
            #with open('/usr/share/sonic/platform/pmon_daemon_control.json','r') as fr:
                #data = json.load(fr)
            #if 'skip_fand' in data.keys():
                #old_val = data['skip_fand']
                #if not old_val:
                    #data['skip_fand'] = True
                    #with open('/usr/share/sonic/platform/pmon_daemon_control.json','w') as fw:
                        #json.dump(data,fw)

        print "Restart the pmon service ..."
        status, output = log_os_system("systemctl start pmon.service", 1)
        if status:
            print "Restarting pmon service failed"
            if FORCE==0:
                return status

        return

if __name__ == "__main__":
    main()
