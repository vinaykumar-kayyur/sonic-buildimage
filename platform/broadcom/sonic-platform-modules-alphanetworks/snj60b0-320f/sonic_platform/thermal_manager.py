from sonic_platform_base.sonic_thermal_control.thermal_manager_base import ThermalManagerBase
from .thermal_infos import FanInfo
from .thermal_infos import ThermalInfo
from .thermal_infos import ChassisInfo
from .thermal_conditions import AnyFanAbsenceCondition
from .thermal_conditions import AllFanAbsenceCondition
from .thermal_conditions import AllFanPresenceCondition
from .thermal_conditions import AnyFanFaultCondition
from .thermal_conditions import AllFanGoodCondition
from .thermal_conditions import AnyFanPresenceChangeCondition
from .thermal_conditions import ThermalOverHighCriticalCondition
from .thermal_actions import SetAllFanSpeedMaxAction
from .thermal_actions import SetAllFanSpeedDefaultAction
from .thermal_actions import ThermalRecoverAction
from .thermal_actions import SwitchPolicyAction

class ThermalManager(ThermalManagerBase):
    @classmethod
    def initialize(cls):
        """
        Initialize thermal manager, including register thermal condition types and thermal action types
        and any other vendor specific initialization.
        :return:
        """
        return True

    @classmethod
    def deinitialize(cls):
        """
        Destroy thermal manager, including any vendor specific cleanup. The default behavior of this function
        is a no-op.
        :return:
        """
        return True
