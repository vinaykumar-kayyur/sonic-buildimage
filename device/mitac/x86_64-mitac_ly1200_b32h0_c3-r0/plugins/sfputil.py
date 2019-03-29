# sfputil.py
#
# Platform-specific SFP transceiver interface for SONiC
#

try:
    import subprocess
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 0
    PORT_END = 31
    PORTS_IN_BLOCK = 32

    EEPROM_OFFSET = 10
    # time period (sec) for querying transceivers
    QUERY_XCVR_PERIOD = 2

    pre_port_dict = {}
    _port_to_eeprom_mapping = {}

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return range(0, self.PORTS_IN_BLOCK + 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    @property
    def qry_xcvr_period(self):
        return self.QUERY_XCVR_PERIOD

    def __init__(self):
        eeprom_path = "/sys/class/i2c-adapter/i2c-{0}/{0}-0050/eeprom"

        for x in range(0, self.port_end + 1):
            self._port_to_eeprom_mapping[x] = eeprom_path.format(x + self.EEPROM_OFFSET)

        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        if port_num > 15:
            cpld_addr=33
            if port_num < 24:
                port_id="_17_24"
            else:
                port_id="_25_32"
        else:
            cpld_addr=32
            if port_num < 8:
               port_id="_1_8"
            else:
               port_id="_9_16"
     
        file_path="/sys/bus/i2c/devices/1-00" + str(cpld_addr) + "/port" + port_id  + "_present"
        try:
            reg_file = open(file_path)
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        content = reg_file.readline().rstrip()
        # content is a string containing the hex representation of the register
        reg_value = int(content, 16)
        port_num = port_num % 8

        # Mask off the bit corresponding to our port
        mask = (1 << port_num)

        # ModPrsL is active low
        if reg_value & mask == 0:
            return True

        return False

    def get_low_power_mode(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        if port_num > 15:
            cpld_addr=33
            if port_num < 24:
                port_id="_17_24"
            else:
                port_id="_25_32"
        else:
            cpld_addr=32
            if port_num < 8:
               port_id="_1_8"
            else:
               port_id="_9_16"
     
        file_path="/sys/bus/i2c/devices/1-00" + str(cpld_addr) + "/port" + port_id  + "_lpmode"

        try:
            reg_file = open(file_path)
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)

        content = reg_file.readline().rstrip()

        # content is a string containing the hex representation of the register
        reg_value = int(content, 16)
        port_num = port_num % 8

        # Mask off the bit corresponding to our por
        mask = (1 << port_num)

        # LPMode is active high
        if reg_value & mask == 0:
            return False

        return True

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        if port_num > 15:
            cpld_addr=33
            if port_num < 24:
                port_id="_17_24"
            else:
                port_id="_25_32"
        else:
            cpld_addr=32
            if port_num < 8:
               port_id="_1_8"
            else:
               port_id="_9_16"
     
        file_path="/sys/bus/i2c/devices/1-00" + str(cpld_addr) + "/port" + port_id  + "_lpmode"

        try:
            reg_file = open(file_path, "r+")
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False
        

        content = reg_file.readline().rstrip()

        # content is a string containing the hex representation of the register
        reg_value = int(content,16)

        # Mask off the bit corresponding to our port
        mask  = (1 << (port_num % 8)) 

        # LPMode is active high; set or clear the bit accordingly
        if lpmode is True:
            reg_value = reg_value | mask
        else:
            reg_value = reg_value & ~mask

        # Convert our register value back to a hex string and write back
        content = hex(reg_value)

        reg_file.seek(0)
        reg_file.write(content)
        reg_file.close()

        return True

    def reset(self, port_num):

        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        if port_num > 15:
            cpld_addr=33
            if port_num < 24:
                port_id="_17_24"
            else:
                port_id="_25_32"
        else:
            cpld_addr=32
            if port_num < 8:
               port_id="_1_8"
            else:
               port_id="_9_16"
     
        file_path="/sys/bus/i2c/devices/1-00" + str(cpld_addr) + "/port" + port_id  +  "_rst"

        try:
            reg_file = open(file_path, "r+")
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        content = reg_file.readline().rstrip()

        # content is a string containing the hex representation of the register
        reg_value = int(content,16)

        # Mask off the bit corresponding to our port
        mask = (1 << (port_num % 8)) 

        # ResetL is active low
        reg_value = reg_value & ~mask

        # Convert our register value back to a hex string and write back
        reg_file.seek(0)
        reg_file.write(hex(reg_value))
        reg_file.close()
       
        # Sleep 1 second to allow it to settle
        time.sleep(1)

        # Flip the bit back high and write back to the register to take port out of reset
        try:
            reg_file = open(file_path, "w+")
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False
        
        reg_value = reg_value | mask
        reg_file.seek(0)
        reg_file.write(hex(reg_value))
        reg_file.close()
 
        return True

    def get_data_not_ready(self ,port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        port = str(10+port_num)
        get_data_cmd = "sudo i2cget -f -y " +port+ " 0x50 0x02 b  2>/dev/null"
        try:
            get_data = subprocess.check_output(get_data_cmd, shell=True)
            data_not_ready = int( bin(int(get_data,16))[-1] )
        except:
            data_not_ready = 1
       
        return data_not_ready   
                
    def get_transceiver_change_event(self):
        
        port_dict = {}
        while True:
            # Get the status of ports
            for port in range(self.port_end + 1):
                presence = self.get_presence(port)
                not_rdy  = self.get_data_not_ready(port)
               
                if presence is True and not_rdy == 0:
                     #qsfp is inserted
                     port_dict[port] = '1'
                else:
                     #qsfp is removed
                     port_dict[port] = '0'

            if len(self.pre_port_dict) != 0:
                if cmp (self.pre_port_dict,port_dict) != 0:
                    self.pre_port_dict = port_dict.copy()
                    return True, port_dict
                
            self.pre_port_dict = port_dict.copy()
            time.sleep(self.qry_xcvr_period)
