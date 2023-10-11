#!/usr/bin/env python
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 1
    PORT_END = 32
    QSFP_PORT_START = 1
    QSFP_PORT_END = 24

    EEPROM_OFFSET = 36
    PORT_INFO_PATH = '/sys/class/hq_fpga'

    _port_name = ""
    _port_to_eeprom_mapping = {}
    _port_to_i2cbus_mapping = {}
    _global_port_pres_dict = {}

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return list(range(self.QSFP_PORT_START, self.QSFP_PORT_END + 1))

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    @property
    def port_to_i2cbus_mapping(self):
        return self._port_to_i2cbus_mapping

    def get_port_name(self, port_num):
        if port_num in self.qsfp_ports:
            self._port_name = "QSFP" + str(port_num)
        else:
            self._port_name = "QSFPDD" + str(port_num)
        return self._port_name

    def init_global_port_presence(self):
        for port_num in range(self.port_start, (self.port_end + 1)):
            presence = self.get_presence(port_num)
            if(presence):
                self._global_port_pres_dict[port_num] = '1'
            else:
                self._global_port_pres_dict[port_num] = '0'
    
    # def get_eeprom_dom_raw(self, port_num):
    #     if port_num in self.qsfp_ports:
    #         # QSFP DOM EEPROM is also at addr 0x50 and thus also stored in eeprom_ifraw
    #         return None
    #     else:
    #         # Read dom eeprom at addr 0x51
    #         return self._read_eeprom_devid(port_num, self.DOM_EEPROM_ADDR, 256)

    def __init__(self):
        # Override port_to_eeprom_mapping for class initialization
        eeprom_path = '/sys/bus/i2c/devices/i2c-{0}/{0}-0050/eeprom'

        for x in range(self.PORT_START, self.PORT_END+1):
            self.port_to_i2cbus_mapping[x] = (x + self.EEPROM_OFFSET)
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                x + self.EEPROM_OFFSET)
        self.init_global_port_presence()

        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):

        # Check for invalid port_num
        if port_num not in list(range(self.port_start, self.port_end + 1)):
            return False

        # Get path for access port presence status
        port_name = self.get_port_name(port_num)
        reg_path = "/".join([self.PORT_INFO_PATH, port_name, "qsfp_modprs"])

        # Read status
        try:
            reg_file = open(reg_path)
            content = reg_file.readline().rstrip()
            reg_value = int(content)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        # Module present is active low
        if reg_value == 0:
            return True

        return False

    def get_low_power_mode(self, port_num):
        # Check for invalid QSFP port_num
        if port_num not in list(range(self.port_start, (self.port_end + 1))):
            return False

        try:
            port_name = self.get_port_name(port_num)
            reg_file = open(
                "/".join([self.PORT_INFO_PATH, port_name, "qsfp_lpmode"]), "r+")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        # Read status
        content = reg_file.readline().rstrip()
        reg_value = int(content, 16)
        # ModPrsL is active low
        if reg_value == 0:
            return False

        return True

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num not in list(range(self.port_start, (self.port_end + 1))):
            return False

        try:
            port_name = self.get_port_name(port_num)
            reg_file = open(
                "/".join([self.PORT_INFO_PATH, port_name, "qsfp_lpmode"]), "r+")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        content = hex(lpmode)

        reg_file.seek(0)
        reg_file.write(content)
        reg_file.close()

        return True

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num not in list(range(self.port_start, (self.port_end + 1))):
            return False

        try:
            port_name = self.get_port_name(port_num)
            reg_file = open(
                "/".join([self.PORT_INFO_PATH, port_name, "qsfp_reset"]), "w")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        # Convert our register value back to a hex string and write back
        reg_file.seek(0)
        reg_file.write(hex(0))
        reg_file.close()

        # Sleep 1 second to allow it to settle
        time.sleep(1)

        # Flip the bit back high and write back to the register to take port out of reset
        try:
            reg_file = open(
                "/".join([self.PORT_INFO_PATH, port_name, "qsfp_reset"]), "w")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_file.seek(0)
        reg_file.write(hex(1))
        reg_file.close()

        return True

    def get_transceiver_change_event(self, timeout=0):
        port_dict = {}
        sleep_time_ms = 500  # Poll interval, in milliseconds
        sleep_time = sleep_time_ms / 1000.0
        elapsed_time_ms = 0
        while True:
            for port_num in list(range(self.port_start, (self.port_end + 1))):
                presence = self.get_presence(port_num)
                if(presence and self._global_port_pres_dict[port_num] == '0'):
                    self._global_port_pres_dict[port_num] = '1'
                    port_dict[port_num] = '1'
                    print ("port {} presence"%port_num)
                elif(not presence and
                     self._global_port_pres_dict[port_num] == '1'):
                    self._global_port_pres_dict[port_num] = '0'
                    port_dict[port_num] = '0'
                    print ("port {} not presence"%port_num)

                if(len(port_dict) > 0):
                    break

            if len(port_dict) > 0:
                break
            if timeout != 0:
                elapsed_time_ms += sleep_time_ms
                if elapsed_time_ms > timeout:
                    break
            time.sleep(sleep_time)

        return True, port_dict

