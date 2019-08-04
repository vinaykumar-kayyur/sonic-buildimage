#!/usr/bin/env python

#############################################################################
# Mellanox
#
# implementation of new platform api
#############################################################################

try:
    import subprocess
    from sonic_platform_base.platform_base import PlatformBase
    from sonic_platform.chassis import Chassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Platform(PlatformBase):
    def __init__(self):
        PlatformBase.__init__(self)
        if self._is_host():
            self._chassis = Chassis()
        else:
            self._chassis = Chassis()
            self._chassis.initialize_psu()
            self._chassis.initialize_fan()
            self._chassis.initialize_sfp()
            self._chassis.initialize_eeprom()
            self._chassis.initialize_components_list()

    def _is_host(self):
        """
        Test whether current process is running on the host or an docker
        return True for host and False for docker
        """
        try:
            subprocess.Popen("docker")
        except OSError, e:
            return False

        return True
