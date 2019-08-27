#!/usr/bin/env python

import os.path
import sys, traceback
sys.path.append('/usr/share/sonic/platform/plugins')
import pddfparse
import json
import argparse

class LedUtil:
    color_map = {
                 "GREEN" : "on",
                 "RED" : "faulty",
                 "OFF" : "off",
		 "ON"  : "on"
                }
    def __init__(self):
        global pddf_obj
        pddf_obj = pddfparse.PddfParse()
        self.path="pddf/devices/led"
        self.cur_state_path="pddf/devices/led/cur_state"

    def set_status_led(self, device_name, index,  color, color_state="SOLID"):
	led_device_name=device_name+'_LED'
	if(not pddf_obj.is_led_device_configured(led_device_name, index)):
		status="ERROR :" + device_name + ' ' + index + " :  is not supported in the platform" 
		return (status)

        pddf_obj.create_attr('device_name', led_device_name,  self.path)
        pddf_obj.create_attr('index', index, self.path)
        pddf_obj.create_attr('color', self.color_map[color], self.cur_state_path)
        pddf_obj.create_attr('color_state', color_state, self.cur_state_path)
        pddf_obj.create_attr('dev_ops', 'set_status',  self.path)
	return ("Executed")

    def get_status_led(self, device_name, index):

	led_device_name=device_name+'_LED'
	if(not pddf_obj.is_led_device_configured(led_device_name, index)):
		status="ERROR : " + device_name + ' ' + index + " : is not supported in the platform" 
		return (status)
 
        pddf_obj.create_attr('device_name', led_device_name,  self.path)

        pddf_obj.create_attr('index', index, self.path)
        pddf_obj.create_attr('dev_ops', 'get_status',  self.path)
        color_f="/sys/kernel/" + self.cur_state_path +"/color"  
        color_state_f="/sys/kernel/" + self.cur_state_path +"/color_state"  

        try:
               with open(color_f, 'r') as f:
                    color = f.read().strip("\r\n")
               with open(color_state_f, 'r') as f:
                    color_state = f.read().strip("\r\n")
        except IOError:
		    status="ERROR :" + color_f + " open failed"
                    return (status) 
	status = "%s-%s:\t%s %s\n"%(device_name, index, color, color_state)
	return (status)



#def main():
#        parser = argparse.ArgumentParser()
#        parser.add_argument("--set", action='store', nargs="+",  help="set led color: --set <device_name> <index> <color> <color_state>")
#        parser.add_argument("--get", action='store', nargs="+", help="get led color: --get <device_name> <index>")
#        args = parser.parse_args()
#        if args.set:
#            obj=LedUtil()
#	    if (len(args.set)==3):
#            	obj.set_status_led(args.set[0], args.set[1], args.set[2])
#	    else:
#            	obj.set_status_led(args.set[0], args.set[1], args.set[2], args.set[3])
#
#        if args.get:
#            obj=LedUtil()
#            obj.get_status_led(args.get[0], args.get[1])

#if __name__ == "__main__" :
#        main()

