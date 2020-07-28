#!/usr/bin/python

from __future__ import print_function
import os
import sys
import logging

FAN_NUM = 5
fans_path = '/sys/class/hwmon/hwmon2/device/ESC601_FAN/'

sensors_path = '/sys/class/hwmon/hwmon2/device/ESC601_BMC/'

cpld_psu_path = '/sys/class/hwmon/hwmon2/device/ESC601_PSU/'

psu1_path = '/sys/class/hwmon/hwmon8/device/' # 0x59
psu2_path = '/sys/class/hwmon/hwmon7/device/' # 0x58

# Get sysfs attribute
def get_attr_value(attr_path):
    retval = 'ERR'
    if not os.path.isfile(attr_path):
        return retval

    try:
        with open(attr_path, 'r') as fd:
            retval = fd.read()
    except Exception as error:
        logging.error("Unable to open ", attr_path, " file !")

    retval = retval.rstrip('\r\n')
    fd.close()
    return retval

def bmc_is_exist():
    value = ''
    bmc_filePath = '/sys/class/hwmon/hwmon2/device/ESC601_BMC/bmc_present'
    if os.path.exists(bmc_filePath):
       value = get_attr_value(bmc_filePath)
       if value.find('not') < 0:
            return True
       else:
            return False
    else:
       return False

def calc_mac_temp():
    value = ''
    value = get_attr_value('/sys/class/hwmon/hwmon2/device/ESC601_BMC/bmc_mac_sensor')
    mac_sensor= int(value,16)/1000.0
    temp1 = -124.28 * mac_sensor * mac_sensor
    temp2 = -422.03 * mac_sensor
    temp_sensor = 384.62 + temp1 + temp2
    return round(temp_sensor,2)

def print_attr_value_lines(sys_path):
    retval = 'ERR'
    if not os.path.isfile(sys_path):
        return retval
    try:
        fo = open(sys_path, "r")
    except Exception as error:
        logging.error("Unable to open ", sys_path, " file !")
    for line in fo.readlines():
        line = line.strip()
        print ("    %s" % line)
    fo.close()
    return retval

def get_fan_alert(number):
    return

def get_fan_inner_rpm(number):
    return

def get_fan_outer_rpm(number):
    return

def sensors_status():
    sys_path = sensors_path + 'bmc_sersor_1'  
    print_attr_value_lines(sys_path)
    sys_path = sensors_path + 'bmc_sersor_2'
    print_attr_value_lines(sys_path)
    sys_path = sensors_path + 'bmc_sersor_3'
    print_attr_value_lines(sys_path)
    sys_path = sensors_path + 'bmc_sersor_4'
    print_attr_value_lines(sys_path)
    return

def sensors_temp():
    print ('    Mac SENSORS TEMP:%.2f degrees (C)'% calc_mac_temp())
    return

def get_voltage():
    return

def fan_status():
    sys_path = fans_path + 'fan_status'
    print ('FAN STATUS:')
    print_attr_value_lines(sys_path)
    return

def fan_present():
    sys_path = fans_path + 'fan_present'
    print ('FAN PRESENT:')
    print_attr_value_lines(sys_path)
    return

def fan_power():
    sys_path = fans_path + 'fan_power'
    print ('FAN POWER:')
    print_attr_value_lines(sys_path)
    return

def fan_speed():
    sys_path = fans_path + 'fan_speed_rpm'
    print ('FAN SPEED:')
    print_attr_value_lines(sys_path)
    return

def is_psu_present(psu_number):
    sys_path = cpld_psu_path + 'psu_present'
    search_str = "PSU {} is present".format(psu_number)
    if os.path.exists(sys_path):
       value = get_attr_value(sys_path)
       if search_str in value:
            return True
       else:
            return False
    
    return False

def show_psu_status(path):
    model = get_attr_value(path+"psu_mfr_model")
    if model != 'ERR':
        print ('    model: {}'.format(model))
    else:
        return

    temp = get_attr_value(path+"psu_vin")
    if temp != 'ERR':
        vin = int(temp)/1000.0
        print ('    Input Voltage:  {:+3.2f} V'.format(vin))
    
    temp = get_attr_value(path+"psu_vout")    
    if temp != 'ERR':
        vout = int(temp)/1000.0
        print ('    Output Voltage: {:+3.2f} V'.format(vout))
    
    temp = get_attr_value(path+"psu_fan_speed_1")
    if temp != 'ERR':
        psufan_speed = int(temp)
        print ('    Fan Speed:      {:3d} RPM'.format(psufan_speed))

    temp = get_attr_value(path+"psu_temp_1")
    if temp != 'ERR':
        temperature = int(temp)/1000.0
        print ('    Temperature:    {:+3.1f} C'.format(temperature))

    temp = get_attr_value(path+"psu_pin")
    if temp != 'ERR':
        pin = int(temp)/1000000.0
        print ('    Input Power:    {:3.2f} W'.format(pin))

    temp = get_attr_value(path+"psu_pout")
    if temp != 'ERR':
        pout = int(temp)/1000000.0
        print ('    Output Power:   {:3.2f} W'.format(pout))

    temp = get_attr_value(path+"psu_iin")
    if temp != 'ERR':
        iin = int(temp)/1000.0
        print ('    Input Current:  {:+3.2f} A'.format(iin))

    temp = get_attr_value(path+"psu_iout")
    if temp != 'ERR':
        iout = int(temp)/1000.0
        print ('    Output Current: {:+3.2f} A'.format(iout),end='')
    
    temp = get_attr_value(path+"psu_iout_max")
    if temp != 'ERR':
        max_iout = int(temp)/1000.0
        print ('  (max = {:+3.2f} A)'.format(max_iout))

    print('')



def psu_status():
    if is_psu_present(1):
        print("PSU1 present")
        show_psu_status(psu1_path)

    if is_psu_present(2):
        print("PSU2 present")
        show_psu_status(psu2_path)

    return


def main():
    """
    Usage: %(scriptName)s command object

    command:
        fan_status     : display fans status(present/power good)
    """

    if len(sys.argv)<2:
        print (main.__doc__)

    for arg in sys.argv[1:]:
        if arg == 'fan_status':
            fan_status()
            fan_present()
            fan_power()
            fan_speed()
        elif arg == 'sensor_status':
            if bmc_is_exist():
                sensors_status()
                sensors_temp()
            else:
                psu_status()

        else:
            print (main.__doc__)

if __name__ == "__main__":
    main()
