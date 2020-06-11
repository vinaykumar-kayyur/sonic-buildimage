#!/usr/bin/env python

try:
    import os
    import sys
    from sonic_platform_pddf_base.pddf_eeprom import PddfEeprom
except ImportError, e:
    raise ImportError(str(e) + "- required module not found")


class Eeprom(PddfEeprom):

    def __init__(self):
        PddfEeprom.__init__(self)

    # Provide the functions/variables below for which implementation is to be overwritten
