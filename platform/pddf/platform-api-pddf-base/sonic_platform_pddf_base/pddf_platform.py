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
    #sys.path.append('/usr/share/sonic/platform')
    from sonic_platform_base.platform_base import PlatformBase
    from sonic_platform.chassis import Chassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class PddfPlatform(PlatformBase):
    """
    PDDF Generic Platform class
    """

    def __init__(self):
        PlatformBase.__init__(self)
        self._chassis = Chassis()



# For testing, remove later on
#if __name__=="__main__":
    #obj = Platform()
