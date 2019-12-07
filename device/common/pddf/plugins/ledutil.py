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
