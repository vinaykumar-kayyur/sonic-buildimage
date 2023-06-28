#!/usr/bin/env python

#############################################################################
# Sfp contains an implementation of SONiC Platform Base API and
# provides the sfp device status which are available in the platform
#############################################################################
try:
    from sonic_platform_base.sfp_base import SfpBase
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436InterfaceId
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436Dom
    from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_InterfaceId
    from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_Dom
    from sonic_platform_base.sonic_sfp.sffbase import sffbase
    from sonic_platform_base.sonic_sfp.sff8024 import type_abbrv_name
    from sonic_platform_base.sonic_sfp.sff8024 import type_of_media_interface
    from sonic_py_common.logger import Logger
    import sys
    import time
    import subprocess
    import os
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

# definitions of the offset and width for values in XCVR info eeprom
XCVR_INTFACE_BULK_OFFSET = 0
XCVR_INTFACE_BULK_WIDTH_QSFP = 20
XCVR_INTFACE_BULK_WIDTH_SFP = 21
XCVR_TYPE_OFFSET = 0
XCVR_TYPE_WIDTH = 1
XCVR_EXT_TYPE_OFFSET = 1
XCVR_EXT_TYPE_WIDTH = 1
XCVR_CONNECTOR_OFFSET = 2
XCVR_CONNECTOR_WIDTH = 1
XCVR_COMPLIANCE_CODE_OFFSET = 3
XCVR_COMPLIANCE_CODE_WIDTH = 8
XCVR_ENCODING_OFFSET = 11
XCVR_ENCODING_WIDTH = 1
XCVR_NBR_OFFSET = 12
XCVR_NBR_WIDTH = 1
XCVR_EXT_RATE_SEL_OFFSET = 13
XCVR_EXT_RATE_SEL_WIDTH = 1
XCVR_CABLE_LENGTH_OFFSET = 14
XCVR_CABLE_LENGTH_WIDTH_QSFP = 5
XCVR_CABLE_LENGTH_WIDTH_SFP = 6
XCVR_VENDOR_NAME_OFFSET = 20
XCVR_VENDOR_NAME_WIDTH = 16
XCVR_VENDOR_OUI_OFFSET = 37
XCVR_VENDOR_OUI_WIDTH = 3
XCVR_VENDOR_PN_OFFSET = 40
XCVR_VENDOR_PN_WIDTH = 16
XCVR_HW_REV_OFFSET = 56
XCVR_HW_REV_WIDTH_OSFP = 2
XCVR_HW_REV_WIDTH_QSFP = 2
XCVR_HW_REV_WIDTH_SFP = 4
XCVR_EXT_SPECIFICATION_COMPLIANCE_OFFSET = 64
XCVR_EXT_SPECIFICATION_COMPLIANCE_WIDTH = 1
XCVR_VENDOR_SN_OFFSET = 68
XCVR_VENDOR_SN_WIDTH = 16
XCVR_VENDOR_DATE_OFFSET = 84
XCVR_VENDOR_DATE_WIDTH = 8
XCVR_DOM_CAPABILITY_OFFSET = 92
XCVR_DOM_CAPABILITY_WIDTH = 2

# definitions of the offset and width for values in XCVR_QSFP_DD info eeprom
XCVR_EXT_TYPE_OFFSET_QSFP_DD = 72
XCVR_EXT_TYPE_WIDTH_QSFP_DD = 2
XCVR_CONNECTOR_OFFSET_QSFP_DD = 75
XCVR_CONNECTOR_WIDTH_QSFP_DD = 1
XCVR_CABLE_LENGTH_OFFSET_QSFP_DD = 74
XCVR_CABLE_LENGTH_WIDTH_QSFP_DD = 1
XCVR_HW_REV_OFFSET_QSFP_DD = 36
XCVR_HW_REV_WIDTH_QSFP_DD = 2
XCVR_VENDOR_DATE_OFFSET_QSFP_DD = 54
XCVR_VENDOR_DATE_WIDTH_QSFP_DD = 8
XCVR_DOM_CAPABILITY_OFFSET_QSFP_DD = 2
XCVR_DOM_CAPABILITY_WIDTH_QSFP_DD = 1
XCVR_MEDIA_TYPE_OFFSET_QSFP_DD = 85
XCVR_MEDIA_TYPE_WIDTH_QSFP_DD = 1
XCVR_FIRST_APPLICATION_LIST_OFFSET_QSFP_DD = 86
XCVR_FIRST_APPLICATION_LIST_WIDTH_QSFP_DD = 32
XCVR_SECOND_APPLICATION_LIST_OFFSET_QSFP_DD = 351
XCVR_SECOND_APPLICATION_LIST_WIDTH_QSFP_DD = 28

XCVR_INTERFACE_DATA_START = 0
XCVR_INTERFACE_DATA_SIZE = 92
SFP_MODULE_ADDRA2_OFFSET = 256
SFP_MODULE_THRESHOLD_OFFSET = 0
SFP_MODULE_THRESHOLD_WIDTH = 56

QSFP_DOM_BULK_DATA_START = 22
QSFP_DOM_BULK_DATA_SIZE = 36
SFP_DOM_BULK_DATA_START = 96
SFP_DOM_BULK_DATA_SIZE = 10

QSFP_DD_DOM_BULK_DATA_START = 14
QSFP_DD_DOM_BULK_DATA_SIZE = 4

# definitions of the offset for values in OSFP info eeprom
OSFP_TYPE_OFFSET = 0
OSFP_VENDOR_NAME_OFFSET = 129
OSFP_VENDOR_PN_OFFSET = 148
OSFP_HW_REV_OFFSET = 164
OSFP_VENDOR_SN_OFFSET = 166

# definitions of the offset for values in QSFP_DD info eeprom
QSFP_DD_TYPE_OFFSET = 0
QSFP_DD_VENDOR_NAME_OFFSET = 1
QSFP_DD_VENDOR_PN_OFFSET = 20
QSFP_DD_VENDOR_SN_OFFSET = 38
QSFP_DD_VENDOR_OUI_OFFSET = 17

#definitions of the offset and width for values in DOM info eeprom
QSFP_DOM_REV_OFFSET = 1
QSFP_DOM_REV_WIDTH = 1
QSFP_TEMPE_OFFSET = 22
QSFP_TEMPE_WIDTH = 2
QSFP_VOLT_OFFSET = 26
QSFP_VOLT_WIDTH = 2
QSFP_VERSION_COMPLIANCE_OFFSET = 1
QSFP_VERSION_COMPLIANCE_WIDTH = 2
QSFP_CHANNL_MON_OFFSET = 34
QSFP_CHANNL_MON_WIDTH = 16
QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH = 24
QSFP_CHANNL_DISABLE_STATUS_OFFSET = 86
QSFP_CHANNL_DISABLE_STATUS_WIDTH = 1
QSFP_CHANNL_RX_LOS_STATUS_OFFSET = 3
QSFP_CHANNL_RX_LOS_STATUS_WIDTH = 1
QSFP_CHANNL_TX_FAULT_STATUS_OFFSET = 4
QSFP_CHANNL_TX_FAULT_STATUS_WIDTH = 1
QSFP_CONTROL_OFFSET = 86
QSFP_CONTROL_WIDTH = 8
QSFP_MODULE_MONITOR_OFFSET = 0
QSFP_MODULE_MONITOR_WIDTH = 9
QSFP_POWEROVERRIDE_OFFSET = 93
QSFP_POWEROVERRIDE_WIDTH = 1
QSFP_POWEROVERRIDE_BIT = 0
QSFP_POWERSET_BIT = 1
QSFP_OPTION_VALUE_OFFSET = 192
QSFP_OPTION_VALUE_WIDTH = 4

QSFP_MODULE_UPPER_PAGE3_START = 384
QSFP_MODULE_THRESHOLD_OFFSET = 0
QSFP_MODULE_THRESHOLD_WIDTH = 24
QSFP_CHANNL_THRESHOLD_OFFSET = 48
QSFP_CHANNL_THRESHOLD_WIDTH = 24

#definitions of the offset and width for values in DOM info eeprom
QSFP_DD_TEMPE_OFFSET = 14
QSFP_DD_TEMPE_WIDTH = 2
QSFP_DD_VOLT_OFFSET = 16
QSFP_DD_VOLT_WIDTH = 2
QSFP_DD_TX_BIAS_OFFSET = 42
QSFP_DD_TX_BIAS_WIDTH = 16
QSFP_DD_RX_POWER_OFFSET = 58
QSFP_DD_RX_POWER_WIDTH = 16
QSFP_DD_TX_POWER_OFFSET = 26
QSFP_DD_TX_POWER_WIDTH = 16
QSFP_DD_CHANNL_FLAGS_SUPPORT_OFFSET = 29
QSFP_DD_CHANNL_FLAGS_SUPPORT_WIDTH = 2
QSFP_DD_CHANNL_MON_SUPPORT_OFFSET = 31
QSFP_DD_CHANNL_MON_SUPPORT_WIDTH = 2
QSFP_DD_CHANNL_MON_OFFSET = 154
QSFP_DD_CHANNL_MON_WIDTH = 48
QSFP_DD_CHANNL_DISABLE_STATUS_OFFSET = 2
QSFP_DD_CHANNL_DISABLE_STATUS_WIDTH = 1
QSFP_DD_CHANNL_RX_LOS_STATUS_OFFSET = 19
QSFP_DD_CHANNL_RX_LOS_STATUS_WIDTH = 1
QSFP_DD_CHANNL_TX_FAULT_STATUS_OFFSET = 7
QSFP_DD_CHANNL_TX_FAULT_STATUS_WIDTH = 1
QSFP_DD_MODULE_THRESHOLD_OFFSET = 0
QSFP_DD_MODULE_THRESHOLD_WIDTH = 72
QSFP_DD_CHANNL_STATUS_OFFSET = 26
QSFP_DD_CHANNL_STATUS_WIDTH = 1

QSFP_TYPE_CODE_LIST = [
    '0d', # QSFP+ or later
    '11' # QSFP28 or later
]

QSFP_DD_TYPE_CODE_LIST = [
    '18' # QSFP-DD Double Density 8X Pluggable Transceiver
]

qsfp_cable_length_tup = ('Length(km)', 'Length OM3(2m)',
                         'Length OM2(m)', 'Length OM1(m)',
                         'Length Cable Assembly(m)')

sfp_cable_length_tup = ('LengthSMFkm-UnitsOfKm', 'LengthSMF(UnitsOf100m)',
                        'Length50um(UnitsOf10m)', 'Length62.5um(UnitsOfm)',
                        'LengthCable(UnitsOfm)', 'LengthOM3(UnitsOf10m)')

sfp_compliance_code_tup = ('10GEthernetComplianceCode', 'InfinibandComplianceCode',
                            'ESCONComplianceCodes', 'SONETComplianceCodes',
                            'EthernetComplianceCodes','FibreChannelLinkLength',
                            'FibreChannelTechnology', 'SFP+CableTechnology',
                            'FibreChannelTransmissionMedia','FibreChannelSpeed')

qsfp_compliance_code_tup = ('10/40G Ethernet Compliance Code', 'SONET Compliance codes',
                            'SAS/SATA compliance codes', 'Gigabit Ethernet Compliant codes',
                            'Fibre Channel link length/Transmitter Technology',
                            'Fibre Channel transmission media', 'Fibre Channel Speed')

QSFP_TYPE = "QSFP"
QSFP_DD_TYPE = "QSFP_DD"

PAUSE_EEPROM_SERVICE_STAMP='/tmp/pause_eeprom_polling'

# Global logger class instance
logger = Logger()

VDM_FREEZE = 128
VDM_UNFREEZE = 0


class ext_qsfp_dd(sffbase):
    version = '1.0'

    qsfp_dd_mon_capability = {
        'Tx_bias_support':
            {'offset': 1,
             'bit': 0,
             'type': 'bitvalue'},
        'Tx_power_support':
            {'offset': 1,
             'bit': 1,
             'type': 'bitvalue'},
        'Rx_power_support':
            {'offset': 1,
             'bit': 2,
             'type': 'bitvalue'},
        'Voltage_support':
            {'offset': 0,
             'bit': 1,
             'type': 'bitvalue'},
        'Temp_support':
            {'offset': 0,
             'bit': 0,
             'type': 'bitvalue'}
    }

    qsfp_dd_flags_capability = {
        'tx_fault':
            {'offset': 0,
             'bit': 0,
             'type': 'bitvalue'},
        'rx_los':
            {'offset': 1,
             'bit': 1,
             'type': 'bitvalue'}
    }

    def parse_mon_capability(self, sn_raw_data, start_pos):
        return sffbase.parse(self, self.qsfp_dd_mon_capability, sn_raw_data, start_pos)

    def parse_flags_capability(self, sn_raw_data, start_pos):
        return sffbase.parse(self, self.qsfp_dd_flags_capability, sn_raw_data, start_pos)

class Sfp(SfpBase):
    """Platform-specific Sfp class"""

    # Port number
    PORT_START = 0
    PORT_END = 31

    port_to_i2c_mapping = {
        0: '10',
        1: '11',
        2: '12',
        3: '13',
        4: '14',
        5: '15',
        6: '16',
        7: '17',
        8: '18',
        9: '19',
        10: '1a',
        11: '1b',
        12: '1c',
        13: '1d',
        14: '1e',
        15: '1f',
        16: '20',
        17: '21',
        18: '22',
        19: '23',
        20: '24',
        21: '25',
        22: '26',
        23: '27',
        24: '28',
        25: '29',
        26: '2a',
        27: '2b',
        28: '2c',
        29: '2d',
        30: '2e',
        31: '2f',
    }

    _sfp_port = range(32, PORT_END + 1)
    RESET_1_16_PATH = "/sys/bus/i2c/devices/0-0006/port{}_reset"
    RESET_17_32_PATH = "/sys/bus/i2c/devices/0-0007/port{}_reset"
    PRS_1_16_PATH = "/sys/bus/i2c/devices/0-0006/port{}_present"
    PRS_17_32_PATH = "/sys/bus/i2c/devices/0-0007/port{}_present"
    LPMODE_1_16_PATH = "/sys/bus/i2c/devices/0-0006/port{}_lpmode"
    LPMODE_17_32_PATH = "/sys/bus/i2c/devices/0-0007/port{}_lpmode"

    def __init__(self, sfp_index, sfp_type):
        # Init index
        self.index = sfp_index
        self.port_num = self.index + 1
        self.abbrv = None

        # Init eeprom path
        eeprom_path_prefix = '/sys/bus/i2c/devices/0-00'
        self.port_to_eeprom1_mapping = {}
        self.port_to_eeprom2_mapping = {}
        self.port_to_eeprom3_mapping = {}
        self.port_to_eeprom4_mapping = {}
        self.port_to_eeprom12_mapping = {}
        self.port_to_power_mode_mapping = {}
        self.port_to_grid_mapping = {}
        self.port_to_freq_mapping = {}
        self.port_to_outp_mapping = {}
        self.port_to_curr_freq_mapping = {}
        self.port_to_fine_tune_freq = {}
        self.port_to_eeprom2f_mapping = {}
        self.port_to_eeprom34_mapping = {}
        self.port_to_eeprom35_mapping = {}
        self.port_to_vdm_freeze_mapping = {}
        for x in range(self.PORT_START, self.PORT_END + 1):
            self.port_to_eeprom1_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom1'
            self.port_to_eeprom2_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom2'
            self.port_to_eeprom3_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom3'
            self.port_to_eeprom4_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom_pg4'
            self.port_to_eeprom12_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom_pg12'
            self.port_to_power_mode_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/power_mode'
            self.port_to_grid_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/grid'
            self.port_to_freq_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/freq'
            self.port_to_outp_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/output_power'
            self.port_to_curr_freq_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/current_freq'
            self.port_to_fine_tune_freq[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/fine_tune_freq'
            self.port_to_eeprom2f_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom_pg2f'
            self.port_to_eeprom34_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom_pg34'
            self.port_to_eeprom35_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/eeprom_pg35'
            self.port_to_vdm_freeze_mapping[x] = eeprom_path_prefix + self.port_to_i2c_mapping[x] + '/vdm_control'

        self._detect_sfp_type(sfp_type)
        self._dom_capability_detect()
        SfpBase.__init__(self)

    def reinit(self):
        self._detect_sfp_type(self.sfp_type)
        self._dom_capability_detect()

    def get_presence(self):
        """
        Retrieves the presence of the SFP
        Returns:
            bool: True if SFP is present, False if not
        """
        presence = False
        try:
            if self.index < 16:
                pres_path=self.PRS_1_16_PATH.format(self.port_num)
            else:
                pres_path=self.PRS_17_32_PATH.format(self.port_num)
            with open(pres_path, 'r') as sfp_presence:
                presence = int(sfp_presence.read(), 16)
        except IOError:
            return False
        logger.log_info("debug:port_ %s sfp presence is %s" % (str(self.index), str(presence)))
        return presence == 1

    def _get_eeprom_by_bmc(self):
        eeprom_path_prefix = '/sys/bus/i2c/devices/0-00'
        mux = int((0x70 + self.index / 8) * 2)
        chan = 1 << (self.index % 8)
        sel_ch_cmd = 'ipmitool raw 0x30 0x25 0x1 {} 0x0 {} 2>/dev/null'.format(mux, chan)
        desel_ch_cmd = 'ipmitool raw 0x30 0x25 0x1 {} 0x0 0x0 2>/dev/null'.format(mux)
        desel_all_ch_cmd = 'ipmitool raw 0x30 0x25 0x1 0xe0 0x0 0x0 2>/dev/null; ipmitool raw 0x30 0x25 0x1 0xe2 0x0 0x0 2>/dev/null; ipmitool raw 0x30 0x25 0x1 0xe4 0x0 0x0 2>/dev/null; ipmitool raw 0x30 0x25 0x1 0xe6 0x0 0x0 2>/dev/null'
        sel_page_cmd = 'ipmitool raw 0x30 0x25 0x1 0xa0 0x0 0x7f {} 2>/dev/null'
        read_lower_cmd = 'ipmitool raw 0x30 0x25 0x1 0xa0 0x80 0x0 2>/dev/null'
        read_upper_cmd = 'ipmitool raw 0x30 0x25 0x1 0xa0 0x80 0x80 2>/dev/null'

        try:
            subprocess.Popen(sel_ch_cmd, stdout=subprocess.PIPE)
            subprocess.Popen(sel_page_cmd.format(0), stdout=subprocess.PIPE)
            time.sleep(0.05)
            p = subprocess.Popen(read_lower_cmd, stdout=subprocess.PIPE)
            out, err = p.communicate()
            # retry if error occurred
            i = 0
            while out == b'' and i < 3:
                subprocess.Popen(desel_all_ch_cmd, stdout=subprocess.PIPE)
                time.sleep(0.05)
                subprocess.Popen(sel_ch_cmd, stdout=subprocess.PIPE)
                subprocess.Popen(sel_page_cmd.format(0), stdout=subprocess.PIPE)
                time.sleep(0.05)
                p = subprocess.Popen(read_lower_cmd, stdout=subprocess.PIPE)
                out, err = p.communicate()
                i = i + 1
            if out == b'':
                return False

            data_lower = out.decode().strip().replace("\n", "")

            i = 0
            p = subprocess.Popen(read_upper_cmd, stdout=subprocess.PIPE)
            out, err = p.communicate()
            while out == b'' and i < 3:
                time.sleep(0.05)
                p = subprocess.Popen(read_upper_cmd, stdout=subprocess.PIPE)
                out, err = p.communicate()
                i = i + 1
            if out == b'':
                return False

            data_upper_page_0 = out.decode().strip().replace("\n", "")

            subprocess.Popen(sel_page_cmd.format(0x1), stdout=subprocess.PIPE)
            p = subprocess.Popen(read_upper_cmd, stdout=subprocess.PIPE)
            out, err = p.communicate()
            data_upper_page_1 = out.decode().strip().replace("\n", "")

            subprocess.Popen(sel_page_cmd.format(0x2), stdout=subprocess.PIPE)
            p = subprocess.Popen(read_upper_cmd, stdout=subprocess.PIPE)
            out, err = p.communicate()
            data_upper_page_2 = out.decode().strip().replace("\n", "")

            subprocess.Popen(sel_page_cmd.format(0x3), stdout=subprocess.PIPE)
            p = subprocess.Popen(read_upper_cmd, stdout=subprocess.PIPE)
            out, err = p.communicate()
            data_upper_page_3 = out.decode().strip().replace("\n", "")

            subprocess.Popen(sel_page_cmd.format(0x10), stdout=subprocess.PIPE)
            p = subprocess.Popen(read_upper_cmd, stdout=subprocess.PIPE)
            out, err = p.communicate()
            data_upper_page_10 = out.decode().strip().replace("\n", "")

            subprocess.Popen(sel_page_cmd.format(0x11), stdout=subprocess.PIPE)
            p = subprocess.Popen(read_upper_cmd, stdout=subprocess.PIPE)
            out, err = p.communicate()
            data_upper_page_11 = out.decode().strip().replace("\n", "")

            subprocess.Popen(sel_page_cmd.format(0), stdout=subprocess.PIPE)
            subprocess.Popen(desel_ch_cmd, stdout=subprocess.PIPE)

            eeprom1 = data_lower + " " + data_upper_page_0
            eeprom2 = data_upper_page_1 + " " + data_upper_page_2
            eeprom3 = data_upper_page_3 + " " + data_upper_page_10 + " " + data_upper_page_11

            os.remove(PAUSE_EEPROM_SERVICE_STAMP)

            eeprom_raw_lower = [int(x, 16) for x in data_lower.split()]
            if eeprom_raw_lower[0] in QSFP_TYPE_CODE_LIST:
                temp = eeprom_raw_lower[22]
                if temp > 128:
                    return False
            elif eeprom_raw_lower[0] in QSFP_DD_TYPE_CODE_LIST:
                temp = eeprom_raw_lower[14]
                if temp > 128:
                    return False

            eeprom1 = eeprom1.replace(" ","")
            eeprom2 = eeprom2.replace(" ","")
            eeprom3 = eeprom3.replace(" ","")

            for i in range(0, 3):
                sysfs_sfp_i2c_client_temp_path = eeprom_path_prefix + self.port_to_i2c_mapping[self.index] + '/temp'
                if i == 0:
                    sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom1_mapping[self.index]
                    eeprom = eeprom1
                elif i == 1:
                    sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom2_mapping[self.index]
                    eeprom = eeprom2
                else:
                    sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom3_mapping[self.index]
                    eeprom = eeprom3

                try:
                    with open(sysfs_sfp_i2c_client_eeprom_path, 'w') as fd:
                        fd.write(eeprom)
                        fd.close()
                    if i == 0:
                        with open(sysfs_sfp_i2c_client_temp_path, 'w') as fd:
                            fd.write(temp)
                            fd.close()
                except IOError:
                    fd.close()
            return True
        except Exception:
            return False

    def read_eeprom_buffer(self):
        with open(PAUSE_EEPROM_SERVICE_STAMP, 'w') as f:
            f.write("")
        f.close()

        time.sleep(0.2)
        rc = self._get_eeprom_by_bmc()


        return rc

    def clear_eeprom_buffer(self):
        for i in range(0, 5):
            if i == 0:
                sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom1_mapping[self.index]
            elif i == 1:
                sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom2_mapping[self.index]
            elif i == 2:
                sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom3_mapping[self.index]
            elif i == 3:
                sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom4_mapping[self.index]
            else:
                sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom12_mapping[self.index]
            try:
                with open(sysfs_sfp_i2c_client_eeprom_path, 'w') as fd:
                    fd.write(" ")
                    fd.close()
            except IOError:
                fd.close()

        try:
            with open(self.port_to_grid_mapping[self.index], "w") as fd:
                fd.write("0")
                fd.close()
        except IOError:
            fd.close()

        try:
            with open(self.port_to_freq_mapping[self.index], "w") as fd:
                fd.write("0")
                fd.close()
        except IOError:
            fd.close()

        try:
            with open(self.port_to_outp_mapping[self.index], "w") as fd:
                fd.write("0")
                fd.close()
        except IOError:
            fd.close()

        try:
            with open(self.port_to_power_mode_mapping[self.index], "w") as fd:
                fd.write("0")
                fd.close()
        except IOError:
            fd.close()

        try:
            with open(self.port_to_eeprom2f_mapping[self.index], 'w') as fd:
                fd.write(" ")
                fd.close()
        except IOError:
            fd.close()

        try:
            with open(self.port_to_eeprom34_mapping[self.index], 'w') as fd:
                fd.write(" ")
                fd.close()
        except IOError:
            fd.close()

        try:
            with open(self.port_to_eeprom35_mapping[self.index], 'w') as fd:
                fd.write(" ")
                fd.close()
        except IOError:
            fd.close()

    def _read_eeprom_specific_bytes(self, offset, num_bytes, page = 0):
        sysfsfile_eeprom = None
        eeprom_raw = []
        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        if page == 4:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom4_mapping[self.index]
            offset = offset - 128
        elif page == 0x2f:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom2f_mapping[self.index]
            offset = offset - 128
        elif page == 0x34:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom34_mapping[self.index]
            offset = offset - 128
        elif page == 0x35:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom35_mapping[self.index]
            offset = offset - 128
        elif offset < 256:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom1_mapping[self.index]
        elif offset < 512:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom2_mapping[self.index]
            offset = offset - 256
        else:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom3_mapping[self.index]
            offset = offset - 512

        try:
            sysfsfile_eeprom = open(sysfs_sfp_i2c_client_eeprom_path, mode="rb", buffering=0)
            sysfsfile_eeprom.seek(offset)
            raw = sysfsfile_eeprom.read(num_bytes)
            if sys.version_info[0] >= 3:
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(raw[n])[2:].zfill(2)
            else:
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(ord(raw[n]))[2:].zfill(2)

        except BaseException:
            pass
        finally:
            if sysfsfile_eeprom:
                sysfsfile_eeprom.close()

        return eeprom_raw

    def _detect_sfp_type(self, sfp_type):
        eeprom_raw = []
        eeprom_raw = self._read_eeprom_specific_bytes(XCVR_TYPE_OFFSET, XCVR_TYPE_WIDTH)
        if eeprom_raw:
            if eeprom_raw[0] in QSFP_TYPE_CODE_LIST:
                self.sfp_type = QSFP_TYPE
                self.abbrv = type_abbrv_name[eeprom_raw[0]]
            elif eeprom_raw[0] in QSFP_DD_TYPE_CODE_LIST:
                self.sfp_type = QSFP_DD_TYPE
                self.abbrv = type_abbrv_name[eeprom_raw[0]]
            else:
                # we don't regonize this identifier value, treat the xSFP module as the default type
                self.sfp_type = sfp_type
                logger.log_info("Identifier value of {} module {} is {} which isn't regonized and will be treated as default type ({})".format(
                    sfp_type, self.index, eeprom_raw[0], sfp_type
                ))
        else:
            # eeprom_raw being None indicates the module is not present.
            # in this case we treat it as the default type according to the SKU
            self.sfp_type = sfp_type
            self.abbrv = type_abbrv_name['18']

    def _dom_capability_detect(self):
        if not self.get_presence():
            self.dom_supported = False
            self.dom_temp_supported = False
            self.dom_volt_supported = False
            self.dom_rx_power_supported = False
            self.dom_tx_bias_power_supported = False
            self.dom_tx_power_supported = False
            self.dom_module_monitor_supported = False
            self.calibration = 0
            return

        self.dom_channel_monitor_supported = True
        self.dom_module_monitor_supported = True
        self.dom_channel_threshold_supported = True
        self.dom_module_threshold_supported = True


        self.dom_supported = False
        self.dom_temp_supported = False
        self.dom_volt_supported = False
        self.dom_rx_power_supported = False
        self.dom_tx_bias_supported = False
        self.dom_tx_power_supported = False
        self.dom_thresholds_supported = False

        if self.sfp_type == QSFP_TYPE:
            self.calibration = 1
            sfpi_obj = sff8436InterfaceId()
            if sfpi_obj is None:
                self.dom_supported = False
            offset = 128

            # QSFP capability byte parse, through this byte can know whether it support tx_power or not.
            # TODO: in the future when decided to migrate to support SFF-8636 instead of SFF-8436,
            # need to add more code for determining the capability and version compliance
            # in SFF-8636 dom capability definitions evolving with the versions.
            qsfp_dom_capability_raw = self._read_eeprom_specific_bytes((offset + XCVR_DOM_CAPABILITY_OFFSET), XCVR_DOM_CAPABILITY_WIDTH)
            if qsfp_dom_capability_raw is not None:
                qsfp_version_compliance_raw = self._read_eeprom_specific_bytes(QSFP_VERSION_COMPLIANCE_OFFSET, QSFP_VERSION_COMPLIANCE_WIDTH)
                qsfp_version_compliance = int(qsfp_version_compliance_raw[0], 16)
                dom_capability = sfpi_obj.parse_dom_capability(qsfp_dom_capability_raw, 0)
                if qsfp_version_compliance >= 0x08:
                    self.dom_temp_supported = dom_capability['data']['Temp_support']['value'] == 'On'
                    self.dom_volt_supported = dom_capability['data']['Voltage_support']['value'] == 'On'
                    self.dom_rx_power_supported = dom_capability['data']['Rx_power_support']['value'] == 'On'
                    self.dom_tx_power_supported = dom_capability['data']['Tx_power_support']['value'] == 'On'
                else:
                    self.dom_temp_supported = True
                    self.dom_volt_supported = True
                    self.dom_rx_power_supported = dom_capability['data']['Rx_power_support']['value'] == 'On'
                    self.dom_tx_power_supported = True
                self.dom_supported = True
                self.calibration = 1
                sfpd_obj = sff8436Dom()
                if sfpd_obj is None:
                    return None
                qsfp_option_value_raw = self._read_eeprom_specific_bytes(QSFP_OPTION_VALUE_OFFSET, QSFP_OPTION_VALUE_WIDTH)
                if qsfp_option_value_raw is not None:
                    optional_capability = sfpd_obj.parse_option_params(qsfp_option_value_raw, 0)
                    self.dom_tx_disable_supported = optional_capability['data']['TxDisable']['value'] == 'On'
                dom_status_indicator = sfpd_obj.parse_dom_status_indicator(qsfp_version_compliance_raw, 1)
                self.qsfp_page3_available = dom_status_indicator['data']['FlatMem']['value'] == 'Off'
            else:
                self.dom_supported = False
                self.dom_temp_supported = False
                self.dom_volt_supported = False
                self.dom_rx_power_supported = False
                self.dom_tx_power_supported = False
                self.calibration = 0
                self.qsfp_page3_available = False

        elif self.sfp_type == QSFP_DD_TYPE:
            sfpi_obj = qsfp_dd_InterfaceId()
            if sfpi_obj is None:
                self.dom_supported = False

            self.dom_temp_supported = True
            self.dom_volt_supported = True
            self.dom_tx_fault_supported = False
            self.dom_rx_los_supported = False

            offset = 0;

            # two types of QSFP-DD cable types supported: Copper and Optical.
            qsfp_dom_capability_raw = self._read_eeprom_specific_bytes((offset + XCVR_DOM_CAPABILITY_OFFSET_QSFP_DD), XCVR_DOM_CAPABILITY_WIDTH_QSFP_DD)

            if qsfp_dom_capability_raw is not None:
                dom_capability = sfpi_obj.parse_dom_capability(qsfp_dom_capability_raw, 0)
                if dom_capability['data']['Flat_MEM']['value'] == 'Off':

                    ext_dd = ext_qsfp_dd()
                    offset = 256
                    mon_sup_raw = self._read_eeprom_specific_bytes(offset + QSFP_DD_CHANNL_MON_SUPPORT_OFFSET, QSFP_DD_CHANNL_MON_SUPPORT_WIDTH)
                    mon_sup_data = ext_dd.parse_mon_capability(mon_sup_raw, 0)

                    self.dom_thresholds_supported = mon_sup_data['data']['Tx_power_support']['value'] == 'On'
                    self.dom_rx_power_supported = mon_sup_data['data']['Tx_power_support']['value'] == 'On'
                    self.dom_tx_power_supported = mon_sup_data['data']['Rx_power_support']['value'] == 'On'
                    self.dom_tx_bias_supported = mon_sup_data['data']['Tx_bias_support']['value'] == 'On'
                    self.dom_supported = True

                    flags_sup_raw = self._read_eeprom_specific_bytes(offset + QSFP_DD_CHANNL_FLAGS_SUPPORT_OFFSET, QSFP_DD_CHANNL_FLAGS_SUPPORT_WIDTH)
                    flags_sup_data = ext_dd.parse_flags_capability(flags_sup_raw, 0)

                    self.dom_tx_fault_supported = flags_sup_data['data']['tx_fault']['value'] == 'On'
                    self.dom_rx_los_supported = flags_sup_data['data']['rx_los']['value'] == 'On'

        else:
            self.dom_supported = False
            self.dom_temp_supported = False
            self.dom_volt_supported = False
            self.dom_rx_power_supported = False
            self.dom_tx_power_supported = False

    def _convert_string_to_num(self, value_str):
        if "-inf" in value_str:
            return 'N/A'
        elif "Unknown" in value_str:
            return 'N/A'
        elif 'dBm' in value_str:
            t_str = value_str.rstrip('dBm')
            return float(t_str)
        elif 'mA' in value_str:
            t_str = value_str.rstrip('mA')
            return float(t_str)
        elif 'C' in value_str:
            t_str = value_str.rstrip('C')
            return float(t_str)
        elif 'Volts' in value_str:
            t_str = value_str.rstrip('Volts')
            return float(t_str)
        else:
            return 'N/A'

    def get_transceiver_info(self):
        """
        Retrieves transceiver info of this SFP

        Returns:
            A dict which contains following keys/values :
        ================================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        type                       |1*255VCHAR     |type of SFP
        hardware_rev               |1*255VCHAR     |hardware version of SFP
        serial                     |1*255VCHAR     |serial number of the SFP
        manufacturer               |1*255VCHAR     |SFP vendor name
        model                      |1*255VCHAR     |SFP model name
        connector                  |1*255VCHAR     |connector information
        encoding                   |1*255VCHAR     |encoding information
        ext_identifier             |1*255VCHAR     |extend identifier
        ext_rateselect_compliance  |1*255VCHAR     |extended rateSelect compliance
        cable_length               |INT            |cable length in m
        mominal_bit_rate           |INT            |nominal bit rate by 100Mbs
        specification_compliance   |1*255VCHAR     |specification compliance
        vendor_date                |1*255VCHAR     |vendor date
        vendor_oui                 |1*255VCHAR     |vendor OUI
        application_advertisement  |1*255VCHAR     |supported applications advertisement
        ================================================================================
        """
        self.reinit()
        info_dict_keys = [
        'type', 'hardware_rev', 'serial', 'manufacturer',
        'model', 'connector', 'encoding', 'ext_identifier',
        'ext_rateselect_compliance', 'cable_type', 'cable_length',
        'nominal_bit_rate', 'specification_compliance', 'vendor_date',
        'vendor_oui', 'application_advertisement', 'type_abbrv_name']

        transceiver_info_dict = {}
        compliance_code_dict = {}
        transceiver_info_dict = dict.fromkeys(info_dict_keys, "NA")
        transceiver_info_dict["specification_compliance"] = '{}'
        transceiver_info_dict['type_abbrv_name'] = self.abbrv

        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 128
            vendor_rev_width = XCVR_HW_REV_WIDTH_QSFP
            interface_info_bulk_width = XCVR_INTFACE_BULK_WIDTH_QSFP

            sfpi_obj = sff8436InterfaceId()
            if sfpi_obj is None:
                print("Error: sfp_object open failed")
                return None

            sfp_interface_bulk_raw = self._read_eeprom_specific_bytes(offset + XCVR_INTERFACE_DATA_START, XCVR_INTERFACE_DATA_SIZE)
            if sfp_interface_bulk_raw is None:
                return None

            start = XCVR_INTFACE_BULK_OFFSET - XCVR_INTERFACE_DATA_START
            end = start + interface_info_bulk_width
            sfp_interface_bulk_data = sfpi_obj.parse_sfp_info_bulk(sfp_interface_bulk_raw[start : end], 0)

            start = XCVR_VENDOR_NAME_OFFSET - XCVR_INTERFACE_DATA_START
            end = start + XCVR_VENDOR_NAME_WIDTH
            sfp_vendor_name_data = sfpi_obj.parse_vendor_name(sfp_interface_bulk_raw[start : end], 0)

            start = XCVR_VENDOR_PN_OFFSET - XCVR_INTERFACE_DATA_START
            end = start + XCVR_VENDOR_PN_WIDTH
            sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(sfp_interface_bulk_raw[start : end], 0)

            start = XCVR_HW_REV_OFFSET - XCVR_INTERFACE_DATA_START
            end = start + vendor_rev_width
            sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(sfp_interface_bulk_raw[start : end], 0)

            start = XCVR_VENDOR_SN_OFFSET - XCVR_INTERFACE_DATA_START
            end = start + XCVR_VENDOR_SN_WIDTH
            sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(sfp_interface_bulk_raw[start : end], 0)

            start = XCVR_VENDOR_OUI_OFFSET - XCVR_INTERFACE_DATA_START
            end = start + XCVR_VENDOR_OUI_WIDTH
            sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(sfp_interface_bulk_raw[start : end], 0)

            start = XCVR_VENDOR_DATE_OFFSET - XCVR_INTERFACE_DATA_START
            end = start + XCVR_VENDOR_DATE_WIDTH
            sfp_vendor_date_data = sfpi_obj.parse_vendor_date(sfp_interface_bulk_raw[start : end], 0)

            transceiver_info_dict['type'] = sfp_interface_bulk_data['data']['type']['value']
            transceiver_info_dict['manufacturer'] = sfp_vendor_name_data['data']['Vendor Name']['value']
            transceiver_info_dict['model'] = sfp_vendor_pn_data['data']['Vendor PN']['value']
            transceiver_info_dict['hardware_rev'] = sfp_vendor_rev_data['data']['Vendor Rev']['value']
            transceiver_info_dict['serial'] = sfp_vendor_sn_data['data']['Vendor SN']['value']
            transceiver_info_dict['vendor_oui'] = sfp_vendor_oui_data['data']['Vendor OUI']['value']
            transceiver_info_dict['vendor_date'] = sfp_vendor_date_data['data']['VendorDataCode(YYYY-MM-DD Lot)']['value']
            transceiver_info_dict['connector'] = sfp_interface_bulk_data['data']['Connector']['value']
            transceiver_info_dict['encoding'] = sfp_interface_bulk_data['data']['EncodingCodes']['value']
            transceiver_info_dict['ext_identifier'] = sfp_interface_bulk_data['data']['Extended Identifier']['value']
            transceiver_info_dict['ext_rateselect_compliance'] = sfp_interface_bulk_data['data']['RateIdentifier']['value']
            transceiver_info_dict['application_advertisement'] = 'N/A'

            for key in qsfp_cable_length_tup:
                if key in sfp_interface_bulk_data['data']:
                    transceiver_info_dict['cable_type'] = key
                    transceiver_info_dict['cable_length'] = str(sfp_interface_bulk_data['data'][key]['value'])

            for key in qsfp_compliance_code_tup:
                if key in sfp_interface_bulk_data['data']['Specification compliance']['value']:
                    compliance_code_dict[key] = sfp_interface_bulk_data['data']['Specification compliance']['value'][key]['value']
            sfp_ext_specification_compliance_raw = self._read_eeprom_specific_bytes(offset + XCVR_EXT_SPECIFICATION_COMPLIANCE_OFFSET, XCVR_EXT_SPECIFICATION_COMPLIANCE_WIDTH)
            if sfp_ext_specification_compliance_raw is not None:
                sfp_ext_specification_compliance_data = sfpi_obj.parse_ext_specification_compliance(sfp_ext_specification_compliance_raw[0 : 1], 0)
                if sfp_ext_specification_compliance_data['data']['Extended Specification compliance']['value'] != "Unspecified":
                    compliance_code_dict['Extended Specification compliance'] = sfp_ext_specification_compliance_data['data']['Extended Specification compliance']['value']
            transceiver_info_dict['specification_compliance'] = str(compliance_code_dict)
            transceiver_info_dict['nominal_bit_rate'] = str(sfp_interface_bulk_data['data']['Nominal Bit Rate(100Mbs)']['value'])

        #QSFP-DD
        else:
            offset = 128

            sfpi_obj = qsfp_dd_InterfaceId()
            if sfpi_obj is None:
                print("Error: sfp_object open failed")
                return None

            sfp_type_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_TYPE_OFFSET), XCVR_TYPE_WIDTH)
            if sfp_type_raw is not None:
                sfp_type_data = sfpi_obj.parse_sfp_type(sfp_type_raw, 0)
            else:
                return None

            sfp_vendor_name_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_NAME_OFFSET), XCVR_VENDOR_NAME_WIDTH)
            if sfp_vendor_name_raw is not None:
                sfp_vendor_name_data = sfpi_obj.parse_vendor_name(sfp_vendor_name_raw, 0)
            else:
                return None

            sfp_vendor_pn_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_PN_OFFSET), XCVR_VENDOR_PN_WIDTH)
            if sfp_vendor_pn_raw is not None:
                sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(sfp_vendor_pn_raw, 0)
            else:
                return None

            sfp_vendor_rev_raw = self._read_eeprom_specific_bytes((offset + XCVR_HW_REV_OFFSET_QSFP_DD), XCVR_HW_REV_WIDTH_QSFP_DD)
            if sfp_vendor_rev_raw is not None:
                sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(sfp_vendor_rev_raw, 0)
            else:
                return None

            sfp_vendor_sn_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_SN_OFFSET), XCVR_VENDOR_SN_WIDTH)
            if sfp_vendor_sn_raw is not None:
                sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(sfp_vendor_sn_raw, 0)
            else:
                return None

            sfp_vendor_oui_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_OUI_OFFSET), XCVR_VENDOR_OUI_WIDTH)
            if sfp_vendor_oui_raw is not None:
                sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(sfp_vendor_oui_raw, 0)
            else:
                return None

            sfp_vendor_date_raw = self._read_eeprom_specific_bytes((offset + XCVR_VENDOR_DATE_OFFSET_QSFP_DD), XCVR_VENDOR_DATE_WIDTH_QSFP_DD)
            if sfp_vendor_date_raw is not None:
                sfp_vendor_date_data = sfpi_obj.parse_vendor_date(sfp_vendor_date_raw, 0)
            else:
                return None

            sfp_connector_raw = self._read_eeprom_specific_bytes((offset + XCVR_CONNECTOR_OFFSET_QSFP_DD), XCVR_CONNECTOR_WIDTH_QSFP_DD)
            if sfp_connector_raw is not None:
                sfp_connector_data = sfpi_obj.parse_connector(sfp_connector_raw, 0)
            else:
                return None

            sfp_ext_identifier_raw = self._read_eeprom_specific_bytes((offset + XCVR_EXT_TYPE_OFFSET_QSFP_DD), XCVR_EXT_TYPE_WIDTH_QSFP_DD)
            if sfp_ext_identifier_raw is not None:
                sfp_ext_identifier_data = sfpi_obj.parse_ext_iden(sfp_ext_identifier_raw, 0)
            else:
                return None

            sfp_cable_len_raw = self._read_eeprom_specific_bytes((offset + XCVR_CABLE_LENGTH_OFFSET_QSFP_DD), XCVR_CABLE_LENGTH_WIDTH_QSFP_DD)
            if sfp_cable_len_raw is not None:
                sfp_cable_len_data = sfpi_obj.parse_cable_len(sfp_cable_len_raw, 0)
            else:
                return None

            sfp_media_type_raw = self._read_eeprom_specific_bytes(XCVR_MEDIA_TYPE_OFFSET_QSFP_DD, XCVR_MEDIA_TYPE_WIDTH_QSFP_DD)
            if sfp_media_type_raw is not None:
                sfp_media_type_dict = sfpi_obj.parse_media_type(sfp_media_type_raw, 0)
                if sfp_media_type_dict is None:
                    return None

                transceiver_info_dict['specification_compliance'] = type_of_media_interface[sfp_media_type_raw[0]]
                host_media_list = ""
                sfp_application_type_first_list = self._read_eeprom_specific_bytes((XCVR_FIRST_APPLICATION_LIST_OFFSET_QSFP_DD), XCVR_FIRST_APPLICATION_LIST_WIDTH_QSFP_DD)
                possible_application_count = 8
                if sfp_application_type_first_list is not None:
                    sfp_application_type_list = sfp_application_type_first_list
                else:
                    return None

                for i in range(0, possible_application_count):
                    if sfp_application_type_list[i * 4] == 'ff':
                        break
                    host_electrical, media_interface = sfpi_obj.parse_application(sfp_media_type_dict, sfp_application_type_list[i * 4], sfp_application_type_list[i * 4 + 1])
                    host_media_list = host_media_list + host_electrical + ' - ' + media_interface + '\n\t\t\t\t   '
            else:
                return None

            transceiver_info_dict['type'] = str(sfp_type_data['data']['type']['value'])
            transceiver_info_dict['manufacturer'] = str(sfp_vendor_name_data['data']['Vendor Name']['value'])
            transceiver_info_dict['model'] = str(sfp_vendor_pn_data['data']['Vendor PN']['value'])
            transceiver_info_dict['hardware_rev'] = str(sfp_vendor_rev_data['data']['Vendor Rev']['value'])
            transceiver_info_dict['serial'] = str(sfp_vendor_sn_data['data']['Vendor SN']['value'])
            transceiver_info_dict['vendor_oui'] = str(sfp_vendor_oui_data['data']['Vendor OUI']['value'])
            transceiver_info_dict['vendor_date'] = str(sfp_vendor_date_data['data']['VendorDataCode(YYYY-MM-DD Lot)']['value'])
            transceiver_info_dict['connector'] = str(sfp_connector_data['data']['Connector']['value'])
            transceiver_info_dict['encoding'] = "Not supported for CMIS cables"
            transceiver_info_dict['ext_identifier'] = str(sfp_ext_identifier_data['data']['Extended Identifier']['value'])
            transceiver_info_dict['ext_rateselect_compliance'] = "Not supported for CMIS cables"
            transceiver_info_dict['cable_type'] = "Length Cable Assembly(m)"
            transceiver_info_dict['cable_length'] = str(sfp_cable_len_data['data']['Length Cable Assembly(m)']['value'])
            transceiver_info_dict['nominal_bit_rate'] = "Not supported for CMIS cables"
            transceiver_info_dict['application_advertisement'] = host_media_list

        if self._is_coherent_module():
            _, _, _, low_freq_supported, high_freq_supported = self.get_supported_freq_config()
            transceiver_info_dict['supported_max_laser_freq'] = high_freq_supported
            transceiver_info_dict['supported_min_laser_freq'] = low_freq_supported

        return transceiver_info_dict

    def get_transceiver_bulk_status(self):
        """
        Retrieves transceiver bulk status of this SFP

        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        RX LOS                     |BOOLEAN        |RX lost-of-signal status,
                                   |               |True if has RX los, False if not.
        TX FAULT                   |BOOLEAN        |TX fault status,
                                   |               |True if has TX fault, False if not.
        Reset status               |BOOLEAN        |reset status,
                                   |               |True if SFP in reset, False if not.
        LP mode                    |BOOLEAN        |low power mode status,
                                   |               |True in lp mode, False if not.
        TX disable                 |BOOLEAN        |TX disable status,
                                   |               |True TX disabled, False if not.
        TX disabled channel        |HEX            |disabled TX channles in hex,
                                   |               |bits 0 to 3 represent channel 0
                                   |               |to channel 3.
        Temperature                |INT            |module temperature in Celsius
        Voltage                    |INT            |supply voltage in mV
        TX bias                    |INT            |TX Bias Current in mA
        RX power                   |INT            |received optical power in mW
        TX power                   |INT            |TX output power in mW
        ========================================================================
        """
        self.reinit()
        transceiver_dom_info_dict = {}

        dom_info_dict_keys = ['temperature',    'voltage',
                              'rx1power',       'rx2power',
                              'rx3power',       'rx4power',
                              'rx5power',       'rx6power',
                              'rx7power',       'rx8power',
                              'tx1bias',        'tx2bias',
                              'tx3bias',        'tx4bias',
                              'tx5bias',        'tx6bias',
                              'tx7bias',        'tx8bias',
                              'tx1power',       'tx2power',
                              'tx3power',       'tx4power',
                              'tx5power',       'tx6power',
                              'tx7power',       'tx8power'
                             ]
        transceiver_dom_info_dict = dict.fromkeys(dom_info_dict_keys, 'N/A')

        #QSFP
        if self.sfp_type == QSFP_TYPE:
            if not self.dom_supported:
                return transceiver_dom_info_dict

            offset = 0
            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return transceiver_dom_info_dict

            dom_data_raw = self._read_eeprom_specific_bytes((offset + QSFP_DOM_BULK_DATA_START), QSFP_DOM_BULK_DATA_SIZE)
            if dom_data_raw is None:
                return transceiver_dom_info_dict

            if self.dom_module_monitor_supported:
                if self.dom_temp_supported:
                    start = QSFP_TEMPE_OFFSET - QSFP_DOM_BULK_DATA_START
                    end = start + QSFP_TEMPE_WIDTH
                    dom_temperature_data = sfpd_obj.parse_temperature(dom_data_raw[start : end], 0)
                    temp = self._convert_string_to_num(dom_temperature_data['data']['Temperature']['value'])
                    if temp is not None:
                        transceiver_dom_info_dict['temperature'] = temp

                if self.dom_volt_supported:
                    start = QSFP_VOLT_OFFSET - QSFP_DOM_BULK_DATA_START
                    end = start + QSFP_VOLT_WIDTH
                    dom_voltage_data = sfpd_obj.parse_voltage(dom_data_raw[start : end], 0)
                    volt = self._convert_string_to_num(dom_voltage_data['data']['Vcc']['value'])
                    if volt is not None:
                        transceiver_dom_info_dict['voltage'] = volt
            if self.dom_channel_monitor_supported:
                start = QSFP_CHANNL_MON_OFFSET - QSFP_DOM_BULK_DATA_START
                end = start + QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH
                dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params_with_tx_power(dom_data_raw[start : end], 0)

                if self.dom_tx_power_supported:
                    transceiver_dom_info_dict['tx1bias'] = dom_channel_monitor_data['data']['TX1Bias']['value']
                    transceiver_dom_info_dict['tx2bias'] = dom_channel_monitor_data['data']['TX2Bias']['value']
                    transceiver_dom_info_dict['tx3bias'] = dom_channel_monitor_data['data']['TX3Bias']['value']
                    transceiver_dom_info_dict['tx4bias'] = dom_channel_monitor_data['data']['TX4Bias']['value']
                    transceiver_dom_info_dict['tx1power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['TX1Power']['value'])
                    transceiver_dom_info_dict['tx2power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['TX2Power']['value'])
                    transceiver_dom_info_dict['tx3power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['TX3Power']['value'])
                    transceiver_dom_info_dict['tx4power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['TX4Power']['value'])

                if self.dom_rx_power_supported:
                    transceiver_dom_info_dict['rx1power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['RX1Power']['value'])
                    transceiver_dom_info_dict['rx2power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['RX2Power']['value'])
                    transceiver_dom_info_dict['rx3power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['RX3Power']['value'])
                    transceiver_dom_info_dict['rx4power'] = self._convert_string_to_num(dom_channel_monitor_data['data']['RX4Power']['value'])


        #QSFP-DD
        else:
            sfpd_obj = qsfp_dd_Dom()
            if sfpd_obj is None:
                return transceiver_dom_info_dict

            if self.dom_module_monitor_supported:

                if self.dom_temp_supported:
                    offset = 0
                    dom_data_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_TEMPE_OFFSET), QSFP_DD_TEMPE_WIDTH)
                    dom_temperature_data = sfpd_obj.parse_temperature(dom_data_raw, 0)
                    temp = self._convert_string_to_num(dom_temperature_data['data']['Temperature']['value'])
                    if temp is not None:
                        transceiver_dom_info_dict['temperature'] = temp

                if self.dom_volt_supported:
                    offset = 0
                    dom_data_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_VOLT_OFFSET), QSFP_DD_VOLT_WIDTH)
                    dom_voltage_data = sfpd_obj.parse_voltage(dom_data_raw, 0)
                    volt = self._convert_string_to_num(dom_voltage_data['data']['Vcc']['value'])
                    if volt is not None:
                        transceiver_dom_info_dict['voltage'] = volt
            if self.dom_channel_monitor_supported:

                offset = 768
                dom_data_raw = self._read_eeprom_specific_bytes(offset + (QSFP_DD_CHANNL_MON_OFFSET - 128), QSFP_DD_CHANNL_MON_WIDTH)
                dom_channel_monitor_data =  sfpd_obj.parse_channel_monitor_params(dom_data_raw, 0)
                if self.dom_tx_power_supported:
                    transceiver_dom_info_dict['tx1power'] = dom_channel_monitor_data['data']['TX1Power']['value']
                    transceiver_dom_info_dict['tx2power'] = dom_channel_monitor_data['data']['TX2Power']['value']
                    transceiver_dom_info_dict['tx3power'] = dom_channel_monitor_data['data']['TX3Power']['value']
                    transceiver_dom_info_dict['tx4power'] = dom_channel_monitor_data['data']['TX4Power']['value']
                    transceiver_dom_info_dict['tx5power'] = dom_channel_monitor_data['data']['TX5Power']['value']
                    transceiver_dom_info_dict['tx6power'] = dom_channel_monitor_data['data']['TX6Power']['value']
                    transceiver_dom_info_dict['tx7power'] = dom_channel_monitor_data['data']['TX7Power']['value']
                    transceiver_dom_info_dict['tx8power'] = dom_channel_monitor_data['data']['TX8Power']['value']

                if self.dom_rx_power_supported:
                    transceiver_dom_info_dict['rx1power'] = dom_channel_monitor_data['data']['RX1Power']['value']
                    transceiver_dom_info_dict['rx2power'] = dom_channel_monitor_data['data']['RX2Power']['value']
                    transceiver_dom_info_dict['rx3power'] = dom_channel_monitor_data['data']['RX3Power']['value']
                    transceiver_dom_info_dict['rx4power'] = dom_channel_monitor_data['data']['RX4Power']['value']
                    transceiver_dom_info_dict['rx5power'] = dom_channel_monitor_data['data']['RX5Power']['value']
                    transceiver_dom_info_dict['rx6power'] = dom_channel_monitor_data['data']['RX6Power']['value']
                    transceiver_dom_info_dict['rx7power'] = dom_channel_monitor_data['data']['RX7Power']['value']
                    transceiver_dom_info_dict['rx8power'] = dom_channel_monitor_data['data']['RX8Power']['value']

                if self.dom_tx_bias_supported:
                    transceiver_dom_info_dict['tx1bias'] = dom_channel_monitor_data['data']['TX1Bias']['value']
                    transceiver_dom_info_dict['tx2bias'] = dom_channel_monitor_data['data']['TX2Bias']['value']
                    transceiver_dom_info_dict['tx3bias'] = dom_channel_monitor_data['data']['TX3Bias']['value']
                    transceiver_dom_info_dict['tx4bias'] = dom_channel_monitor_data['data']['TX4Bias']['value']
                    transceiver_dom_info_dict['tx5bias'] = dom_channel_monitor_data['data']['TX5Bias']['value']
                    transceiver_dom_info_dict['tx6bias'] = dom_channel_monitor_data['data']['TX6Bias']['value']
                    transceiver_dom_info_dict['tx7bias'] = dom_channel_monitor_data['data']['TX7Bias']['value']
                    transceiver_dom_info_dict['tx8bias'] = dom_channel_monitor_data['data']['TX8Bias']['value']

        return transceiver_dom_info_dict

    def get_transceiver_threshold_info(self):
        """
        Retrieves transceiver threshold info of this SFP

        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        temphighalarm              |FLOAT          |High Alarm Threshold value of temperature in Celsius.
        templowalarm               |FLOAT          |Low Alarm Threshold value of temperature in Celsius.
        temphighwarning            |FLOAT          |High Warning Threshold value of temperature in Celsius.
        templowwarning             |FLOAT          |Low Warning Threshold value of temperature in Celsius.
        vcchighalarm               |FLOAT          |High Alarm Threshold value of supply voltage in mV.
        vcclowalarm                |FLOAT          |Low Alarm Threshold value of supply voltage in mV.
        vcchighwarning             |FLOAT          |High Warning Threshold value of supply voltage in mV.
        vcclowwarning              |FLOAT          |Low Warning Threshold value of supply voltage in mV.
        rxpowerhighalarm           |FLOAT          |High Alarm Threshold value of received power in dBm.
        rxpowerlowalarm            |FLOAT          |Low Alarm Threshold value of received power in dBm.
        rxpowerhighwarning         |FLOAT          |High Warning Threshold value of received power in dBm.
        rxpowerlowwarning          |FLOAT          |Low Warning Threshold value of received power in dBm.
        txpowerhighalarm           |FLOAT          |High Alarm Threshold value of transmit power in dBm.
        txpowerlowalarm            |FLOAT          |Low Alarm Threshold value of transmit power in dBm.
        txpowerhighwarning         |FLOAT          |High Warning Threshold value of transmit power in dBm.
        txpowerlowwarning          |FLOAT          |Low Warning Threshold value of transmit power in dBm.
        txbiashighalarm            |FLOAT          |High Alarm Threshold value of tx Bias Current in mA.
        txbiaslowalarm             |FLOAT          |Low Alarm Threshold value of tx Bias Current in mA.
        txbiashighwarning          |FLOAT          |High Warning Threshold value of tx Bias Current in mA.
        txbiaslowwarning           |FLOAT          |Low Warning Threshold value of tx Bias Current in mA.
        ========================================================================
        """
        self.reinit()
        transceiver_dom_threshold_info_dict = {}

        dom_info_dict_keys = ['temphighalarm',    'temphighwarning',
                              'templowalarm',     'templowwarning',
                              'vcchighalarm',     'vcchighwarning',
                              'vcclowalarm',      'vcclowwarning',
                              'rxpowerhighalarm', 'rxpowerhighwarning',
                              'rxpowerlowalarm',  'rxpowerlowwarning',
                              'txpowerhighalarm', 'txpowerhighwarning',
                              'txpowerlowalarm',  'txpowerlowwarning',
                              'txbiashighalarm',  'txbiashighwarning',
                              'txbiaslowalarm',   'txbiaslowwarning'
                             ]
        transceiver_dom_threshold_info_dict = dict.fromkeys(dom_info_dict_keys, 'N/A')

        #QSFP
        if self.sfp_type == QSFP_TYPE:
            if not self.dom_supported or not self.qsfp_page3_available:
                return transceiver_dom_threshold_info_dict

            offset = 512
            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return transceiver_dom_threshold_info_dict

            dom_module_threshold_raw = self._read_eeprom_specific_bytes((offset + QSFP_MODULE_THRESHOLD_OFFSET), QSFP_MODULE_THRESHOLD_WIDTH)
            if dom_module_threshold_raw is None:
                return transceiver_dom_threshold_info_dict

            dom_module_threshold_data = sfpd_obj.parse_module_threshold_values(dom_module_threshold_raw, 0)

            dom_channel_threshold_raw = self._read_eeprom_specific_bytes((offset + QSFP_CHANNL_THRESHOLD_OFFSET),
                                      QSFP_CHANNL_THRESHOLD_WIDTH)
            if dom_channel_threshold_raw is None:
                return transceiver_dom_threshold_info_dict
            dom_channel_threshold_data = sfpd_obj.parse_channel_threshold_values(dom_channel_threshold_raw, 0)

            # Threshold Data
            if self.dom_module_threshold_supported:
                transceiver_dom_threshold_info_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
                transceiver_dom_threshold_info_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
                transceiver_dom_threshold_info_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
                transceiver_dom_threshold_info_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
                transceiver_dom_threshold_info_dict['vcchighalarm'] = dom_module_threshold_data['data']['VccHighAlarm']['value']
                transceiver_dom_threshold_info_dict['vcchighwarning'] = dom_module_threshold_data['data']['VccHighWarning']['value']
                transceiver_dom_threshold_info_dict['vcclowalarm'] = dom_module_threshold_data['data']['VccLowAlarm']['value']
                transceiver_dom_threshold_info_dict['vcclowwarning'] = dom_module_threshold_data['data']['VccLowWarning']['value']
            if self.dom_channel_threshold_supported:
                transceiver_dom_threshold_info_dict['rxpowerhighalarm'] = dom_channel_threshold_data['data']['RxPowerHighAlarm']['value']
                transceiver_dom_threshold_info_dict['rxpowerhighwarning'] = dom_channel_threshold_data['data']['RxPowerHighWarning']['value']
                transceiver_dom_threshold_info_dict['rxpowerlowalarm'] = dom_channel_threshold_data['data']['RxPowerLowAlarm']['value']
                transceiver_dom_threshold_info_dict['rxpowerlowwarning'] = dom_channel_threshold_data['data']['RxPowerLowWarning']['value']
                transceiver_dom_threshold_info_dict['txbiashighalarm'] = dom_channel_threshold_data['data']['TxBiasHighAlarm']['value']
                transceiver_dom_threshold_info_dict['txbiashighwarning'] = dom_channel_threshold_data['data']['TxBiasHighWarning']['value']
                transceiver_dom_threshold_info_dict['txbiaslowalarm'] = dom_channel_threshold_data['data']['TxBiasLowAlarm']['value']
                transceiver_dom_threshold_info_dict['txbiaslowwarning'] = dom_channel_threshold_data['data']['TxBiasLowWarning']['value']
                transceiver_dom_threshold_info_dict['txpowerhighalarm'] = dom_channel_threshold_data['data']['TxPowerHighAlarm']['value']
                transceiver_dom_threshold_info_dict['txpowerhighwarning'] = dom_channel_threshold_data['data']['TxPowerHighWarning']['value']
                transceiver_dom_threshold_info_dict['txpowerlowalarm'] = dom_channel_threshold_data['data']['TxPowerLowAlarm']['value']
                transceiver_dom_threshold_info_dict['txpowerlowwarning'] = dom_channel_threshold_data['data']['TxPowerLowWarning']['value']

        #QSFP-DD
        else:
            if not self.dom_supported:
                return transceiver_dom_threshold_info_dict

            if not self.dom_thresholds_supported:
                return transceiver_dom_threshold_info_dict

            sfpd_obj = qsfp_dd_Dom()
            if sfpd_obj is None:
                return transceiver_dom_threshold_info_dict

            # page 02 (we put page 2 to byte 384~511)
            offset = 384
            dom_module_threshold_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_MODULE_THRESHOLD_OFFSET), QSFP_DD_MODULE_THRESHOLD_WIDTH)
            if dom_module_threshold_raw is None:
                return transceiver_dom_threshold_info_dict

            dom_module_threshold_data = sfpd_obj.parse_module_threshold_values(dom_module_threshold_raw, 0)

            # Threshold Data
            if self.dom_module_threshold_supported:
                transceiver_dom_threshold_info_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
                transceiver_dom_threshold_info_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
                transceiver_dom_threshold_info_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
                transceiver_dom_threshold_info_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
                transceiver_dom_threshold_info_dict['vcchighalarm'] = dom_module_threshold_data['data']['VccHighAlarm']['value']
                transceiver_dom_threshold_info_dict['vcchighwarning'] = dom_module_threshold_data['data']['VccHighWarning']['value']
                transceiver_dom_threshold_info_dict['vcclowalarm'] = dom_module_threshold_data['data']['VccLowAlarm']['value']
                transceiver_dom_threshold_info_dict['vcclowwarning'] = dom_module_threshold_data['data']['VccLowWarning']['value']
            if self.dom_channel_threshold_supported:
                transceiver_dom_threshold_info_dict['rxpowerhighalarm'] = dom_module_threshold_data['data']['RxPowerHighAlarm']['value']
                transceiver_dom_threshold_info_dict['rxpowerhighwarning'] = dom_module_threshold_data['data']['RxPowerHighWarning']['value']
                transceiver_dom_threshold_info_dict['rxpowerlowalarm'] = dom_module_threshold_data['data']['RxPowerLowAlarm']['value']
                transceiver_dom_threshold_info_dict['rxpowerlowwarning'] = dom_module_threshold_data['data']['RxPowerLowWarning']['value']
                transceiver_dom_threshold_info_dict['txbiashighalarm'] = dom_module_threshold_data['data']['TxBiasHighAlarm']['value']
                transceiver_dom_threshold_info_dict['txbiashighwarning'] = dom_module_threshold_data['data']['TxBiasHighWarning']['value']
                transceiver_dom_threshold_info_dict['txbiaslowalarm'] = dom_module_threshold_data['data']['TxBiasLowAlarm']['value']
                transceiver_dom_threshold_info_dict['txbiaslowwarning'] = dom_module_threshold_data['data']['TxBiasLowWarning']['value']
                transceiver_dom_threshold_info_dict['txpowerhighalarm'] = dom_module_threshold_data['data']['TxPowerHighAlarm']['value']
                transceiver_dom_threshold_info_dict['txpowerhighwarning'] = dom_module_threshold_data['data']['TxPowerHighWarning']['value']
                transceiver_dom_threshold_info_dict['txpowerlowalarm'] = dom_module_threshold_data['data']['TxPowerLowAlarm']['value']
                transceiver_dom_threshold_info_dict['txpowerlowwarning'] = dom_module_threshold_data['data']['TxPowerLowWarning']['value']

        return transceiver_dom_threshold_info_dict

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP
        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        # SFP doesn't support this feature
        return False

    def get_rx_los(self):
        """
        Retrieves the RX LOS (lost-of-signal) status of SFP

        Returns:
            A Boolean, True if SFP has RX LOS, False if not.
            Note : RX LOS status is latched until a call to get_rx_los or a reset.
        """
        if not self.dom_supported:
            return None

        rx_los_list = []
        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0
            dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_CHANNL_RX_LOS_STATUS_OFFSET), QSFP_CHANNL_RX_LOS_STATUS_WIDTH)
            if dom_channel_monitor_raw is not None:
                rx_los_data = int(dom_channel_monitor_raw[0], 16)
                rx_los_list.append(rx_los_data & 0x01 != 0)
                rx_los_list.append(rx_los_data & 0x02 != 0)
                rx_los_list.append(rx_los_data & 0x04 != 0)
                rx_los_list.append(rx_los_data & 0x08 != 0)

        #QSFP-DD
        else:
            # page 11h (we put page 11 to byte 768~895)
            if self.dom_rx_los_supported:
                offset = 768
                dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_CHANNL_RX_LOS_STATUS_OFFSET), QSFP_DD_CHANNL_RX_LOS_STATUS_WIDTH)
                if dom_channel_monitor_raw is not None:
                    rx_los_data = int(dom_channel_monitor_raw[0], 16)
                    rx_los_list.append(rx_los_data & 0x01 != 0)
                    rx_los_list.append(rx_los_data & 0x02 != 0)
                    rx_los_list.append(rx_los_data & 0x04 != 0)
                    rx_los_list.append(rx_los_data & 0x08 != 0)
                    rx_los_list.append(rx_los_data & 0x10 != 0)
                    rx_los_list.append(rx_los_data & 0x20 != 0)
                    rx_los_list.append(rx_los_data & 0x40 != 0)
                    rx_los_list.append(rx_los_data & 0x80 != 0)

        return rx_los_list

    def get_tx_fault(self):
        """
        Retrieves the TX fault status of SFP

        Returns:
            A Boolean, True if SFP has TX fault, False if not
            Note : TX fault status is lached until a call to get_tx_fault or a reset.
        """
        self.reinit()
        if not self.dom_supported:
            return None

        tx_fault_list = []
        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0
            dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_CHANNL_TX_FAULT_STATUS_OFFSET), QSFP_CHANNL_TX_FAULT_STATUS_WIDTH)
            if dom_channel_monitor_raw is not None:
                tx_fault_data = int(dom_channel_monitor_raw[0], 16)
                tx_fault_list.append(tx_fault_data & 0x01 != 0)
                tx_fault_list.append(tx_fault_data & 0x02 != 0)
                tx_fault_list.append(tx_fault_data & 0x04 != 0)
                tx_fault_list.append(tx_fault_data & 0x08 != 0)

        #QSFP-DD
        else:
            # page 11h (we put page 11 to byte 768~895)
            if self.dom_tx_fault_supported:
                offset = 768
                dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_CHANNL_TX_FAULT_STATUS_OFFSET), QSFP_DD_CHANNL_TX_FAULT_STATUS_WIDTH)
                if dom_channel_monitor_raw is not None:
                    tx_fault_data = int(dom_channel_monitor_raw[0], 16)
                    tx_fault_list.append(tx_fault_data & 0x01 != 0)
                    tx_fault_list.append(tx_fault_data & 0x02 != 0)
                    tx_fault_list.append(tx_fault_data & 0x04 != 0)
                    tx_fault_list.append(tx_fault_data & 0x08 != 0)
                    tx_fault_list.append(tx_fault_data & 0x10 != 0)
                    tx_fault_list.append(tx_fault_data & 0x20 != 0)
                    tx_fault_list.append(tx_fault_data & 0x40 != 0)
                    tx_fault_list.append(tx_fault_data & 0x80 != 0)

        return tx_fault_list

    def get_tx_disable(self):
        """
        Retrieves the tx_disable status of this SFP

        Returns:
            A Boolean, True if tx_disable is enabled, False if disabled

        for QSFP, the disable states of each channel which are the lower 4 bits in byte 85 page a0
        for SFP, the TX Disable State and Soft TX Disable Select is ORed as the tx_disable status returned
                 These two bits are bit 7 & 6 in byte 110 page a2 respectively
        """
        self.reinit()
        if not self.dom_supported:
            return None

        tx_disable_list = []
        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0
            dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_CHANNL_DISABLE_STATUS_OFFSET), QSFP_CHANNL_DISABLE_STATUS_WIDTH)
            if dom_channel_monitor_raw is not None:
                tx_disable_data = int(dom_channel_monitor_raw[0], 16)
                tx_disable_list.append(tx_disable_data & 0x01 != 0)
                tx_disable_list.append(tx_disable_data & 0x02 != 0)
                tx_disable_list.append(tx_disable_data & 0x04 != 0)
                tx_disable_list.append(tx_disable_data & 0x08 != 0)

        #QSFP-DD
        else:
            # page 10h (we put page 10 to byte 640~767)
            offset = 640
            dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_CHANNL_DISABLE_STATUS_OFFSET), QSFP_DD_CHANNL_DISABLE_STATUS_WIDTH)
            if dom_channel_monitor_raw is not None:
                tx_disable_data = int(dom_channel_monitor_raw[0], 16)
                tx_disable_list.append(tx_disable_data & 0x01 != 0)
                tx_disable_list.append(tx_disable_data & 0x02 != 0)
                tx_disable_list.append(tx_disable_data & 0x04 != 0)
                tx_disable_list.append(tx_disable_data & 0x08 != 0)
                tx_disable_list.append(tx_disable_data & 0x10 != 0)
                tx_disable_list.append(tx_disable_data & 0x20 != 0)
                tx_disable_list.append(tx_disable_data & 0x40 != 0)
                tx_disable_list.append(tx_disable_data & 0x80 != 0)

        return tx_disable_list

    def get_tx_disable_channel(self):
        """
        Retrieves the TX disabled channels in this SFP
        Returns:
            A hex of 4 bits (bit 0 to bit 3 as channel 0 to channel 3) to represent
            TX channels which have been disabled in this SFP.
            As an example, a returned value of 0x5 indicates that channel 0
            and channel 2 have been disabled.
        """
        # SFP doesn't support this feature
        return 0

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        lpmode = False
        try:
            if self.index < 16:
                lpmode_path=self.LPMODE_1_16_PATH.format(self.port_num)
            else:
                lpmode_path=self.LPMODE_17_32_PATH.format(self.port_num)
            with open(lpmode_path, 'r') as sfp_lpmode:
                lpmode = int(sfp_lpmode.read(), 16)
        except IOError:
            return False
        return lpmode == 1

    def get_power_override(self):
        """
        Retrieves the power-override status of this SFP
        Returns:
            A Boolean, True if power-override is enabled, False if disabled
        """
        # SFP doesn't support this feature
        return False

    def get_temperature(self):
        """
        Retrieves the temperature of this SFP

        Returns:
            An integer number of current temperature in Celsius
        """
        self.reinit()
        if not self.dom_supported:
            return None
        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0

            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return None

            if self.dom_temp_supported:
                dom_temperature_raw = self._read_eeprom_specific_bytes((offset + QSFP_TEMPE_OFFSET), QSFP_TEMPE_WIDTH)
                if dom_temperature_raw is not None:
                    dom_temperature_data = sfpd_obj.parse_temperature(dom_temperature_raw, 0)
                    temp = self._convert_string_to_num(dom_temperature_data['data']['Temperature']['value'])
                    return temp
                else:
                    return None
            else:
                return None

        #QSFP-DD
        else:
            offset = 0

            sfpd_obj = qsfp_dd_Dom()
            if sfpd_obj is None:
                return None

            if self.dom_temp_supported:
                dom_temperature_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_TEMPE_OFFSET), QSFP_DD_TEMPE_WIDTH)
                if dom_temperature_raw is not None:
                    dom_temperature_data = sfpd_obj.parse_temperature(dom_temperature_raw, 0)
                    temp = self._convert_string_to_num(dom_temperature_data['data']['Temperature']['value'])
                    return temp
            return None

    def get_voltage(self):
        """
        Retrieves the supply voltage of this SFP

        Returns:
            An integer number of supply voltage in mV
        """
        self.reinit()
        if not self.dom_supported:
            return None

        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0

            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return None

            if self.dom_volt_supported:
                dom_voltage_raw = self._read_eeprom_specific_bytes((offset + QSFP_VOLT_OFFSET), QSFP_VOLT_WIDTH)
                if dom_voltage_raw is not None:
                    dom_voltage_data = sfpd_obj.parse_voltage(dom_voltage_raw, 0)
                    voltage = self._convert_string_to_num(dom_voltage_data['data']['Vcc']['value'])
                    return voltage
                else:
                    return None
            return None

        #QSFP-DD
        else:
            offset = 0

            sfpd_obj = qsfp_dd_Dom()
            if sfpd_obj is None:
                return None

            if self.dom_volt_supported:
                dom_voltage_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_VOLT_OFFSET), QSFP_DD_VOLT_WIDTH)
                if dom_voltage_raw is not None:
                    dom_voltage_data = sfpd_obj.parse_voltage(dom_voltage_raw, 0)
                    voltage = self._convert_string_to_num(dom_voltage_data['data']['Vcc']['value'])
                    return voltage
            return None

    def get_tx_bias(self):
        """
        Retrieves the TX bias current of this SFP

        Returns:
            A list of four integer numbers, representing TX bias in mA
            for channel 0 to channel 4.
            Ex. ['110.09', '111.12', '108.21', '112.09']
        """
        self.reinit()
        tx_bias_list = []

        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0

            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return None

            dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_CHANNL_MON_OFFSET), QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH)
            if dom_channel_monitor_raw is not None:
                dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params_with_tx_power(dom_channel_monitor_raw, 0)
                tx_bias_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX1Bias']['value']))
                tx_bias_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX2Bias']['value']))
                tx_bias_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX3Bias']['value']))
                tx_bias_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX4Bias']['value']))

        #QSFP-DD
        else:
            # page 11h (we put page 1 to byte 768~895)
            if dom_tx_bias_power_supported:
                offset = 768
                sfpd_obj = qsfp_dd_Dom()
                if sfpd_obj is None:
                    return None

                dom_tx_bias_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_TX_BIAS_OFFSET), QSFP_DD_TX_BIAS_WIDTH)
                if dom_tx_bias_raw is not None:
                    dom_tx_bias_data = sfpd_obj.parse_dom_tx_bias(dom_tx_bias_raw, 0)
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX1Bias']['value']))
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX2Bias']['value']))
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX3Bias']['value']))
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX4Bias']['value']))
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX5Bias']['value']))
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX6Bias']['value']))
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX7Bias']['value']))
                    tx_bias_list.append(self._convert_string_to_num(dom_tx_bias_data['data']['TX8Bias']['value']))

        return tx_bias_list

    def get_rx_power(self):
        """
        Retrieves the received optical power for this SFP

        Returns:
            A list of four integer numbers, representing received optical
            power in mW for channel 0 to channel 4.
            Ex. ['1.77', '1.71', '1.68', '1.70']
        """
        self.reinit()
        rx_power_list = []

        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0

            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return None

            if self.dom_rx_power_supported:
                dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_CHANNL_MON_OFFSET), QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH)
                if dom_channel_monitor_raw is not None:
                    dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params_with_tx_power(dom_channel_monitor_raw, 0)
                    rx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['RX1Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['RX2Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['RX3Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['RX4Power']['value']))
                else:
                    return None
            else:
                return None

        #QSFP-DD
        elif self.sfp_type == QSFP_DD_TYPE:
            # page 11h (we put page 11 to byte 768~895)
            if self.dom_rx_power_supported:
                offset = 768
                sfpd_obj = qsfp_dd_Dom()
                if sfpd_obj is None:
                    return None

                dom_rx_power_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_RX_POWER_OFFSET), QSFP_DD_RX_POWER_WIDTH)
                if dom_rx_power_raw is not None:
                    dom_rx_power_data = sfpd_obj.parse_dom_rx_power(dom_rx_power_raw, 0)
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX1Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX2Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX3Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX4Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX5Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX6Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX7Power']['value']))
                    rx_power_list.append(self._convert_string_to_num(dom_rx_power_data['data']['RX8Power']['value']))

        return rx_power_list

    def get_tx_power(self):
        """
        Retrieves the TX power of this SFP

        Returns:
            A list of four integer numbers, representing TX power in mW
            for channel 0 to channel 4.
            Ex. ['1.86', '1.86', '1.86', '1.86']
        """
        self.reinit()
        tx_power_list = []

        #QSFP
        if self.sfp_type == QSFP_TYPE:
            offset = 0

            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return None

            if self.dom_tx_power_supported:
                dom_channel_monitor_raw = self._read_eeprom_specific_bytes((offset + QSFP_CHANNL_MON_OFFSET), QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH)
                if dom_channel_monitor_raw is not None:
                    dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params_with_tx_power(dom_channel_monitor_raw, 0)
                    tx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX1Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX2Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX3Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_channel_monitor_data['data']['TX4Power']['value']))
                else:
                    return None
            else:
                return None

        #QSFP-DD
        else:
            # page 11h (we put page 11 to byte 768~895)
            if self.dom_tx_power_supported:
                offset = 768
                sfpd_obj = qsfp_dd_Dom()
                if sfpd_obj is None:
                    return None

                dom_tx_power_raw = self._read_eeprom_specific_bytes((offset + QSFP_DD_TX_POWER_OFFSET), QSFP_DD_TX_POWER_WIDTH)
                if dom_tx_power_raw is not None:
                    dom_tx_power_data = sfpd_obj.parse_dom_tx_power(dom_tx_power_raw, 0)
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX1Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX2Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX3Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX4Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX5Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX6Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX7Power']['value']))
                    tx_power_list.append(self._convert_string_to_num(dom_tx_power_data['data']['TX8Power']['value']))

        return tx_power_list

    def reset(self):
        """
        Reset SFP and return all user module settings to their default srate.
        Returns:
            A boolean, True if successful, False if not
        """
        try:
            if self.index < 16:
                file_path=self.RESET_1_16_PATH.format(self.port_num)
            else:
                file_path=self.RESET_17_32_PATH.format(self.port_num)

            with open(file_path, 'w') as fd:
                fd.write(str(1))
                time.sleep(1)
                fd.write(str(0))
                time.sleep(1)

        except IOError:
            return False

        return True

    def tx_disable(self, tx_disable):
        """
        Disable SFP TX for all channels
        Args:
            tx_disable : A Boolean, True to enable tx_disable mode, False to disable
                         tx_disable mode.
        Returns:
            A boolean, True if tx_disable is set successfully, False if not
        """
        # SFP doesn't support this feature
        return False

    def tx_disable_channel(self, channel, disable):
        """
        Sets the tx_disable for specified SFP channels
        Args:
            channel : A hex of 4 bits (bit 0 to bit 3) which represent channel 0 to 3,
                      e.g. 0x5 for channel 0 and channel 2.
            disable : A boolean, True to disable TX channels specified in channel,
                      False to enable
        Returns:
            A boolean, True if successful, False if not
        """
        # SFP doesn't support this feature
        return False

    def set_lpmode(self, lpmode):
        """
        Sets the lpmode (low power mode) of SFP
        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override
        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        try:
            if self.index < 16:
                lpmode_path=self.LPMODE_1_16_PATH.format(self.port_num)
            else:
                lpmode_path=self.LPMODE_17_32_PATH.format(self.port_num)
            val_file = open(lpmode_path, 'w')
            val_file.write('1' if lpmode else '0')
            val_file.close()
            self.set_power_override(True, True if lpmode is True else False)
            return True
        except IOError:
            val_file.close()
            return False

    def set_power_override(self, power_override, power_set):
        """
        Sets SFP power level using power_override and power_set
        Args:
            power_override :
                    A Boolean, True to override set_lpmode and use power_set
                    to control SFP power, False to disable SFP power control
                    through power_override/power_set and use set_lpmode
                    to control SFP power.
            power_set :
                    Only valid when power_override is True.
                    A Boolean, True to set SFP to low power mode, False to set
                    SFP to high power mode.
        Returns:
            A boolean, True if power-override and power_set are set successfully,
            False if not
        """
        if not self.get_presence():
            return False
        if self.sfp_type == QSFP_TYPE:
            try:
                pwr_mode = self._read_eeprom_specific_bytes(QSFP_POWEROVERRIDE_OFFSET, QSFP_POWEROVERRIDE_WIDTH)
                power_override_bit = (1 << 0) if power_override else 0
                power_set_bit      = (1 << 1) if power_set else (1 << 3)

                # Write to eeprom
                with open(self.port_to_power_mode_mapping[self.index], "w") as fd:
                    fd.write(str((power_override_bit | power_set_bit)))
                    time.sleep(0.01)
                    fd.close()
            except Exception as e:
                print ('Error: unable to open file: ', str(e))
                fd.close()
                return False
            return True
        elif self.sfp_type == QSFP_DD_TYPE:
            try:
                power_override_bit = (1 << 6)
                power_set_bit      = (1 << 4) if power_set else (0 << 4)

                # Write to eeprom
                with open(self.port_to_power_mode_mapping[self.index], "w") as fd:
                    fd.write(str((power_override_bit | power_set_bit)))
                    time.sleep(0.01)
                    fd.close()
            except Exception as e:
                print ('Error: unable to open file: ', str(e))
                fd.close()
                return False
            return True

    def read_eeprom(self, offset, num_bytes):
        """
        read eeprom specfic bytes beginning from a random offset with size as num_bytes

        Args:
             offset :
                     Integer, the offset from which the read transaction will start
             num_bytes:
                     Integer, the number of bytes to be read

        Returns:
            bytearray, if raw sequence of bytes are read correctly from the offset of size num_bytes
            None, if the read_eeprom fails
        """
        if not self.get_presence():
            return False
        self.reinit()
        if self.sfp_type == QSFP_DD_TYPE:
            #offset check
            if offset < 256:
                return bytearray([int(x, 16) for x in self._read_eeprom_specific_bytes(offset, num_bytes)])
            elif offset >= (0x4 * 128 + 128) and offset < (0x5 * 128 + 128):
                return bytearray([int(x, 16) for x in self._read_eeprom_specific_bytes(offset - (0x4 * 128), num_bytes, 4)])
            else:
                return None
        else:
            return None

    def write_eeprom(self, offset, num_bytes, write_buffer):
        """
        write eeprom specfic bytes beginning from a random offset with size as num_bytes
        and write_buffer as the required bytes

        Args:
             offset :
                     Integer, the offset from which the read transaction will start
             num_bytes:
                     Integer, the number of bytes to be written
             write_buffer:
                     bytearray, raw bytes buffer which is to be written beginning at the offset

        Returns:
            a Boolean, true if the write succeeded and false if it did not succeed.
        """
        if not self.get_presence():
            return False
        self.reinit()
        if self.sfp_type == QSFP_DD_TYPE:
            #offset check
            if offset == (0x12 * 128 + 128):
                # Write to eeprom
                with open(self.port_to_grid_mapping[self.index], "w") as fd:
                    fd.write(str((int(str(write_buffer.hex()), 16))))
                    time.sleep(0.01)
                    fd.close()
            elif offset == (0x12 * 128 + 136):
                # Write to eeprom
                with open(self.port_to_freq_mapping[self.index], "w") as fd:
                    fd.write(str((int(str(write_buffer.hex()), 16))))
                    time.sleep(0.01)
                    fd.close()
            elif offset == (0x12 * 128 + 200):
                # Write to eeprom
                with open(self.port_to_outp_mapping[self.index], "w") as fd:
                    fd.write(str((int(str(write_buffer.hex()), 16))))
                    time.sleep(0.01)
                    fd.close()
            else:
                return False
        else:
            return False

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """

        name='port'+str(self.index + 1)
        return name

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        transceiver_dom_info_dict = self.get_transceiver_info()
        return transceiver_dom_info_dict.get("model", "N/A")

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        transceiver_dom_info_dict = self.get_transceiver_info()
        return transceiver_dom_info_dict.get("serial", "N/A")

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self.get_presence() and not self.get_reset_status()

    def get_position_in_parent(self):
        """
        Returns:
            Temp return 0
        """
        return 0

    def is_replaceable(self):
        """
        Retrieves if replaceable
        Returns:
            A boolean value, True if replaceable
        """
        return True

    def get_error_description(self):
        """
        Get error description

        Args:
            error_code: The error code returned by _get_error_code

        Returns:
            The error description
        """
        if self.get_presence():
            return self.SFP_STATUS_OK
        else:
            return self.SFP_STATUS_UNPLUGGED

    def _convert_str_to_int(self, data, data_len, unit=1):
        val = 0
        for i in range(data_len):
            val = val + (int(data[i], 16) << (data_len - 1 - i) * 8)
        mask = 1 << (data_len * 8 - 1)
        val = int((-(val & mask) | (val & (mask - 1))) / unit)
        return val

    def _convert_str_to_float(self, data, data_len, unit=1.0):
        val = 0
        for i in range(data_len):
            val = val + (int(data[i], 16) << (data_len - 1 - i) * 8)
        mask = 1 << (data_len * 8 - 1)
        val = (-(val & mask) | (val & (mask - 1))) / unit
        return val

    def _is_coherent_module(self):
        """
        Check if module type is ZR

        Args:
           None

        Returns:
            True if module type is ZR. False if module type is not ZR.
        """
        # Media type is in page 0, offset 85
        # media interface is in page 0 ,offset 87, 91, 95, 99, 103, 107, 111 and 115
        # The type of ZR is 0x6, 0x3E, 0x3F, 0x46, 0x47, 0x48 and 0x49
        media_type = int(self._read_eeprom_specific_bytes(85, 1)[0], 16)
        if media_type == 0x2:
            for i in range(0, 8):
                media_intf = int(self._read_eeprom_specific_bytes(87 + 4 * i, 1)[0], 16)
                if media_intf == 0x6 or media_intf == 0x3E or media_intf == 0x3F or media_intf == 0x46 or \
                        media_intf == 0x47 or media_intf == 0x48 or media_intf == 0x49:
                    return True
        return False

    def get_supported_freq_config(self):
        '''
        This function returns the supported freq grid, low and high supported channel in 75GHz grid,
        and low and high frequency supported in GHz.
        allowed channel number bound in 75 GHz grid
        allowed frequency bound in 75 GHz grid
        '''
        # Get GRID
        grid_supported = self._read_eeprom_specific_bytes(128, 1, 0x4)
        grid_supported = self._convert_str_to_int(grid_supported, 1)

        # Get Low Frequency
        low_ch_num = self._read_eeprom_specific_bytes(158, 2, 0x4)
        low_ch_num = self._convert_str_to_int(low_ch_num, 2)

        # Get high Frequency
        hi_ch_num = self._read_eeprom_specific_bytes(160, 2, 0x4)
        hi_ch_num = self._convert_str_to_int(hi_ch_num, 2)

        # Get support frequency
        low_freq_supported = 193100 + low_ch_num * 25
        high_freq_supported = 193100 + hi_ch_num * 25
        return grid_supported, low_ch_num, hi_ch_num, low_freq_supported, high_freq_supported

    def set_laser_freq(self, freq, grid=75):
        '''
        This function sets the laser frequency. Unit in GHz
        ZR application will not support fine tuning of the laser
        SONiC will only support 75 GHz frequency grid
        Return True if the provision succeeds, False if it fails
        '''
        if not self._is_coherent_module():
            return False

        # Get frequency config
        grid_supported, low_ch_num, hi_ch_num, _, _ = self.get_supported_freq_config()
        grid_supported_75GHz = (grid_supported >> 7) & 0x1
        grid_supported_100GHz = (grid_supported >> 5) & 0x1

        support_fine_tune = self._read_eeprom_specific_bytes(129, 1, 0x4)
        support_fine_tune = True if int(support_fine_tune[0], 16) == 0x80 else False

        # Check frequency 
        if grid == 75:
            if not grid_supported_75GHz:
                return False
            freq_grid = 0x70
            if support_fine_tune:
                freq_grid = 0x71
            channel_number = int(round((freq - 193100) / 25))
            if not channel_number % 3 == 0:
                return False
        elif grid == 100:
            if not grid_supported_100GHz:
                return False
            freq_grid = 0x50
            if support_fine_tune:
                freq_grid = 0x51
            channel_number = int(round((freq - 193100) / 100))
        else:
            return False

        # Read Grid Space
        try:
            with open(self.port_to_grid_mapping[self.index], "r") as fd:
                read_grid = int(fd.read(), 16)
        except IOError:
            return False
        new_grid = (read_grid & 0x0E) | (freq_grid & 0xF1)
        # Write Grid Space
        try:
            with open(self.port_to_grid_mapping[self.index], "w") as fd:
                fd.write(str(new_grid))
        except IOError:
            return False

        # Check if frequency is valid
        if channel_number > hi_ch_num or channel_number < low_ch_num:
            raise False

        # Write Frequency
        try:
            with open(self.port_to_freq_mapping[self.index], "w") as fd:
                fd.write(str(channel_number))
        except IOError:
            return False

        if support_fine_tune:
            if grid == 75:
                new_freq = channel_number * 25 + 193100
            elif grid == 100:
                new_freq = channel_number * 75 + 193100
            else:
                return False
            fine_tune_freq = int((freq - new_freq) * 1000)
            try:
                with open(self.port_to_fine_tune_freq[self.index], "w") as f:
                    f.write(str(fine_tune_freq))
            except IOError:
                return False
        return True

    def get_current_laser_freq(self):
        '''
        This function returns the monitored laser frequency. Unit in GHz
        '''
        with open(self.port_to_curr_freq_mapping[self.index], "r") as fd:
            freq = int(fd.read())
        return freq / 1000

    def get_tuning_in_progress(self):
        '''
        This function returns tuning in progress status on media lane
        False means tuning not in progress
        True means tuning in progress
        '''
        return bool(int(self._read_eeprom_specific_bytes(222, 1, 0x12)[0], 16))

    def get_support_fine_tuning(self):
        support_fine_tune = self._read_eeprom_specific_bytes(129, 1, 0x4)
        return True if int(support_fine_tune[0], 16) == 0x80 else False

    def get_supported_power_config(self):
        '''
        This function returns the supported TX power range
        '''
        # Get Low Power
        lo_pwr = self._read_eeprom_specific_bytes(198, 2, 0x4)
        lo_pwr = self._convert_str_to_float(lo_pwr, 2, 100)

        # Get Low Power
        hi_pwr = self._read_eeprom_specific_bytes(200, 2, 0x4)
        hi_pwr = self._convert_str_to_float(hi_pwr, 2, 100)
        return lo_pwr, hi_pwr

    def set_tx_power(self, tx_power):
        '''
        This function sets the TX output power. Unit in dBm
        Return True if the provision succeeds, False if it fails
        '''
        if not self._is_coherent_module():
            return False
        min_prog_tx_output_power, max_prog_tx_output_power = self.get_supported_power_config()
        if tx_power > max_prog_tx_output_power or tx_power < min_prog_tx_output_power:
            return False
        tx_power = int(tx_power * 100)
        try:
            with open(self.port_to_outp_mapping[self.index], "w") as f:
                f.write(str(tx_power))
        except IOError:
            return False
        return True

    def get_pm_all(self):
        '''
        This function returns the PMs reported in Page 34h and 35h in OIF C-CMIS document
        CD:     unit in ps/nm
        DGD:    unit in ps
        SOPMD:  unit in ps^2
        PDL:    unit in dB
        OSNR:   unit in dB
        ESNR:   unit in dB
        CFO:    unit in MHz
        TXpower:unit in dBm
        RXpower:unit in dBm
        RX sig power:   unit in dBm
        SOPROC: unit in krad/s
        MER:    unit in dB
        '''
        # When raised by the host, causes the module to freeze and hold all
        # reported statistics reporting registers (minimum, maximum and
        # average values)in Pages 24h-27h.
        # When ceased by the host, releases the freeze request, allowing the
        # reported minimum, maximum and average values to update again.
        try:
            with open(self.port_to_vdm_freeze_mapping[self.index], "w") as f:
                f.write(str(VDM_FREEZE))
            while True:
                val = self._read_eeprom_specific_bytes(144, 1, 0x2f)
                val = int(self._convert_str_to_float(val, 1)) & 0x80
                if val == VDM_FREEZE:
                    break
                time.sleep(1)

            time.sleep(1)

            with open(self.port_to_vdm_freeze_mapping[self.index], "w") as f:
                f.write(str(VDM_UNFREEZE))
            while True:
                val = self._read_eeprom_specific_bytes(144, 1, 0x2f)
                val = int(self._convert_str_to_float(val, 1)) & 0x80
                if val == VDM_UNFREEZE:
                    break
                time.sleep(1)
        except IOError as except_info:
            return None
        PM_dict = dict()

        # 128 RX_BITS_PM
        data_len = 8
        data = self._read_eeprom_specific_bytes(128, data_len, 0x34)
        rx_bits_pm = self._convert_str_to_float(data, data_len)

        # 136 RX_BITS_SUB_INTERVAL_PM
        data_len = 8
        data = self._read_eeprom_specific_bytes(136, data_len, 0x34)
        rx_bits_subint_pm = self._convert_str_to_float(data, data_len)

        # 144 RX_CORR_BITS_PM
        data_len = 8
        data = self._read_eeprom_specific_bytes(144, data_len, 0x34)
        rx_corr_bits_pm = self._convert_str_to_float(data, data_len)

        # 152 RX_MIN_CORR_BITS_SUB_INTERVAL_PM
        data_len = 8
        data = self._read_eeprom_specific_bytes(152, data_len, 0x34)
        rx_min_corr_bits_subint_pm = self._convert_str_to_float(data, data_len)

        # 160 RX_MAX_CORR_BITS_SUB_INTERVAL_PM
        data_len = 8
        data = self._read_eeprom_specific_bytes(160, data_len, 0x34)
        rx_max_corr_bits_subint_pm = self._convert_str_to_float(data, data_len)

        if (rx_bits_subint_pm != 0) and (rx_bits_pm != 0):
            PM_dict['preFEC_BER_avg'] = rx_corr_bits_pm * 1.0 / rx_bits_pm
            PM_dict['preFEC_BER_min'] = rx_min_corr_bits_subint_pm * 1.0 / rx_bits_subint_pm
            PM_dict['preFEC_BER_max'] = rx_max_corr_bits_subint_pm * 1.0 / rx_bits_subint_pm
        # when module is low power, still need these values to show 1.0
        else:
            PM_dict['preFEC_BER_avg'] = 1.0
            PM_dict['preFEC_BER_min'] = 1.0
            PM_dict['preFEC_BER_max'] = 1.0

        # 168 RX_FRAMES_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(168, data_len, 0x34)
        rx_frames_pm = self._convert_str_to_float(data, data_len)

        # 172 RX_FRAMES_SUB_INTERVAL_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(172, data_len, 0x34)
        rx_frames_subint_pm = self._convert_str_to_float(data, data_len)

        # 176  RX_FRAMES_UNCORR_ERR_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(176, data_len, 0x34)
        rx_frames_uncorr_err_pm = self._convert_str_to_float(data, data_len)

        # 180 RX_MIN_FRAMES_UNCORR_ERR_SUB_INTERVAL_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(180, data_len, 0x34)
        rx_min_frames_uncorr_err_subint_pm = self._convert_str_to_float(data, data_len)

        # 184 RX_MAX_FRAMES_UNCORR_ERR_SUB_INTERVAL_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(184, data_len, 0x34)
        rx_max_frames_uncorr_err_subint_pm = self._convert_str_to_float(data, data_len)

        if (rx_frames_subint_pm != 0) and (rx_frames_pm != 0):
            PM_dict['preFEC_uncorr_frame_ratio_avg'] = rx_frames_uncorr_err_pm * 1.0 / rx_frames_subint_pm
            PM_dict['preFEC_uncorr_frame_ratio_min'] = rx_min_frames_uncorr_err_subint_pm * 1.0 / rx_frames_subint_pm
            PM_dict['preFEC_uncorr_frame_ratio_max'] = rx_max_frames_uncorr_err_subint_pm * 1.0 / rx_frames_subint_pm
        # when module is low power, still need these values
        else:
            PM_dict['preFEC_uncorr_frame_ratio_avg'] = 0
            PM_dict['preFEC_uncorr_frame_ratio_min'] = 0
            PM_dict['preFEC_uncorr_frame_ratio_max'] = 0

        # 128 RX_AVG_CD_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(128, data_len, 0x35)
        PM_dict['rx_cd_avg'] = self._convert_str_to_float(data, data_len)

        # 132 RX_MIN_CD_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(132, data_len, 0x35)
        PM_dict['rx_cd_min'] = self._convert_str_to_float(data, data_len)

        # 136 RX_MAX_CD_PM
        data_len = 4
        data = self._read_eeprom_specific_bytes(136, data_len, 0x35)
        PM_dict['rx_cd_max'] = self._convert_str_to_float(data, data_len)

        # 140 RX_AVG_DGD_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(140, data_len, 0x35)
        PM_dict['rx_dgd_avg'] = self._convert_str_to_float(data, data_len, 100.0)

        # 142 RX_MIN_DGD_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(142, data_len, 0x35)
        PM_dict['rx_dgd_min'] = self._convert_str_to_float(data, data_len, 100.0)

        # 144 RX_MAX_DGD_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(144, data_len, 0x35)
        PM_dict['rx_dgd_max'] = self._convert_str_to_float(data, data_len, 100.0)

        # 146 RX_AVG_SOPMD_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(146, data_len, 0x35)
        PM_dict['rx_sopmd_avg'] = self._convert_str_to_float(data, data_len, 100.0)

        # 148 RX_AVG_SOPMD_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(148, data_len, 0x35)
        PM_dict['rx_sopmd_min'] = self._convert_str_to_float(data, data_len, 100.0)

        # 150 RX_AVG_SOPMD_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(150, data_len, 0x35)
        PM_dict['rx_sopmd_max'] = self._convert_str_to_float(data, data_len, 100.0)

        # 152 RX_AVG_PDL_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(152, data_len, 0x35)
        PM_dict['rx_pdl_avg'] = self._convert_str_to_float(data, data_len, 10.0)

        # 154 RX_MIN_PDL_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(154, data_len, 0x35)
        PM_dict['rx_pdl_min'] = self._convert_str_to_float(data, data_len, 10.0)

        # 156 RX_MAX_PDL_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(156, data_len, 0x35)
        PM_dict['rx_pdl_max'] = self._convert_str_to_float(data, data_len, 10.0)

        # 158 RX_AVG_OSNR_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(158, data_len, 0x35)
        PM_dict['rx_osnr_avg'] = self._convert_str_to_float(data, data_len, 10.0)

        # 160 RX_MIN_OSNR_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(160, data_len, 0x35)
        PM_dict['rx_osnr_min'] = self._convert_str_to_float(data, data_len, 10.0)

        # 162 RX_MAX_OSNR_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(162, data_len, 0x35)
        PM_dict['rx_osnr_max'] = self._convert_str_to_float(data, data_len, 10.0)

        # 164 RX_MAX_OSNR_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(162, data_len, 0x35)
        PM_dict['rx_esnr_avg'] = self._convert_str_to_float(data, data_len, 10.0)

        # 166 RX_MAX_OSNR_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(162, data_len, 0x35)
        PM_dict['rx_esnr_min'] = self._convert_str_to_float(data, data_len, 10.0)

        # 168 RX_MAX_OSNR_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(168, data_len, 0x35)
        PM_dict['rx_esnr_max'] = self._convert_str_to_float(data, data_len, 10.0)

        # 170 RX_AVG_CFO_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(170, data_len, 0x35)
        PM_dict['rx_cfo_avg'] = self._convert_str_to_float(data, data_len)

        # 172 RX_MIN_CFO_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(172, data_len, 0x35)
        PM_dict['rx_cfo_min'] = self._convert_str_to_float(data, data_len)

        # 174 RX_MAX_CFO_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(174, data_len, 0x35)
        PM_dict['rx_cfo_max'] = self._convert_str_to_float(data, data_len)

        # 176 RX_AVG_EVM_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(176, data_len, 0x35)
        PM_dict['rx_evm_avg'] = self._convert_str_to_float(data, data_len, 655.35)

        # 178 RX_MIN_EVM_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(178, data_len, 0x35)
        PM_dict['rx_evm_min'] = self._convert_str_to_float(data, data_len, 655.35)

        # 180 RX_MAX_EVM_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(180, data_len, 0x35)
        PM_dict['rx_evm_max'] = self._convert_str_to_float(data, data_len, 655.35)

        # 182 TX_AVG_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(182, data_len, 0x35)
        PM_dict['tx_power_avg'] = self._convert_str_to_float(data, data_len, 100.0)

        # 184 TX_MIN_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(184, data_len, 0x35)
        PM_dict['tx_power_min'] = self._convert_str_to_float(data, data_len, 100.0)

        # 186 TX_MAX_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(186, data_len, 0x35)
        PM_dict['tx_power_max'] = self._convert_str_to_float(data, data_len, 100.0)

        # 188 RX_AVG_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(188, data_len, 0x35)
        PM_dict['rx_power_avg'] = self._convert_str_to_float(data, data_len, 100.0)

        # 190 RX_MIN_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(190, data_len, 0x35)
        PM_dict['rx_power_min'] = self._convert_str_to_float(data, data_len, 100.0)

        # 174 RX_MAX_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(192, data_len, 0x35)
        PM_dict['rx_power_max'] = self._convert_str_to_float(data, data_len, 100.0)

        # 194 RX_AVG_SIG_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(194, data_len, 0x35)
        PM_dict['rx_sigpwr_avg'] = self._convert_str_to_float(data, data_len, 100.0)

        # 196 RX_MIN_SIG_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(196, data_len, 0x35)
        PM_dict['rx_sigpwr_min'] = self._convert_str_to_float(data, data_len, 100.0)

        # 198 RX_MAX_SIG_POWER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(198, data_len, 0x35)
        PM_dict['rx_sigpwr_max'] = self._convert_str_to_float(data, data_len, 100.0)

        # 200 RX_AVG_SOPROC_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(200, data_len, 0x35)
        PM_dict['rx_soproc_avg'] = self._convert_str_to_float(data, data_len, 10.0)

        # 202 RX_MIN_SOPROC_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(202, data_len, 0x35)
        PM_dict['rx_soproc_min'] = self._convert_str_to_float(data, data_len, 10.0)

        # 204 RX_MAX_SOPROC_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(204, data_len, 0x35)
        PM_dict['rx_soproc_max'] = self._convert_str_to_float(data, data_len, 10.0)

        # 206 RX_AVG_MER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(206, data_len, 0x35)
        PM_dict['rx_mer_avg'] = self._convert_str_to_float(data, data_len, 10.0)

        # 208 RX_MIN_MER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(208, data_len, 0x35)
        PM_dict['rx_mer_min'] = self._convert_str_to_float(data, data_len, 10.0)

        # 210 RX_MAX_MER_PM
        data_len = 2
        data = self._read_eeprom_specific_bytes(210, data_len, 0x35)
        PM_dict['rx_mer_max'] = self._convert_str_to_float(data, data_len, 10.0)

        return PM_dict

    def get_transceiver_pm(self):
        """
        Retrieves PM for this xcvr
        Returns:
            A dict containing the following keys/values :
        ========================================================================
        key                          = TRANSCEIVER_PM|ifname            ; information of PM on port
        ; field                      = value
        prefec_ber_avg               = FLOAT                            ; prefec ber avg
        prefec_ber_min               = FLOAT                            ; prefec ber min
        prefec_ber_max               = FLOAT                            ; prefec ber max
        uncorr_frames_avg            = FLOAT                            ; uncorrected frames ratio avg
        uncorr_frames_min            = FLOAT                            ; uncorrected frames ratio min
        uncorr_frames_max            = FLOAT                            ; uncorrected frames ratio max
        cd_avg                       = FLOAT                            ; chromatic dispersion avg
        cd_min                       = FLOAT                            ; chromatic dispersion min
        cd_max                       = FLOAT                            ; chromatic dispersion max
        dgd_avg                      = FLOAT                            ; differential group delay avg
        dgd_min                      = FLOAT                            ; differential group delay min
        dgd_max                      = FLOAT                            ; differential group delay max
        sopmd_avg                    = FLOAT                            ; second order polarization mode dispersion avg
        sopmd_min                    = FLOAT                            ; second order polarization mode dispersion min
        sopmd_max                    = FLOAT                            ; second order polarization mode dispersion max
        pdl_avg                      = FLOAT                            ; polarization dependent loss avg
        pdl_min                      = FLOAT                            ; polarization dependent loss min
        pdl_max                      = FLOAT                            ; polarization dependent loss max
        osnr_avg                     = FLOAT                            ; optical signal to noise ratio avg
        osnr_min                     = FLOAT                            ; optical signal to noise ratio min
        osnr_max                     = FLOAT                            ; optical signal to noise ratio max
        esnr_avg                     = FLOAT                            ; electrical signal to noise ratio avg
        esnr_min                     = FLOAT                            ; electrical signal to noise ratio min
        esnr_max                     = FLOAT                            ; electrical signal to noise ratio max
        cfo_avg                      = FLOAT                            ; carrier frequency offset avg
        cfo_min                      = FLOAT                            ; carrier frequency offset min
        cfo_max                      = FLOAT                            ; carrier frequency offset max
        soproc_avg                   = FLOAT                            ; state of polarization rate of change avg
        soproc_min                   = FLOAT                            ; state of polarization rate of change min
        soproc_max                   = FLOAT                            ; state of polarization rate of change max
        tx_power_avg                 = FLOAT                            ; tx output power avg
        tx_power_min                 = FLOAT                            ; tx output power min
        tx_power_max                 = FLOAT                            ; tx output power max
        rx_tot_power_avg             = FLOAT                            ; rx total power avg
        rx_tot_power_min             = FLOAT                            ; rx total power min
        rx_tot_power_max             = FLOAT                            ; rx total power max
        rx_sig_power_avg             = FLOAT                            ; rx signal power avg
        rx_sig_power_min             = FLOAT                            ; rx signal power min
        rx_sig_power_max             = FLOAT                            ; rx signal power max
        ========================================================================
        """
        if not self._is_coherent_module():
            return False
        trans_pm = dict()
        PM_dict = self.get_pm_all()
        trans_pm['prefec_ber_avg'] = PM_dict['preFEC_BER_avg']
        trans_pm['prefec_ber_min'] = PM_dict['preFEC_BER_min']
        trans_pm['prefec_ber_max'] = PM_dict['preFEC_BER_max']
        trans_pm['uncorr_frames_avg'] = PM_dict['preFEC_uncorr_frame_ratio_avg']
        trans_pm['uncorr_frames_min'] = PM_dict['preFEC_uncorr_frame_ratio_min']
        trans_pm['uncorr_frames_max'] = PM_dict['preFEC_uncorr_frame_ratio_max']
        trans_pm['cd_avg'] = PM_dict['rx_cd_avg']
        trans_pm['cd_min'] = PM_dict['rx_cd_min']
        trans_pm['cd_max'] = PM_dict['rx_cd_max']
        trans_pm['dgd_avg'] = PM_dict['rx_dgd_avg']
        trans_pm['dgd_min'] = PM_dict['rx_dgd_min']
        trans_pm['dgd_max'] = PM_dict['rx_dgd_max']
        trans_pm['sopmd_avg'] = PM_dict['rx_sopmd_avg']
        trans_pm['sopmd_min'] = PM_dict['rx_sopmd_min']
        trans_pm['sopmd_max'] = PM_dict['rx_sopmd_max']
        trans_pm['pdl_avg'] = PM_dict['rx_pdl_avg']
        trans_pm['pdl_min'] = PM_dict['rx_pdl_min']
        trans_pm['pdl_max'] = PM_dict['rx_pdl_max']
        trans_pm['osnr_avg'] = PM_dict['rx_osnr_avg']
        trans_pm['osnr_min'] = PM_dict['rx_osnr_min']
        trans_pm['osnr_max'] = PM_dict['rx_osnr_max']
        trans_pm['esnr_avg'] = PM_dict['rx_esnr_avg']
        trans_pm['esnr_min'] = PM_dict['rx_esnr_min']
        trans_pm['esnr_max'] = PM_dict['rx_esnr_max']
        trans_pm['cfo_avg'] = PM_dict['rx_cfo_avg']
        trans_pm['cfo_min'] = PM_dict['rx_cfo_min']
        trans_pm['cfo_max'] = PM_dict['rx_cfo_max']
        trans_pm['evm_avg'] = PM_dict['rx_evm_avg']
        trans_pm['evm_min'] = PM_dict['rx_evm_min']
        trans_pm['evm_max'] = PM_dict['rx_evm_max']
        trans_pm['soproc_avg'] = PM_dict['rx_soproc_avg']
        trans_pm['soproc_min'] = PM_dict['rx_soproc_min']
        trans_pm['soproc_max'] = PM_dict['rx_soproc_max']
        trans_pm['tx_power_avg'] = PM_dict['tx_power_avg']
        trans_pm['tx_power_min'] = PM_dict['tx_power_min']
        trans_pm['tx_power_max'] = PM_dict['tx_power_max']
        trans_pm['rx_tot_power_avg'] = PM_dict['rx_power_avg']
        trans_pm['rx_tot_power_min'] = PM_dict['rx_power_min']
        trans_pm['rx_tot_power_max'] = PM_dict['rx_power_max']
        trans_pm['rx_sig_power_avg'] = PM_dict['rx_sigpwr_avg']
        trans_pm['rx_sig_power_min'] = PM_dict['rx_sigpwr_min']
        trans_pm['rx_sig_power_max'] = PM_dict['rx_sigpwr_max']

        return trans_pm
