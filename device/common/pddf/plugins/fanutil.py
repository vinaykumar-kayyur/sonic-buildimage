#!/usr/bin/env python


# Sample pddf_fanutil file 
# All the supported FAN SysFS aattributes are
#- fan<idx>_present
#- fan<idx>_direction
#- fan<idx>_front_rpm
#- fan<idx>_rear_rpm
#- fan<idx>_pwm
#- fan<idx>_fault
# where idx is in the range [1-8]
#


import os.path
import sys, traceback, time
sys.path.append('/usr/share/sonic/platform/plugins')
import pddfparse
import json

try:
    from sonic_fan.fan_base import FanBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

class FanUtil(FanBase):
    """PDDF generic FAN util class"""

    def __init__(self):
        FanBase.__init__(self)
        global pddf_obj
        global plugin_data
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)) + '/../pddf/pd-plugin.json')) as pd:
            plugin_data = json.load(pd)

        pddf_obj = pddfparse.PddfParse()
        self.platform = pddf_obj.get_platform()

    def get_num_fans(self):
        return self.platform['num_fans']

    def get_presence(self, idx):
        # 1 based fan index
        if idx<1 or idx>self.platform['num_fans']:
            print "Invalid fan index %d\n"%idx
            return False

        attr_name = "fan" + str(idx) + "_present"
        sysfs_path = pddf_obj.get_path("FAN-CTRL", attr_name)

        try:
            with open(sysfs_path, 'r') as f:
                presence = int(f.read())
        except IOError:
            return False
        
        status = (True if presence==1 else False)
        return status

    def get_status(self, idx):
        # 1 based fan index
        if idx<1 or idx>self.platform['num_fans']:
            print "Invalid fan index %d\n"%idx
            return False

        front_speed = self.get_speed(idx)
        rear_speed = self.get_speed_rear(idx)
        status = True if (front_speed != 0 and rear_speed != 0) else False
        return status

    def get_direction(self, idx):
        # 1 based fan index
        if idx<1 or idx>self.platform['num_fans']:
            print "Invalid fan index %d\n"%idx
            return None

        attr = "fan" + str(idx) + "_direction"
        path = pddf_obj.get_path("FAN-CTRL", attr)
        try:
            with open(path, 'r') as f:
                val = f.read()
        except IOError:
            return None

        vmap = plugin_data['FAN']['direction']['valmap']
        if val.rstrip('\n') in vmap:
            direction = vmap[val.rstrip('\n')]
        else:
            direction = val

        return direction

    def get_directions(self):
        num_fan = self.get_num_fan();

        for i in range(1, num_fan+1):
            attr = "fan" + str(i) + "_direction"
            path = pddf_obj.get_path("FAN-CTRL", attr)
            #print "%d-%s"%(i,path)
            try:
                with open(path, 'r') as f:
                    val = int(f.read())
            except IOError:
                return False

            vmap = plugin_data['FAN']['direction']['valmap']
            direction = vmap[str(val)]

            print "FAN-%d direction is %s"%(i, direction)

        return 0

    def get_speed(self, idx):
        # 1 based fan index
        if idx<1 or idx>self.platform['num_fans']:
            print "Invalid fan index %d\n"%idx
            return 0

        attr = "fan" + str(idx) + "_front_rpm"
        path = pddf_obj.get_path("FAN-CTRL", attr)
        try:
            with open(path, 'r') as f:
                frpm = int(f.read())
        except IOError:
            return 0

        return frpm

    def get_speed_rear(self, idx):
        # 1 based fan index
        if idx<1 or idx>self.platform['num_fans']:
            print "Invalid fan index %d\n"%idx
            return 0

        attr = "fan" + str(idx) + "_rear_rpm"
        path = pddf_obj.get_path("FAN-CTRL", attr)
        try:
            with open(path, 'r') as f:
                rrpm = int(f.read())
        except IOError:
            return 0

        return rrpm

    def get_speeds(self):
        num_fan = self.get_num_fan();
        ret = "FAN_INDEX\t\tFRONT_RPM\t\tREAR_RPM\n"

        for i in range(1, num_fan+1):
            attr1 = "fan" + str(i) + "_front_rpm"
            attr2 = "fan" + str(i) + "_rear_rpm"
            path1 = pddf_obj.get_path("FAN-CTRL", attr1)
            path2 = pddf_obj.get_path("FAN-CTRL", attr2)
            try:
                with open(path1, 'r') as f1:
                    frpm = int(f1.read())
                with open(path2, 'r') as f2:
                    rrpm = int(f2.read())
            except IOError:
                return False

            ret += "FAN-%d\t\t\t%d\t\t\t%d\n"%(i, frpm, rrpm)

        return ret

    def set_speed(self, val):
        if val<0 or val>100:
            print "Error: Invalid speed %d. Please provide a valid speed percentage"%val
            return False
        
        num_fan = self.platform['num_fans']
        duty_cycle_to_pwm = eval(plugin_data['FAN']['duty_cycle_to_pwm'])
        pwm = duty_cycle_to_pwm(val)
        print "New Speed: %d%% - PWM value to be set is %d\n"%(val,pwm)

        status = 0
        for i in range(1, num_fan+1):
            attr = "fan" + str(i) + "_pwm"
            node = pddf_obj.get_path("FAN-CTRL", attr)
            try:
                with open(node, 'w') as f:
                    f.write(str(pwm))
            except IOError:
                return False

        return True

    def dump_sysfs(self):
        return pddf_obj.cli_dump_dsysfs('fan')

    def get_change_event(self):
        """
        TODO: This function need to be implemented
        when decide to support monitoring FAN(fand)
        on this platform.
        """
        raise NotImplementedError


