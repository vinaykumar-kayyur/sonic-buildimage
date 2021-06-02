import os.path

try:
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    def __init__(self):
        PsuBase.__init__(self)
        self.Base_bus_number = 5
        self.psu_path = "/sys/bus/i2c/devices/{}-0058/"
        self.psu_oper_status = "in1_input"
        self.psu_oper_status2 = "in2_input"
        self.psu_presence = "i2cget -y {} 0x50 0x00"
        self.psu_mfr_model = "psu_mfr_model"
        self.psu_mfr_serial = "psu_mfr_serial"
        self.psu_mfr_id = "psu_mfr_id"
        self.psu_output_vol="in2_input"
        self.psu_output_curr="curr2_input"
        self.psu_output_power="power2_input"
        self.psu_fan_rpm="fan1_input"

    def get_num_psus(self):
        """
        Retrieves the number of PSUs available on the device

        :return: An integer, the number of PSUs available on the device
        """
        return 2

    def get_psu_status(self, index):
        if index is None:
            return False
        status = 0
        #index from 1, psu attribute bus from 40
        try:
            with open(self.psu_path.format(index + self.Base_bus_number) + self.psu_oper_status, 'r') as power_status:
                if int(power_status.read()) == 0 :
                    return False
                else:
                    with open(self.psu_path.format(index + self.Base_bus_number) + self.psu_oper_status2, 'r') as power_status2:
                        if int(power_status2.read()) == 0 :
                            return False
                        else:
                            status = 1
        except IOError:
            return False
        return status == 1

    def get_psu_presence(self, index):
        if index is None:
            return False
        status = 0
        try:
            p = os.popen(self.psu_presence.format(index + self.Base_bus_number)+ "> /dev/null 2>&1")
            if p.readline() != None:
                status = 1
            p.close()
        except IOError:
            return False
        return status == 1

    def _read_file(self,file_path, file_pattern, index=0):
        return_value = 0
        try:
            with open(os.path.join(file_path.format(index+5), file_pattern), 'r') as file_to_read:
            #with open(os.path.join(file_path.format(index), file_pattern), 'r') as file_to_read:
                return_value = (file_to_read.read())
        except IOError:
            log_err("Read file {} failed".format(self.fan_path + file_pattern.format(index)))
            return return_value
        return return_value

    def get_model(self, index):
        model = self._read_file(self.psu_path,self.psu_mfr_model, index)
        return model

    def get_mfr_id(self, index):
        return

    def get_serial(self, index):
        serial = self._read_file(self.psu_path,self.psu_mfr_serial, index)
        return serial

    def get_output_voltage(self, index):
        val = int(self._read_file(self.psu_path,self.psu_output_vol, index))
        voltage =  val/1000
        return voltage

    def get_output_current(self, index):
        val = int(self._read_file(self.psu_path,self.psu_output_curr, index))
        current = val/100
        return current

    def get_output_power(self, index):
        val = int( self._read_file(self.psu_path,self.psu_output_power, index))
        power = val/1000000
        return power

    def get_fan_rpm(self, index, fan_idx):
        rpm = self._read_file(self.psu_path,self.psu_fan_rpm, index)
        return rpm

    def get_direction(self,index):
        return "N/a"