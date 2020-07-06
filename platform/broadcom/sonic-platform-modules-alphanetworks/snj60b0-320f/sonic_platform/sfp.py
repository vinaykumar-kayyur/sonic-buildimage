#!/usr/bin/env python

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the SFP management routines
#
#############################################################################

try:
    import os.path
    import time
    from sonic_platform_base.sfp_base import SfpBase
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436InterfaceId
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436Dom
    from sonic_platform_base.sonic_sfp.sff8472 import sff8472InterfaceId
    from sonic_platform_base.sonic_sfp.sff8472 import sff8472Dom
    from sonic_platform_base.sonic_sfp.sff8472 import sffbase
    from sonic_platform_base.sonic_sfp.inf8628 import inf8628InterfaceId
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
# XCVR_CABLE_LENGTH_WIDTH_SFP = 6
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
XCVR_DOM_CAPABILITY_WIDTH = 1

# definitions of the offset for values in OSFP info eeprom
OSFP_TYPE_OFFSET = 0
OSFP_VENDOR_NAME_OFFSET = 129
OSFP_VENDOR_PN_OFFSET = 148
OSFP_HW_REV_OFFSET = 164
OSFP_VENDOR_SN_OFFSET = 166

#definitions of the offset and width for values in DOM info eeprom
QSFP_DOM_REV_OFFSET = 1
QSFP_DOM_REV_WIDTH = 1
QSFP_TEMPE_OFFSET = 22
QSFP_TEMPE_WIDTH = 2
QSFP_VOLT_OFFSET = 26
QSFP_VOLT_WIDTH = 2
QSFP_CHANNL_MON_OFFSET = 34
QSFP_CHANNL_MON_WIDTH = 16
QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH = 24
QSFP_CONTROL_OFFSET = 86
QSFP_CONTROL_WIDTH = 8
QSFP_CHANNL_RX_LOS_STATUS_OFFSET = 3
QSFP_CHANNL_RX_LOS_STATUS_WIDTH = 1
QSFP_CHANNL_TX_FAULT_STATUS_OFFSET = 4
QSFP_CHANNL_TX_FAULT_STATUS_WIDTH = 1
QSFP_POWEROVERRIDE_OFFSET = 93
QSFP_POWEROVERRIDE_WIDTH = 1
QSFP_MODULE_THRESHOLD_OFFSET = 128
QSFP_MODULE_THRESHOLD_WIDTH = 24
QSFP_CHANNEL_THRESHOLD_OFFSET = 176
QSFP_CHANNEL_THRESHOLD_WIDTH = 16


SFP_TEMPE_OFFSET = 96
SFP_TEMPE_WIDTH = 2
SFP_VOLT_OFFSET = 98
SFP_VOLT_WIDTH = 2
SFP_CHANNL_MON_OFFSET = 100
SFP_CHANNL_MON_WIDTH = 6
SFP_MODULE_THRESHOLD_OFFSET = 0
SFP_MODULE_THRESHOLD_WIDTH = 40
SFP_CHANNL_THRESHOLD_OFFSET = 112
SFP_CHANNL_THRESHOLD_WIDTH = 2
SFP_STATUS_CONTROL_OFFSET = 110
SFP_STATUS_CONTROL_WIDTH = 1
SFP_TX_DISABLE_HARD_BIT = 7
SFP_TX_DISABLE_SOFT_BIT = 6


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

PAGE_OFFSET = 0
KEY_OFFSET = 1
KEY_WIDTH = 2
FUNC_NAME = 3

INFO_OFFSET = 128
DOM_OFFSET = 0
DOM_OFFSET1 = 384

CPLD_PORT_NUM = 8
SFP_PATH = "/sys/bus/i2c/devices/{0}-005f"
SFPPLUS_PATH = "/sys/bus/i2c/devices/{0}-005e"
SFPPLUS_EEPROM_PATH = "/sys/bus/i2c/devices/{0}-0050"

class Alpha_Sfp(SfpBase):
    """Platform-specific Sfp class"""
    _port_start = 0
    _port_end = 34

    sfp_status = 0

    port_to_eeprom = {}

    port_to_i2cbus_0 = {
         1 : 13,
         2 : 14,
         3 : 15,
         4 : 16,
         5 : 12,
         6 : 11,
    }

    port_to_i2cbus_1 = {
         1 : 14,
         2 : 15,
         3 : 16,
         4 : 17,
         5 : 13,
         6 : 12,
    }

    port_to_i2cbus_mapping = {}

    sfpplus_eeprom_path = SFPPLUS_EEPROM_PATH+"/sfp_eeprom"
    eeprom_path = SFP_PATH+"/sfp{1}_eeprom"
    port_reset_path = SFP_PATH+"/sfp{1}_port_reset"
    present_path = SFP_PATH+"/sfp{1}_is_present"
    sfpplus_present_path = SFPPLUS_PATH+"/sfp_present"
    lpmode_path = SFP_PATH+"/sfp{1}_lpmode"

    # Read out any bytes from any offset
    def __read_eeprom_specific_bytes(self, offset, num_bytes):
        sysfsfile_eeprom = None
        eeprom_raw = []
        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        try:
            sysfsfile_eeprom = open(self.port_to_eeprom[self.index], mode="rb", buffering=0)
            sysfsfile_eeprom.seek(offset)
            raw = sysfsfile_eeprom.read(num_bytes)
            for n in range(0, num_bytes):
                eeprom_raw[n] = hex(ord(raw[n]))[2:].zfill(2)
        except Exception as e:
            pass
        finally:
            if sysfsfile_eeprom:
                sysfsfile_eeprom.close()

        return eeprom_raw

    def __init__(self, sfp_index, sfp_type):
        SfpBase.__init__(self)
        self.index = sfp_index

        # index is 0-based
        if sfp_index < self._port_start or sfp_index >= self._port_end:
            print "Invalid port index %d"%sfp_index
            return

        self.is_qsfp_port = True if (sfp_type=='QSFP' or sfp_type=='QSFP28') else False
        self.is_osfp_port = True if (sfp_type=='OSFP' or sfp_type=='QSFP-DD') else False
        self.is_sfp_port = True if (sfp_type=='SFP') else False

        path = self.present_path
        port_path = path.format(self.port_to_i2cbus_0[1], 1)
        if not os.path.exists(port_path):
            self.port_to_i2cbus_mapping = self.port_to_i2cbus_1
        else:
            self.port_to_i2cbus_mapping = self.port_to_i2cbus_0

        index = (self.index % CPLD_PORT_NUM) + 1
        cpld_index = (self.index / CPLD_PORT_NUM) + 1
        if cpld_index == 5:
            path = self.sfpplus_eeprom_path
            if index == 1:
                self.port_to_eeprom[self.index] = path.format(self.port_to_i2cbus_mapping[cpld_index])
            else:
                self.port_to_eeprom[self.index] = path.format(self.port_to_i2cbus_mapping[cpld_index+1])
        else:
            path = self.eeprom_path
            self.port_to_eeprom[self.index] = path.format(self.port_to_i2cbus_mapping[cpld_index], index)

        self.info_dict_keys = ['type', 'hardwarerev', 'serialnum', 'manufacturename', 'modelname', 'Connector', 'encoding', 'ext_identifier',
                               'ext_rateselect_compliance', 'cable_type', 'cable_length', 'nominal_bit_rate', 'specification_compliance', 'vendor_date', 'vendor_oui']

        self.dom_dict_keys = ['rx_los', 'tx_fault', 'reset_status', 'power_lpmode', 'tx_disable', 'tx_disable_channel', 'temperature', 'voltage',
                              'rx1power', 'rx2power', 'rx3power', 'rx4power', 'tx1bias', 'tx2bias', 'tx3bias', 'tx4bias', 'tx1power', 'tx2power', 'tx3power', 'tx4power']

        self.threshold_dict_keys = ['temphighalarm', 'temphighwarning', 'templowalarm', 'templowwarning', 'vcchighalarm', 'vcchighwarning', 'vcclowalarm', 'vcclowwarning', 'rxpowerhighalarm', 'rxpowerhighwarning',
                                    'rxpowerlowalarm', 'rxpowerlowwarning', 'txpowerhighalarm', 'txpowerhighwarning', 'txpowerlowalarm', 'txpowerlowwarning', 'txbiashighalarm', 'txbiashighwarning', 'txbiaslowalarm', 'txbiaslowwarning']

        SfpBase.__init__(self)

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not
        """
        cpld_index = (self.index / CPLD_PORT_NUM) + 1
        index = (self.index % CPLD_PORT_NUM) + 1
        if cpld_index == 5:
            path = self.sfpplus_present_path
            port_path = path.format(0)
        else:
            path = self.present_path
            port_path = path.format(self.port_to_i2cbus_mapping[cpld_index], index)

        try:
            reg_file = open(port_path, 'r')
            reg_value = int(reg_file.readline().rstrip(), 16)
            reg_file.close()
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        if cpld_index == 5:
            if reg_value == 3:
                # SFP+ 1 and 0 is not present, 0 is present
                reg_value = 0
            else:
                if index == 1:
                    reg_value = (reg_value < 2)
                else:
                    reg_value = ((reg_value % 2) == 0)
        return reg_value

    def get_presence_all(self):
        bitmap = ""
        port = self._port_start

        while (port >= self._port_start) and (port <= self._port_end):
            self.index = port
            reg_value = self.get_presence()

            if reg_value:
                bitmap += '1' + " "
            else:
                bitmap += '0' + " "

            port += 1

        content = bitmap.split(" ")
        content = "".join(content[::-1])

        return int(content, 2)

    def get_transceiver_info(self):
        """
        Retrieves transceiver info of this SFP

        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information	
        ---------------------------|---------------|----------------------------
        type                       |1*255VCHAR     |type of SFP
        hardwarerev                |1*255VCHAR     |hardware version of SFP
        serialnum                  |1*255VCHAR     |serial number of the SFP
        manufacturename            |1*255VCHAR     |SFP vendor name
        modelname                  |1*255VCHAR     |SFP model name
        Connector                  |1*255VCHAR     |connector information
        encoding                   |1*255VCHAR     |encoding information
        ext_identifier             |1*255VCHAR     |extend identifier
        ext_rateselect_compliance  |1*255VCHAR     |extended rateSelect compliance
        cable_length               |INT            |cable length in m
        mominal_bit_rate           |INT            |nominal bit rate by 100Mbs
        specification_compliance   |1*255VCHAR     |specification compliance
        vendor_date                |1*255VCHAR     |vendor date
        vendor_oui                 |1*255VCHAR     |vendor OUI
        ========================================================================
        """
        # check present status
        if not self.get_presence():
            return None


        if self.is_osfp_port:
            sfpi_obj = inf8628InterfaceId()
            offset = 0
            type_offset = OSFP_TYPE_OFFSET
            vendor_rev_width = XCVR_HW_REV_WIDTH_OSFP
            hw_rev_offset = OSFP_HW_REV_OFFSET
            vendor_name_offset = OSFP_VENDOR_NAME_OFFSET
            vendor_pn_offset = OSFP_VENDOR_PN_OFFSET
            vendor_sn_offset = OSFP_VENDOR_SN_OFFSET
            # cable_length_width = XCVR_CABLE_LENGTH_WIDTH_QSFP
            interface_info_bulk_width = XCVR_INTFACE_BULK_WIDTH_QSFP
            sfp_type = 'OSFP'

        elif self.is_qsfp_port:
            sfpi_obj = sff8436InterfaceId()
            offset = 128
            type_offset = XCVR_TYPE_OFFSET
            vendor_rev_width = XCVR_HW_REV_WIDTH_QSFP
            hw_rev_offset = XCVR_HW_REV_OFFSET
            vendor_name_offset = XCVR_VENDOR_NAME_OFFSET
            vendor_pn_offset = XCVR_VENDOR_PN_OFFSET
            vendor_sn_offset = XCVR_VENDOR_SN_OFFSET
            # cable_length_width = XCVR_CABLE_LENGTH_WIDTH_QSFP
            interface_info_bulk_width = XCVR_INTFACE_BULK_WIDTH_QSFP
            sfp_type = 'QSFP'
        else:
            sfpi_obj = sff8472InterfaceId()
            offset = 0
            type_offset = XCVR_TYPE_OFFSET
            vendor_rev_width = XCVR_HW_REV_WIDTH_SFP
            hw_rev_offset = XCVR_HW_REV_OFFSET
            vendor_name_offset = XCVR_VENDOR_NAME_OFFSET
            vendor_pn_offset = XCVR_VENDOR_PN_OFFSET
            vendor_sn_offset = XCVR_VENDOR_SN_OFFSET
            # cable_length_width = XCVR_CABLE_LENGTH_WIDTH_SFP
            interface_info_bulk_width = XCVR_INTFACE_BULK_WIDTH_SFP
            sfp_type = 'SFP'

        if sfpi_obj is None:
            return None
        

        if self.is_osfp_port:
            sfp_type_raw = self.__read_eeprom_specific_bytes((offset + type_offset), XCVR_TYPE_WIDTH)
            if sfp_type_raw is not None:
                sfp_type_data = sfpi_obj.parse_sfp_type(sfp_type_raw, 0)
                sfp_type_abbrv_name = sfpi_obj.parse_sfp_type_abbrv_name(sfp_typ_raw, 0)
        else:
            sfp_interface_bulk_raw = self.__read_eeprom_specific_bytes((offset + XCVR_INTFACE_BULK_OFFSET), interface_info_bulk_width)
            if sfp_interface_bulk_raw is not None:
                sfp_interface_bulk_data = sfpi_obj.parse_sfp_info_bulk(sfp_interface_bulk_raw, 0)

            sfp_vendor_oui_raw = self.__read_eeprom_specific_bytes((offset + XCVR_VENDOR_OUI_OFFSET), XCVR_VENDOR_OUI_WIDTH)
            if sfp_vendor_oui_raw is not None:
                sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(sfp_vendor_oui_raw, 0)

            sfp_vendor_date_raw = self.__read_eeprom_specific_bytes((offset + XCVR_VENDOR_DATE_OFFSET), XCVR_VENDOR_DATE_WIDTH)
            if sfp_vendor_date_raw is not None:
                sfp_vendor_date_data = sfpi_obj.parse_vendor_date(sfp_vendor_date_raw, 0)


        sfp_vendor_name_raw = self.__read_eeprom_specific_bytes(
            (offset + vendor_name_offset), XCVR_VENDOR_NAME_WIDTH)
        sfp_vendor_name_data = sfpi_obj.parse_vendor_name(
            sfp_vendor_name_raw, 0)

        sfp_vendor_pn_raw = self.__read_eeprom_specific_bytes(
            (offset + vendor_pn_offset), XCVR_VENDOR_PN_WIDTH)
        sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(
            sfp_vendor_pn_raw, 0)

        sfp_vendor_rev_raw = self.__read_eeprom_specific_bytes(
            (offset + hw_rev_offset), vendor_rev_width)
        sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(
            sfp_vendor_rev_raw, 0)

        sfp_vendor_sn_raw = self.__read_eeprom_specific_bytes(
            (offset + vendor_sn_offset), XCVR_VENDOR_SN_WIDTH)
        sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(
            sfp_vendor_sn_raw, 0)

        xcvr_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')
        compliance_code_dict = dict()

        if sfp_interface_bulk_data:
            xcvr_info_dict['type'] = sfp_interface_bulk_data['data']['type']['value']
            xcvr_info_dict['Connector'] = sfp_interface_bulk_data['data']['Connector']['value']
            xcvr_info_dict['encoding'] = sfp_interface_bulk_data['data']['EncodingCodes']['value']
            xcvr_info_dict['ext_identifier'] = sfp_interface_bulk_data['data']['Extended Identifier']['value']
            xcvr_info_dict['ext_rateselect_compliance'] = sfp_interface_bulk_data['data']['RateIdentifier']['value']
            xcvr_info_dict['type_abbrv_name'] = sfp_interface_bulk_data['data']['type_abbrv_name']['value']
        else:
            xcvr_info_dict['type'] = sfp_type_data['data']['type']['value'] if sfp_type_data else 'N/A'
            xcvr_info_dict['type_abbrv_name'] = sfp_type_abbrv_name['data']['type_abbrv_name']['value'] if sfp_type_abbrv_name else 'N/A'

        xcvr_info_dict['manufacturename'] = sfp_vendor_name_data['data']['Vendor Name']['value'] if sfp_vendor_name_data else 'N/A'
        xcvr_info_dict['modelname'] = sfp_vendor_pn_data['data']['Vendor PN']['value'] if sfp_vendor_pn_data else 'N/A'
        xcvr_info_dict['hardwarerev'] = sfp_vendor_rev_data['data']['Vendor Rev']['value'] if sfp_vendor_rev_data else 'N/A'
        xcvr_info_dict['serialnum'] = sfp_vendor_sn_data['data']['Vendor SN']['value'] if sfp_vendor_sn_data else 'N/A'
        xcvr_info_dict['vendor_oui'] = sfp_vendor_oui_data['data']['Vendor OUI']['value'] if sfp_vendor_oui_data else 'N/A'
        xcvr_info_dict['vendor_date'] = sfp_vendor_date_data['data']['VendorDataCode(YYYY-MM-DD Lot)']['value'] if sfp_vendor_date_data else 'N/A'
        xcvr_info_dict['cable_type'] = "Unknown"
        xcvr_info_dict['cable_length'] = "Unknown"

        if sfp_type == 'QSFP':
            for key in qsfp_cable_length_tup:
                if key in sfp_interface_bulk_data['data']:
                    xcvr_info_dict['cable_type'] = key
                    xcvr_info_dict['cable_length'] = str(sfp_interface_bulk_data['data'][key]['value'])

            for key in qsfp_compliance_code_tup:
                if key in sfp_interface_bulk_data['data']['Specification compliance']['value']:
                    compliance_code_dict[key] = sfp_interface_bulk_data['data']['Specification compliance']['value'][key]['value']
            xcvr_info_dict['specification_compliance'] = str(compliance_code_dict)

            nkey='Nominal Bit Rate(100Mbs)'
            if nkey in sfp_interface_bulk_data['data']:
                xcvr_info_dict['nominal_bit_rate'] = str(sfp_interface_bulk_data['data']['Nominal Bit Rate(100Mbs)']['value'])
            else:
                xcvr_info_dict['nominal_bit_rate'] = 'N/A'
        else:
            for key in sfp_cable_length_tup:
                if key in sfp_interface_bulk_data['data']:
                    xcvr_info_dict['cable_type'] = key
                    xcvr_info_dict['cable_length'] = str(sfp_interface_bulk_data['data'][key]['value'])

            for key in sfp_compliance_code_tup:
                if key in sfp_interface_bulk_data['data']['Specification compliance']['value']:
                    compliance_code_dict[key] = sfp_interface_bulk_data['data']['Specification compliance']['value'][key]['value']
            xcvr_info_dict['specification_compliance'] = str(compliance_code_dict)

            xcvr_info_dict['nominal_bit_rate'] = str(sfp_interface_bulk_data['data']['NominalSignallingRate(UnitsOf100Mbd)']['value'])

        return xcvr_info_dict

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
        # check present status
        if not self.get_presence():
            return None

        xcvr_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')

        if self.is_osfp_port:
            # Below part is added to avoid fail xcvrd, shall be implemented later
            pass
        elif self.is_qsfp_port:
            # QSFPs
            offset = 0
            offset_xcvr = 128

            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return None

            sfpi_obj = sff8436InterfaceId()
            if sfpi_obj is None:
                return None

            qsfp_dom_capability_raw = self.__read_eeprom_specific_bytes(
                (offset_xcvr + XCVR_DOM_CAPABILITY_OFFSET), XCVR_DOM_CAPABILITY_WIDTH)
            if qsfp_dom_capability_raw is not None:
                qspf_dom_capability_data = sfpi_obj.parse_qsfp_dom_capability(
                    qsfp_dom_capability_raw, 0)
            else:
                return None

            dom_temperature_raw = self.__read_eeprom_specific_bytes( (offset + QSFP_TEMPE_OFFSET), QSFP_TEMPE_WIDTH)
            if dom_temperature_raw is not None:
                dom_temperature_data = sfpd_obj.parse_temperature(dom_temperature_raw, 0)
            else:
                return None

            dom_voltage_raw = self.__read_eeprom_specific_bytes( (offset + QSFP_VOLT_OFFSET), QSFP_VOLT_WIDTH)
            if dom_voltage_raw is not None:
                dom_voltage_data = sfpd_obj.parse_voltage(dom_voltage_raw, 0)
            else:
                return None

            qsfp_dom_rev_raw = self.__read_eeprom_specific_bytes( (offset + QSFP_DOM_REV_OFFSET), QSFP_DOM_REV_WIDTH)
            if qsfp_dom_rev_raw is not None:
                qsfp_dom_rev_data = sfpd_obj.parse_sfp_dom_rev(qsfp_dom_rev_raw, 0)
            else:
                return None

            xcvr_dom_info_dict['temperature'] = dom_temperature_data['data']['Temperature']['value']
            xcvr_dom_info_dict['voltage'] = dom_voltage_data['data']['Vcc']['value']

            # The tx_power monitoring is only available on QSFP which compliant with SFF-8636
            # and claimed that it support tx_power with one indicator bit.
            dom_channel_monitor_data = {}
            qsfp_dom_rev = qsfp_dom_rev_data['data']['dom_rev']['value']
            qsfp_tx_power_support = qspf_dom_capability_data['data']['Tx_power_support']['value']
            if (qsfp_dom_rev[0:8] != 'SFF-8636' or (qsfp_dom_rev[0:8] == 'SFF-8636' and qsfp_tx_power_support != 'on')):
                dom_channel_monitor_raw = self.__read_eeprom_specific_bytes((offset + QSFP_CHANNL_MON_OFFSET), QSFP_CHANNL_MON_WIDTH)
                if dom_channel_monitor_raw is not None:
                    dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params(dom_channel_monitor_raw, 0)
                else:
                    return None

                xcvr_dom_info_dict['tx1power'] = 'N/A'
                xcvr_dom_info_dict['tx2power'] = 'N/A'
                xcvr_dom_info_dict['tx3power'] = 'N/A'
                xcvr_dom_info_dict['tx4power'] = 'N/A'
            else:
                dom_channel_monitor_raw = self.__read_eeprom_specific_bytes((offset + QSFP_CHANNL_MON_OFFSET), QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH)
                if dom_channel_monitor_raw is not None:
                    dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params_with_tx_power(dom_channel_monitor_raw, 0)
                else:
                    return None


                xcvr_dom_info_dict['tx1power'] = dom_channel_monitor_data['data']['TX1Power']['value']
                xcvr_dom_info_dict['tx2power'] = dom_channel_monitor_data['data']['TX2Power']['value']
                xcvr_dom_info_dict['tx3power'] = dom_channel_monitor_data['data']['TX3Power']['value']
                xcvr_dom_info_dict['tx4power'] = dom_channel_monitor_data['data']['TX4Power']['value']

            if dom_channel_monitor_raw:
                xcvr_dom_info_dict['temperature'] = dom_temperature_data['data']['Temperature']['value']
                xcvr_dom_info_dict['voltage'] = dom_voltage_data['data']['Vcc']['value']
                xcvr_dom_info_dict['rx1power'] = dom_channel_monitor_data['data']['RX1Power']['value']
                xcvr_dom_info_dict['rx2power'] = dom_channel_monitor_data['data']['RX2Power']['value']
                xcvr_dom_info_dict['rx3power'] = dom_channel_monitor_data['data']['RX3Power']['value']
                xcvr_dom_info_dict['rx4power'] = dom_channel_monitor_data['data']['RX4Power']['value']
                xcvr_dom_info_dict['tx1bias'] = dom_channel_monitor_data['data']['TX1Bias']['value']
                xcvr_dom_info_dict['tx2bias'] = dom_channel_monitor_data['data']['TX2Bias']['value']
                xcvr_dom_info_dict['tx3bias'] = dom_channel_monitor_data['data']['TX3Bias']['value']
                xcvr_dom_info_dict['tx4bias'] = dom_channel_monitor_data['data']['TX4Bias']['value']

        else:
            # SFPs
            offset = 256

            sfpd_obj = sff8472Dom()
            if sfpd_obj is None:
                return None

            dom_temperature_raw = self.__read_eeprom_specific_bytes( (offset + SFP_TEMPE_OFFSET), SFP_TEMPE_WIDTH)
            if dom_temperature_raw is not None:
                dom_temperature_data = sfpd_obj.parse_temperature(dom_temperature_raw, 0)
            else:
                return None

            dom_voltage_raw = self.__read_eeprom_specific_bytes( (offset + SFP_VOLT_OFFSET), SFP_VOLT_WIDTH)
            if dom_voltage_raw is not None:
                dom_voltage_data = sfpd_obj.parse_voltage(dom_voltage_raw, 0)
            else:
                return None

            dom_channel_monitor_raw = self.__read_eeprom_specific_bytes( (offset + SFP_CHANNL_MON_OFFSET), SFP_CHANNL_MON_WIDTH)
            if dom_channel_monitor_raw is not None:
                dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params(dom_channel_monitor_raw, 0)
            else:
                return None

            xcvr_dom_info_dict['temperature'] = dom_temperature_data['data']['Temperature']['value']
            xcvr_dom_info_dict['voltage'] = dom_voltage_data['data']['Vcc']['value']
            xcvr_dom_info_dict['rx1power'] = dom_channel_monitor_data['data']['RXPower']['value']
            xcvr_dom_info_dict['rx2power'] = 'N/A'
            xcvr_dom_info_dict['rx3power'] = 'N/A'
            xcvr_dom_info_dict['rx4power'] = 'N/A'
            xcvr_dom_info_dict['tx1bias'] = dom_channel_monitor_data['data']['TXBias']['value']
            xcvr_dom_info_dict['tx2bias'] = 'N/A'
            xcvr_dom_info_dict['tx3bias'] = 'N/A'
            xcvr_dom_info_dict['tx4bias'] = 'N/A'
            xcvr_dom_info_dict['tx1power'] = dom_channel_monitor_data['data']['TXPower']['value']
            xcvr_dom_info_dict['tx2power'] = 'N/A'
            xcvr_dom_info_dict['tx3power'] = 'N/A'
            xcvr_dom_info_dict['tx4power'] = 'N/A'

        xcvr_dom_info_dict['rx_los'] = self.get_rx_los()
        xcvr_dom_info_dict['tx_fault'] = self.get_tx_fault()
        xcvr_dom_info_dict['reset_status'] = self.get_reset_status()
        xcvr_dom_info_dict['lp_mode'] = self.get_lpmode()


        return xcvr_dom_info_dict

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
        # check present status
        if not self.get_presence():
            return None

        xcvr_dom_threshold_info_dict = dict.fromkeys(self.threshold_dict_keys, 'N/A')

        if self.is_osfp_port:
            # Below part is added to avoid fail xcvrd, shall be implemented later
            pass
        elif self.is_qsfp_port:
            # QSFPs
            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return None

            dom_thres_raw = self.__read_eeprom_specific_bytes(QSFP_MODULE_THRESHOLD_OFFSET, QSFP_MODULE_THRESHOLD_WIDTH)

            if dom_thres_raw:
                module_threshold_values = sfpd_obj.parse_module_threshold_values(
                    dom_thres_raw, 0)
                module_threshold_data = module_threshold_values.get('data')
                if module_threshold_data:
                    xcvr_dom_threshold_info_dict['temphighalarm'] = module_threshold_data['TempHighAlarm']['value']
                    xcvr_dom_threshold_info_dict['templowalarm'] = module_threshold_data['TempLowAlarm']['value']
                    xcvr_dom_threshold_info_dict['temphighwarning'] = module_threshold_data['TempHighWarning']['value']
                    xcvr_dom_threshold_info_dict['templowwarning'] = module_threshold_data['TempLowWarning']['value']
                    xcvr_dom_threshold_info_dict['vcchighalarm'] = module_threshold_data['VccHighAlarm']['value']
                    xcvr_dom_threshold_info_dict['vcclowalarm'] = module_threshold_data['VccLowAlarm']['value']
                    xcvr_dom_threshold_info_dict['vcchighwarning'] = module_threshold_data['VccHighWarning']['value']
                    xcvr_dom_threshold_info_dict['vcclowwarning'] = module_threshold_data['VccLowWarning']['value']

            dom_thres_raw = self.__read_eeprom_specific_bytes(QSFP_CHANNEL_THRESHOLD_OFFSET, QSFP_CHANNEL_THRESHOLD_WIDTH)
            if dom_thres_raw:
                channel_threshold_values = sfpd_obj.parse_channel_threshold_values(
                    dom_thres_raw, 0)
                channel_threshold_data = channel_threshold_values.get('data')
                if channel_threshold_data:
                    xcvr_dom_threshold_info_dict['rxpowerhighalarm'] = channel_threshold_data['RxPowerHighAlarm']['value']
                    xcvr_dom_threshold_info_dict['rxpowerlowalarm'] = channel_threshold_data['RxPowerLowAlarm']['value']
                    xcvr_dom_threshold_info_dict['rxpowerhighwarning'] = channel_threshold_data['RxPowerHighWarning']['value']
                    xcvr_dom_threshold_info_dict['rxpowerlowwarning'] = channel_threshold_data['RxPowerLowWarning']['value']
                    xcvr_dom_threshold_info_dict['txpowerhighalarm'] = "0.0dBm"
                    xcvr_dom_threshold_info_dict['txpowerlowalarm'] = "0.0dBm"
                    xcvr_dom_threshold_info_dict['txpowerhighwarning'] = "0.0dBm"
                    xcvr_dom_threshold_info_dict['txpowerlowwarning'] = "0.0dBm"
                    xcvr_dom_threshold_info_dict['txbiashighalarm'] = channel_threshold_data['TxBiasHighAlarm']['value']
                    xcvr_dom_threshold_info_dict['txbiaslowalarm'] = channel_threshold_data['TxBiasLowAlarm']['value']
                    xcvr_dom_threshold_info_dict['txbiashighwarning'] = channel_threshold_data['TxBiasHighWarning']['value']
                    xcvr_dom_threshold_info_dict['txbiaslowwarning'] = channel_threshold_data['TxBiasLowWarning']['value']

        else:
            # SFPs
            sfpd_obj = sff8472Dom()
            offset = 256
            eeprom_ifraw = self.__read_eeprom_specific_bytes(0, offset)
            sfpi_obj = sff8472InterfaceId(eeprom_ifraw)
            cal_type = sfpi_obj.get_calibration_type()
            sfpd_obj._calibration_type = cal_type

            dom_module_threshold_raw = self.__read_eeprom_specific_bytes(
                (offset + SFP_MODULE_THRESHOLD_OFFSET), SFP_MODULE_THRESHOLD_WIDTH)
            if dom_module_threshold_raw is not None:
                dom_module_threshold_data = sfpd_obj.parse_alarm_warning_threshold(
                    dom_module_threshold_raw, 0)

                xcvr_dom_threshold_info_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
                xcvr_dom_threshold_info_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
                xcvr_dom_threshold_info_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
                xcvr_dom_threshold_info_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
                xcvr_dom_threshold_info_dict['vcchighalarm'] = dom_module_threshold_data['data']['VoltageHighAlarm']['value']
                xcvr_dom_threshold_info_dict['vcclowalarm'] = dom_module_threshold_data['data']['VoltageLowAlarm']['value']
                xcvr_dom_threshold_info_dict['vcchighwarning'] = dom_module_threshold_data['data']['VoltageHighWarning']['value']
                xcvr_dom_threshold_info_dict['vcclowwarning'] = dom_module_threshold_data['data']['VoltageLowWarning']['value']
                xcvr_dom_threshold_info_dict['txbiashighalarm'] = dom_module_threshold_data['data']['BiasHighAlarm']['value']
                xcvr_dom_threshold_info_dict['txbiaslowalarm'] = dom_module_threshold_data['data']['BiasLowAlarm']['value']
                xcvr_dom_threshold_info_dict['txbiashighwarning'] = dom_module_threshold_data['data']['BiasHighWarning']['value']
                xcvr_dom_threshold_info_dict['txbiaslowwarning'] = dom_module_threshold_data['data']['BiasLowWarning']['value']
                xcvr_dom_threshold_info_dict['txpowerhighalarm'] = dom_module_threshold_data['data']['TXPowerHighAlarm']['value']
                xcvr_dom_threshold_info_dict['txpowerlowalarm'] = dom_module_threshold_data['data']['TXPowerLowAlarm']['value']
                xcvr_dom_threshold_info_dict['txpowerhighwarning'] = dom_module_threshold_data['data']['TXPowerHighWarning']['value']
                xcvr_dom_threshold_info_dict['txpowerlowwarning'] = dom_module_threshold_data['data']['TXPowerLowWarning']['value']
                xcvr_dom_threshold_info_dict['rxpowerhighalarm'] = dom_module_threshold_data['data']['RXPowerHighAlarm']['value']
                xcvr_dom_threshold_info_dict['rxpowerlowalarm'] = dom_module_threshold_data['data']['RXPowerLowAlarm']['value']
                xcvr_dom_threshold_info_dict['rxpowerhighwarning'] = dom_module_threshold_data['data']['RXPowerHighWarning']['value']
                xcvr_dom_threshold_info_dict['rxpowerlowwarning'] = dom_module_threshold_data['data']['RXPowerLowWarning']['value']



        return xcvr_dom_threshold_info_dict

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP

        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        cpld_index = (self.index / CPLD_PORT_NUM) + 1
        index = (self.index % CPLD_PORT_NUM) + 1
        if cpld_index == 5:
           # Not support reset for SFP+
           return True

        path = self.port_reset_path
        port_path = path.format(self.port_to_i2cbus_mapping[cpld_index], index)

        try:
            reg_file = open(port_path)
            reg_value = int(reg_file.readline().rstrip(), 16)

            reg_file.close()
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        return reg_value

    def get_rx_los(self):
        """
        Retrieves the RX LOS (lost-of-signal) status of SFP

        Returns:
            A Boolean, True if SFP has RX LOS, False if not.
            Note : RX LOS status is latched until a call to get_rx_los or a reset.
        """
        rx_los = None
        if not self.get_presence():
            return rx_los

        # read the values from EEPROM
        if self.is_osfp_port:
            pass
        elif self.is_qsfp_port:
            dom_channel_monitor_raw = self.__read_eeprom_specific_bytes(
                QSFP_CHANNL_RX_LOS_STATUS_OFFSET, QSFP_CHANNL_RX_LOS_STATUS_WIDTH) if self.get_presence() else None
            if dom_channel_monitor_raw is not None:
                rx_los_data = int(dom_channel_monitor_raw[0], 16)
                rx_los = True if ((rx_los_data & 0xF) == 0xF) else False
        else:
            # SFP ports
            status_control_raw = self.__read_eeprom_specific_bytes(
                SFP_STATUS_CONTROL_OFFSET, SFP_STATUS_CONTROL_WIDTH)
            if status_control_raw:
                data = int(status_control_raw[0], 16)
                rx_los = (sffbase().test_bit(data, 1) != 0)

        return rx_los

    def get_tx_fault(self):
        """
        Retrieves the TX fault status of SFP

        Returns:
            A Boolean, True if SFP has TX fault, False if not
            Note : TX fault status is lached until a call to get_tx_fault or a reset.
        """
        tx_fault = None
        if not self.get_presence():
            return tx_fault

        # read the values from EEPROM
        if self.is_osfp_port:
            pass
        elif self.is_qsfp_port:
            dom_channel_monitor_raw = self.__read_eeprom_specific_bytes(
                QSFP_CHANNL_TX_FAULT_STATUS_OFFSET, QSFP_CHANNL_TX_FAULT_STATUS_WIDTH) if self.get_presence() else None
            if dom_channel_monitor_raw is not None:
                tx_fault_data = int(dom_channel_monitor_raw[0], 16)
                tx_fault = True if ((tx_fault_data & 0xF) == 0xF) else False
        else:
            # SFP
            status_control_raw = self.__read_eeprom_specific_bytes(
                SFP_STATUS_CONTROL_OFFSET, SFP_STATUS_CONTROL_WIDTH)
            if status_control_raw:
                data = int(status_control_raw[0], 16)
                tx_fault = (sffbase().test_bit(data, 2) != 0)

        return tx_fault

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        index = (self.index % 8)
        i2c_index = (self.index / 8) + 1
        path = self.lpmode_path
        if i2c_index == 5:
            return False
        else:
            port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))

        try:
            reg_file = open(port_path)
            reg_value = int(reg_file.readline().rstrip(), 16)

            reg_file.close()
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        return reg_value

    def reset(self):
        """
        Reset SFP and return all user module settings to their default srate.
        Returns:
            A boolean, True if successful, False if not
        """
        cpld_index = (self.index / CPLD_PORT_NUM) + 1
        index = (self.index % CPLD_PORT_NUM) + 1
        if cpld_index == 5:
           # Not support reset for SFP+
           return True
        else:
            path = self.port_reset_path
        port_path = path.format(self.port_to_i2cbus_mapping[cpld_index], index)
          
        try:
            reg_file = open(port_path, 'w')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        # reset
        reg_file.write('1')

        time.sleep(1)

        reg_file.write('0')

        reg_file.close()
        return True

    def set_lpmode(self, lpmode):
        """
        Sets the lpmode (low power mode) of SFP
        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override
        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        index = (self.index % 8)
        i2c_index = (self.index / 8) + 1
        path = self.lpmode_path
        if i2c_index == 5:
            raise NotImplementedError
        else:
            port_path = path.format(self.port_to_i2cbus_mapping[i2c_index], (index + 1))

        try:
            reg_file = open(port_path, 'w')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        if lpmode == True:
            reg_file.write('1')
        else:
            reg_file.write('0')

        reg_file.close()
        return True