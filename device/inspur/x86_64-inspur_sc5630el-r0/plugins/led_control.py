#!/usr/bin/env python
#
# led_control.py
# 
# Platform-specific LED control functionality for SONiC
#

import syslog
try:
    import time
    import sys
    from subprocess import Popen, PIPE


except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

UNDEFINED_COLOR = 0
GREEN_COLOR  = 1 #echo 1
YELLOW_COLOR = 2 #echo 3
RED_COLOR    = 3 #echo 2

class LedControlBase(object):
#    __metaclass__ = abc.ABCMeta
#    @abc.abstractmethod

### SC5630EL specified ###
    read_fan_fault = 0
    is_fan_all_OK = 0
    read_power_status = 0
    is_power_all_OK = 0
    is_thermal_high = 0
    is_reset_button_push = 0
##########################

def sysled_task():
    while True:
        system_led_check()
        time.sleep(5)

########## SC5630EL System LED checking
def system_led_check():
    global read_fan_fault, read_power_status, is_fan_all_OK, is_power_all_OK, is_thermal_high, is_reset_button_push
    is_fan_all_OK = 0
    is_power1_all_OK = 0
    is_power2_all_OK = 0
    is_thermal_high = 0
    is_reset_button_push = 0
    #Power LED control
    with open("/sys/bus/i2c/devices/101-0068/psu1_power_good", "r") as f1:
        read_power_status = f1.read()
        if str(read_power_status) == str("1\n"):
            is_power1_all_OK += 0
        else:
            is_power1_all_OK += 1
    with open("/sys/bus/i2c/devices/101-0068/psu1_present", "r") as f1:
        read_power_status = f1.read()
        if str(read_power_status) == str("0\n"):
            is_power1_all_OK += 0
        else:
            is_power1_all_OK += 1
    with open("/sys/bus/i2c/devices/101-0068/psu2_power_good", "r") as f1:
        read_power_status = f1.read()
        if str(read_power_status) == str("1\n"):
            is_power2_all_OK += 0
        else:
            is_power2_all_OK += 1
    with open("/sys/bus/i2c/devices/101-0068/psu2_present", "r") as f1:
        read_power_status = f1.read()
        if str(read_power_status) == str("0\n"):
            is_power2_all_OK += 0
        else:
            is_power2_all_OK += 1
    with open("/sys/bus/i2c/devices/101-0068/pwr_led", "w") as f11:
        if int(is_power1_all_OK) != 0 and int(is_power2_all_OK) != 0:
            f11.write("2")
        elif int(is_power1_all_OK) == 0 and int(is_power2_all_OK) == 0:
            f11.write("1")
        else:
            f11.write("3")
    #Because BMC already implement,we mark fan led
        """
    #FAN LED control
        process = Popen('echo 18 > /sys/class/gpio/export', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)
    with open("/sys/class/gpio/gpio18/value", "r") as f1:
        read_fan_status = f1.read()
        if str(read_fan_status) == str("1\n"):
        is_fan_all_OK = is_fan_all_OK + 1 
        process = Popen('echo 18 > /sys/class/gpio/unexport', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)
            
        process = Popen('echo 19 > /sys/class/gpio/export', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)

        with open("/sys/class/gpio/gpio19/value", "r") as f1:
            read_fan_status = f1.read()
            if str(read_fan_status) == str("1\n"):
                is_fan_all_OK = is_fan_all_OK + 1
                
    process = Popen('echo 19 > /sys/class/gpio/unexport', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)
            
            
    process = Popen('echo 20 > /sys/class/gpio/export', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)

        with open("/sys/class/gpio/gpio20/value", "r") as f1:
            read_fan_status = f1.read()
            if str(read_fan_status) == str("1\n"):
                is_fan_all_OK = is_fan_all_OK + 1
                
    process = Popen('echo 20 > /sys/class/gpio/unexport', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)        
            
    process = Popen('echo 21 > /sys/class/gpio/export', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)

        with open("/sys/class/gpio/gpio21/value", "r") as f1:
            read_fan_status = f1.read()
            if str(read_fan_status) == str("1\n"):
                is_fan_all_OK = is_fan_all_OK + 1
                
    process = Popen('echo 21 > /sys/class/gpio/unexport', stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)    


        with open("/sys/bus/i2c/devices/101-0068/fan_led", "w") as f11:
        if int(is_fan_all_OK) >= 2:
            f11.write("2")    
            elif int(is_fan_all_OK) == 1:
        f11.write("1")
        else:    
                f11.write("0") 
        """        
        try:
            with open("/sys/bus/i2c/devices/98-001c/hwmon/hwmon5/temp3_input", "r") as f3:
                is_thermal_high = f3.read()
                if int(is_thermal_high) >= 70000:
                    is_thermal_high = 1
                else:
                    is_thermal_high = 0
        except Exception, e:
            print("Failed to read temp3_input: %s" % str(e))

        is_hw_ok = hw_check()
        with open("/sys/bus/i2c/devices/101-0068/sys_status_led", "w") as f2:
            if is_hw_ok == RED_COLOR or is_thermal_high == 1:
                f2.write("2")
            elif is_hw_ok == YELLOW_COLOR:
                f2.write("3")
            else:
                f2.write("1")
        return
##########

class LedControl(LedControlBase):
    

    # Constructor

    def led_init(self):
        #Initialize all front-panel status LEDs to green
    #Because BMC already implement,we mark fan led    
        """       
    with open("/sys/bus/i2c/devices/101-0068/fan_led", "w") as f:
            f.write("0")
        """ 
        #with open("/sys/bus/i2c/devices/101-0068/loc_led", "w") as f:
        #    f.write("0")
    #with open("/sys/bus/i2c/devices/101-0068/pwr_led", "w") as f:
        #    f.write("0")    
        #sysled_task()
        #                                                                                                
        return True 



    def __init__(self):
        #Initialize all front-panel status LEDs to green
        #Because BMC already implement,we mark fan led
        """
        with open("/sys/bus/i2c/devices/101-0068/fan_led", "w") as f:
            f.write("0")
        """
        with open("/sys/bus/i2c/devices/101-0068/loc_led", "w") as f:
            f.write("0")
        with open("/sys/bus/i2c/devices/101-0068/pwr_led", "w") as f:
            f.write("0")
        sysled_task()

        return
        # Initialize all front-panel status LEDs to green
        # Initialize: Turn on front panel LEDs
           



class HwUtilBase(object):
### Victoria specified 
### id =1 : switch
### id =2 : vrhot
    id = 0
    name = '0'
    value = UNDEFINED_COLOR
##########################
    def check(self):
        return value


class SwitchControl(HwUtilBase):
    
    def __init__(self):
        self.name = 'switch'
        self.id = 1
        self.value = UNDEFINED_COLOR
        return

########## Victoria switch checking
    def check(self):
        cmd = 'lspci | grep -iE "broadcom.*\(rev 01\)"'
        check_process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        restr, err = check_process.communicate()
        if restr == '':
            print("lspci exec fail")
            self.value = UNDEFINED_COLOR
        else:
            if restr.find('01') != -1:
                self.value = GREEN_COLOR
            else:
                print("Undefined error, reason = %s" % restr)
                self.value = UNDEFINED_COLOR
        return self.value

class VRHOTControl(HwUtilBase):
    def __init__(self):
        self.name = 'vrhot'
        self.id = 2
        self.value = UNDEFINED_COLOR
        return

#### Victoria vrhot checking, Return yellow if any error occurs
#### @return 
    def check(self):
        pvddq_vrhot_value = self.check_pvddq_vrhot()
        pvccin_vrhot_value = self.check_pvccin_vrhot()
        vddcore_vrhot_value = self.check_vddcore_vrhot()
        return max(pvddq_vrhot_value, pvccin_vrhot_value, vddcore_vrhot_value)

#### Victoria vddcore_vrhot checking, Return yellow if any error occurs
#### @return 
    def check_vddcore_vrhot(self):
        #VDD_CORE_VR_HOT checking
        ##export the gpio
        vddcore_vrhot_value = UNDEFINED_COLOR
        try:
            process = Popen('echo 45 > /sys/class/gpio/export', stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = process.communicate()
            if stderr:
                print("_gpio_export exec fail, reason = %s" % stderr)
                vddcore_vrhot_value = UNDEFINED_COLOR
            else:
                ##read the value
                with open("/sys/class/gpio/gpio45/value", "r") as f1:
                    read_vrhot_status = f1.read()
                    if str(read_vrhot_status) == str("1\n"):
                        vddcore_vrhot_value = GREEN_COLOR
                    elif str(read_vrhot_status) == str("0\n"):
                        vddcore_vrhot_value = YELLOW_COLOR
                    else:
                        vddcore_vrhot_value = UNDEFINED_COLOR
                ##unexported the gpio
                process = Popen('echo 45 > /sys/class/gpio/unexport', stdout=PIPE, stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                if stderr:
                    print("_gpio_unexport exec fail, reason = %s" % stderr)
        except Exception, e:
            print("Failed to read VDDCORE_VRHOT: %s" % str(e))
        ##return
        return vddcore_vrhot_value

##########   
#### Victoria pvddq_vrhot checking, Return yellow if any error occurs
#### @return 
    def check_pvddq_vrhot(self):
        #PVDDQ_VRHOT checking
        pvddq_vrhot_value = UNDEFINED_COLOR
        try:
            ##export the gpio
            process = Popen('echo 43 > /sys/class/gpio/export', stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = process.communicate()
            if stderr:
                print("_gpio_export exec fail, reason = %s" % stderr)
                pvddq_vrhot_value = UNDEFINED_COLOR
            else:
                ##read the value
                with open("/sys/class/gpio/gpio43/value", "r") as f1:
                    read_vrhot_status = f1.read()
                    if str(read_vrhot_status) == str("1\n"):
                        pvddq_vrhot_value = GREEN_COLOR
                    elif str(read_vrhot_status) == str("0\n"):
                        pvddq_vrhot_value = YELLOW_COLOR
                    else:
                        pvddq_vrhot_value = UNDEFINED_COLOR
                ##unexported the gpio
                process = Popen('echo 43 > /sys/class/gpio/unexport', stdout=PIPE, stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                if stderr:
                    print("_gpio_unexport exec fail, reason = %s" % stderr)
        except Exception, e:
            print("Failed to read PVDDQ_VRHOT: %s" % str(e))

        ##return
        return pvddq_vrhot_value

##########   

##########   
#### Victoria pvccin_vrhot checking, Return yellow if any error occurs
#### @return 
    def check_pvccin_vrhot(self):
        #PVCCIN_VRHOT checking
        pvccin_vrhot_value = UNDEFINED_COLOR
        try:
            ##export the gpio
            process = Popen('echo 44 > /sys/class/gpio/export', stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = process.communicate()
            if stderr:
                print("_gpio_export exec fail, reason = %s" % stderr)
                pvccin_vrhot_value = UNDEFINED_COLOR
            else:
                ##read the value
                with open("/sys/class/gpio/gpio44/value", "r") as f1:
                    read_vrhot_status = f1.read()
                    if str(read_vrhot_status) == str("1\n"):
                        pvccin_vrhot_value = GREEN_COLOR
                    elif str(read_vrhot_status) == str("0\n"):
                        pvccin_vrhot_value = YELLOW_COLOR
                    else:
                        pvccin_vrhot_value = UNDEFINED_COLOR
                ##unexported the gpio
                process = Popen('echo 44 > /sys/class/gpio/unexport', stdout=PIPE, stderr=PIPE, shell=True)
                stdout, stderr = process.communicate()
                if stderr:
                    print("_gpio_unexport exec fail, reason = %s" % stderr)
        except Exception, e:
            print("Failed to read PVCCIN_VRHOT: %s" % str(e))
        ##return
        return pvccin_vrhot_value

##########   



### @return light color
###   Beause the color has priority, red > yellow > green
###   So return the largest value of the color
def hw_check():
    return max([ SwitchControl().check(), VRHOTControl().check() ])

'''
def sys_led_hw_control():
    hw_check_color = hw_check()
    with open("/sys/bus/i2c/devices/101-0068/sys_status_led", "w") as f:
        if hw_check_color == RED_COLOR:
            f.write("2")
        elif hw_check_color ==  YELLOW_COLOR:
            f.write("3")
        elif hw_check_color == GREEN_COLOR:
            f.write("1")
        else:
            #something wrong happend
            print('Something wrong happend in hw_util')
def sysled_task():
    while True:
        sys_led_control()
        time.sleep(5)

class HwLedControl(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run():
        sysled_task()
'''
