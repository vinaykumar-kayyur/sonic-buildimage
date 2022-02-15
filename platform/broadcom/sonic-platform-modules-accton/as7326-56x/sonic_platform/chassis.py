#!/usr/bin/env python

#############################################################################
# PDDF
# Module contains an implementation of SONiC Chassis API
#
#############################################################################

try:
    import json
    import sys
    from sonic_platform_pddf_base.pddf_chassis import PddfChassis
    from .event import SfpEvent
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_COMPONENT = 4
CONFIG_DB_PATH = "/etc/sonic/config_db.json"

class Chassis(PddfChassis):
    """
    PDDF Platform-specific Chassis class
    """

    SYSLED_DEV_NAME = "DIAG_LED"
    def __init__(self, pddf_data=None, pddf_plugin_data=None):
        PddfChassis.__init__(self, pddf_data, pddf_plugin_data)
        self.__initialize_components()
        self._sfpevent = SfpEvent(self.get_all_sfps())

    def __initialize_components(self):
        from sonic_platform.component import Component
        for index in range(NUM_COMPONENT):
            component = Component(index)
            self._component_list.append(component)

    # Provide the functions/variables below for which implementation is to be overwritten
    def get_change_event(self, timeout=0):
        return self._sfpevent.get_sfp_event(timeout)
    
    def get_sfp(self, index):
        """
        Retrieves sfp represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the sfp to retrieve.
                   The index should be the sequence of a physical port in a chassis,
                   starting from 0.
                   For example, 0 for Ethernet0, 1 for Ethernet4 and so on.

        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None

        try:
            # The index will start from 1
            sfp = self._sfp_list[index-1]
            
        except IndexError:
            sys.stderr.write("SFP index {} out of range (0-{})\n".format(
                             index, len(self._sfp_list)-1))
        return sfp

    def initizalize_system_led(self):
        return

    def get_status_led(self):  # originally, it is set_status_led(self, color), but it will cause thermalctld fail
        return self.get_system_led(self.SYSLED_DEV_NAME)

    def set_status_led(self, color):
        return self.set_system_led(self.SYSLED_DEV_NAME, color)
