#############################################################################
# Mellanox
#
# Module contains an implementation of SONiC Platform Base API and
# provides the FANs status which are available in the platform
#
#############################################################################

import os.path
import subprocess

try:
    from sonic_platform_base.fan_base import FanBase
    from sonic_py_common.logger import Logger
    from .led import FanLed, ComponentFaultyIndicator
    from . import utils
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

# Global logger class instance
logger = Logger()

PWM_MAX = 255

FAN_PATH = "/var/run/hw-management/thermal/"
CONFIG_PATH = "/var/run/hw-management/config"

FAN_DIR = "/var/run/hw-management/thermal/fan{}_dir"
FAN_DIR_VALUE_EXHAUST = 0
FAN_DIR_VALUE_INTAKE = 1
COOLING_STATE_PATH = "/var/run/hw-management/thermal/cooling_cur_state"


class MlnxFan(FanBase):
    MIN_VALID_COOLING_LEVEL = 1
    MAX_VALID_COOLING_LEVEL = 10
    
    def __init__(self, fan_index, position):
        super(MlnxFan, self).__init__()
        self.index = fan_index + 1
        self.position = position

    def get_name(self):
        return self._name

    def get_speed(self):
        """
        Retrieves the speed of fan

        Returns:
            int: percentage of the max fan speed
        """
        speed = 0
        speed_in_rpm = utils.read_int_from_file(self.fan_speed_get_path)

        max_speed_in_rpm = utils.read_int_from_file(self.fan_max_speed_path)
        if max_speed_in_rpm == 0:
            return speed_in_rpm

        speed = 100*speed_in_rpm//max_speed_in_rpm
        if speed > 100:
            speed = 100

        return speed

    def set_status_led(self, color):
        """
        Set led to expected color

        Args:
            color: A string representing the color with which to set the
                   fan module status LED

        Returns:
            bool: True if set success, False if fail. 
        """
        return self.led.set_status(color)

    def get_status_led(self):
        """
        Gets the state of the fan status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        return self.led.get_status()

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan

        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        # The tolerance value is fixed as 50% for all the Mellanox platform
        return 50

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device
        Returns:
            integer: The 1-based relative physical position in parent device
        """
        return self.position

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return False

    @classmethod
    def set_cooling_level(cls, level, cur_state):
        """
        Change cooling level. The input level should be an integer value [1, 10].
        1 means 10%, 2 means 20%, 10 means 100%.
        """
        if level < cls.MIN_VALID_COOLING_LEVEL or level > cls.MAX_VALID_COOLING_LEVEL:
            raise RuntimeError("Failed to set cooling level, level value must be in range [{}, {}], got {}".format(
                cls.MIN_VALID_COOLING_LEVEL,
                cls.MAX_VALID_COOLING_LEVEL,
                level
                ))

        try:
            # Reset FAN cooling level vector. According to low level team,
            # if we need set cooling level to X, we need first write a (10+X) 
            # to cooling_cur_state file to reset the cooling level vector.
            utils.write_file(COOLING_STATE_PATH, level + 10, raise_exception=True)

            # We need set cooling level after resetting the cooling level vector 
            utils.write_file(COOLING_STATE_PATH, cur_state, raise_exception=True)
        except (ValueError, IOError) as e:
            raise RuntimeError("Failed to set cooling level - {}".format(e))

    @classmethod
    def get_cooling_level(cls):
        try:
            return utils.read_int_from_file(COOLING_STATE_PATH, raise_exception=True)
        except (ValueError, IOError) as e:
            raise RuntimeError("Failed to get cooling level - {}".format(e))


class PsuFan(MlnxFan):
    # PSU fan speed vector
    PSU_FAN_SPEED = ['0x3c', '0x3c', '0x3c', '0x3c', '0x3c',
                     '0x3c', '0x3c', '0x46', '0x50', '0x5a', '0x64']

    def __init__(self, fan_index, position, psu):
        super(PsuFan, self).__init__(fan_index, position)
        self._name = 'psu{}_fan{}'.format(self.index, position)
        self.psu = psu

        from .psu import Psu
        self.led = ComponentFaultyIndicator(Psu.get_shared_led())
        self.fan_speed_get_path = os.path.join(FAN_PATH, "psu{}_fan1_speed_get".format(self.index))
        self.fan_presence_path = os.path.join(FAN_PATH, "psu{}_fan1_speed_get".format(self.index))
        self.fan_max_speed_path = os.path.join(CONFIG_PATH, "psu_fan_max")
        self.fan_min_speed_path = os.path.join(CONFIG_PATH, "psu_fan_min")
        self.psu_i2c_bus_path = os.path.join(CONFIG_PATH, 'psu{0}_i2c_bus'.format(self.index))
        self.psu_i2c_addr_path = os.path.join(CONFIG_PATH, 'psu{0}_i2c_addr'.format(self.index))
        self.psu_i2c_command_path = os.path.join(CONFIG_PATH, 'fan_command')

    def get_direction(self):
        """
        Retrieves the fan's direction

        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction

        Notes:
            What Mellanox calls forward: 
            Air flows from fans side to QSFP side, for example: MSN2700-CS2F
            which means intake in community
            What Mellanox calls reverse:
            Air flow from QSFP side to fans side, for example: MSN2700-CS2R
            which means exhaust in community
            According to hw-mgmt:
                1 stands for forward, in other words intake
                0 stands for reverse, in other words exhaust
        """
        return self.FAN_DIRECTION_NOT_APPLICABLE

    def get_status(self):
        """
        Retrieves the operational status of fan

        Returns:
            bool: True if fan is operating properly, False if not
        """
        return True

    def get_presence(self):
        """
        Retrieves the presence status of fan

        Returns:
            bool: True if fan is present, False if not
        """
        return self.psu.get_presence() and self.psu.get_powergood_status() and os.path.exists(self.fan_presence_path)

    def get_target_speed(self):
        """
        Retrieves the expected speed of fan

        Returns:
            int: percentage of the max fan speed
        """
        try:
            # Get PSU fan target speed according to current system cooling level
            cooling_level = self.get_cooling_level()
            return int(self.PSU_FAN_SPEED[cooling_level], 16)
        except Exception:
            return self.get_speed()

    def set_speed(self, speed):
        """
        Set fan speed to expected value

        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)

        Returns:
            bool: True if set success, False if fail. 
        """
        if not self.get_presence():
            return False

        try:
            bus = utils.read_str_from_file(self.psu_i2c_bus_path, raise_exception=True)
            addr = utils.read_str_from_file(self.psu_i2c_addr_path, raise_exception=True)
            command = utils.read_str_from_file(self.psu_i2c_command_path, raise_exception=True)
            speed = self.PSU_FAN_SPEED[int(speed // 10)]
            command = "i2cset -f -y {0} {1} {2} {3} wp".format(bus, addr, command, speed)
            subprocess.check_call(command, shell = True, universal_newlines=True)
            return True
        except subprocess.CalledProcessError as ce:
            logger.log_error('Failed to call command {}, return code={}, command output={}'.format(ce.cmd, ce.returncode, ce.output))
            return False
        except Exception as e:
            logger.log_error('Failed to set PSU FAN speed - {}'.format(e))
            return False

class Fan(MlnxFan):
    """Platform-specific Fan class"""

    min_cooling_level = 2

    def __init__(self, fan_index, fan_drawer, position):
        super(Fan, self).__init__(fan_index, position)
    
        self.fan_drawer = fan_drawer
        self.led = ComponentFaultyIndicator(self.fan_drawer.get_led())

        self._name = "fan{}".format(self.index)
        self.fan_speed_get_path = os.path.join(FAN_PATH, "fan{}_speed_get".format(self.index))
        self.fan_speed_set_path = os.path.join(FAN_PATH, "fan{}_speed_set".format(self.index))
        self.fan_max_speed_path = os.path.join(FAN_PATH, "fan{}_max".format(self.index))
        self.fan_min_speed_path = os.path.join(FAN_PATH, "fan{}_min".format(self.index))
        
        self.fan_status_path = os.path.join(FAN_PATH, "fan{}_fault".format(self.index))

    def get_direction(self):
        """
        Retrieves the fan's direction

        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction

        Notes:
            What Mellanox calls forward: 
            Air flows from fans side to QSFP side, for example: MSN2700-CS2F
            which means intake in community
            What Mellanox calls reverse:
            Air flow from QSFP side to fans side, for example: MSN2700-CS2R
            which means exhaust in community
            According to hw-mgmt:
                1 stands for forward, in other words intake
                0 stands for reverse, in other words exhaust
        """
        return self.fan_drawer.get_direction()

    def get_status(self):
        """
        Retrieves the operational status of fan

        Returns:
            bool: True if fan is operating properly, False if not
        """

        return utils.read_int_from_file(self.fan_status_path, 1) == 0

    def get_presence(self):
        """
        Retrieves the presence status of fan

        Returns:
            bool: True if fan is present, False if not
        """
        return self.fan_drawer.get_presence()

    def get_target_speed(self):
        """
        Retrieves the expected speed of fan

        Returns:
            int: percentage of the max fan speed
        """
        pwm = utils.read_int_from_file(self.fan_speed_set_path)
        return int(round(pwm*100.0/PWM_MAX))

    def set_speed(self, speed):
        """
        Set fan speed to expected value

        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)

        Returns:
            bool: True if set success, False if fail. 
        """
        status = True

        try:
            cooling_level = int(speed // 10)
            if cooling_level < self.min_cooling_level:
                cooling_level = self.min_cooling_level
                speed = self.min_cooling_level * 10
            self.set_cooling_level(cooling_level, cooling_level)
            pwm = int(PWM_MAX*speed/100.0)
            utils.write_file(self.fan_speed_set_path, pwm, raise_exception=True)
        except (ValueError, IOError):
            status = False

        return status
