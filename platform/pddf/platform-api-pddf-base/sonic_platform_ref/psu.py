#!/usr/bin/env python
#


try:
    import os.path
    import sys, traceback
    from sonic_platform_pddf_base.pddf_psu import PddfPsu
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")


class Psu(PddfPsu):
    """PDDF Platform-Specific PSU class"""

    def __init__(self, index):
        PddfPsu.__init__(self, index)
        
    # Provide the functions/variables below for which implementation is to be overwritten

