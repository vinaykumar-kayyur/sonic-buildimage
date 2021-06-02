# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase
    from sonic_sfp.sff8472 import sff8472InterfaceId
    from sonic_sfp.sff8436 import sff8436InterfaceId
    from sonic_sfp.sff8436 import sff8436Dom
    from sonic_sfp.sff8472 import sff8472Dom

except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""
    #SFP 1-48 ,QSFP 49-54
    PORT_START = 0
    PORT_END = 53
    QPORT_START = 48
    QPORT_END = 53

    EEPROM_OFFSET = 81

    CPLD_SWITCH = 0

    _port_to_eeprom_mapping = {}

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return range(self.QPORT_START, self.QPORT_END)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def __init__(self):
        eeprom_path = "/sys/bus/i2c/devices/{0}-0050/eeprom"

        for x in range(0, self.port_end + 1):
            self._port_to_eeprom_mapping[x] = eeprom_path.format(x + self.EEPROM_OFFSET)

        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False
        # Retrieve file path of presence
        port = (str(port_num + 1)).zfill(2)

        # SWPLD2 modprs for sfp port 1~32
        # SWPLD3 modprs for sfp port 33~48
        # SWPLD3 modprs for qsfp port 49~54
        if port_num  < 32:
            present_path = "SWPLD2/sfp_p{}_modprs".format(port)
        elif port_num < 48:
            present_path = "SWPLD3/sfp_p{}_modprs".format(port)
        else:
            present_path = "SWPLD3/qsfp_p{}_modprs".format(port)

        try:
            with open("/sys/devices/platform/delta-ag7648v2-swpld.0/" + present_path, 'r') as present:
                if int(present.readline()) == 0:
                    return True
        except IOError as e:
            print ("Error: unable to open file: %s" % str(e))
            return False

        return False

    def get_low_power_mode(self, port_num):
        # Check for invalid port_num
        if port_num < self.QPORT_START or port_num > self.QPORT_END:
            return False

        # Retrieve file path of presence
        port = (str(port_num + 1)).zfill(2)

        # SWPLD3 for port 49-54
        lpmode_path = "SWPLD3/qsfp_p{}_lpmode".format(port)

        try:
            with open("/sys/devices/platform/delta-ag7648v2-swpld.0/" + lpmode_path, 'r') as lpmode:
                if int(lpmode.readline()) == 1:
                    return True
        except IOError as e:
            print ("Error: unable to open file: %s" % str(e))
            return False

        return False

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num < self.QPORT_START or port_num > self.QPORT_END:
            return False

        # Retrieve file path of presence
        port = (str(port_num + 1)).zfill(2)

        # SWPLD3 for port 49-54
        lpmode_path = "SWPLD3/qsfp_p{}_lpmode".format(port)

        try:
            file = open("/sys/devices/platform/delta-ag7648v2-swpld.0/" + lpmode_path, 'r+')
        except IOError as e:
            print ("Error: unable to open file: %s" % str(e))
            return False

        file.seek(0)
        if lpmode is True:
            # "1" for lpmode on
            file.write('1')
        else:
            # "0" for lpmode off
            file.write('0')
        file.close()

        return True

    def reset(self, port_num):

        # Check for invalid port_num
        if port_num < self.QPORT_START or port_num > self.QPORT_END:
            return False

        # Retrieve file path of presence
        port = (str(port_num + 1)).zfill(2)

        # SWPLD3 for port 49-54
        reset_path = "SWPLD3/qsfp_p{}_rst".format(port)

        try:
            file = open("/sys/devices/platform/delta-ag7648v2-swpld.0/" + reset_path, 'r+')
        except IOError as e:
            print ("Error: unable to open file: %s" % str(e))
            return False

        file.seek(0)
        file.write('0')
        file.close()

        # Sleep 1 second to allow it to settle
        time.sleep(1)

        # Flip the bit back high and write back to the register to take port out of reset
        try:
            file = open("/sys/devices/platform/delta-ag7648v2-swpld.0/" + reset_path, 'r+')
        except IOError as e:
            print ("Error: unable to open file: %s" % str(e))
            return False

        file.seek(0)
        file.write('1')
        file.close()

        return True

    def get_eeprom_dict(self, port_num):
        sfp_data = {}

        eeprom_ifraw = self.get_eeprom_raw(port_num)
        eeprom_domraw = self.get_eeprom_dom_raw(port_num)

        if eeprom_ifraw is None:
            return None

        if port_num in self.osfp_ports:
            sfpi_obj = inf8628InterfaceId(eeprom_ifraw)
            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()
            return sfp_data
        elif port_num in self.qsfp_ports:
            sfpi_obj = sff8436InterfaceId(eeprom_ifraw)
            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()
            # For Qsfp's the dom data is part of eeprom_if_raw
            # The first 128 bytes

            sfpd_obj = sff8436Dom(eeprom_ifraw)
            if sfpd_obj is not None:
                sfp_data['dom'] = sfpd_obj.get_data_pretty()

            return sfp_data
        else:
            sfpi_obj = sff8472InterfaceId(eeprom_ifraw)
            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()
                cal_type = sfpi_obj.get_calibration_type()

            if eeprom_domraw is not None:
                sfpd_obj = sff8472Dom(eeprom_domraw, cal_type)
                if sfpd_obj is not None:
                    sfp_data['dom'] = sfpd_obj.get_data_pretty()

            return sfp_data

    def get_transceiver_change_event(self):
        """
        TODO: This function need to be implemented
        when decide to support monitoring SFP(Xcvrd)
        on this platform.
        """
        raise NotImplementedError