#!/usr/bin/env python3
# -*- coding: utf-8 -*-

########################################################################
# Ragile
#
# Module contains a platform specific implementation of SONiC Platform
# Base PCIe class
#
########################################################################

try:
    from sonic_platform_base.sonic_pcie.pcie_common import PcieUtil
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Pcie(PcieUtil):
    """Ragile Platform-specific Pcie class"""

    def __init__(self, platform_path):
        PcieUtil.__init__(self, platform_path)

