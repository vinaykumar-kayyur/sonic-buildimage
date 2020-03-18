import os
from sonic_platform_base.sonic_thermal_control.thermal_manager_base import ThermalManagerBase
from .thermal_actions import *
from .thermal_conditions import *
from .thermal_infos import *


class ThermalManager(ThermalManagerBase):
    @classmethod
    def start_thermal_control_algorithm(cls):
        """
        Start thermal control algorithm

        Returns:
            bool: True if set success, False if fail. 
        """
        from .thermal import Thermal
        Thermal.set_thermal_algorithm_status(True)

    @classmethod
    def stop_thermal_control_algorithm(cls):
        """
        Stop thermal control algorithm

        Returns:
            bool: True if set success, False if fail. 
        """
        from .thermal import Thermal
        Thermal.set_thermal_algorithm_status(False)


