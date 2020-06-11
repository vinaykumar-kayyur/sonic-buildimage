#!/usr/bin/env python

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
#
#############################################################################


try:
    import os
    import sys
    sys.path.append('/usr/share/sonic/device/pddf/sonic_platform')
    from sonic_platform_pddf_base.pddf_platform import PddfPlatform
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Platform(PddfPlatform):
    """
    PDDF Platform-Specific Platform Class
    """

    def __init__(self):
        PddfPlatform.__init__(self)

    # Provide the functions/variables below for which implementation is to be overwritten


# For testing, remove later on
#if __name__=="__main__":
    #obj = Platform()
