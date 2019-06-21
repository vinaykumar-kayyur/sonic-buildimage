#!/usr/bin/env python
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

import sys, getopt
import logging
import os
import commands
import threading
import time
import syslog

DEBUG = False
STOP = False
FAN_NUM = 5
PASS = 0
FAIL = 1

i2c_prefix = '/sys/bus/i2c/devices/'
status_nodes = {'fan': ['5-0070'],
		'psu':['2-0058', '3-0059']}
system_led_node = '7-0075'
status_alert = {'fan': ['wrongAirflow_alert', 'outerRPMOver_alert', 'outerRPMUnder_alert', 'outerRPMZero_alert', 'innerRPMOver_alert', 'innerRPMUnder_alert', 'innerRPMZero_alert', 'notconnect_alert'],
		'psu': ['vout_over_voltage', 'iout_over_current_fault', 'iout_over_current_warning', 'iput_over_current_warning', 'iput_insufficient', 'temp_over_temp_fault', 'temp_over_temp_warning']}

led_command = {'sys_led': {'green':'0', 'amber':'1', 'off':'2', 'blink_green':'3', 'blink_amber':'4'},
		'pwr_led': {'green':'0', 'amber':'1', 'off':'2', 'blink_green':'3', 'blink_amber':'4'},
		'loc_led': {'on':'0', 'off':'1', 'blink':'2'},
		'fan_led': {'green':'0', 'amber':'1', 'off':'2', 'blink_green':'3', 'blink_amber':'4'},
		'cpld_allled_ctrl': {'off':'0', 'mix':'1', 'amber':'2', 'normal':'3'},
		'serial_led_enable': {'disable':'0', 'enable':'1'}}

pre_fan_led_status = 0
pre_pwr_led_status = 0

def dbg_print(string):
	if DEBUG == True:
		print string    
	return

def do_cmd(cmd, show):
	logging.info('Run :' + cmd)  
	status, output = commands.getstatusoutput(cmd)    
	dbg_print(cmd + "with result:" + str(status))
	dbg_print("output:" + output)    
	if status:
		logging.info('Failed :' + cmd)
		if show:
			print('Failed :' + cmd)
	return  status, output

def read_file(path):
	try:
		file = open(path)
	except IOError as e:
		print "Error: unable to open file: %s" % str(e)
		return False

	value = int(file.readline().rstrip())
	file.close()

	return value

def write_file(path, value):
	try:
		file = open(path, "r+")
	except IOError as e:
		print "Error: unable to open file: %s" % str(e)
		return False

	file.seek(0)
	file.write(str(value))
	file.close()

	return

def check_platform_fan():
	global pre_fan_led_status
	fan_result = 0
	fan_status_node = status_nodes['fan']
	fan_alert = status_alert['fan']
	fan_led = led_command['fan_led']

	status, output = do_cmd("ls " + i2c_prefix, 1)
	if output.find(fan_status_node[0]) != -1:
		for num in range(0,FAN_NUM):
			for alert_type in fan_alert:
				path = i2c_prefix + fan_status_node[0] + "/fan" + str(num+1) + "_" + alert_type
				fan_result += read_file(path)

	if fan_result != PASS:
		if pre_fan_led_status != fan_led["blink_amber"]:
			path = i2c_prefix + system_led_node + "/fan_led"
			write_file(path, fan_led["blink_amber"])
			pre_fan_led_status = fan_led["blink_amber"]
			syslog.syslog(syslog.LOG_ERR, 'FAN Status Error !!!')
		return FAIL

	if pre_fan_led_status != fan_led["green"]:
		path = i2c_prefix + system_led_node + "/fan_led"
		write_file(path, fan_led["green"])
		pre_fan_led_status = fan_led["green"]
		syslog.syslog(syslog.LOG_WARNING, 'FAN Status Normal !!!')
	return PASS

def check_platform_psu():
	global pre_pwr_led_status
	psu_result = 0
	psu_status_node = status_nodes['psu']
	psu_alert = status_alert['psu']
	psu_led = led_command['pwr_led']

	status, output = do_cmd("ls " + i2c_prefix, 1)
	if output.find(psu_status_node[0]) != -1 and output.find(psu_status_node[1]) != -1:
		for nodes in psu_status_node:
			for alert_type in psu_alert:
				path = i2c_prefix + nodes + "/" + alert_type
				psu_result += read_file(path)

	if psu_result != PASS:
		if pre_pwr_led_status != psu_led["blink_amber"]:
			path = i2c_prefix + system_led_node + "/pwr_led"
			write_file(path, psu_led["blink_amber"])
			pre_pwr_led_status = psu_led["blink_amber"]
			syslog.syslog(syslog.LOG_ERR, 'PSU Status Error !!!')
		return FAIL

	if pre_pwr_led_status != psu_led["green"]:
		path = i2c_prefix + system_led_node + "/pwr_led"
		write_file(path, psu_led["green"])
		pre_pwr_led_status = psu_led["green"]
		syslog.syslog(syslog.LOG_WARNING, 'PSU Status Normal !!!')
	return PASS

def pega_check_platform_status():
	while(True):
		total_result = 0
		if STOP == True:
			return
		total_result += check_platform_fan()
		total_result += check_platform_psu()
		time.sleep(1)
	return

def main():
	for arg in sys.argv[1:]:           
		if arg == 'run':
			pega_check_platform_status()
		elif arg == 'stop':
			STOP = True

if __name__ == "__main__":
	main()
