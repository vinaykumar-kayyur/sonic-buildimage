try:
    from sonic_platform_base.sonic_pcie.pcie_common import PcieUtil

    from sonic_platform.eeprom import Eeprom
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Pcie(PcieUtil):
    def __init__(self, platform_path):
        PcieUtil.__init__(self, platform_path)

        if Eeprom().get_data()['0x21'] == 'Wedge100BF-32X-O-HVDC':
            self._conf_rev = 2
