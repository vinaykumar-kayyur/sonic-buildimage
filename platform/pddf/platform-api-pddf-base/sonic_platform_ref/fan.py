#!/usr/bin/env python


try:
    import os.path
    import sys
    from sonic_platform_pddf_base.pddf_fan import PddfFan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Fan(PddfFan):
    """PDDF Platform-Specific Fan class"""

    def __init__(self, tray_idx, fan_idx=0, is_psu_fan=False, psu_index=0):
        # idx is 0-based 
        PddfFan.__init__(self, tray_idx, fan_idx, is_psu_fan, psu_index)

    # Provide the functions/variables below for which implementation is to be overwritten e.g.
    #def get_name(self):
        #if self.is_psu_fan:
            #return "PSU_FAN{}".format(self.fan_index)
        #else:
            #return "Fantray{}_{}".format(self.fantray_index, {1:'Front', 2:'Rear'}.get(self.fan_index,'none'))

