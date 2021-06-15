import os
from sonic_py_common.logger import Logger

from . import utils

logger = Logger()
SN_VPD_FIELD = "SN_VPD_FIELD"
PN_VPD_FIELD = "PN_VPD_FIELD"
REV_VPD_FIELD = "REV_VPD_FIELD"


class VpdParser:
    def __init__(self, file_path):
        self.vpd_data = {}
        self.vpd_file = file_path
        self.vpd_file_last_mtime = None

    def _read_data(self):
        if not os.path.exists(self.vpd_file):
            self.vpd_data = {}
            return

        try:
            mtime = os.stat(self.vpd_file).st_mtime
            if mtime != self.vpd_file_last_mtime:
                self.vpd_file_last_mtime = mtime
                self.vpd_data = utils.read_key_value_file(self.vpd_file)
        except Exception as e:
            self.vpd_data = {}
        
    def _get_data(self):
        self._read_data()
        return self.vpd_data

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        vpd_data = self._get_data()
        if PN_VPD_FIELD not in vpd_data:
            logger.log_error("Fail to read model number: No key {} in VPD {}".format(PN_VPD_FIELD, self.vpd_file))
            return ''
        return vpd_data[PN_VPD_FIELD]

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        vpd_data = self._get_data()
        if SN_VPD_FIELD not in vpd_data:
            logger.log_error("Fail to read serial number: No key {} in VPD {}".format(SN_VPD_FIELD, self.vpd_file))
            return ''
        return vpd_data[SN_VPD_FIELD]

    def get_revision(self):
        """
        Retrieves the hardware revision of the device

        Returns:
            string: Revision value of device
        """
        vpd_data = self._get_data()
        if REV_VPD_FIELD not in vpd_data:
            logger.log_error("Fail to read revision: No key {} in VPD {}".format(REV_VPD_FIELD, self.vpd_file))
            return ''
        return vpd_data[REV_VPD_FIELD]
