#!/usr/bin/env python

#############################################################################
# Accton
#
# Module contains an implementation of SONiC FAN Base API and
# provides various info about the FANs which are available in the platform
#
#############################################################################

import os.path
import logging

try:
    from sonic_fan.fan_base import FanBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

class FanUtil(FanBase):
    """Platform-specific FANutil class"""

    FANTRAY_NUM_ON_MAIN_BOARD = 6
    NUM_FANS_PERTRAY = 2
    FANTRAY_NUM_1_IDX = 1
    FANTRAY_NUM_2_IDX = 2
    FANTRAY_NUM_3_IDX = 3
    FANTRAY_NUM_4_IDX = 4
    FANTRAY_NUM_5_IDX = 5
    FANTRAY_NUM_6_IDX = 6

    BASE_VAL_PATH = '/sys/bus/i2c/devices/0-005e/{0}'
    FAN_DUTY_PATH = '/sys/bus/i2c/devices/0-005e/fan_pwm'

    logger = logging.getLogger(__name__)

    def __init__(self, log_level=logging.DEBUG):
        FanBase.__init__(self)
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        self.logger.addHandler(ch)
        
        self.num_fans = (self.FANTRAY_NUM_ON_MAIN_BOARD*self.NUM_FANS_PERTRAY)

    def get_num_fans(self):
        return self.num_fans

    def get_status(self, index):
        if index is None:
            return False

        if index < self.FANTRAY_NUM_1_IDX or index > self.num_fans:
            self.logger.debug('Invalid FAN index:%d', index)
            return False

        status = 0
        tray_index = ((index-1)/self.NUM_FANS_PERTRAY) + 1
        attr_name = 'fan' + str(tray_index) + '_fault'
        node = self.BASE_VAL_PATH.format(attr_name)
        try:
            with open(node, 'r') as fault:
                status = int(fault.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return False

        return False if (status>0) else True

    def get_presence(self, index):
        if index is None:
            return False

        if index < self.FANTRAY_NUM_1_IDX or index > self.num_fans:
            self.logger.debug('Invalid FAN index:%d', index)
            return False

        status = 0
        tray_index = ((index-1)/self.NUM_FANS_PERTRAY) + 1
        attr_name = 'fan' + str(tray_index) + '_present'
        node = self.BASE_VAL_PATH.format(attr_name)
        try:
            with open(node, 'r') as presence_status:
                status = int(presence_status.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return False

        return status == 1

    def get_direction(self, index):
        if index is None:
            return None

        if index < self.FANTRAY_NUM_1_IDX or index > self.num_fans:
            self.logger.debug('Invalid FAN index:%d', index)
            return None

        direction = ""
        tray_index = ((index-1)/self.NUM_FANS_PERTRAY) + 1
        attr_name = 'fan' + str(tray_index) + '_direction'
        node = self.BASE_VAL_PATH.format(attr_name)
        try:
            with open(node, 'r') as fan_dir:
                direction = int(fan_dir.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return None

        if direction==1:
            return "INTAKE"
        else:
            return "EXHAUST"

    def get_speed(self, index):
        if index is None:
            return 0

        if index < self.FANTRAY_NUM_1_IDX or index > self.num_fans:
            self.logger.debug('Invalid FAN index:%d', index)
            return 0

        frpm = 0
        tray_index = ((index-1)/self.NUM_FANS_PERTRAY) + 1
        fan_type = 'front' if (index%self.NUM_FANS_PERTRAY) else 'rear'
        attr_name = 'fan' + str(tray_index) + '_{}_speed_rpm'.format(fan_type)
        node = self.BASE_VAL_PATH.format(attr_name)
        try:
            with open(node, 'r') as speed:
                frpm = int(speed.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return 0

        return frpm

    def set_speed(self, val):
        if val<0 or val>100:
            self.logger.debug('Error: Invalid speed %d. Please provide a valid duty-cycle percentage', val)
            return False

        node = self.FAN_DUTY_PATH
        val = int(round(val * 255.0 / 100))
        try:
            with open(node, 'w') as dc:
                dc.write(str(val))
        except IOError:
            return False

        return True
