#!/usr/bin/env python
#
# Sample pddf_psuutil file 
#
# All the supported PSU SysFS aattributes are 
#- psu_present
#- psu_model_name
#- psu_power_good
#- psu_mfr_id
#- psu_serial_num
#- psu_fan_dir
#- psu_v_out
#- psu_i_out
#- psu_p_out
#- psu_fan1_speed_rpm
#

import os.path
import sys, traceback
sys.path.append('/usr/share/sonic/platform/plugins')
import pddfparse
import json

try:
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")


class PsuUtil(PsuBase):
    """PDDF generic PSU util class"""

    def __init__(self):
        PsuBase.__init__(self)
        global pddf_obj
        global plugin_data
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)) + '/../pddf/pd-plugin.json')) as pd:
            plugin_data = json.load(pd)

        pddf_obj = pddfparse.PddfParse()
        self.platform = pddf_obj.get_platform()

    def get_num_psus(self):
        return int(self.platform['num_psus'])

    def get_psu_status(self, index):
        if index is None:
            return False

        status = 0
        device = "PSU" + "%d"%index
        node = pddf_obj.get_path(device,"psu_power_good")
        try:
            with open(node, 'r') as f:
                status = f.read()
        except IOError:
            return False
        vmap = plugin_data['PSU']['psu_power_good']['valmap']

        if status.rstrip('\n') in vmap:
            return vmap[status.rstrip('\n')]
        else:
            return False

    def get_psu_presence(self, index):
        if index is None:
            return False

        status = 0
        device = "PSU" + "%d"%index
        node = pddf_obj.get_path(device,"psu_present")
        try:
            with open(node, 'r') as f:
                status = f.read()
        except IOError:
            return False
        vmap = plugin_data['PSU']['psu_present']['valmap']

        if status.rstrip('\n') in vmap:
            return vmap[status.rstrip('\n')]
        else:
            return False

    def get_powergood_status(self, idx):
        if idx is None:
            return False

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return False

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_power_good")
        try:
            with open(node, 'r') as power_status:
                status = int(power_status.read())
        except IOError:
            return False

        if status == 0:
            return False
        else:
            return True

    def get_model(self, idx):
        if idx is None:
            return None

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return None

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_model_name")
        try:
            with open(node, 'r') as f:
                model = f.read()
        except IOError:
            return None

        return model.rstrip('\n')

    def get_mfr_id(self, idx):
        if idx is None:
            return None

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return None

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_mfr_id")
        try:
            with open(node, 'r') as f:
                mfr = f.read()
        except IOError:
            return None

        return mfr.rstrip('\n')

    def get_serial(self, idx):
        if idx is None:
            return None

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return None

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_serial_num")
        try:
            with open(node, 'r') as f:
                serial = f.read()
        except IOError:
            return None

        return serial.rstrip('\n')

    def get_direction(self, idx):
        if idx is None:
            return None

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return None

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_fan_dir")
        try:
            with open(node, 'r') as f:
                direction = f.read()
        except IOError:
            return None

        airflow_dir = direction.rstrip('\n')
        vmap = plugin_data['PSU']['psu_fan_dir']['valmap']

        if airflow_dir in vmap:
            airflow_dir_real = vmap[airflow_dir]
        else:
            airflow_dir_real = airflow_dir
            
        return airflow_dir_real

    def get_output_voltage(self, idx):
        if idx is None:
            return 0

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return 0

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_v_out")
        try:
            with open(node, 'r') as f:
                v_out = int(f.read())
        except IOError:
            return 0

        return v_out

    def get_output_current(self, idx):
        if idx is None:
            return 0

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return 0

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_i_out")
        try:
            with open(node, 'r') as f:
                i_out = int(f.read())
        except IOError:
            return 0

        return i_out

    def get_output_power(self, idx):
        if idx is None:
            return 0

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return 0

        device = "PSU"+"%d"%(idx)
        node = pddf_obj.get_path(device, "psu_p_out")
        try:
            with open(node, 'r') as f:
                p_out = int(f.read())
        except IOError:
            return 0

        return p_out

    def get_fan_speed(self, idx, fan_idx):
        if idx is None or fan_idx is None:
            return 0

        if idx<1 or idx>self.platform['num_psus']:
            print "Invalid index %d\n"%idx
            return 0


        device = "PSU"+"%d"%(idx)
        num_fans = pddf_obj.get_num_psu_fans(device)

        if fan_idx<1 or fan_idx>num_fans:
            print "Invalid PSU-fan index %d\n"%fan_idx
            return 0

        node = pddf_obj.get_path(device, "psu_fan"+str(fan_idx)+"_speed_rpm")
        try:
            with open(node, 'r') as f:
                fan_rpm = int(f.read())
        except IOError:
            return 0

        return fan_rpm


    def dump_sysfs(self):
        return pddf_obj.cli_dump_dsysfs('psu')

