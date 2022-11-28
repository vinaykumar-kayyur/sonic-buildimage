#!/usr/bin/env python

try:
    import natsort
    from sonic_platform_pddf_base.pddf_sfp import PddfSfp
    from sonic_platform_base.sonic_sfp.sfputilhelper import SfpUtilHelper
    from sonic_py_common import device_info
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")


class Sfp(PddfSfp):
    """
    PDDF Platform-Specific Sfp class
    """

    def __init__(self, index, pddf_data=None, pddf_plugin_data=None):
        PddfSfp.__init__(self, index, pddf_data, pddf_plugin_data)

    # Provide the functions/variables below for which implementation is to be overwritten
    def get_position_in_parent(self):
        """Retrieves 1-based relative physical position in parent device."""
        return self.port_index
    
    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True    
