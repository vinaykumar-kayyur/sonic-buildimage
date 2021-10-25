#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Import modules
# ----------------------------------------------------------------------------
import os
import os.path
import sys
import getopt
import time
import commands     # For python2 only
#import subprocess   # Instead of commands library in python3
import imp
import syslog


# ----------------------------------------------------------------------------
# Platform specific configurable variables
# ----------------------------------------------------------------------------
# Platform global information
INSPUR_MODLE_NAME   = 'sc5630el'    # Need to match this python script file name
VERSION             = "v1.0"        # module version
SYNCD_SOCKET_PATH = '/run/docker-syncd/sswsyncd.socket'
SFPUTIL_PATH = '/usr/share/sonic/device/x86_64-inspur_sc5630el-r0/plugins/sfputil.py'
SFPUTIL_CLASS_NAME = 'SfpUtil' 


PLATFORM_MODULES = [
    'lpc_ich',
    'i2c-i801',
    'i2c-dev',
    'i2c-mux-pca954x',
    'gpio-pca953x',
    'emc1403',
    'inspur-pca9641',
    'inspur-psu',
    'inspur_sc5630el_cpld',
    'optoe',
    'ipmi_msghandler',
    'ipmi_devintf',
    'inspur_sc5630el_platform',
    'insp_sc5630el_psu',
    'insp_sc5630el_eeprom',
    'insp_sc5630el_sfp'
]


# ----------------------------------------------------------------------------
# Global variables
# ----------------------------------------------------------------------------
DEBUG_EN = False
SIM_EN   = False
# ----------------------------------------------------------------------------
# Debug messages
# ----------------------------------------------------------------------------
def DEG_MSG(msg):
    if DEBUG_EN == True:
        print ("[DEBMSG_%s]: %s" % (INSPUR_MODLE_NAME, msg))
        syslog.syslog(syslog.LOG_ERR, "[DEBMSG_%s]: %s" % (INSPUR_MODLE_NAME, msg))

# ----------------------------------------------------------------------------
# Execute system command
# ----------------------------------------------------------------------------
def exec_syscmd(cmd):
    cmd_status = 0
    cmd_resp = ""

    if SIM_EN == True:
        cmd_resp = "<dry-run>"
    else:
        cmd_status, cmd_resp = commands.getstatusoutput(cmd)

    DEG_MSG("ExecSysCmd: " + str(cmd) + " , Result: " + str(cmd_resp))
    return cmd_status, cmd_resp

# ----------------------------------------------------------------------------
# Local functions
# ----------------------------------------------------------------------------
def module_exist(module_name):
    cmd_status, cmd_resp = exec_syscmd("lsmod | grep " + module_name)
    if cmd_status:
            return False

    return True if len(cmd_resp) else False

def file_path_exist(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False

# Install platform kernel modules and register I2C devices
def modules_install():
		#remove default drivers to avoid modprobe order conflicts
    cmd_status, cmd_resp = exec_syscmd("rmmod i2c_ismt ")
    cmd_status, cmd_resp = exec_syscmd("rmmod i2c-i801 ")
    #setup driver dependency
    cmd_status, cmd_resp = exec_syscmd("depmod -a ")
    
    # Install platform kernel modules
    for module_name in PLATFORM_MODULES:
        if module_exist(module_name) == False:
            cmd_status, cmd_resp = exec_syscmd("modprobe " + module_name)
            if cmd_status:
                print (cmd_resp)
                syslog.syslog(syslog.LOG_ERR,cmd_resp)

    # Hardcode to set IPMI interface
    if module_exist("ipmi_si") == False:
        time.sleep(90)
        exec_syscmd("modprobe ipmi_si type=kcs ports=0xca2 slave_addrs=0x10")
        time.sleep(1)
        if file_path_exist("/dev/ipmi0") == False:
            exec_syscmd("rmmod ipmi_si")
    # use ipmi to access cpu eeprom
    cmd_status, cmd_resp = exec_syscmd("echo sc5630el_eeprom 0x6f > /sys/bus/i2c/devices/i2c-0/new_device")

    # use sensors -s command to load sensors.conf
    cmd_status, cmd_resp = exec_syscmd("/usr/bin/sensors -s > /dev/null 2>&1")

    # initial front panel led status 
    with open("/sys/bus/i2c/devices/101-0068/os_control", "w") as f:
        f.write("1")
    with open("/sys/bus/i2c/devices/101-0068/sys_status_led", "w") as f:
        f.write("1")
    exec_syscmd("sed -i 's/OpenSSH_7.4p1/OpenSSH      /g' /usr/sbin/sshd")
    # wait syncd ready and then do port initialization
    try:
    #   wait_syncd_ready()
        port_initialization()
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR,"port initialization exception e =%s" % str(e))
      
# Remove platform kernel modules and unregister I2C devices
def modules_remove():
    # Remove platform kernel modules
    for module_name in reversed(PLATFORM_MODULES):
        if module_exist(module_name) == True:
            cmd_status, cmd_resp = exec_syscmd("rmmod " + module_name)
            if cmd_status:
                print (cmd_resp)
                syslog.syslog(syslog.LOG_ERR,cmd_resp)

# Wait syncd until it is ready
def wait_syncd_ready():
    while True:
        exists = os.path.exists(SYNCD_SOCKET_PATH)
        syslog.syslog(syslog.LOG_ERR, "wating for syncd, exists = %d" % exists)
        if exists:
            break
        else:
            time.sleep(3)

def port_initialization():
    m = imp.load_source(SFPUTIL_CLASS_NAME, SFPUTIL_PATH)
    inst = m.SfpUtil()
    ret = inst.port_init()
    if ret:
        print ("sfp port initialization done")
        syslog.syslog(syslog.LOG_ERR, "sfp port initialization done")
    else:
        print ("sfp port initialization Fail")
        syslog.syslog(syslog.LOG_ERR, "sfp port initialization Fail")

# Show cpld version
def modules_cpldvr():
    with open("/sys/bus/i2c/devices/101-0068/first_cpld_version", "r") as f1:
        CPLD_FIRST = f1.read()
    with open("/sys/bus/i2c/devices/101-0068/second_cpld_version", "r") as f2:
        CPLD_SECOND = f2.read()
    with open("/sys/bus/i2c/devices/101-0068/third_cpld_version", "r") as f3:
        CPLD_THIRD = f3.read()
    print ("cpld First_version:%s" %(CPLD_FIRST))
    print ("cpld Second_version:%s" %(CPLD_SECOND))
    print ("cpld Third_version:%s" %(CPLD_THIRD))

def modules_locate():
    with open("/sys/bus/i2c/devices/101-0068/loc_led", "w") as f:
        f.write("1")
def modules_rlocate():
    with open("/sys/bus/i2c/devices/101-0068/loc_led", "w") as f:
        f.write("0")
     

# ----------------------------------------------------------------------------
# Show usage message
# ----------------------------------------------------------------------------
def show_usage_msg():
    usage_msg = """
Usage: inspur_%s_util.py [options] command

options:
    -h | --help      : Show help message
    -v | --version   : Show script version
    -d | --debug     : Run with debug mode
    -s | --simulator : Dry-run system commands
command:
    install         : Install platform modules
    clean           : Remove platform modules
    cpldvr          : Show cpld version
    locate_on       : turn on locate led
    locate_off      : trun off locate led
"""
    print (usage_msg)
    sys.exit(0)

# ----------------------------------------------------------------------------
# Show python script version
# ----------------------------------------------------------------------------
def show_version():
    print ("inspur_" + INSPUR_MODLE_NAME + ".py: " + VERSION)

# ----------------------------------------------------------------------------
# Main function
# ----------------------------------------------------------------------------
def main():
    global DEBUG_EN
    global SIM_EN

    if len(sys.argv) < 1:
        show_usage_msg()

    try:
        options, args = getopt.getopt(sys.argv[1:],
                                      'hvds',
                                      ['help', 'version', 'debug', 'simulator'])
    except getopt.GetoptError:
        show_usage_msg()
        return 0

    # Process input arguments
    for opt, arg in options:
        if opt in ('-h', '--help'):
            show_usage_msg()
        elif opt in ('-v', '--version'):
            show_version()
            return 0
        elif opt in ('-d', '--debug'):
            DEBUG_EN = True
        elif opt in ('-s', '--simulator'):
            SIM_EN = True

    if len(args) == 0:
        print ("Error usage: Missing command argument!")
        syslog.syslog(syslog.LOG_ERR, "Error usage: Missing command argument!")
        
        show_usage_msg()

    for arg in args:
        if arg == 'install':
           modules_install()
        elif arg == 'clean':
           modules_remove()
	elif arg == 'cpldvr':
           modules_cpldvr()
        elif arg == 'locate_on':
           modules_locate()
        elif arg == 'locate_off':
           modules_rlocate()
        else:
            print ("Error usage: Invalid command!")
            syslog.syslog(syslog.LOG_ERR, "Error usage: Invalid command!")
            show_usage_msg()

    return 0

if __name__ == '__main__':
    main()
