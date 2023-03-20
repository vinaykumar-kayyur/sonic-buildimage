#
# ssd_util.py
#
# Generic implementation of the SSD health API

try:
    import re
    import subprocess
    from sonic_platform_base.sonic_ssd.ssd_base import SsdBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

SMARTCTL = "smartctl {} -a"
INNODISK = "iSmart -d {}"
VIRTIUM  = "SmartCmd -m {}"

NOT_AVAILABLE = "N/A"


class SsdUtil(SsdBase):
    """
    Generic implementation of the SSD health API
    """
    model = NOT_AVAILABLE
    serial = NOT_AVAILABLE
    firmware = NOT_AVAILABLE
    temperature = NOT_AVAILABLE
    health = NOT_AVAILABLE
    ssd_info = NOT_AVAILABLE
    vendor_ssd_info = NOT_AVAILABLE

    def __init__(self, diskdev):
        self.vendor_ssd_utility = {
            "Generic" : { "utility" : SMARTCTL, "parser" : self.parse_generic_ssd_info }
        }

        self.model_attr = {
             "SATA ER2-GD240"        : { "temperature" : "190\s*(.+?)\n", "health" : "202\s*(.+?)\n" },
             "INTEL SSDSCKKB240G801" : { "temperature" : "194\s*(.+?)\n", "health" : "233\s*(.+?)\n" }
        }
        self.attr_info_rule = "[\s\S]*SMART Attributes Data Structure revision number: 1|SMART Error Log Version[\s\S]*"
        self.dev = diskdev
        # Generic part
        self.fetch_generic_ssd_info(diskdev)
        self.parse_generic_ssd_info()

    def _execute_shell(self, cmd):
        process = subprocess.Popen(cmd.split(), universal_newlines=True, stdout=subprocess.PIPE)
        output, error = process.communicate()
        exit_code = process.returncode
        if exit_code:
            return None
        return output

    def _parse_re(self, pattern, buffer):
        res_list = re.findall(pattern, buffer)
        return res_list[0] if res_list else NOT_AVAILABLE

    def fetch_generic_ssd_info(self, diskdev):
        self.ssd_info = self._execute_shell(self.vendor_ssd_utility["Generic"]["utility"].format(diskdev))

    def parse_generic_ssd_info(self):
        self.model = self._parse_re('Device Model:\s*(.+?)\n', self.ssd_info)
        self.serial = self._parse_re('Serial Number:\s*(.+?)\n', self.ssd_info)
        self.firmware = self._parse_re('Firmware Version:\s*(.+?)\n', self.ssd_info)
        self.health = self._parse_re(self.model_attr[self.model]["health"], re.sub(self.attr_info_rule,"",self.ssd_info)).split()[-7]
        self.temperature = self._parse_re(self.model_attr[self.model]["temperature"], re.sub(self.attr_info_rule,"",self.ssd_info)).split()[-1]
        self.vendor_ssd_info = re.sub(self.attr_info_rule,"",self.ssd_info)

    def get_health(self):
        """
        Retrieves current disk health in percentages
        Returns:
            A float number of current ssd health
            e.g. 83.5
        """
        return self.health

    def get_temperature(self):
        """
        Retrieves current disk temperature in Celsius
        Returns:
            A float number of current temperature in Celsius
            e.g. 40.1
        """
        return self.temperature

    def get_model(self):
        """
        Retrieves model for the given disk device
        Returns:
            A string holding disk model as provided by the manufacturer
        """
        return self.model

    def get_firmware(self):
        """
        Retrieves firmware version for the given disk device
        Returns:
            A string holding disk firmware version as provided by the manufacturer
        """
        return self.firmware

    def get_serial(self):
        """
        Retrieves serial number for the given disk device
        Returns:
            A string holding disk serial number as provided by the manufacturer
        """
        return self.serial

    def get_vendor_output(self):
        """
        Retrieves vendor specific data for the given disk device
        Returns:
            A string holding some vendor specific disk information
        """
        return self.vendor_ssd_info
