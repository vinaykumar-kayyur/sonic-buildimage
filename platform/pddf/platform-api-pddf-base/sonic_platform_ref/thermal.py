#!/usr/bin/env python


try:
    import os.path
    import sys, traceback
    from sonic_platform_pddf_base.pddf_thermal import PddfThermal
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")



class Thermal(PddfThermal):
    """PDDF Platform-Specific Thermal class"""

    def __init__(self, index):
        PddfThermal.__init__(self, index)

    # Provide the functions/variables below for which implementation is to be overwritten

#temp=ThermalUtil()
#num_temps = temp.get_num_thermals()
##temp.get_thermal_info()
#temp.show_temp_values()
