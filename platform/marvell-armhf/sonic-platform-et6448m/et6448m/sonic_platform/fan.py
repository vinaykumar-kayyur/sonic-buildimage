#!/usr/bin/env python
########################################################################
# Marvell et6448m
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Fans' information which are available in the platform
#
########################################################################
try:
    import os
    from sonic_platform_base.fan_base import FanBase
    from sonic_platform.eeprom import Eeprom
    from sonic_daemon_base.daemon_base import Logger
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")
smbus_present = 1
try:
   import smbus
except ImportError as e:
   smbus_present = 0
MAX_FAN_SPEED = 19000
WORKING_FAN_SPEED = 960
logger = Logger('fan')
class Fan(FanBase):
    """Marvell platform-specific Fan class"""
    def __init__(self, fan_index, psu_fan=False, dependency=None):
        self.is_psu_fan = psu_fan
        SYS_ADT7473_DIR = "/sys/bus/i2c/devices/0-002e/"
        if not self.is_psu_fan:
            # Fan is 1-based in et6448m platforms
            self.index = fan_index + 1
            self.set_fan_speed_reg = SYS_ADT7473_DIR + "pwm{}".format(self.index)
            self.get_fan_speed_reg = SYS_ADT7473_DIR + "fan{}_input".format(self.index)
            #self.eeprom = Eeprom(is_fan=True, fan_index=self.index)
            self.max_fan_speed = MAX_FAN_SPEED
            self.supported_led_color = ['off', 'green', 'amber']
            if self.get_presence() and self.get_status():
                self.set_status_led(self.STATUS_LED_COLOR_GREEN)
        else:
            # this is a PSU Fan
            self.index = fan_index
            self.dependency = dependency
    def _get_i2c_register(self, reg_file):
        # On successful read, returns the value read from given
        # reg_name and on failure returns 'ERR'
        rv = 'ERR'
        if (not os.path.isfile(reg_file)):
            return rv
        try:
            with open(reg_file, 'r') as fd:
                rv = fd.read()
        except:
            rv = 'ERR'
        rv = rv.rstrip('\r\n')
        rv = rv.lstrip(" ")
        return rv
    def _set_i2c_register(self, reg_file, value):
        # On successful write, the value read will be written on
        # reg_name and on failure returns 'ERR'
        rv = 'ERR'
        if (not os.path.isfile(reg_file)):
            return rv
        try:
            with open(reg_file, 'w') as fd:
                rv = fd.write(str(value))
        except:
            rv = 'ERR'
        return rv
    def get_name(self):
        """
        Retrieves the name of the Fan
        Returns:
            string: The name of the Fan
        """
        if not self.is_psu_fan:
            return "Fan{}".format(self.index)
        else:
            return "PSU{} Fan".format(self.index)
    def get_presence(self):
        """
        Retrieves the presence of the Fan Unit
        Returns:
            bool: True if Fan is present, False if not
        """
        if smbus_present == 0:
            logger.log_info(" PMON fan - smbus ERROR - DEBUG presence   ")
        else :
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICE_REG = 0xb
            fanstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
        if self.index == 1:
            fanstatus = fanstatus&1
            if fanstatus == 1 :
                 return False
        if self.index == 2:
            fanstatus = fanstatus&2
            if fanstatus == 2 :
                return False
        return True
    def get_model(self):
        """
        Retrieves the model number of the Fan
        Returns:
            string: Part number of Fan
        """
        return 'NA'
    def get_serial(self):
        """
        Retrieves the serial number of the Fan
        Returns:
            string: Serial number of Fan
        """
        return 'NA'
    def get_status(self):
        """
        Retrieves the operational status of the Fan
        Returns:
            bool: True if Fan is operating properly, False if not
        """
        status = False
        fan_speed = self._get_i2c_register(self.get_fan_speed_reg)
        if (fan_speed != 'ERR'):
            if (int(fan_speed) > WORKING_FAN_SPEED):
                status = True
        return status
    def get_direction(self):
        """
        Retrieves the fan airflow direction
        Possible fan directions (relative to port-side of device)
        Returns:
            A string, either FAN_DIRECTION_INTAKE or
            FAN_DIRECTION_EXHAUST depending on fan direction
        """
        return 'FAN_DIRECTION_INTAKE'
    def get_speed(self):
        """
        Retrieves the speed of a Front FAN in the tray in revolutions per minute defined
                by 1-based index
        :param index: An integer, 1-based index of the FAN of which to query speed
        :return: integer, denoting front FAN speed
        """
        speed = 0
        fan_speed = self._get_i2c_register(self.get_fan_speed_reg)
        if (fan_speed != 'ERR'):
            speed = int(fan_speed)
        else:
            speed = 0
        return speed
    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan
        Returns:
            An integer, the percentage of variance from target speed
            which is considered tolerable
        """
        if self.get_presence():
            # The tolerance value is fixed as 25% for this platform
            tolerance = 25
        else:
            tolerance = 0
        return tolerance
    def set_speed(self, speed):
        """
        Set fan speed to expected value
        Args:
            speed: An integer, the percentage of full fan speed to set
            fan to, in the range 0 (off) to 100 (full speed)
        Returns:
            bool: True if set success, False if fail.
        """
        if self.is_psu_fan:
            return False
        # Set current fan duty cycle
        # - 0x00 : fan off
        # - 0x40 : 25% duty cycle
        # - 0x80 : 50% duty cycle (default)
        # - 0xff : 100% duty cycle (full speed)
        if speed in range(0,5):
            fandutycycle = 0x00
        elif speed in range(6,40):
            fandutycycle = 0x40
        elif speed in range(41,75):
            fandutycycle = 0x80
        elif speed in range(76,100):
            fandutycycle = 0x80
        else:
            return False
        rv = self._set_i2c_register(self.set_fan_speed_reg , fandutycycle )
        if (rv != 'ERR'):
            return True
        else:
            return False
    def set_status_led(self, color):
        """
        Set led to expected color
        Args:
            color: A string representing the color with which to set the
                   fan module status LED
        Returns:
            bool: True if set success, False if fail.
            off , amber and green are the only settings et6448m fans
        """
        if self.is_psu_fan or (color not in self.supported_led_color):
            return False
        if (color == self.STATUS_LED_COLOR_RED):
            return False
  #      bus = smbus.SMBus(0)
  #      DEVICE_ADDRESS = 0x41
  #      DEVICE_REG = 0x08
  #
  #      if self.index == 1:
  #          logger.log_info(" fan1 set_status_led  = %s  " % color )
  #
  #          #bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG, fanleds)
  #      if self.index == 2:
  #          logger.log_info(" fan2 set_status_led  = %s  " % color )
  #          #bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG, fanleds)
  #
  #      if (color == self.STATUS_LED_COLOR_AMBER):
  #          value = 0x01 << ((self.index - 1) * 2)
  #      elif (color == self.STATUS_LED_COLOR_GREEN):
  #          value = 0x02 << ((self.index - 1) * 2)
  #      elif (color == self.STATUS_LED_COLOR_OFF):
  #          value = 0x00 << ((self.index - 1) * 2)
  #      else:
  #          return False
        return True
    def get_status_led(self):
        """
        Gets the state of the fan status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
        if self.is_psu_fan:
            return False
  #      bus = smbus.SMBus(0)
  #      DEVICE_ADDRESS = 0x41
  #      DEVICE_REG = 0x08
  #      fanleds = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)
  #
  #      if self.index == 1:
  #          logger.log_info(" fan1 get_status_led  = %d  " % fanleds )
  #
  #      if self.index == 2:
  #          logger.log_info(" fan2 get_status_led  = %d  " % fanleds )
  #      logger.log_info("  fan get_status_led  = %d  " % self.index )
        return self.STATUS_LED_COLOR_GREEN
    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0
            (off) to 100 (full speed)
        """
        speed = 0
        fan_speed = self._get_i2c_register(self.get_fan_speed_reg)
        if (fan_speed != 'ERR'):
            speed = int(fan_speed)
        else:
            speed = 0
        return speed

