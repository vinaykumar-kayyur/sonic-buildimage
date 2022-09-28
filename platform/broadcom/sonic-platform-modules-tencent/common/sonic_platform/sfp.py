#!/usr/bin/python
# -*- coding: UTF-8 -*-

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
#
#############################################################################
import os
import re
import sys
import copy
import time
import syslog
import datetime
import traceback

configfile_pre = "/usr/local/bin/"
sys.path.append(configfile_pre)

try:
    from ctypes import create_string_buffer
    from platform_intf import *
    from plat_hal.baseutil import baseutil
    from sonic_platform_base.sfp_base import SfpBase
    from sonic_platform_base.sonic_sfp.sff8472 import sff8472InterfaceId
    from sonic_platform_base.sonic_sfp.sff8472 import sff8472Dom
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436InterfaceId
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436Dom
    from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_InterfaceId
    from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_Dom
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

#############################################################################
PORT_START = 0
PORT_END   = 0

PORT_SFP_START     = 0
PORT_SFP_END       = 0
PORT_QSFP_START    = 0
PORT_QSFP_END      = 0
PORT_QSFP_DD_START = 0
PORT_QSFP_DD_END   = 0

EEPROM_OFFSET = 0

global_sfp_config = {
    "flag" : False,
}

#############################################################################
LOG_DEBUG_LEVEL  = 1
LOG_ERROR_LEVEL  = 2
SFP_DEBUG_FILE   = "/etc/.sfp_debug_flag"

IDENTITY_EEPROM_ADDR = 0x50

INFO_OFFSET = 128
DOM_OFFSET  = 0
DOM_OFFSET1 = 384

SFP_TYPE  = "SFP"
QSFP_TYPE = "QSFP"
QSFP_DD_TYPE = "QSFP-DD"
OSFP_TYPE = "OSFP"

SFP_OPTOE     = 2
QSFP_OPTOE    = 1
QSFP_DD_OPTOE = 3

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
XCVR_VENDOR_SN_OFFSET = 68
XCVR_VENDOR_SN_WIDTH = 16
XCVR_VENDOR_DATE_OFFSET = 84
XCVR_VENDOR_DATE_WIDTH = 8
XCVR_DOM_CAPABILITY_OFFSET = 92
XCVR_DOM_CAPABILITY_WIDTH = 2
QSFP_DD_XCVR_DOM_CAPABILITY_OFFSET = (159 - 128)
QSFP_DD_XCVR_DOM_CAPABILITY_WIDTH = 2

XCVR_INTERFACE_DATA_START = 0
XCVR_INTERFACE_DATA_SIZE = 92

XCVR_TEMPE_OFFSET = 14
XCVR_TEMPE_WIDTH = 2

QSFP_DOM_BULK_DATA_START = 22
QSFP_DOM_BULK_DATA_SIZE = 36
SFP_DOM_BULK_DATA_START = 96
SFP_DOM_BULK_DATA_SIZE = 10

# definitions of the offset for values in OSFP info eeprom
OSFP_TYPE_OFFSET = 0
OSFP_VENDOR_NAME_OFFSET = 129
OSFP_VENDOR_PN_OFFSET = 148
OSFP_HW_REV_OFFSET = 164
OSFP_VENDOR_SN_OFFSET = 166

# definitions of the offset for values in QSFP DD info eeprom
QSFP_DD_TYPE_OFFSET = 0
QSFP_DD_TYPE_WIDTH = 1
QSFP_DD_CONNECTOR_TYPE_OFFSET = 203
QSFP_DD_CONNECTOR_WIDTH = 1
QSFP_DD_VENDOR_NAME_OFFSET = 129
QSFP_DD_VENDOR_NAME_WIDTH = 16
QSFP_DD_VENDOR_PN_OFFSET = 148
QSFP_DD_VENDOR_PN_WIDTH = 16
QSFP_DD_HW_REV_OFFSET = 164
QSFP_DD_HW_REV_WIDTH = 2
QSFP_DD_VENDOR_SN_OFFSET = 166
QSFP_DD_VENDOR_SN_WIDTH = 16
QSFP_DD_VENDOR_OUI_OFFSET = 145
QSFP_DD_VENDOR_OUI_WIDTH = 3
QSFP_DD_VENDOR_DATE_OFFSET = 182
QSFP_DD_VENDOR_DATE_WIDTH = 8
QSFP_DD_EXT_IDEN_OFFSET = 200
QSFP_DD_EXT_IDEN_WIDTH = 2
QSFP_DD_CABLE_LENGTH_BULK_OFFSET = 202
QSFP_DD_CABLE_LENGTH_BULK_WIDTH = 65
QSFP_DD_VOLT_OFFSET = 16
QSFP_DD_VOLT_WIDTH = 2
QSFP_DD_CHANNEL_MON_OFFSET = 17 * 128 + 154
QSFP_DD_CHANNEL_MON_WIDTH = 48
QSFP_DD_MODULE_THRESHOLD_OFFSET = 2 * 128 + 128
QSFP_DD_MODULE_THRESHOLD_WIDTH = 72
QSFP_DD_APPLICATION_ADVERTISING_OFFSET = 85
QSFP_DD_APPLICATION_ADVERTISING_WIDTH = 1
QSFP_DD_FLAT_MEMORY_OFFSET = 2
QSFP_DD_FLAT_MEMORY_WIDTH = 1

QSFP_DD_CHANNEL_RX_LOS_STATUS_OFFSET = 17 * 128 + 147
QSFP_DD_CHANNEL_RX_LOS_STATUS_WIDTH = 1
QSFP_DD_CHANNEL_TX_FAULT_STATUS_OFFSET = 17 * 128 + 135
QSFP_DD_CHANNEL_TX_FAULT_STATUS_WIDTH = 1
QSFP_DD_CHANNEL_TX_DISABLE_STATUS_OFFSET = 16 * 128 + 130
QSFP_DD_CHANNEL_TX_DISABLE_STATUS_WIDTH = 1
QSFP_DD_LPMODE_STATUS_OFFSET = 16 * 128 + 26
QSFP_DD_LPMODE_STATUS_WIDTH = 1

# Offset for values in QSFP eeprom
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
QSFP_POWERMODE_OFFSET = 93
QSFP_POWEROVERRIDE_WIDTH = 1
QSFP_POWERSET_BIT = 1
QSFP_OPTION_VALUE_OFFSET = 192
QSFP_OPTION_VALUE_WIDTH = 4
QSFP_MODULE_UPPER_PAGE3_START = 384
QSFP_MODULE_THRESHOLD_WIDTH = 24
QSFP_MODULE_THRESHOLD_OFFSET = 128
QSFP_CHANNL_THRESHOLD_OFFSET = 176
QSFP_CHANNL_THRESHOLD_WIDTH = 24

SFP_MODULE_ADDRA2_OFFSET = 256
SFP_MODULE_THRESHOLD_OFFSET = 0
SFP_MODULE_THRESHOLD_WIDTH = 56
SFP_CHANNL_THRESHOLD_OFFSET = 112
SFP_CHANNL_THRESHOLD_WIDTH = 2

SFP_TEMPE_OFFSET = 96
SFP_TEMPE_WIDTH = 2
SFP_VOLT_OFFSET = 98
SFP_VOLT_WIDTH = 2
SFP_CHANNL_MON_OFFSET = 100
SFP_CHANNL_MON_WIDTH = 6
SFP_CHANNL_STATUS_OFFSET = 110
SFP_CHANNL_STATUS_WIDTH = 1

qsfp_cable_length_tup = ('Length(km)', 'Length OM3(2m)',
                         'Length OM2(m)', 'Length OM1(m)',
                         'Length Cable Assembly(m)')

sfp_cable_length_tup = ('LengthSMFkm-UnitsOfKm', 'LengthSMF(UnitsOf100m)',
                        'Length50um(UnitsOf10m)', 'Length62.5um(UnitsOfm)',
                        'LengthCable(UnitsOfm)', 'LengthOM3(UnitsOf10m)')

cable_length_tup = ('Length Cable Assembly(m)', 'Length OM2(m)',
                         'Length OM3(2m)', 'Length OM4(2m)',
                         'Length OM5(2m)', 'Length SMF(km)')

sfp_compliance_code_tup = ('10GEthernetComplianceCode', 'InfinibandComplianceCode',
                           'ESCONComplianceCodes', 'SONETComplianceCodes',
                           'EthernetComplianceCodes', 'FibreChannelLinkLength',
                           'FibreChannelTechnology', 'SFP+CableTechnology',
                           'FibreChannelTransmissionMedia', 'FibreChannelSpeed')

qsfp_compliance_code_tup = ('10/40G Ethernet Compliance Code', 'SONET Compliance codes',
                            'SAS/SATA compliance codes', 'Gigabit Ethernet Compliant codes',
                            'Fibre Channel link length/Transmitter Technology',
                            'Fibre Channel transmission media', 'Fibre Channel Speed')

class Sfp(SfpBase):
    """
    DELLEMC Platform-specific Sfp class
    """

    SFP_DEVICE_TYPE  = "optoe2"
    QSFP_DEVICE_TYPE = "optoe1"
    QSFP_DD_DEVICE_TYPE = "optoe3"
    port_to_i2cbus_mapping = {}

    def __init__(self, index):
        # init sfp_cfg
        sfp_cfg = SfpConfig()
        self.sfplog = SfpLog()

        self.index = index
        self.port_num = self.index + PORT_START
        self.cage_type = self.get_cage_type()
        self.sfp_type = self.get_sfp_type()
        self.lane_nums = self.get_lane_nums()
        self.dom_supported = False
        for x in range(PORT_START, PORT_END + 1):
            self.port_to_i2cbus_mapping[x] = (x + EEPROM_OFFSET)

        self.info_dict_keys = ['type', 'type_abbrv_name', 'hardware_rev', 'serial', 'manufacturer', 'model', 'connector', 'encoding', 'ext_identifier',
                               'ext_rateselect_compliance', 'cable_type', 'cable_length', 'nominal_bit_rate', 'specification_compliance',
                               'vendor_date', 'vendor_oui', 'application_advertisement']

        self.dom_dict_keys = ['rx_los', 'tx_fault', 'reset_status', 'lp_mode', 'tx_disable', 'tx_disabled_channel', 'temperature', 'voltage',
                              'rx1power', 'rx2power', 'rx3power', 'rx4power','rx5power', 'rx6power', 'rx7power', 'rx8power',
                              'tx1bias', 'tx2bias', 'tx3bias', 'tx4bias', 'tx5bias', 'tx6bias', 'tx7bias', 'tx8bias',
                              'tx1power', 'tx2power', 'tx3power', 'tx4power', 'tx5power', 'tx6power', 'tx7power', 'tx8power']

        self.threshold_dict_keys = ['temphighalarm', 'temphighwarning', 'templowalarm', 'templowwarning',
                                    'vcchighalarm', 'vcchighwarning', 'vcclowalarm', 'vcclowwarning',
                                    'rxpowerhighalarm', 'rxpowerhighwarning', 'rxpowerlowalarm', 'rxpowerlowwarning',
                                    'txpowerhighalarm', 'txpowerhighwarning', 'txpowerlowalarm', 'txpowerlowwarning',
                                    'txbiashighalarm', 'txbiashighwarning', 'txbiaslowalarm', 'txbiaslowwarning']

        self.__dom_capability_detect()

    @property
    def qsfp_ports(self):
        return range(PORT_QSFP_START, PORT_QSFP_END)

    @property
    def qsfp_dd_ports(self):
        return range(PORT_QSFP_DD_START, PORT_QSFP_DD_END)

    def __dom_capability_detect(self):
        self.sfplog.log_debug("dom_capability_detect")
        if (self.check_port_validity() is False
            or self.get_presence() is False):
            self.dom_supported = False
            self.dom_temp_supported = False
            self.dom_volt_supported = False
            self.dom_rx_power_supported = False
            self.dom_tx_power_supported = False
            self.qsfp_page3_available = False
            self.calibration = 0
            return None

        if self.sfp_type == "QSFP":
            self.calibration = 1
            sfpi_obj = sff8436InterfaceId()
            if sfpi_obj is None:
                self.dom_supported = False
            offset = 128

            # QSFP capability byte parse, through this byte can know whether it support tx_power or not.
            # TODO: in the future when decided to migrate to support SFF-8636 instead of SFF-8436,
            # need to add more code for determining the capability and version compliance
            # in SFF-8636 dom capability definitions evolving with the versions.
            qsfp_dom_capability_raw = self.read_eeprom((offset + XCVR_DOM_CAPABILITY_OFFSET), XCVR_DOM_CAPABILITY_WIDTH)
            if qsfp_dom_capability_raw is not None:
                qsfp_version_compliance_raw = self.read_eeprom(QSFP_VERSION_COMPLIANCE_OFFSET, QSFP_VERSION_COMPLIANCE_WIDTH)
                qsfp_version_compliance = int(qsfp_version_compliance_raw[0], 16)
                if hasattr(sfpi_obj, 'parse_qsfp_dom_capability'):
                    self.sfplog.log_debug("use parse_qsfp_dom_capability")
                    dom_capability = sfpi_obj.parse_qsfp_dom_capability(qsfp_dom_capability_raw, 0)
                else:
                    self.sfplog.log_debug("use parse_dom_capability")
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
                qsfp_option_value_raw = self.read_eeprom(QSFP_OPTION_VALUE_OFFSET, QSFP_OPTION_VALUE_WIDTH)
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

        elif self.sfp_type == "QSFP-DD":
            self.calibration = 1
            sfpi_obj = qsfp_dd_InterfaceId()
            if sfpi_obj is None:
                self.dom_supported = False

            # Flat memory (Page00h supported only)
            qsfp_dd_flat_memory_raw = self.read_eeprom(QSFP_DD_FLAT_MEMORY_OFFSET, QSFP_DD_FLAT_MEMORY_WIDTH)
            if qsfp_dd_flat_memory_raw is not None:
                self.dom_temp_supported = True
                self.dom_volt_supported = True
                qsfp_dd_flat_memory = sfpi_obj.parse_dom_capability(qsfp_dd_flat_memory_raw, 0)
                if qsfp_dd_flat_memory['data']['Flat_MEM']['value'] == 'Off':
                    offset = 256
                    qsfp_dd_dom_capability_raw = self.read_eeprom(offset + QSFP_DD_XCVR_DOM_CAPABILITY_OFFSET,
                                                                QSFP_DD_XCVR_DOM_CAPABILITY_WIDTH)
                    if qsfp_dd_dom_capability_raw is not None:
                        self.dom_supported = True
                        self.calibration = 1

                        qsfp_dd_dom_capability_data = int(qsfp_dd_dom_capability_raw[0], 16)
                        if qsfp_dd_dom_capability_data & 0x01 != 0:
                            self.dom_temp_supported = True
                        if qsfp_dd_dom_capability_data & 0x02 != 0:
                            self.dom_volt_supported = True

                        qsfp_dd_dom_capability_data = int(qsfp_dd_dom_capability_raw[1], 16)
                        if qsfp_dd_dom_capability_data & 0x01 != 0:
                            self.dom_tx_bias_supported = True
                        if qsfp_dd_dom_capability_data & 0x02 != 0:
                            self.dom_tx_power_supported = True
                        if qsfp_dd_dom_capability_data & 0x04 != 0:
                            self.dom_rx_power_supported = True
                else:
                    self.dom_supported = False
                    self.dom_tx_bias_supported = False
                    self.dom_rx_power_supported = False
                    self.dom_tx_power_supported = False
                    self.calibration = 0
            else:
                self.dom_supported = False
                self.dom_temp_supported = False
                self.dom_volt_supported = False
                self.dom_tx_bias_supported = False
                self.dom_rx_power_supported = False
                self.dom_tx_power_supported = False
                self.calibration = 0

        elif self.sfp_type == "SFP":
            sfpi_obj = sff8472InterfaceId()
            if sfpi_obj is None:
                return None
            sfp_dom_capability_raw = self.read_eeprom(XCVR_DOM_CAPABILITY_OFFSET, XCVR_DOM_CAPABILITY_WIDTH)
            if sfp_dom_capability_raw is not None:
                sfp_dom_capability = int(sfp_dom_capability_raw[0], 16)
                self.dom_supported = (sfp_dom_capability & 0x40 != 0)
                if self.dom_supported:
                    self.dom_temp_supported = True
                    self.dom_volt_supported = True
                    self.dom_rx_power_supported = True
                    self.dom_tx_power_supported = True
                    if sfp_dom_capability & 0x20 != 0:
                        self.calibration = 1
                    elif sfp_dom_capability & 0x10 != 0:
                        self.calibration = 2
                    else:
                        self.calibration = 0
                else:
                    self.dom_temp_supported = False
                    self.dom_volt_supported = False
                    self.dom_rx_power_supported = False
                    self.dom_tx_power_supported = False
                    self.calibration = 0
                self.dom_tx_disable_supported = (
                    int(sfp_dom_capability_raw[1], 16) & 0x40 != 0)
        else:
            self.dom_supported = False
            self.dom_temp_supported = False
            self.dom_volt_supported = False
            self.dom_rx_power_supported = False
            self.dom_tx_power_supported = False

    def __add_new_sfp_device(self, sysfs_sfp_i2c_adapter_path, devaddr, devtype):
        try:
            sysfs_nd_path = "%s/new_device" % sysfs_sfp_i2c_adapter_path

            # Write device address to new_device file
            nd_file = open(sysfs_nd_path, "w")
            nd_str = "%s %s" % (devtype, hex(devaddr))
            nd_file.write(nd_str)
            nd_file.close()

        except Exception as err:
            self.sfplog.log_error("Error writing to new device file: %s" % str(err))
            return 1
        else:
            return 0

    def __get_port_eeprom_path(self, port_num, devid):
        if self.check_port_validity() is False:
            return None

        if (global_sfp_config["eeprom_path_s3ip_flag"] is True
            or global_sfp_config["eeprom_path_rg_plat_flag"] is True):
            sysfs_eeprom_path = global_sfp_config["sfp_sysfs_path"][self.port_num].get("eeprom_path", None)
            if sysfs_eeprom_path is not None:
                self.sfplog.log_debug("eeprom_path:%s" % sysfs_eeprom_path)
                return sysfs_eeprom_path

        eeprom_path = '/sys/bus/i2c/devices/i2c-{0}/{0}-0050'
        i2c_path = '/sys/bus/i2c/devices/i2c-{0}'
        sysfs_sfp_i2c_client_path = eeprom_path.format(self.port_to_i2cbus_mapping[port_num])
        sysfs_sfp_i2c_adapter_path= i2c_path.format(self.port_to_i2cbus_mapping[port_num])
        # If sfp device is not present on bus, Add it
        if not os.path.exists(sysfs_sfp_i2c_client_path):
            if port_num in self.qsfp_ports:
                ret = self.__add_new_sfp_device(
                        sysfs_sfp_i2c_adapter_path, devid, self.QSFP_DEVICE_TYPE)
            elif port_num in self.qsfp_dd_ports:
                ret = self.__add_new_sfp_device(
                        sysfs_sfp_i2c_adapter_path, devid, self.QSFP_DD_DEVICE_TYPE)
            else:
                ret = self.__add_new_sfp_device(
                        sysfs_sfp_i2c_adapter_path, devid, self.SFP_DEVICE_TYPE)
            if ret != 0:
                self.sfplog.log_error("Error adding sfp device")
                return None

        sysfs_sfp_i2c_client_eeprom_path = "%s/eeprom" % sysfs_sfp_i2c_client_path
        self.sfplog.log_debug("eeprom_path:%s" % sysfs_sfp_i2c_client_eeprom_path)
        return sysfs_sfp_i2c_client_eeprom_path

    def __convert_string_to_num(self, value_str):
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
            self.sfplog.log_debug("value_str:%s match failure" % value_str)
            return 'N/A'


    def check_port_validity(self):
        # Check for invalid self.port_num (self.port_num from 0)
        if self.port_num < PORT_START or self.port_num > PORT_END:
            self.sfplog.log_error("port_num:%d is invalid" % self.port_num)
            return False
        return True

    def get_dom_supported(self, refresh_flag=True):
        if refresh_flag:
            self.__dom_capability_detect()
        self.sfplog.log_debug("port_num:%d dom_supported:%s" % (self.port_num, self.dom_supported))
        return self.dom_supported

    def get_cage_type(self):
        if self.check_port_validity() is False:
            return None

        cage_type = global_sfp_config["cage_type"][self.port_num]
        self.sfplog.log_debug("port_num:%d cage_type:%s" % (self.port_num, cage_type))
        return cage_type

    def get_sfp_type(self):
        """
        Return sfp type
            SFP
            QSFP
            QSFP-DD
        """
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        current_sfp_type = self._sfp_type()
        cage_type = self.get_cage_type()
        if current_sfp_type == cage_type:
            self.sfp_type = cage_type
        else:
            self.check_sfp_optoe_type()

        self.sfplog.log_debug("port_num:%d get_sfp_type:%s" % (self.port_num, self.sfp_type))
        return self.sfp_type

    def _sfp_type(self, eeprom_raw=None):
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        try:
            if not eeprom_raw:
                eeprom_raw = self.read_eeprom(XCVR_TYPE_OFFSET, XCVR_TYPE_WIDTH)
            if eeprom_raw is not None:
                # A0h Byte 0 is '1e' or '18' means the transceiver is QSFP-DD
                if (eeprom_raw[0] == '1e' or eeprom_raw[0] == '18'):
                    sfp_type = QSFP_DD_TYPE
               # A0h Byte 0 is '0d' or '11' means the transceiver is QSFP
                elif (eeprom_raw[0] == '0d' or eeprom_raw[0] == '11'):
                    sfp_type = QSFP_TYPE
                # A0h Byte 0 is '03' means the transceiver is SFP
                elif (eeprom_raw[0] == '03'):
                    sfp_type = SFP_TYPE
            else:
                self.sfplog.log_debug("port_num:%d unknown sfp type" % self.port_num)
                return None
        except Exception as e:
            print(traceback.format_exc())

        self.sfplog.log_debug("port_num:%d sfp_type:%s" % (self.port_num, sfp_type))
        return sfp_type

    def check_optoe_type(self, optoe_type):
        if self.check_port_validity() is False:
            return True

        try:
            port_id = self.get_sfp_port_id()
            ret, output = platform_get_optoe_type(port_id)
            if ret is False:
                self.sfplog.log_error("port %s get optoe type fail, output:%s" % (port_id, output))
            if int(output) != optoe_type:
                ret, output = platform_set_optoe_type(port_id, optoe_type)
                if ret is False:
                    self.sfplog.log_error("port %s set optoe type fail, output:%s" % (port_id, output))
                self.sfplog.log_debug("port_num:%d optoe_type:%s set success" % (port_id, optoe_type))

        except Exception as e:
            print(traceback.format_exc())

    def check_sfp_optoe_type(self):
        self.sfp_type = self._sfp_type()

        try:
            if self.sfp_type == "QSFP-DD":
                self.check_optoe_type(QSFP_DD_OPTOE)
            elif self.sfp_type == "QSFP":
                self.check_optoe_type(QSFP_OPTOE)
            elif self.sfp_type == "SFP":
                self.check_optoe_type(SFP_OPTOE)
            else:
                self.sfplog.log_error("port_num:%d check optoe_type fail" % self.port_num)
        except Exception as e:
            print(traceback.format_exc())

        self.sfplog.log_debug("port_num:%d check optoe type success" % self.port_num)

    def get_lane_nums(self):
        if self.check_port_validity() is False:
            return 0

        lane_nums = 0
        try:
            if self.sfp_type == QSFP_TYPE:
                lane_nums = 4
            elif self.sfp_type == QSFP_DD_TYPE:
                lane_nums = 8
            elif self.sfp_type == SFP_TYPE:
                lane_nums = 1
        except Exception as e:
            print(traceback.format_exc())

        self.sfplog.log_debug("port_num:%d sfp_type:%s lane_nums:%d" % (self.port_num, self.sfp_type, lane_nums))
        return lane_nums

    def get_flip_flag(self, info_flag):
        '''flip is Fasle  | 0: True, 1: Flase'''
        '''flip is True   | 1: True, 0: Flase'''
        if self.check_port_validity() is False:
            return False

        cpld_key = info_flag + "_cpld"
        flip_flag = global_sfp_config["sfp_cpld_info"][self.port_num][cpld_key].get("flip_flag", False)
        self.sfplog.log_debug("port_num:%d %s flip_flag:%s" % (self.port_num, info_flag, flip_flag))
        return flip_flag

    def get_libplatform_flag(self):
        libplatform_flag = global_sfp_config.get("libplatform_flag", False)
        return libplatform_flag

    def get_sfp_cpld_info(self, info_flag):
        if self.check_port_validity() is False:
            return False, None, None, None

        cpld_key = info_flag + "_cpld"
        if global_sfp_config["sfp_cpld_info"][self.port_num].get(cpld_key, None) is None:
            self.sfplog.log_error("port_num:%d cpld info is None" % (self.port_num))
            return False, None, None, None

        dev_id = global_sfp_config["sfp_cpld_info"][self.port_num][cpld_key].get("dev_id", None)
        offset = global_sfp_config["sfp_cpld_info"][self.port_num][cpld_key].get("offset", None)
        offset_bit = global_sfp_config["sfp_cpld_info"][self.port_num][cpld_key].get("offset_bit", None)
        if (dev_id is None
            or offset is None
            or offset_bit is None):
            self.sfplog.log_error("port_num:%d %s cpld info is None , dev_id:%d offset:0x%x offset_bit:%d " % (
                self.port_num, info_flag, dev_id, offset, offset_bit))
            return False, None, None, None

        self.sfplog.log_debug("port_num:%d %s dev_id:%d offset:0x%x offset_bit:%d" % (
            self.port_num, info_flag, dev_id, offset, offset_bit))
        return True, dev_id, offset, offset_bit

    def get_sfp_port_id(self):
        port_id = 0
        if global_sfp_config["port_index_start"] == 0:
            port_id = self.port_num + 1
        else:
            port_id = self.port_num

        return port_id

    """Sfp Util"""
    def read_eeprom_one_time_by_platform(self, offset, num_bytes):
        port_id = self.get_sfp_port_id()
        ret, info = platform_sfp_read(port_id, offset, num_bytes)
        if (ret is False
            or info is None):
            self.sfplog.log_error("port_num:%d port_id:%d offset:%d num_bytes:%d platform_sfp_read fail, \
                info:%s" % (self.port_num, port_id, offset, num_bytes, info))
            return None

        try:
            eeprom_raw = []
            for i in range(0, num_bytes):
                eeprom_raw.append("0x00")
            if len(info) == 0:
                return None
            for n in range(0, len(info)):
                eeprom_raw[n] = hex(info[n])[2:].zfill(2)
        except Exception as err:
            self.sfplog.log_error("port_num:%d port_id:%d offset:%d num_bytes:%d platform_sfp_read fail, \
                info:%s" % (self.port_num, port_id, offset, num_bytes, info))
            self.sfplog.log_error(traceback.format_exc())
            return None

        self.sfplog.log_debug("port_num:%d port_id:%d offset:%d num_bytes:%d platform_sfp_read success, \
            eeprom_raw:%s" % (self.port_num, port_id, offset, num_bytes, eeprom_raw))
        return eeprom_raw

    def write_eeprom_one_time_by_platform(self, offset, write_buffer):
        val_list = []
        if isinstance(write_buffer, list):
            val_list = write_buffer
        else:
            val_list.append(write_buffer)

        port_id = self.get_sfp_port_id()
        ret, info = platform_sfp_write(port_id, offset, val_list)
        if ret is False:
            self.sfplog.log_error("port_num:%d offset:%d write_buffer:%s val_list:%s platform_sfp_write fail, \
                info:%s" % ( self.port_num, offset, write_buffer, val_list, info))
            return False

        self.sfplog.log_debug("port_num:%d offset:%d write_buffer:%s val_list:%s platform_sfp_write success" % (
            self.port_num, offset, val_list, write_buffer))
        return True

    def read_eeprom_one_time_by_sysfs(self, offset, num_bytes):
        eeprom_path = self.__get_port_eeprom_path(self.port_num, IDENTITY_EEPROM_ADDR)
        if eeprom_path is None:
            self.sfplog.log_error("eeprom_path is None")
            return None
        try:
            with open(eeprom_path, mode="rb", buffering=0) as eeprom:
                eeprom.seek(offset)
                raw = eeprom.read(num_bytes)
        except Exception as err:
            self.sfplog.log_error(traceback.format_exc())
            return None

        try:
            eeprom_raw = []
            for i in range(0, num_bytes):
                eeprom_raw.append("0x00")
            if len(raw) == 0:
                return None
            for n in range(0, len(raw)):
                eeprom_raw[n] = hex(raw[n])[2:].zfill(2)
        except Exception as err:
            self.sfplog.log_error("port_num:%d offset:%d num_bytes:%d eeprom_path:%s read_eeprom by sysfs fail" % (
                self.port_num, offset, num_bytes, eeprom_path))
            self.sfplog.log_error(traceback.format_exc())
            return None

        self.sfplog.log_debug("port_num:%d offset:%d num_bytes:%d eeprom_path:%s read_eeprom by sysfs success, \
            eeprom_raw:%s" % (self.port_num, offset, num_bytes, eeprom_path, eeprom_raw))
        return eeprom_raw

    def write_eeprom_one_time_by_sysfs(self, offset, write_buffer):
        eeprom_path = self.__get_port_eeprom_path(self.port_num, IDENTITY_EEPROM_ADDR)
        if eeprom_path is None:
            self.sfplog.log_error("eeprom_path is None")
            return False

        buffer = None
        try:
            if isinstance(write_buffer, list):
                buffer = create_string_buffer(len(write_buffer))
                for i in range(len(write_buffer)):
                    buffer[i] = bytes([write_buffer[i],])
            else:
                buffer = create_string_buffer(1)
                buffer[0] = bytes([write_buffer,])
        except Exception as e:
            self.sfplog.log_error(traceback.format_exc(e))

        try:
            with open(eeprom_path, "wb+") as eeprom:
                eeprom.seek(offset)
                eeprom.write(buffer)
            time.sleep(0.01)
        except Exception as e:
            self.sfplog.log_error(traceback.format_exc(e))
            return False

        self.sfplog.log_debug("port_num:%d offset:%d write_buffer:%s eeprom_path:%s write_eeprom by sysfs success" % (
            self.port_num, offset, eeprom_path, write_buffer))
        return True

    def read_eeprom_one_time(self, offset, num_bytes):
        if self.get_libplatform_flag():
            return self.read_eeprom_one_time_by_platform(offset, num_bytes)
        else:
            return self.read_eeprom_one_time_by_sysfs(offset, num_bytes)

    def write_eeprom_one_time(self, offset, write_buffer):
        if self.get_libplatform_flag():
            return self.write_eeprom_one_time_by_platform(offset, write_buffer)
        else:
            return self.write_eeprom_one_time_by_sysfs(offset, write_buffer)

    def read_eeprom(self, offset, num_bytes):
        if self.check_port_validity() is False:
            return None

        eeprom_raw = None
        # add retry time, interval 200ms, up to 2000ms
        try:
            for i in range(10):
                eeprom_raw = self.read_eeprom_one_time(offset, num_bytes)
                if eeprom_raw is None:
                    time.sleep(0.2)
                    continue
                break
        except Exception as e:
            self.sfplog.log_error(traceback.format_exc(e))

        return eeprom_raw

    def write_eeprom(self, offset, write_buffer):
        if self.check_port_validity() is False:
            return False

        # add retry time, interval 200ms, up to 2000ms
        try:
            for i in range(10):
                ret = self.write_eeprom_one_time(offset, write_buffer)
                if ret is False:
                    time.sleep(0.2)
                    continue
                break
        except Exception as e:
            self.sfplog.log_error(traceback.format_exc(e))

        return ret

    def read_cpld_by_libplatform(self, info_flag):
        if self.check_port_validity() is False:
            return False

        ret, dev_id, offset, _ = self.get_sfp_cpld_info(info_flag)
        if ret is False:
            return False, []

        ret, info = platform_reg_read(0, dev_id, offset, 1)
        if (ret is False
            or info is None
            or len(info) == 0):
            self.sfplog.log_debug("dev_id:%d offset:0x%x, %s platform_reg_read by libplatform fail, \
                info:%s" % (dev_id, offset, info_flag, info))
            return False, []

        self.sfplog.log_debug("dev_id:%d offset:0x%x, %s platform_reg_read by libplatform success, \
            info:%s" % (dev_id, offset, info_flag, info))

        return True, info

    def write_cpld_by_libplatform(self, info_flag, val):
        if self.check_port_validity() is False:
            return False

        ret, dev_id, offset, _ = self.get_sfp_cpld_info(info_flag)
        if ret is False:
            return False

        val_list = []
        if isinstance(val, list):
            val_list = val
        else:
            val_list.append(val)

        ret, info = platform_reg_write(0, dev_id, offset, val_list)
        if ret is False:
            self.sfplog.log_error("dev_id:%d offset:0x%x, %s val_list:%s platform_reg_write by libplatform fail, \
                info:%s" % (dev_id, offset, info_flag, val_list, info))
            return False

        self.sfplog.log_debug("dev_id:%d offset:0x%x, %s val_list:%s platform_reg_write by libplatform success" % (
                dev_id, offset, info_flag, val_list))
        return True

    def read_cpld_by_sysfs(self, info_flag):
        val = 0
        sysfs_key = info_flag + "_path"
        sysfs_path = global_sfp_config["sfp_sysfs_path"][self.port_num].get(sysfs_key, None)
        if sysfs_path is None:
            self.sfplog.log_error("sysfs_path is None")
            return False, 0

        try:
            with open(sysfs_path, "rb") as data:
                sysfs_data = data.read(2)
                if sysfs_data != "":
                    val = int(sysfs_data, 16)
        except Exception as err:
            self.sfplog.log_error(traceback.format_exc())
            return False, 0

        self.sfplog.log_debug("sysfs_path:%s read_cpld success, val:%d" % (sysfs_path, val))
        return True, val

    def write_cpld_by_sysfs(self, info_flag, val):
        sysfs_key = info_flag + "_path"
        sysfs_path = global_sfp_config["sfp_sysfs_path"][self.port_num].get(sysfs_key, None)
        if sysfs_path is None:
            self.sfplog.log_error("sysfs_path is None")
            return False

        try:
            with open(sysfs_path, "r+") as data:
                data.seek(0)
                sres = hex(val)[2:]
                data.write(sres)
        except Exception as err:
            self.sfplog.log_error(traceback.format_exc())
            return False

        self.sfplog.log_debug("write sysfs_path:%s success, val:%d" % (sysfs_path, val))
        return True


    """Sfp transceiver"""
    def get_transceiver_info_sfp_dict(self):
        compliance_code_dict = {}
        transceiver_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')

        offset = 0
        vendor_rev_width = XCVR_HW_REV_WIDTH_SFP
        interface_info_bulk_width = XCVR_INTFACE_BULK_WIDTH_SFP

        sfpi_obj = sff8472InterfaceId()
        if sfpi_obj is None:
            self.sfplog.log_error("sfpi_obj sff8472 is None")
            return None

        sfp_interface_bulk_raw = self.read_eeprom(offset + XCVR_INTERFACE_DATA_START, XCVR_INTERFACE_DATA_SIZE)
        if sfp_interface_bulk_raw is None:
            self.sfplog.log_debug("SFP sfp_interface_bulk_raw is None")
            return None

        start = XCVR_INTFACE_BULK_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + interface_info_bulk_width
        sfp_interface_bulk_data = sfpi_obj.parse_sfp_info_bulk(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_NAME_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_NAME_WIDTH
        sfp_vendor_name_data = sfpi_obj.parse_vendor_name(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_PN_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_PN_WIDTH
        sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_HW_REV_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + vendor_rev_width
        sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_SN_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_SN_WIDTH
        sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_OUI_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_OUI_WIDTH
        sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_DATE_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_DATE_WIDTH
        sfp_vendor_date_data = sfpi_obj.parse_vendor_date(sfp_interface_bulk_raw[start: end], 0)
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

        for key in sfp_cable_length_tup:
            if key in sfp_interface_bulk_data['data']:
                transceiver_info_dict['cable_type'] = key
                transceiver_info_dict['cable_length'] = str(sfp_interface_bulk_data['data'][key]['value'])

        for key in sfp_compliance_code_tup:
            if key in sfp_interface_bulk_data['data']['Specification compliance']['value']:
                compliance_code_dict[key] = sfp_interface_bulk_data['data']['Specification compliance']['value'][key]['value']
        transceiver_info_dict['specification_compliance'] = str(compliance_code_dict)
        transceiver_info_dict['nominal_bit_rate'] = str(sfp_interface_bulk_data['data']['NominalSignallingRate(UnitsOf100Mbd)']['value'])

        self.sfplog.log_debug("port_num:%d transceiver_info_dict:%s" % (self.port_num, transceiver_info_dict))
        return transceiver_info_dict

    def get_transceiver_bulk_status_sfp_dict(self):
        if self.get_dom_supported() is False:
            return None

        transceiver_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')

        offset = 256
        sfpd_obj = sff8472Dom()
        if sfpd_obj is None:
            self.sfplog.log_error("sfpd_obj sff8472Dom is None")
            return None

        sfpd_obj._calibration_type = self.calibration
        if sfpd_obj._calibration_type == 1:
            dom_data_raw = self.read_eeprom((offset + SFP_DOM_BULK_DATA_START), SFP_DOM_BULK_DATA_SIZE)
            start = SFP_TEMPE_OFFSET - SFP_DOM_BULK_DATA_START
            end = start + SFP_TEMPE_WIDTH
            dom_temperature_data = sfpd_obj.parse_temperature(dom_data_raw[start: end], 0)

            start = SFP_VOLT_OFFSET - SFP_DOM_BULK_DATA_START
            end = start + SFP_VOLT_WIDTH
            dom_voltage_data = sfpd_obj.parse_voltage(dom_data_raw[start: end], 0)

            start = SFP_CHANNL_MON_OFFSET - SFP_DOM_BULK_DATA_START
            end = start + SFP_CHANNL_MON_WIDTH
            dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params(dom_data_raw[start: end], 0)
        else:
            dom_data_raw = self.read_eeprom((offset), offset + 256)
            dom_temperature_data = sfpd_obj.parse_temperature(dom_data_raw, 0)
            dom_voltage_data = sfpd_obj.parse_voltage(dom_data_raw, 0)
            dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params(dom_data_raw, 0)

        transceiver_dom_info_dict['temperature'] = self.__convert_string_to_num(dom_temperature_data['data']['Temperature']['value'])
        transceiver_dom_info_dict['voltage'] = self.__convert_string_to_num(dom_voltage_data['data']['Vcc']['value'])
        transceiver_dom_info_dict['rx1power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['RXPower']['value'])
        transceiver_dom_info_dict['tx1bias'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['TXBias']['value'])
        transceiver_dom_info_dict['tx1power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['TXPower']['value'])

        transceiver_dom_info_dict['rx_los'] = self.get_rx_los()
        transceiver_dom_info_dict['tx_fault'] = self.get_tx_fault()
        transceiver_dom_info_dict['reset_status'] = self.get_reset_status()
        transceiver_dom_info_dict['tx_disable'] = self.get_tx_disable()
        transceiver_dom_info_dict['tx_disabled_channel'] = self.get_tx_disable_channel()
        transceiver_dom_info_dict['lp_mode'] = self.get_lpmode()

        self.sfplog.log_debug("port_num:%d transceiver_dom_info_dict:%s" % (self.port_num, transceiver_dom_info_dict))
        return transceiver_dom_info_dict

    def get_transceiver_threshold_info_sfp_dict(self):
        transceiver_dom_threshold_info_dict = dict.fromkeys(self.threshold_dict_keys, 'N/A')

        sfpd_obj = sff8472Dom(None, self.calibration)
        if sfpd_obj is None:
            self.sfplog.log_error("sfpd_obj sff8472Dom is None")
            return None

        offset = SFP_MODULE_ADDRA2_OFFSET
        sfpd_obj._calibration_type = self.calibration
        if sfpd_obj._calibration_type == 1:
            dom_module_threshold_raw = self.read_eeprom((offset + SFP_MODULE_THRESHOLD_OFFSET), SFP_MODULE_THRESHOLD_WIDTH)
        else:
            dom_module_threshold_raw = self.read_eeprom((offset), offset + 256)
        if dom_module_threshold_raw is None:
            self.sfplog.log_debug("dom_module_threshold_raw is None")
            return None
        dom_module_threshold_data = sfpd_obj.parse_alarm_warning_threshold(dom_module_threshold_raw, 0)

        # Threshold Data
        transceiver_dom_threshold_info_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
        transceiver_dom_threshold_info_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
        transceiver_dom_threshold_info_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
        transceiver_dom_threshold_info_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
        transceiver_dom_threshold_info_dict['vcchighalarm'] = dom_module_threshold_data['data']['VoltageHighAlarm']['value']
        transceiver_dom_threshold_info_dict['vcclowalarm'] = dom_module_threshold_data['data']['VoltageLowAlarm']['value']
        transceiver_dom_threshold_info_dict['vcchighwarning'] = dom_module_threshold_data['data']['VoltageHighWarning']['value']
        transceiver_dom_threshold_info_dict['vcclowwarning'] = dom_module_threshold_data['data']['VoltageLowWarning']['value']
        transceiver_dom_threshold_info_dict['txbiashighalarm'] = dom_module_threshold_data['data']['BiasHighAlarm']['value']
        transceiver_dom_threshold_info_dict['txbiaslowalarm'] = dom_module_threshold_data['data']['BiasLowAlarm']['value']
        transceiver_dom_threshold_info_dict['txbiashighwarning'] = dom_module_threshold_data['data']['BiasHighWarning']['value']
        transceiver_dom_threshold_info_dict['txbiaslowwarning'] = dom_module_threshold_data['data']['BiasLowWarning']['value']
        transceiver_dom_threshold_info_dict['txpowerhighalarm'] = dom_module_threshold_data['data']['TXPowerHighAlarm']['value']
        transceiver_dom_threshold_info_dict['txpowerlowalarm'] = dom_module_threshold_data['data']['TXPowerLowAlarm']['value']
        transceiver_dom_threshold_info_dict['txpowerhighwarning'] = dom_module_threshold_data['data']['TXPowerHighWarning']['value']
        transceiver_dom_threshold_info_dict['txpowerlowwarning'] = dom_module_threshold_data['data']['TXPowerLowWarning']['value']
        transceiver_dom_threshold_info_dict['rxpowerhighalarm'] = dom_module_threshold_data['data']['RXPowerHighAlarm']['value']
        transceiver_dom_threshold_info_dict['rxpowerlowalarm'] = dom_module_threshold_data['data']['RXPowerLowAlarm']['value']
        transceiver_dom_threshold_info_dict['rxpowerhighwarning'] = dom_module_threshold_data['data']['RXPowerHighWarning']['value']
        transceiver_dom_threshold_info_dict['rxpowerlowwarning'] = dom_module_threshold_data['data']['RXPowerLowWarning']['value']

        self.sfplog.log_debug("port_num:%d transceiver_dom_threshold_info_dict:%s" % (self.port_num, transceiver_dom_threshold_info_dict))
        return transceiver_dom_threshold_info_dict

    def get_transceiver_info_qsfp_dict(self):
        compliance_code_dict = {}
        transceiver_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')

        offset = 128
        vendor_rev_width = XCVR_HW_REV_WIDTH_QSFP
        interface_info_bulk_width = XCVR_INTFACE_BULK_WIDTH_QSFP

        sfpi_obj = sff8436InterfaceId()
        if sfpi_obj is None:
            self.sfplog.log_error("sfpi_obj sff8436 is None")
            return None

        sfp_interface_bulk_raw = self.read_eeprom(offset + XCVR_INTERFACE_DATA_START, XCVR_INTERFACE_DATA_SIZE)
        if sfp_interface_bulk_raw is None:
            self.sfplog.log_debug("SFP sfp_interface_bulk_raw is None")
            return None

        start = XCVR_INTFACE_BULK_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + interface_info_bulk_width
        sfp_interface_bulk_data = sfpi_obj.parse_sfp_info_bulk(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_NAME_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_NAME_WIDTH
        sfp_vendor_name_data = sfpi_obj.parse_vendor_name(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_PN_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_PN_WIDTH
        sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_HW_REV_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + vendor_rev_width
        sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_SN_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_SN_WIDTH
        sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_OUI_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_OUI_WIDTH
        sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(sfp_interface_bulk_raw[start: end], 0)

        start = XCVR_VENDOR_DATE_OFFSET - XCVR_INTERFACE_DATA_START
        end = start + XCVR_VENDOR_DATE_WIDTH
        sfp_vendor_date_data = sfpi_obj.parse_vendor_date(sfp_interface_bulk_raw[start: end], 0)
        transceiver_info_dict['type'] = sfp_interface_bulk_data['data']['type']['value']
        transceiver_info_dict['type_abbrv_name'] = sfp_interface_bulk_data['data']['type_abbrv_name']['value']
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
        for key in qsfp_cable_length_tup:
            if key in sfp_interface_bulk_data['data']:
                transceiver_info_dict['cable_type'] = key
                transceiver_info_dict['cable_length'] = str(sfp_interface_bulk_data['data'][key]['value'])

        for key in qsfp_compliance_code_tup:
            if key in sfp_interface_bulk_data['data']['Specification compliance']['value']:
                compliance_code_dict[key] = sfp_interface_bulk_data['data']['Specification compliance']['value'][key]['value']
        transceiver_info_dict['specification_compliance'] = str(compliance_code_dict)
        transceiver_info_dict['nominal_bit_rate'] = str(sfp_interface_bulk_data['data']['Nominal Bit Rate(100Mbs)']['value'])

        self.sfplog.log_debug("port_num:%d transceiver_info_dict:%s" % (self.port_num, transceiver_info_dict))
        return transceiver_info_dict

    def get_transceiver_bulk_status_qsfp_dict(self):
        transceiver_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')
        offset = 128
        self.__dom_capability_detect()
        qsfp_dom_capability_raw = self.read_eeprom((offset + XCVR_DOM_CAPABILITY_OFFSET), XCVR_DOM_CAPABILITY_WIDTH)
        if qsfp_dom_capability_raw is not None:
            self.dom_supported = True
        if self.get_dom_supported(False) is False:
            return None

        offset = 0
        sfpd_obj = sff8436Dom()
        if sfpd_obj is None:
            self.sfplog.log_error("sfpd_obj sff8436Dom is None")
            return None

        dom_data_raw = self.read_eeprom((offset + QSFP_DOM_BULK_DATA_START), QSFP_DOM_BULK_DATA_SIZE)
        if dom_data_raw is None:
            self.sfplog.log_debug("QSFP dom_data_raw is None")
            return None

        if self.dom_temp_supported:
            start = QSFP_TEMPE_OFFSET - QSFP_DOM_BULK_DATA_START
            end = start + QSFP_TEMPE_WIDTH
            dom_temperature_data = sfpd_obj.parse_temperature(dom_data_raw[start: end], 0)
            temp = self.__convert_string_to_num(dom_temperature_data['data']['Temperature']['value'])
            if temp is not None:
                transceiver_dom_info_dict['temperature'] = temp

        if self.dom_volt_supported:
            start = QSFP_VOLT_OFFSET - QSFP_DOM_BULK_DATA_START
            end = start + QSFP_VOLT_WIDTH
            dom_voltage_data = sfpd_obj.parse_voltage(dom_data_raw[start: end], 0)
            volt = self.__convert_string_to_num(dom_voltage_data['data']['Vcc']['value'])
            if volt is not None:
                transceiver_dom_info_dict['voltage'] = volt

        start = QSFP_CHANNL_MON_OFFSET - QSFP_DOM_BULK_DATA_START
        end = start + QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH
        dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params_with_tx_power(dom_data_raw[start: end], 0)

        if self.dom_tx_power_supported:
            transceiver_dom_info_dict['tx1power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['TX1Power']['value'])
            transceiver_dom_info_dict['tx2power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['TX2Power']['value'])
            transceiver_dom_info_dict['tx3power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['TX3Power']['value'])
            transceiver_dom_info_dict['tx4power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['TX4Power']['value'])

        if self.dom_rx_power_supported:
            transceiver_dom_info_dict['rx1power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['RX1Power']['value'])
            transceiver_dom_info_dict['rx2power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['RX2Power']['value'])
            transceiver_dom_info_dict['rx3power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['RX3Power']['value'])
            transceiver_dom_info_dict['rx4power'] = self.__convert_string_to_num(dom_channel_monitor_data['data']['RX4Power']['value'])

        transceiver_dom_info_dict['tx1bias'] = dom_channel_monitor_data['data']['TX1Bias']['value']
        transceiver_dom_info_dict['tx2bias'] = dom_channel_monitor_data['data']['TX2Bias']['value']
        transceiver_dom_info_dict['tx3bias'] = dom_channel_monitor_data['data']['TX3Bias']['value']
        transceiver_dom_info_dict['tx4bias'] = dom_channel_monitor_data['data']['TX4Bias']['value']

        transceiver_dom_info_dict['rx_los'] = self.get_rx_los()
        transceiver_dom_info_dict['tx_fault'] = self.get_tx_fault()
        transceiver_dom_info_dict['reset_status'] = self.get_reset_status()
        transceiver_dom_info_dict['tx_disable'] = self.get_tx_disable()
        transceiver_dom_info_dict['tx_disabled_channel'] = self.get_tx_disable_channel()
        transceiver_dom_info_dict['lp_mode'] = self.get_lpmode()

        self.sfplog.log_debug("port_num:%d transceiver_dom_info_dict:%s" % (self.port_num, transceiver_dom_info_dict))
        return transceiver_dom_info_dict

    def get_transceiver_threshold_info_qsfp_dict(self):
        if self.qsfp_page3_available is False:
            self.sfplog.log_debug("self.qsfp_page3_available is False")
            return None

        transceiver_dom_threshold_info_dict = dict.fromkeys(self.threshold_dict_keys, 'N/A')

        # Dom Threshold data starts from offset 384
        # Revert offset back to 0 once data is retrieved
        offset = QSFP_MODULE_UPPER_PAGE3_START
        sfpd_obj = sff8436Dom()
        if sfpd_obj is None:
            self.sfplog.log_error("sfpd_obj sff8436Dom is None")
            return None

        dom_module_threshold_raw = self.read_eeprom((offset + QSFP_MODULE_THRESHOLD_OFFSET), QSFP_MODULE_THRESHOLD_WIDTH)
        if dom_module_threshold_raw is None:
            self.sfplog.log_debug("QSFP dom_module_threshold_raw is None")
            return None

        dom_channel_threshold_raw = self.read_eeprom((offset + QSFP_CHANNL_THRESHOLD_OFFSET), QSFP_CHANNL_THRESHOLD_WIDTH)
        if dom_channel_threshold_raw is None:
            self.sfplog.log_debug("QSFP dom_channel_threshold_raw is None")
            return None

        dom_module_threshold_data = sfpd_obj.parse_module_threshold_values(dom_module_threshold_raw, 0)
        dom_channel_threshold_data = sfpd_obj.parse_channel_threshold_values(dom_channel_threshold_raw, 0)

        transceiver_dom_threshold_info_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
        transceiver_dom_threshold_info_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
        transceiver_dom_threshold_info_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
        transceiver_dom_threshold_info_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
        transceiver_dom_threshold_info_dict['vcchighalarm'] = dom_module_threshold_data['data']['VccHighAlarm']['value']
        transceiver_dom_threshold_info_dict['vcchighwarning'] = dom_module_threshold_data['data']['VccHighWarning']['value']
        transceiver_dom_threshold_info_dict['vcclowalarm'] = dom_module_threshold_data['data']['VccLowAlarm']['value']
        transceiver_dom_threshold_info_dict['vcclowwarning'] = dom_module_threshold_data['data']['VccLowWarning']['value']
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

        self.sfplog.log_debug("port_num:%d transceiver_dom_threshold_info_dict:%s" % (self.port_num, transceiver_dom_threshold_info_dict))
        return transceiver_dom_threshold_info_dict

    def get_transceiver_info_qsfp_dd_dict(self):
        transceiver_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')

        sfpi_obj = qsfp_dd_InterfaceId()
        if sfpi_obj is None:
            self.sfplog.log_error("sfpi_obj qsfp_dd is None")
            return None

        offset = 0
        sfp_type_data_raw = self.read_eeprom(offset + XCVR_TYPE_OFFSET, XCVR_TYPE_WIDTH)
        if not sfp_type_data_raw:
            return None
        sfp_type_data = sfpi_obj.parse_sfp_type(sfp_type_data_raw, 0)
        transceiver_info_dict['type'] = sfp_type_data['data']['type']['value']
        sfp_connector_type_raw = self.read_eeprom((offset + QSFP_DD_CONNECTOR_TYPE_OFFSET), QSFP_DD_CONNECTOR_WIDTH)
        if sfp_connector_type_raw is not None:
            sfp_connector_type_data = sfpi_obj.parse_connector(sfp_connector_type_raw, 0)
            transceiver_info_dict['connector'] = sfp_connector_type_data['data']['Connector']['value']
        else:
            return None

        sfp_type_abbrv_name_raw = self.read_eeprom((offset + QSFP_DD_TYPE_OFFSET), QSFP_DD_TYPE_WIDTH)
        if sfp_type_abbrv_name_raw is not None:
            sfp_type_abbrv_name = sfpi_obj.parse_sfp_type_abbrv_name(sfp_type_abbrv_name_raw, 0)
            transceiver_info_dict['type_abbrv_name'] = sfp_type_abbrv_name['data']['type_abbrv_name']['value']
        else:
            return None

        sfp_vendor_name_raw = self.read_eeprom((offset + QSFP_DD_VENDOR_NAME_OFFSET), QSFP_DD_VENDOR_NAME_WIDTH)
        if sfp_vendor_name_raw is not None:
            sfp_vendor_name_data = sfpi_obj.parse_vendor_name(sfp_vendor_name_raw, 0)
            transceiver_info_dict['manufacturer'] = sfp_vendor_name_data['data']['Vendor Name']['value']
        else:
            return None

        sfp_vendor_pn_raw = self.read_eeprom((offset + QSFP_DD_VENDOR_PN_OFFSET), QSFP_DD_VENDOR_PN_WIDTH)
        if sfp_vendor_pn_raw is not None:
            sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(sfp_vendor_pn_raw, 0)
            transceiver_info_dict['model'] = sfp_vendor_pn_data['data']['Vendor PN']['value']
        else:
            return None

        sfp_vendor_rev_raw = self.read_eeprom((offset + QSFP_DD_HW_REV_OFFSET), QSFP_DD_HW_REV_WIDTH)
        if sfp_vendor_rev_raw is not None:
            sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(sfp_vendor_rev_raw, 0)
            transceiver_info_dict['hardware_rev'] = sfp_vendor_rev_data['data']['Vendor Rev']['value']
        else:
            return None

        sfp_vendor_sn_raw = self.read_eeprom((offset + QSFP_DD_VENDOR_SN_OFFSET), QSFP_DD_VENDOR_SN_WIDTH)
        if sfp_vendor_sn_raw is not None:
            sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(sfp_vendor_sn_raw, 0)
            transceiver_info_dict['serial'] = sfp_vendor_sn_data['data']['Vendor SN']['value']
        else:
            return None

        sfp_vendor_oui_raw = self.read_eeprom((offset + QSFP_DD_VENDOR_OUI_OFFSET), QSFP_DD_VENDOR_OUI_WIDTH)
        if sfp_vendor_oui_raw is not None:
            sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(sfp_vendor_oui_raw, 0)
            transceiver_info_dict['vendor_oui'] = sfp_vendor_oui_data['data']['Vendor OUI']['value']
        else:
            return None

        sfp_vendor_date_raw = self.read_eeprom((offset + QSFP_DD_VENDOR_DATE_OFFSET), QSFP_DD_VENDOR_DATE_WIDTH)
        if sfp_vendor_date_raw is not None:
            sfp_vendor_date_data = sfpi_obj.parse_vendor_date(sfp_vendor_date_raw, 0)
            transceiver_info_dict['vendor_date'] = sfp_vendor_date_data['data']['VendorDataCode(YYYY-MM-DD Lot)']['value']
        else:
            return None

        sfp_ext_identifier_raw = self.read_eeprom((offset + QSFP_DD_EXT_IDEN_OFFSET), QSFP_DD_EXT_IDEN_WIDTH)
        if sfp_ext_identifier_raw is not None:
            sfp_ext_identifier_data = sfpi_obj.parse_ext_iden(sfp_ext_identifier_raw, 0)
            transceiver_info_dict['ext_identifier'] = sfp_ext_identifier_data['data']['Extended Identifier']['value']
        else:
            return None

        sfp_cable_length_raw = self.read_eeprom((offset + QSFP_DD_CABLE_LENGTH_BULK_OFFSET), QSFP_DD_CABLE_LENGTH_BULK_WIDTH)
        if sfp_cable_length_raw is not None:
            sfp_cable_length_data = sfpi_obj.parse_cable_len(sfp_cable_length_raw, 0)
            for key in cable_length_tup:
                if key in sfp_cable_length_data['data']:
                    transceiver_info_dict['cable_type'] = key
                    transceiver_info_dict['cable_length'] = str(sfp_cable_length_data['data'][key]['value'])
        else:
            return None

        interface_bulk_raw = self.read_eeprom((offset + XCVR_INTERFACE_DATA_START), XCVR_INTERFACE_DATA_SIZE)
        if not interface_bulk_raw:
            return None

        self.sfplog.log_debug("port_num:%d transceiver_info_dict:%s" % (self.port_num, transceiver_info_dict))
        return transceiver_info_dict

    def get_transceiver_bulk_status_qsfp_dd_dict(self):
        sfpd_obj = qsfp_dd_Dom()
        if not sfpd_obj:
            self.sfplog.log_error("sfpd_obj qsfp_dd_Dom is None")
            return None

        transceiver_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')

        offset = 0

        self.__dom_capability_detect()
        if self.dom_temp_supported:
            dom_temperature_raw = self.read_eeprom((offset + XCVR_TEMPE_OFFSET), XCVR_TEMPE_WIDTH)
            if dom_temperature_raw is not None:
                dom_temperature_data = sfpd_obj.parse_temperature(dom_temperature_raw, 0)
                transceiver_dom_info_dict['temperature'] = dom_temperature_data['data']['Temperature']['value']
            else:
                return None

        if self.dom_volt_supported:
            dom_voltage_raw = self.read_eeprom((offset + QSFP_DD_VOLT_OFFSET), QSFP_DD_VOLT_WIDTH)
            if dom_voltage_raw is not None:
                dom_voltage_data = sfpd_obj.parse_voltage(dom_voltage_raw, 0)
                transceiver_dom_info_dict['voltage'] = dom_voltage_data['data']['Vcc']['value']
            else:
                return None

        if self.dom_supported:
            dom_channel_monitor_raw = self.read_eeprom((offset + QSFP_DD_CHANNEL_MON_OFFSET), QSFP_DD_CHANNEL_MON_WIDTH)
            if  dom_channel_monitor_raw is None:
                self.sfplog.log_debug(" QSFP-DD dom_channel_monitor_raw is None")
                return None

            dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params(dom_channel_monitor_raw, 0)

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

                transceiver_dom_info_dict['rx_los'] = self.get_rx_los()
                transceiver_dom_info_dict['tx_fault'] = self.get_tx_fault()
                transceiver_dom_info_dict['lp_mode'] = self.get_lpmode()
                transceiver_dom_info_dict['tx_disable'] = self.get_tx_disable()
                transceiver_dom_info_dict['tx_disabled_channel'] = self.get_tx_disable_channel()

        self.sfplog.log_debug("port_num:%d transceiver_dom_info_dict:%s" % (self.port_num, transceiver_dom_info_dict))
        return transceiver_dom_info_dict

    def get_transceiver_threshold_info_qsfp_dd_dict(self):
        sfpd_obj = qsfp_dd_Dom()
        if sfpd_obj is None:
            self.sfplog.log_error("sfpd_obj qsfp_dd_Dom is None")
            return None

        transceiver_dom_threshold_info_dict = dict.fromkeys(self.threshold_dict_keys, 'N/A')

        offset = 0
        dom_module_threshold_raw = self.read_eeprom(offset + QSFP_DD_MODULE_THRESHOLD_OFFSET, QSFP_DD_MODULE_THRESHOLD_WIDTH)
        if dom_module_threshold_raw is None:
            self.sfplog.log_debug("QSFP-DD dom_module_threshold_raw is None")
            return None
        dom_module_threshold_data = sfpd_obj.parse_module_threshold_values(dom_module_threshold_raw, 0)

        transceiver_dom_threshold_info_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
        transceiver_dom_threshold_info_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
        transceiver_dom_threshold_info_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
        transceiver_dom_threshold_info_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
        transceiver_dom_threshold_info_dict['vcchighalarm'] = dom_module_threshold_data['data']['VccHighAlarm']['value']
        transceiver_dom_threshold_info_dict['vcclowalarm'] = dom_module_threshold_data['data']['VccLowAlarm']['value']
        transceiver_dom_threshold_info_dict['vcchighwarning'] = dom_module_threshold_data['data']['VccHighWarning']['value']
        transceiver_dom_threshold_info_dict['vcclowwarning'] = dom_module_threshold_data['data']['VccLowWarning']['value']
        transceiver_dom_threshold_info_dict['txbiashighalarm'] = dom_module_threshold_data['data']['TxBiasHighAlarm']['value']
        transceiver_dom_threshold_info_dict['txbiaslowalarm'] = dom_module_threshold_data['data']['TxBiasLowAlarm']['value']
        transceiver_dom_threshold_info_dict['txbiashighwarning'] = dom_module_threshold_data['data']['TxBiasHighWarning']['value']
        transceiver_dom_threshold_info_dict['txbiaslowwarning'] = dom_module_threshold_data['data']['TxBiasLowWarning']['value']
        transceiver_dom_threshold_info_dict['txpowerhighalarm'] = dom_module_threshold_data['data']['TxPowerHighAlarm']['value']
        transceiver_dom_threshold_info_dict['txpowerlowalarm'] = dom_module_threshold_data['data']['TxPowerLowAlarm']['value']
        transceiver_dom_threshold_info_dict['txpowerhighwarning'] = dom_module_threshold_data['data']['TxPowerHighWarning']['value']
        transceiver_dom_threshold_info_dict['txpowerlowwarning'] = dom_module_threshold_data['data']['TxPowerLowWarning']['value']
        transceiver_dom_threshold_info_dict['rxpowerhighalarm'] = dom_module_threshold_data['data']['RxPowerHighAlarm']['value']
        transceiver_dom_threshold_info_dict['rxpowerlowalarm'] = dom_module_threshold_data['data']['RxPowerLowAlarm']['value']
        transceiver_dom_threshold_info_dict['rxpowerhighwarning'] = dom_module_threshold_data['data']['RxPowerHighWarning']['value']
        transceiver_dom_threshold_info_dict['rxpowerlowwarning'] = dom_module_threshold_data['data']['RxPowerLowWarning']['value']

        self.sfplog.log_debug("port_num:%d transceiver_dom_threshold_info_dict:%s" % (self.port_num, transceiver_dom_threshold_info_dict))
        return transceiver_dom_threshold_info_dict

    def get_transceiver_info_dict(self):
        """
        Retrieves transceiver info of this SFP

        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        type                       |1*255VCHAR     |type of SFP
        type_abbrv_name            |1*255VCHAR     |type_abbrv_name of SFP
        hardware_rev               |1*255VCHAR     |hardware version of SFP
        serial                     |1*255VCHAR     |serial number of the SFP
        manufacturer               |1*255VCHAR     |SFP vendor name
        model                      |1*255VCHAR     |SFP model name
        connector                  |1*255VCHAR     |connector information
        encoding                   |1*255VCHAR     |encoding information
        ext_identifier             |1*255VCHAR     |extend identifier
        ext_rateselect_compliance  |1*255VCHAR     |extended rateSelect compliance
        cable_length               |INT            |cable length in m
        nominal_bit_rate           |INT            |nominal bit rate by 100Mbs
        specification_compliance   |1*255VCHAR     |specification compliance
        vendor_date                |1*255VCHAR     |vendor date
        vendor_oui                 |1*255VCHAR     |vendor OUI
        application_advertisement  |1*255VCHAR     |supported applications advertisement
        ========================================================================
        """
        if self.sfp_type == SFP_TYPE:
            return self.get_transceiver_info_sfp_dict()
        elif self.sfp_type == QSFP_TYPE:
            return self. get_transceiver_info_qsfp_dict()
        elif self.sfp_type == QSFP_DD_TYPE:
            return self. get_transceiver_info_qsfp_dd_dict()
        else:
            return None

    def get_transceiver_bulk_status_dict(self):
        """
        Retrieves transceiver bulk status of this SFP

        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        rx_los                     |BOOLEAN        |RX loss-of-signal status, True if has RX los, False if not.
        tx_fault                   |BOOLEAN        |TX fault status, True if has TX fault, False if not.
        reset_status               |BOOLEAN        |reset status, True if SFP in reset, False if not.
        lp_mode                    |BOOLEAN        |low power mode status, True in lp mode, False if not.
        tx_disable                 |BOOLEAN        |TX disable status, True TX disabled, False if not.
        tx_disabled_channel        |HEX            |disabled TX channels in hex, bits 0 to 3 represent channel 0
                                   |               |to channel 3.
        temperature                |INT            |module temperature in Celsius
        voltage                    |INT            |supply voltage in mV
        tx<n>bias                  |INT            |TX Bias Current in mA, n is the channel number,
                                   |               |for example, tx2bias stands for tx bias of channel 2.
        rx<n>power                 |INT            |received optical power in mW, n is the channel number,
                                   |               |for example, rx2power stands for rx power of channel 2.
        tx<n>power                 |INT            |TX output power in mW, n is the channel number,
                                   |               |for example, tx2power stands for tx power of channel 2.
        ========================================================================
        """
        if self.sfp_type == SFP_TYPE:
            return self.get_transceiver_bulk_status_sfp_dict()
        elif self.sfp_type == QSFP_TYPE:
            return self. get_transceiver_bulk_status_qsfp_dict()
        elif self.sfp_type == QSFP_DD_TYPE:
            return self. get_transceiver_bulk_status_qsfp_dd_dict()
        else:
            return None

    def get_transceiver_threshold_info_dict(self):
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
        if self.sfp_type == SFP_TYPE:
            return self.get_transceiver_threshold_info_sfp_dict()
        elif self.sfp_type == QSFP_TYPE:
            return self. get_transceiver_threshold_info_qsfp_dict()
        elif self.sfp_type == QSFP_DD_TYPE:
            return self. get_transceiver_threshold_info_qsfp_dd_dict()
        else:
            return None

    def get_transceiver_dict(self, dict_flag):
        transceiver_info_dict = None
        check_valid_flag = True
        # add retry time, interval 500ms, up to 1500ms
        for i in range(3):
            if dict_flag == "transceiver_info":
                transceiver_info_dict = self.get_transceiver_info_dict()
            elif dict_flag == "transceiver_bulk_status":
                transceiver_info_dict = self.get_transceiver_bulk_status_dict()
            elif dict_flag == "transceiver_threshold_info":
                transceiver_info_dict = self.get_transceiver_threshold_info_dict()
            else:
                break

            if transceiver_info_dict is None:
                time.sleep(0.05)
                continue
            for key in transceiver_info_dict:
                dict_info = "%s :%s" % (str(key), str(transceiver_info_dict[key]))
                if ((re.search("Unknown", dict_info)) or (re.search("Non-hexadecimal", dict_info))):
                    check_valid_flag = False
                    self.sfplog.log_debug("sleep 500ms, retry")
                    time.sleep(0.05)
                    continue
            if check_valid_flag:
                break

        return transceiver_info_dict


    """Sfp cpld"""
    def get_presence_by_libplatform(self):
        try:
            ret, _, _, offset_bit = self.get_sfp_cpld_info("presence")
            if ret is False:
                return False
            ret, info = self.read_cpld_by_libplatform("presence")
            if ret:
                if self.get_flip_flag("presence") is False:
                    return (info[0] & (1 << offset_bit) == 0)
                else:
                    return (info[0] & (1 << offset_bit) != 0)
        except Exception as err:
            self.sfplog.log_error(traceback.format_exc())

        return False

    def get_presence_by_sysfs(self):
        try:
            ret, result = self.read_cpld_by_sysfs("presence")
            if ret is False:
                return False

            if (global_sfp_config["presence_path_s3ip_flag"] is False
                and global_sfp_config["presence_path_rg_plat_flag"] is False):
                result = int(result, 16)
                # ModPrsL is active low
                return result & (1 << ((self.port_num - 1) % 8)) == 0
            else:
                return result == 1
        except Exception as err:
            self.sfplog.log_error(traceback.format_exc())

        return False

    def set_reset_by_libplatform(self, reset):
        """
        Reset SFP and return all user module settings to their default srate.

        Returns:
            A boolean, True if successful, False if not
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type != SFP_TYPE:
            try:
                val = []
                ret, info = self.read_cpld_by_libplatform("reset")
                if ret is False:
                    return False

                ret, _, _, offset_bit = self.get_sfp_cpld_info("reset")
                if ret is False:
                    return False

                if self.get_flip_flag("reset") is False:
                    if reset:
                        val.append(info[0] & (~(1 << offset_bit)))
                    else:
                        val.append(info[0] | (1 << offset_bit))
                else:
                    if reset:
                        val.append(info[0] | (1 << offset_bit))
                    else:
                        val.append(info[0] & (~(1 << offset_bit)))

                ret = self.write_cpld_by_libplatform("reset", val)
                if ret is False:
                    return False
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
            return True
        else:
            # SFP doesn't support this feature
            return False

        return False

    def set_reset_by_sysfs(self, reset):
        """
        Reset SFP and return all user module settings to their default srate.

        Returns:
            A boolean, True if successful, False if not
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type != SFP_TYPE:
            try:
                if (global_sfp_config["reset_path_s3ip_flag"] is False
                    and global_sfp_config["reset_path_rg_plat_flag"] is False):
                    ret, result = self.read_cpld_by_sysfs("reset")
                    if ret is False:
                        return False
                    if reset:
                        result = result | (1 << ((self.port_num - 1) % 8))
                    else:
                        result = result & (~(1 << ((self.port_num - 1) % 8)))
                else:
                    if reset:
                        result = 1
                    else:
                        result = 0

                ret = self.write_cpld_by_sysfs("reset", result)
                if ret is False:
                    return False
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
            return True
        else:
            # SFP doesn't support this feature
            return False

        return False

    def set_reset(self, reset):
        """
        Reset SFP and return all user module settings to their default srate.

        Returns:
            A boolean, True if successful, False if not
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type != SFP_TYPE:
            try:
                if self.get_libplatform_flag():
                    return self.set_reset_by_libplatform(reset)
                else:
                    return self.set_reset_by_sysfs(reset)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
        else:
            # SFP doesn't support this feature
            return False

        return False

    def get_tx_disable_by_libplatform(self):
        """
        Retrieves the tx_disable status of this SFP

        Returns:
            A Boolean, True if tx_disable is enabled, False if disabled
        """
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        if self.get_dom_supported() is False:
            return None

        tx_disable_list = []
        if self.sfp_type == SFP_TYPE:
            try:
                ret, _, _, offset_bit = self.get_sfp_cpld_info("txdis")
                if ret is False:
                    return None
                ret, info = self.read_cpld_by_libplatform("txdis")
                if ret:
                    # ModPrsL is active low
                    if self.get_flip_flag("txdis") is False:
                        tx_disable_list.append(info[0] & (1 << offset_bit) == 0)
                    else:
                        tx_disable_list.append(info[0] & (1 << offset_bit) != 0)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return None

        return tx_disable_list

    def get_tx_disable_by_sysfs(self):
        """
        Retrieves the tx_disable status of this SFP

        Returns:
            A Boolean, True if tx_disable is enabled, False if disabled
        """
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        tx_disable_list = []
        if self.sfp_type == SFP_TYPE:
            try:
                ret, result = self.read_cpld_by_sysfs("txdis")
                if ret is False:
                    return None
                if (global_sfp_config["txdis_path_s3ip_flag"] is False
                    and global_sfp_config["txdis_path_rg_plat_flag"] is False):
                    # ModPrsL is active low
                    tx_disable_list.append(result & (1 << ((self.port_num - 1) % 8)) != 0)
                else:
                    tx_disable_list.append(result == 1)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return None

        return tx_disable_list

    def get_reset_status_by_libplatform(self):
        """
        Retrieves the reset status of SFP

        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type != SFP_TYPE:
            try:
                ret, _, _, offset_bit = self.get_sfp_cpld_info("reset")
                if ret is False:
                    return False
                ret, info = self.read_cpld_by_libplatform("reset")
                if ret:
                    if self.get_flip_flag("reset") is False:
                        return (info[0] & (1 << offset_bit) == 0)
                    else:
                        return (info[0] & (1 << offset_bit) != 0)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False

        return False

    def get_reset_status_by_sysfs(self):
        """
        Retrieves the reset status of SFP

        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type != SFP_TYPE:
            try:
                ret, result = self.read_cpld_by_sysfs("reset")
                if ret is False:
                    return False

                if (global_sfp_config["reset_path_s3ip_flag"] is False
                    and global_sfp_config["reset_path_rg_plat_flag"] is False):
                    reset_status = result & (1 << ((self.port_num - 1) % 8)) == 0
                else:
                    reset_status = result == 1
                return reset_status
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False

        return False

    def set_tx_disable_by_libplatform(self, tx_disable):
        """
        Disable SFP TX for all channels

        Args:
            tx_disable : A Boolean, True to enable tx_disable mode, False to disable
                         tx_disable mode.

        Returns:
            A boolean, True if tx_disable is set successfully, False if not
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type == SFP_TYPE:
            try:
                val = []
                ret, info = self.read_cpld_by_libplatform("txdis")
                if ret is False:
                    return False

                ret, _, _, offset_bit = self.get_sfp_cpld_info("txdis")
                if ret is False:
                    return False
                if self.get_flip_flag("txdis") is False:
                    if tx_disable:
                        val.append(info[0] & (~(1 << offset_bit)))
                    else:
                        val.append(info[0] | (1 << offset_bit))
                else:
                    if tx_disable:
                        val.append(info[0] | (1 << offset_bit))
                    else:
                        val.append(info[0] & (~(1 << offset_bit)))

                ret = self.write_cpld_by_libplatform("txdis", val)
                if ret is False:
                    return False
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
            return True

        return False

    def set_tx_disable_by_sysfs(self, tx_disable):
        """
        Disable SFP TX for all channels

        Args:
            tx_disable : A Boolean, True to enable tx_disable mode, False to disable
                         tx_disable mode.

        Returns:
            A boolean, True if tx_disable is set successfully, False if not
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type == SFP_TYPE:
            try:
                if (global_sfp_config["txdis_path_s3ip_flag"] is False
                    and global_sfp_config["txdis_path_rg_plat_flag"] is False):
                    result = self.read_cpld_by_sysfs("txdis")
                    if tx_disable:
                        result = result | (1 << ((self.port_num - 1) % 8))
                    else:
                        result = result & (~(1 << ((self.port_num - 1) % 8)))
                else:
                    if tx_disable:
                        result = 1
                    else:
                        result = 0
                ret = self.write_cpld_by_sysfs("txdis", result)
                if ret is False:
                    return False
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
            return True

        return False


    """Sfp api"""
    def get_presence(self):
        if self.check_port_validity() is False:
            return False

        if self.get_libplatform_flag():
            presence = self.get_presence_by_libplatform()
        else:
            presence = self.get_presence_by_sysfs()

        self.sfplog.log_debug("port_num:%d presence:%s" % (self.port_num, presence))
        return presence

    def get_transceiver_info(self):
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        return self.get_transceiver_dict("transceiver_info")

    def get_transceiver_bulk_status(self):
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        return self.get_transceiver_dict("transceiver_bulk_status")

    def get_transceiver_threshold_info(self):
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        if self.get_dom_supported() is False:
            return None

        return self.get_transceiver_dict("transceiver_threshold_info")

    def get_temperature(self):
        """
        Retrieves the temperature of this SFP

        Returns:
            An integer number of current temperature in Celsius
        """
        transceiver_bulk_status = self.get_transceiver_bulk_status()
        if transceiver_bulk_status is None:
            return None

        return transceiver_bulk_status.get("temperature", "N/A")

    def get_voltage(self):
        """
        Retrieves the supply voltage of this SFP

        Returns:
            An integer number of supply voltage in mV
        """
        transceiver_bulk_status = self.get_transceiver_bulk_status()
        if transceiver_bulk_status is None:
            return None

        return transceiver_bulk_status.get("voltage", "N/A")

    def get_tx_bias(self):
        """
        Retrieves the TX bias current of this SFP

        Returns:
            A list of four integer numbers, representing TX bias in mA
            for channel 0 to channel 4.
            Ex. ['110.09', '111.12', '108.21', '112.09']
        """

        tx_bias_list = []
        transceiver_bulk_status = self.get_transceiver_bulk_status()
        if transceiver_bulk_status is None:
            return None

        for lane_num in range(1, self.lane_nums + 1):
            tx_bias_list.append(transceiver_bulk_status.get('tx{}bias'.format(lane_num)))

        return tx_bias_list

    def get_rx_power(self):
        """
        Retrieves the received optical power for this SFP

        Returns:
            A list of four integer numbers, representing received optical
            power in mW for channel 0 to channel 4.
            Ex. ['1.77', '1.71', '1.68', '1.70']
        """
        rx_power_list = []
        transceiver_bulk_status = self.get_transceiver_bulk_status()
        if transceiver_bulk_status is None:
            return None

        for lane_num in range(1, self.lane_nums + 1):
            rx_power_list.append(transceiver_bulk_status.get('rx{}power'.format(lane_num)))

        return rx_power_list

    def get_tx_power(self):
        """
        Retrieves the TX power of this SFP

        Returns:
            A list of four integer numbers, representing TX power in mW
            for channel 0 to channel 4.
            Ex. ['1.86', '1.86', '1.86', '1.86']
        """
        tx_power_list = []
        transceiver_bulk_status = self.get_transceiver_bulk_status()
        if transceiver_bulk_status is None:
            return None

        for lane_num in range(1, self.lane_nums + 1):
            tx_power_list.append(transceiver_bulk_status.get('tx{}power'.format(lane_num)))

        return tx_power_list

    def get_rx_los(self):
        """
        Retrieves the RX LOS (lost-of-signal) status of SFP
        Returns:
            A Boolean, True if SFP has RX LOS, False if not.
            Note : RX LOS status is latched until a call to get_rx_los or a reset.
        """
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        if self.get_dom_supported() is False:
            return None

        rx_los_list = []
        if self.sfp_type == QSFP_TYPE:
            offset = 0
            dom_channel_monitor_raw = self.read_eeprom((offset + QSFP_CHANNL_RX_LOS_STATUS_OFFSET), QSFP_CHANNL_RX_LOS_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("QSFP dom_channel_monitor_raw is None")
                return None
            rx_los_data = int(dom_channel_monitor_raw[0], 16)
            rx_los_list.append(rx_los_data & 0x01 != 0)
            rx_los_list.append(rx_los_data & 0x02 != 0)
            rx_los_list.append(rx_los_data & 0x04 != 0)
            rx_los_list.append(rx_los_data & 0x08 != 0)

        elif self.sfp_type == QSFP_DD_TYPE:
            offset = 0
            dom_channel_monitor_raw = self.read_eeprom((offset + QSFP_DD_CHANNEL_RX_LOS_STATUS_OFFSET), QSFP_DD_CHANNEL_RX_LOS_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("QSFP-DD dom_channel_monitor_raw is None")
                return None
            rx_los_data = int(dom_channel_monitor_raw[0], 16)
            rx_los_list.append(rx_los_data & 0x01 != 0)
            rx_los_list.append(rx_los_data & 0x02 != 0)
            rx_los_list.append(rx_los_data & 0x04 != 0)
            rx_los_list.append(rx_los_data & 0x08 != 0)
            rx_los_list.append(rx_los_data & 0x10 != 0)
            rx_los_list.append(rx_los_data & 0x20 != 0)
            rx_los_list.append(rx_los_data & 0x40 != 0)
            rx_los_list.append(rx_los_data & 0x80 != 0)

        elif self.sfp_type == SFP_TYPE:
            offset = 256
            dom_channel_monitor_raw = self.read_eeprom((offset + SFP_CHANNL_STATUS_OFFSET), SFP_CHANNL_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("SFP dom_channel_monitor_raw is None")
                return None
            rx_los_data = int(dom_channel_monitor_raw[0], 16)
            rx_los_list.append(rx_los_data & 0x02 != 0)

        return rx_los_list

    def get_tx_fault(self):
        """
        Retrieves the TX fault status of SFP
        Returns:
            A Boolean, True if SFP has TX fault, False if not
            Note : TX fault status is lached until a call to get_tx_fault or a reset.
        """
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        if self.get_dom_supported() is False:
            return None

        tx_fault_list = []
        if self.sfp_type == QSFP_TYPE:
            offset = 0
            dom_channel_monitor_raw = self.read_eeprom((offset + QSFP_CHANNL_TX_FAULT_STATUS_OFFSET), QSFP_CHANNL_TX_FAULT_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("QSFP dom_channel_monitor_raw is None")
                return None
            tx_fault_data = int(dom_channel_monitor_raw[0], 16)
            tx_fault_list.append(tx_fault_data & 0x01 != 0)
            tx_fault_list.append(tx_fault_data & 0x02 != 0)
            tx_fault_list.append(tx_fault_data & 0x04 != 0)
            tx_fault_list.append(tx_fault_data & 0x08 != 0)

        elif self.sfp_type == QSFP_DD_TYPE:
            offset = 0
            dom_channel_monitor_raw = self.read_eeprom((offset + QSFP_DD_CHANNEL_TX_FAULT_STATUS_OFFSET), QSFP_DD_CHANNEL_TX_FAULT_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("QSFP-DD dom_channel_monitor_raw is None")
                return None
            tx_fault_data = int(dom_channel_monitor_raw[0], 16)
            tx_fault_list.append(tx_fault_data & 0x01 != 0)
            tx_fault_list.append(tx_fault_data & 0x02 != 0)
            tx_fault_list.append(tx_fault_data & 0x04 != 0)
            tx_fault_list.append(tx_fault_data & 0x08 != 0)
            tx_fault_list.append(tx_fault_data & 0x10 != 0)
            tx_fault_list.append(tx_fault_data & 0x20 != 0)
            tx_fault_list.append(tx_fault_data & 0x40 != 0)
            tx_fault_list.append(tx_fault_data & 0x80 != 0)

        elif self.sfp_type == SFP_TYPE:
            offset = 256
            dom_channel_monitor_raw = self.read_eeprom((offset + SFP_CHANNL_STATUS_OFFSET), SFP_CHANNL_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("SFP dom_channel_monitor_raw is None")
                return None
            tx_fault_data = int(dom_channel_monitor_raw[0], 16)
            tx_fault_list.append(tx_fault_data & 0x04 != 0)

        return tx_fault_list

    def get_tx_disable(self):
        """
        Retrieves the tx_disable status of this SFP

        Returns:
            A Boolean, True if tx_disable is enabled, False if disabled
        """
        if self.check_port_validity() is False:
            return None

        if self.get_presence() is False:
            return None

        if self.get_dom_supported() is False:
            return None

        tx_disable_list = []
        if self.sfp_type == QSFP_TYPE:
            offset = 0
            dom_channel_monitor_raw = self.read_eeprom((offset + QSFP_CHANNL_DISABLE_STATUS_OFFSET), QSFP_CHANNL_DISABLE_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("QSFP dom_channel_monitor_raw is None")
                return None
            tx_disable_data = int(dom_channel_monitor_raw[0], 16)
            tx_disable_list.append(tx_disable_data & 0x01 != 0)
            tx_disable_list.append(tx_disable_data & 0x02 != 0)
            tx_disable_list.append(tx_disable_data & 0x04 != 0)
            tx_disable_list.append(tx_disable_data & 0x08 != 0)

        elif self.sfp_type == QSFP_DD_TYPE:
            offset = 0
            dom_channel_monitor_raw = self.read_eeprom((offset + QSFP_DD_CHANNEL_TX_DISABLE_STATUS_OFFSET), QSFP_DD_CHANNEL_TX_DISABLE_STATUS_WIDTH)
            if dom_channel_monitor_raw is None:
                self.sfplog.log_debug("QSFP-DD dom_channel_monitor_raw is None")
                return None
            tx_disable_data = int(dom_channel_monitor_raw[0], 16)
            tx_disable_list.append(tx_disable_data & 0x01 != 0)
            tx_disable_list.append(tx_disable_data & 0x02 != 0)
            tx_disable_list.append(tx_disable_data & 0x04 != 0)
            tx_disable_list.append(tx_disable_data & 0x08 != 0)
            tx_disable_list.append(tx_disable_data & 0x10 != 0)
            tx_disable_list.append(tx_disable_data & 0x20 != 0)
            tx_disable_list.append(tx_disable_data & 0x40 != 0)
            tx_disable_list.append(tx_disable_data & 0x80 != 0)

        elif self.sfp_type == SFP_TYPE:
            try:
                if self.get_libplatform_flag():
                    return self.get_tx_disable_by_libplatform()
                else:
                    return self.get_tx_disable_by_sysfs()
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return None

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
        tx_disable_list = self.get_tx_disable()
        if tx_disable_list is None:
            return 0

        tx_disabled = 0
        for i in range(len(tx_disable_list)):
            if tx_disable_list[i]:
                tx_disabled |= 1 << i

        return tx_disabled

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        '''
        Not support LPMode pin to control lpmde.
        This function is affected by the  Power_over-ride and Power_set software control bits (byte 93 bits 0,1)
        '''
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type == QSFP_TYPE:
            offset = 0
            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return False

            dom_control_raw = self.read_eeprom(offset + QSFP_CONTROL_OFFSET, QSFP_CONTROL_WIDTH)
            if dom_control_raw is None:
                self.sfplog.log_debug("QSFP dom_control_raw is None")
                return False
            dom_control_data = sfpd_obj.parse_control_bytes(dom_control_raw, 0)
            lpmode = (dom_control_data['data']['PowerSet']['value'] == 'On')
            power_override = ( dom_control_data['data']['PowerOverride']['value'] == 'On')
            if lpmode == power_override == True:
                return True

        elif self.sfp_type == QSFP_DD_TYPE:
            offset = 0
            sfpd_obj = qsfp_dd_Dom()
            if sfpd_obj is None:
                return False
            dom_control_raw = self.read_eeprom((offset + QSFP_DD_LPMODE_STATUS_OFFSET), QSFP_DD_LPMODE_STATUS_WIDTH)
            if dom_control_raw is None:
                self.sfplog.log_debug("QSFP-DD dom_control_raw is None")
                return False
            power_data = int(dom_control_raw[0], 16)
            lpmode = power_data & 0x10 != 0
            if lpmode == True:
                return True

        elif self.sfp_type == SFP_TYPE:
            # SFP doesn't support this feature
            self.sfplog.log_debug("SFP not support low power mode setting.")
            return False

        return False

    def get_power_override(self):
        """
        Retrieves the power-override status of this SFP

        Returns:
            A Boolean, True if power-override is enabled, False if disabled
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type == QSFP_TYPE:
            offset = 0
            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return False

            dom_control_raw = self.read_eeprom(offset + QSFP_CONTROL_OFFSET, QSFP_CONTROL_WIDTH) if self.get_presence() else None
            if dom_control_raw is None:
                self.sfplog.log_debug("QSFP dom_control_raw is None")
                return False
            dom_control_data = sfpd_obj.parse_control_bytes(dom_control_raw, 0)
            power_override = (dom_control_data['data']['PowerOverride']['value'] == 'On')
            return power_override
        elif self.sfp_type == SFP_TYPE:
            # SFP doesn't support this feature
            return False

        return False

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP

        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type != SFP_TYPE:
            try:
                if self.get_libplatform_flag():
                    return self.get_reset_status_by_libplatform()
                else:
                    return self.get_reset_status_by_sysfs()
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
        else:
            # SFP doesn't support this feature
            return False

        return False

    def tx_disable(self, tx_disable):
        """
        Disable SFP TX for all channels

        Args:
            tx_disable : A Boolean, True to enable tx_disable mode, False to disable
                         tx_disable mode.

        Returns:
            A boolean, True if tx_disable is set successfully, False if not
        """
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.get_dom_supported() is False:
            return False

        if self.sfp_type == QSFP_TYPE:
            try:
                return self.tx_disable_channel(0xf, tx_disable)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
        elif self.sfp_type == QSFP_DD_TYPE:
            try:
                return self.tx_disable_channel(0xff, tx_disable)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
        elif self.sfp_type == SFP_TYPE:
            try:
                if self.get_libplatform_flag():
                    return self.set_tx_disable_by_libplatform(tx_disable)
                else:
                    return self.set_tx_disable_by_sysfs(tx_disable)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False

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
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.get_dom_supported() is False:
            return False

        if self.sfp_type == QSFP_TYPE:
            offset = 0
            if 0 <= channel <= 0xf:
                try:
                    channel_state = self.get_tx_disable_channel()
                    if disable:
                        tx_disable_ctl = channel_state | channel
                    else:
                        tx_disable_ctl = channel_state & (~channel)

                    return self.write_eeprom(offset + QSFP_CONTROL_OFFSET, tx_disable_ctl)
                except Exception as err:
                    self.sfplog.log_error(traceback.format_exc())
                    return False
        elif self.sfp_type == QSFP_DD_TYPE:
            offset = 0
            if 0 <= channel <= 0xff:
                try:
                    channel_state = self.get_tx_disable_channel()
                    if disable:
                        tx_disable_ctl = channel_state | channel
                    else:
                        tx_disable_ctl = channel_state & (~channel)

                    return self.write_eeprom(offset + QSFP_DD_CHANNEL_TX_DISABLE_STATUS_OFFSET, tx_disable_ctl)
                except Exception as err:
                    self.sfplog.log_error(traceback.format_exc())
                    return False
        elif self.sfp_type == SFP_TYPE:
            # SFP doesn't support this feature
            return False

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
        '''
        Not support LPMode pin to control lpmde.
        This function is affected by the  Power_over-ride and Power_set software control bits (byte 93 bits 0,1)
        '''
        if lpmode:
            return self.set_power_override(True, lpmode)
        else:
            return self.set_power_override(False, lpmode)

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
        if self.check_port_validity() is False:
            return False

        if self.get_presence() is False:
            return False

        if self.sfp_type == QSFP_TYPE:
            offset = 0
            try:
                power_override_bit = 0
                if power_override:
                    power_override_bit |= 1 << 0

                power_set_bit = 0
                if power_set:
                    power_set_bit |= 1 << 1

                data = power_override_bit | power_set_bit
                return self.write_eeprom(offset + QSFP_POWERMODE_OFFSET, data)
            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())
                return False
        elif self.sfp_type == SFP_TYPE:
            # SFP doesn't support this feature
            return False

        return False

    def reset(self):
        """
        Reset SFP and return all user module settings to their default state.

        Returns:
            A boolean, True if successful, False if not
        """
        self.sfplog.log_debug('port_num:%d resetting...' % self.port_num)
        ret = self.set_reset(True)
        if ret:
            time.sleep(0.5)
            ret = self.set_reset(False)

        return ret

class SfpConfig():

    """SfpConfig class"""

    def __init__(self):
        self.sfplog = SfpLog()
        self.get_sfp_config()

    def get_port_start(self):
        return global_sfp_config.get("port_start", None)

    def get_port_end(self):
        return global_sfp_config.get("port_end", None)

    def get_eeprom_offset(self):
        return global_sfp_config.get("eeprom_offset", None)

    def get_port_index_start(self):
        return global_sfp_config.get("port_index_start", None)

    def get_sfp_config_flag(self):
        return global_sfp_config.get("flag", False)

    def dump_global_sfp_config(self, dump_flag=False):
        if dump_flag is False:
            return
        self.sfplog.log_debug("dump_global_sfp_config start================================")
        for key in global_sfp_config:
            if key not in ["sfp_sysfs_path", "sfp_cpld_info"]:
                dict_info = "%s: %s" % (str(key), str(global_sfp_config[key]))
                self.sfplog.log_debug(dict_info)
        if global_sfp_config["libplatform_flag"] is False:
            for key in global_sfp_config["sfp_sysfs_path"]:
                dict_info = "%s presence_path:%s" % (str(key), str(global_sfp_config["sfp_sysfs_path"][key]["presence_path"]))
                self.sfplog.log_debug(dict_info)
                dict_info = "%s txdis_path:%s" % (str(key), str(global_sfp_config["sfp_sysfs_path"][key]["txdis_path"]))
                self.sfplog.log_debug(dict_info)
                dict_info = "%s reset_path:%s" % (str(key), str(global_sfp_config["sfp_sysfs_path"][key]["reset_path"]))
                self.sfplog.log_debug(dict_info)
        else:
            for key in global_sfp_config["sfp_cpld_info"]:
                if global_sfp_config["sfp_cpld_info"][key]["presence_cpld"] is None:
                    dict_info = "%s presence_cpld None" % (str(key))
                else:
                    dict_info = "%s presence_cpld dev_id:%s offset:%s offset_bit:%s" % (
                        str(key),
                        str(global_sfp_config["sfp_cpld_info"][key]["presence_cpld"]["dev_id"]),
                        hex(global_sfp_config["sfp_cpld_info"][key]["presence_cpld"]["offset"]),
                        str(global_sfp_config["sfp_cpld_info"][key]["presence_cpld"]["offset_bit"]))
                self.sfplog.log_debug(dict_info)

                if global_sfp_config["sfp_cpld_info"][key]["txdis_cpld"] is None:
                    dict_info = "%s txdis_cpld None" % (str(key))
                else:
                    dict_info = "%s txdis_cpld dev_id:%s offset:%s offset_bit:%s" % (
                        str(key),
                        str(global_sfp_config["sfp_cpld_info"][key]["txdis_cpld"]["dev_id"]),
                        hex(global_sfp_config["sfp_cpld_info"][key]["txdis_cpld"]["offset"]),
                        str(global_sfp_config["sfp_cpld_info"][key]["txdis_cpld"]["offset_bit"]))
                self.sfplog.log_debug(dict_info)

                if global_sfp_config["sfp_cpld_info"][key]["reset_cpld"] is None:
                    dict_info = "%s reset_cpld None" % (str(key))
                else:
                    dict_info = "%s reset_cpld dev_id:%s offset:%s offset_bit:%s" % (
                        str(key),
                        str(global_sfp_config["sfp_cpld_info"][key]["reset_cpld"]["dev_id"]),
                        hex(global_sfp_config["sfp_cpld_info"][key]["reset_cpld"]["offset"]),
                        str(global_sfp_config["sfp_cpld_info"][key]["reset_cpld"]["offset_bit"]))
                self.sfplog.log_debug(dict_info)
        self.sfplog.log_debug("dump_global_sfp_config end================================")

    def assign_to_global_variable(self, sfp_config):
        global PORT_START
        global PORT_END
        global PORT_SFP_START
        global PORT_SFP_END
        global PORT_QSFP_START
        global PORT_QSFP_END
        global PORT_QSFP_DD_START
        global PORT_QSFP_DD_END
        global EEPROM_OFFSET

        PORT_START = sfp_config["port_start"]
        PORT_END = sfp_config["port_end"]
        PORT_SFP_START = sfp_config["port_sfp_start"]
        PORT_SFP_END = sfp_config["port_sfp_end"]
        PORT_QSFP_START = sfp_config["port_qsfp_start"]
        PORT_QSFP_END = sfp_config["port_qsfp_end"]
        PORT_QSFP_DD_START = sfp_config["port_qsfp_dd_start"]
        PORT_QSFP_DD_END = sfp_config["port_qsfp_dd_end"]
        EEPROM_OFFSET = sfp_config["eeprom_offset"]

    def parse_port_range(self, cage_type_list, port_index_start):
        port_start = 0
        port_end = 0
        if cage_type_list:
            port_start = 0 + port_index_start
            port_end = len(cage_type_list) - 1 + port_index_start

        return port_start, port_end

    def parse_cage_type_range(self, cage_type_list, cage_type, port_index_start):
        cage_type_start = -1
        cage_type_end = -1
        if cage_type not in cage_type_list:
            return cage_type_start, cage_type_end

        index = -1
        index_list = []
        cage_type_start = cage_type_list.index(cage_type) + port_index_start
        for i in range(0, cage_type_list.count(cage_type)):
            index = cage_type_list.index(cage_type, index + 1)
            index_list.append(index)
        cage_type_end = index_list[-1] + port_index_start
        self.sfplog.log_debug("cage_type: %-4s range: %d-%2d" % (cage_type, cage_type_start, cage_type_end))

        return cage_type_start, cage_type_end

    def get_cage_type_range(self, sfp_config, cage_type_list):
        sfp_config["port_sfp_start"], sfp_config["port_sfp_end"] = self.parse_cage_type_range(
            cage_type_list, "SFP", sfp_config["port_index_start"])
        sfp_config["port_qsfp_start"], sfp_config["port_qsfp_end"] = self.parse_cage_type_range(
            cage_type_list, "QSFP", sfp_config["port_index_start"])
        sfp_config["port_qsfp_dd_start"], sfp_config["port_qsfp_dd_end"] = self.parse_cage_type_range(
            cage_type_list, "QSFP-DD", sfp_config["port_index_start"])

    def parse_cage_type(self, port, cage_type_list, port_index_start):
        return cage_type_list[port - port_index_start] if cage_type_list else None

    def get_cage_type(self, sfp_config, cage_type_list):
        sfp_config["cage_type"] = {}
        for i in range(sfp_config["port_start"], sfp_config["port_end"] + 1):
            sfp_config["cage_type"].update({i : {}})
            cage_type = self.parse_cage_type(i, cage_type_list, sfp_config["port_index_start"])
            sfp_config["cage_type"][i]= cage_type

    def parse_sysfs_path(self, port, sysfs_path_dict):
        sysfs_path = None

        if sysfs_path_dict is None:
            return None

        for key in sysfs_path_dict:
            key_port_start = int(key.split("_")[0])
            key_port_end = int(key.split("_")[1])
            if key_port_start <= port <= key_port_end:
                sysfs_path = sysfs_path_dict[key]
        return sysfs_path

    def parse_sysfs_config(self, sfp_config, SFP_CFG):
        sfp_config["eeprom_path_s3ip_flag"] = SFP_CFG.get("eeprom_path_s3ip_flag", False)
        sfp_config["presence_path_s3ip_flag"] = SFP_CFG.get("presence_path_s3ip_flag", False)
        sfp_config["txdis_path_s3ip_flag"] = SFP_CFG.get("txdis_path_s3ip_flag", False)
        sfp_config["reset_path_s3ip_flag"] = SFP_CFG.get("reset_path_s3ip_flag", False)
        sfp_config["eeprom_path_rg_plat_flag"] = SFP_CFG.get("eeprom_path_rg_plat_flag", False)
        sfp_config["presence_path_rg_plat_flag"] = SFP_CFG.get("presence_path_rg_plat_flag", False)
        sfp_config["txdis_path_rg_plat_flag"] = SFP_CFG.get("txdis_path_rg_plat_flag", False)
        sfp_config["reset_path_rg_plat_flag"] = SFP_CFG.get("reset_path_rg_plat_flag", False)

        sfp_config["sfp_sysfs_path"] = {}
        for i in range(sfp_config["port_start"], sfp_config["port_end"] + 1):
            lport = i
            if sfp_config["port_index_start"] == 0:
                lport = i + 1

            '''parse sysfs file path'''
            sfp_config["sfp_sysfs_path"].update({i : {}})
            if sfp_config["eeprom_path_s3ip_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["eeprom_path"] = "/sys/s3ip/transceiver/eth%s/eeprom" % lport
            elif sfp_config["eeprom_path_rg_plat_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["eeprom_path"] = "/sys/rg_plat/sff/sff%s/eeprom" % lport
            else:
                sfp_config["sfp_sysfs_path"][i]["eeprom_path"] = None

            if sfp_config["presence_path_s3ip_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["presence_path"] = "/sys/s3ip/transceiver/eth%s/present" % lport
            elif sfp_config["presence_path_rg_plat_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["presence_path"] = "/sys/rg_plat/sff/sff%s/present" % lport
            else:
                presence_dict = copy.deepcopy(SFP_CFG.get("presence_path", None))
                presence_path = self.parse_sysfs_path(i, presence_dict)
                sfp_config["sfp_sysfs_path"][i]["presence_path"] = presence_path

            if sfp_config["txdis_path_s3ip_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["txdis_path"] = "/sys/s3ip/transceiver/eth%s/tx_disable" % lport
            elif sfp_config["txdis_path_rg_plat_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["txdis_path"] = "/sys/rg_plat/sff/sff%s/tx_disable" % lport
            else:
                txdis_dict = copy.deepcopy(SFP_CFG.get("txdis_path", None))
                txdis_path = self.parse_sysfs_path(i, txdis_dict)
                sfp_config["sfp_sysfs_path"][i]["txdis_path"] = txdis_path

            if sfp_config["reset_path_s3ip_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["reset_path"] = "/sys/s3ip/transceiver/eth%s/reset" % lport
            elif sfp_config["reset_path_rg_plat_flag"] is True:
                sfp_config["sfp_sysfs_path"][i]["reset_path"] = "/sys/rg_plat/sff/sff%s/reset" % lport
            else:
                reset_dict = copy.deepcopy(SFP_CFG.get("reset_path", None))
                reset_path = self.parse_sysfs_path(i, reset_dict)
                sfp_config["sfp_sysfs_path"][i]["reset_path"] = reset_path

    def get_config_range_int(self, range_str):
        if not range_str:
            return []

        int_range_strs = range_str.split(',')
        range_res = []
        for int_range_str in int_range_strs:
            if '-' in int_range_str:
                range_s = int(int_range_str.split('-')[0])
                range_e = int(int_range_str.split('-')[1]) + 1
            else:
                range_s = int(int_range_str)
                range_e = int(int_range_str) + 1

            range_res = range_res + list(range(range_s, range_e))

        return range_res

    def get_cpld_info(self, cpld_info, port_num):
        if cpld_info is None:
            return False, None, None, None, None

        dev_id_dict = cpld_info.get('dev_id', None)
        if dev_id_dict is None:
            return False, None, None, None, None

        for dev_id in dev_id_dict:
            offset_dict = dev_id_dict[dev_id].get('offset', None)
            if offset_dict is None:
                return False, None, None, None, None

            for offset in offset_dict:
                offset_ports_list = self.get_config_range_int(offset_dict[offset])
                if port_num in offset_ports_list:
                    offset_bit = offset_ports_list.index(port_num)

                    # parse specific_offset_bit
                    offset_bit_dict = dev_id_dict[dev_id].get('offset_bit', None)
                    if offset_bit_dict is not None:
                        specific_offset_bit = offset_bit_dict.get(port_num, None)
                        if offset_bit is not None:
                            offset_bit = specific_offset_bit

                    # parse specific_flip_flag
                    flip_flag = False
                    flip_port_range = dev_id_dict[dev_id].get('flip', None)
                    if flip_port_range is not None:
                        flip_ports_list = self.get_config_range_int(flip_port_range)
                        if port_num in flip_ports_list:
                            flip_flag = True

                    return True, dev_id, offset, offset_bit, flip_flag
        return False, None, None, None, None

    def parse_cpld_info(self, sfp_config, cpld_info, cpld_key, port_num):
        sfp_config["sfp_cpld_info"][port_num].update({cpld_key : {}})
        if sfp_config["port_index_start"] == 0:
            ret, dev_id, offset, offset_bit, flip_flag = self.get_cpld_info(cpld_info, port_num + 1)
        else:
            ret, dev_id, offset, offset_bit, flip_flag = self.get_cpld_info(cpld_info, port_num)

        sfp_config["sfp_cpld_info"][port_num][cpld_key]["dev_id"] = dev_id
        sfp_config["sfp_cpld_info"][port_num][cpld_key]["offset"] = offset
        sfp_config["sfp_cpld_info"][port_num][cpld_key]["offset_bit"] = offset_bit
        sfp_config["sfp_cpld_info"][port_num][cpld_key]["flip_flag"] = flip_flag

        if ret is False:
            sfp_config["sfp_cpld_info"][port_num][cpld_key] = None
            return False
        return True

    def parse_cpld_config(self, sfp_config, SFP_CFG):
        sfp_config["sfp_cpld_info"] = {}
        for i in range(sfp_config["port_start"], sfp_config["port_end"] + 1):
            '''parse cpld info'''
            sfp_config["sfp_cpld_info"].update({i : {}})
            presence_cpld = copy.deepcopy(SFP_CFG.get("presence_cpld", None))
            if presence_cpld is not None:
                self.parse_cpld_info(sfp_config, presence_cpld, "presence_cpld", i)
            else:
                sfp_config["sfp_cpld_info"][i]["presence_cpld"] = None

            txdis_cpld = copy.deepcopy(SFP_CFG.get("txdis_cpld", None))
            if txdis_cpld is not None:
                self.parse_cpld_info(sfp_config, txdis_cpld, "txdis_cpld", i)
            else:
                sfp_config["sfp_cpld_info"][i]["txdis_cpld"] = None

            reset_cpld = copy.deepcopy(SFP_CFG.get("reset_cpld", None))
            if reset_cpld is not None:
                self.parse_cpld_info(sfp_config, reset_cpld, "reset_cpld", i)
            else:
                sfp_config["sfp_cpld_info"][i]["reset_cpld"] = None

    def get_sfp_config(self):
        if not self.get_sfp_config_flag():
            self.sfplog.log_debug('get_sfp_config start.')
            conf = None
            sfp_config = {}
            try:
                conf = baseutil.get_config()
                SFP_CFG = copy.deepcopy(conf.get("sfps", None))
                if SFP_CFG is None:
                    self.sfplog.log_error("SFP_CFG is None")
                    self.sfplog.log_debug('get_sfp_config end.')
                    return None
                else:
                    self.sfplog.log_debug("SFP_CFG %s" % SFP_CFG)

                cage_type_list = SFP_CFG.get("cage_type", None)
                port_index_start = SFP_CFG.get("port_index_start", 0)
                sfp_config["port_index_start"] = port_index_start
                sfp_config["port_start"], sfp_config["port_end"] = self.parse_port_range(cage_type_list, port_index_start)
                sfp_config["eeprom_offset"] = SFP_CFG.get("eeprom_offset", None)
                sfp_config["libplatform_flag"] = SFP_CFG.get("libplatform_flag", False)

                if sfp_config["libplatform_flag"] is False:
                    self.parse_sysfs_config(sfp_config, SFP_CFG)
                else:
                    self.parse_cpld_config(sfp_config, SFP_CFG)
                self.get_cage_type_range(sfp_config, cage_type_list)
                self.get_cage_type(sfp_config, cage_type_list)
                self.assign_to_global_variable(sfp_config)

            except Exception as err:
                self.sfplog.log_error(traceback.format_exc())

            sfp_config["flag"] = True
            global global_sfp_config
            global_sfp_config = copy.deepcopy(sfp_config)
            self.dump_global_sfp_config(True)
            self.sfplog.log_debug('get_sfp_config end.')

class SfpLog():
    """SfpLog class"""

    def __init__(self, level=LOG_ERROR_LEVEL, log_also_print_to_console=False):
        self.log_level = LOG_ERROR_LEVEL
        self.log_also_print_to_console = log_also_print_to_console

    def set_log_level(self, level):
        if (level == LOG_DEBUG_LEVEL
            or level == LOG_ERROR_LEVEL):
            self.log_level = level
        else:
            self.log_error("unavailable loglevel:%d" % level)

    def set_log_also_print_to_console(self, console_val):
        self.log_also_print_to_console = console_val

    def judge_debug_file(self):
        if os.path.exists(SFP_DEBUG_FILE) is True:
            self.set_log_level(LOG_DEBUG_LEVEL)
            self.set_log_also_print_to_console(True)
        else:
            self.set_log_level(LOG_ERROR_LEVEL)
            self.set_log_also_print_to_console(False)

    def log_debug(self, msg):
        self.judge_debug_file()
        funcName = sys._getframe().f_back.f_code.co_name
        lineNumber = sys._getframe().f_back.f_lineno
        dt_ms = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        info_str = dt_ms + "| DEBUG Sfp: " + funcName + ": " + str(lineNumber)
        log_info_gather = "%-40s| %s" % (info_str, str(msg))
        if self.log_level <= LOG_DEBUG_LEVEL:
            try:
                syslog.openlog("Sfp")
                syslog.syslog(syslog.LOG_DEBUG, msg)
                syslog.closelog()

                if self.log_also_print_to_console:
                    print(log_info_gather)
            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)

    def log_error(self, msg):
        self.judge_debug_file()
        funcName = sys._getframe().f_back.f_code.co_name
        lineNumber = sys._getframe().f_back.f_lineno
        dt_ms = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        info_str = dt_ms + "| ERROR Sfp: " + funcName + ": " + str(lineNumber)
        log_info_gather = "%-40s| %s" % (info_str, str(msg))
        if self.log_level <= LOG_ERROR_LEVEL:
            try:
                syslog.openlog("Sfp")
                syslog.syslog(syslog.LOG_ERR, msg)
                syslog.closelog()

                if self.log_also_print_to_console:
                    print(log_info_gather)
            except Exception as except_result:
                msg = traceback.format_exc()
                print("Exception_info:\n%s" % msg)
