from sonic_platform_base.sonic_thermal_control.thermal_action_base import ThermalPolicyActionBase
from sonic_platform_base.sonic_thermal_control.thermal_json_object import thermal_json_object
from sonic_daemon_base.daemon_base import Logger

__all__ = [
"SetAllFanSpeedMaxAction",
"SetAllFanSpeedDefaultAction",
"ThermalRecoverAction",
"SwitchPolicyAction",
]

logger = Logger('alpha')

class SetFanSpeedAction(ThermalPolicyActionBase):
    """
    Base thermal action class to set speed for fans
    """
    @classmethod
    def set_all_fan_speed(cls, thermal_info_dict, speed):
        from .thermal_infos import FanInfo
        if FanInfo.INFO_NAME in thermal_info_dict and isinstance(thermal_info_dict[FanInfo.INFO_NAME], FanInfo):
            fan_info_obj = thermal_info_dict[FanInfo.INFO_NAME]
            for fan in fan_info_obj.get_presence_fans():
                fan.set_speed(speed) 


@thermal_json_object('fan.all.set_speed_max')
class SetAllFanSpeedMaxAction(SetFanSpeedAction):
    """
    Action to set max speed for all fans
    """
    def execute(self, thermal_info_dict):
        """
        Set max speed for all fans
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        max_speed = 100
        SetAllFanSpeedMaxAction.set_all_fan_speed(thermal_info_dict, max_speed)

@thermal_json_object('fan.all.set_speed_default')
class SetAllFanSpeedDefaultAction(SetFanSpeedAction):
    """
    Action to set default speed for all fans
    """
    def execute(self, thermal_info_dict):
        """
        Set default speed for all fans
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        default_speed = 50
        SetAllFanSpeedDefaultAction.set_all_fan_speed(thermal_info_dict, default_speed)    


@thermal_json_object('thermal.temp_check_and_set_all_fan_speed')
class ThermalRecoverAction(SetFanSpeedAction):
    """
    Action to check thermal sensor temperature change status and set speed for all fans
    """
    def execute(self, thermal_info_dict):
        """
        Check check thermal sensor temperature change status and set speed for all fans
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        default_speed = 50
        max_speed = 100
        from .thermal_infos import ThermalInfo
        if ThermalInfo.INFO_NAME in thermal_info_dict and isinstance(thermal_info_dict[ThermalInfo.INFO_NAME], ThermalInfo):
            thermal_info_obj = thermal_info_dict[ThermalInfo.INFO_NAME]
            if thermal_info_obj.is_warm_up_and_over_high_threshold():
                ThermalRecoverAction.set_all_fan_speed(thermal_info_dict, max_speed)
            elif thermal_info_obj.is_cold_down_and_below_low_threshold():
                ThermalRecoverAction.set_all_fan_speed(thermal_info_dict, default_speed)


@thermal_json_object('switch.shutdown')
class SwitchPolicyAction(ThermalPolicyActionBase):
    """
    Base class for thermal action. Once all thermal conditions in a thermal policy are matched,
    all predefined thermal action will be executed.
    """
    def execute(self, thermal_info_dict):
        """
        Take action when thermal condition matches. For example, adjust speed of fan or shut
        down the switch.
        :param thermal_info_dict: A dictionary stores all thermal information.
        :return:
        """
        logger.log_warning("Alarm for temperature critical is detected, reboot DUT")
        # import os
        # os.system('reboot')
