#!/usr/bin/env python

#############################################################################
# Huaqin
#
# Module contains an implementation of SONiC Platform Base API and
# provides the psu status which are available in the platform
#
#############################################################################

__author__ = 'Vincent Meng'
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Development"

import urllib3
import re
import json

try:
    from sonic_platform_base.psu_base import PsuBase
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

PSU_NAME_LIST = ["PSU1", "PSU2"]
PSU_NUM_FAN = [1,1]

class Psu(PsuBase):
    """Platform-specific PSUutil class"""

    def __init__(self, PsuIndex):
        PsuBase.__init__(self)
        self.index = PsuIndex
        self.psu_url = "http://240.1.1.1:8080/api/psu/" + "psu" + str(self.index + 1)
        self.http = urllib3.PoolManager()

        self.psu_info = None
        for index in range(0, PSU_NUM_FAN[self.index]):
            fan = Fan(fan_index=index, is_psu_fan=True, psu_index=self.index)
            self._fan_list.append(fan)

    def request_data(self):
        # Reqest data from BMC if not exist.
        resp = self.http.request('GET', self.psu_url)
        if not resp:
            return None
        psu_info = resp.data.decode('utf-8')
        psu_json = json.loads(psu_info)
        if not psu_json or 'data' not in psu_json:
            return None

        self.psu_info = psu_json.get('data')
        
        return self.psu_info

    def airflow_selector(self, pn):
        # Set airflow type
        airflow = "Unknown"
        return airflow

    def get_name(self):
        """
        psu_n = "N/A"
        psu_key = "PSU" + str(self.index + 1)
        pn_key = "PN"
        print("psu name: %s" % psu_key)

        try:
            # Request and validate sensor's information.
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_n
            is_psu = self.psu_info.get(psu_key)
            if is_psu is None:
                return psu_n
            pn_temp = str(is_psu.get(pn_key))
            if pn_temp is not None:
                psu_n = pn_temp if pn_temp.strip() != "" else "N/A"

        except:
            print("Error: Unable to access PSU name")
            return "N/A"

        return psu_n
        """
        return PSU_NAME_LIST[self.index]

    def get_num_psus(self):
        """
        Retrieves the number of PSUs available on the device
        :return: An integer, the number of PSUs available on the device
        """

        num_psus = 2

        return num_psus

    def get_model(self):
        """
        Get the model of the psu,

        :param index: An integer, 1-based index of the PSU.
        :return: Model ID
        """
        modelid = "N/A"
        model_key = "ModelId"

        try:
            # Request and validate sensor's information.
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return modelid
            psu_model = str(self.psu_info.get(model_key))
            if psu_model is not None:
                modelid = psu_model if psu_model.strip() != "" else "N/A"

        except:
            print("Error: Unable to access PSU model")
            return "N/A"

        return modelid
                

    def get_status(self):
        """
        Retrieves the oprational status of power supply unit (PSU) defined
                by 1-based index <index>
        :param index: An integer, 1-based index of the PSU of which to query status
        :return: Boolean, True if PSU is operating properly, False if PSU is faulty
        """
        # init data
        status_key = "Status"
        psu_status = False

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return False
            # Get PSU power status.
            outputs = str(self.psu_info["Outputs"][status_key])
            inputs = str(self.psu_info["Inputs"][status_key])
            if "True" == outputs and "True" == inputs:
                psu_status = True

        except:
            print("Error: Unable to access PSU power status")
            return False

        return psu_status

    def get_presence(self):
        """
        Retrieves the presence status of power supply unit (PSU) defined
                by 1-based index <index>
        :param index: An integer, 1-based index of the PSU of which to query status
        :return: Boolean, True if PSU is plugged, False if not
        """
        # Init data
        presence_key = "Present"
        psu_presence = False
        
        try:
            # Request and validate sensor's information.
            #self.psu_status_list, self.psu_info = self.request_data()
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return False
            presence = str(self.psu_info.get(presence_key))
            if "yes" in presence:
                psu_presence = True
                
            # Get PSU present status.

        except:
            print("Error: Unable to access PSU presence status")
            return False

        return psu_presence

    def get_serial(self):
        """
        Get the serial number of the psu,

        :param index: An integer, 1-based index of the PSU.
        :return: Serial number
        """
        serial_number = "N/A"
        sn_key = "SN"

        try:
            # Request and validate sensor's information.
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return serial_number
            psu_sn = str(self.psu_info.get(sn_key))
            if psu_sn is not None:
                serial_number = psu_sn if psu_sn.strip() != "" else "N/A"

        except:
            print("Error: Unable to access PSU serial")
            return "N/A"

        return serial_number

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable
        """
        return True

    def get_voltage(self):
        """
        psu voltage output
        """
        # init data
        vout_key = "Voltage"
        psu_vout = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_vout 
            # Get PSU power status.
            outputs = self.psu_info.get("Outputs")
            if outputs is None:
                return psu_vout
            psu_vout = outputs[vout_key]["Value"]/1000

        except:
            print("Error: Unable to access PSU power status")
            return psu_vout
        return psu_vout

    def get_voltage_low_thershold(self):
        """
        psu voltage low threshold output
        """
        # init data
        vout_key = "Voltage"
        psu_lowvout = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_lowvout
            # Get PSU power status.
            outputs = self.psu_info.get("Outputs")
            if outputs is None:
                return psu_lowvout
            psu_lowvout = outputs[vout_key]["Min"]/1000

        except:
            print("Error: Unable to access PSU voltage low thershold")
            return psu_lowvout

        return psu_lowvout


    def get_voltage_high_thershold(self):
        """
        psu voltage high threshold output
        """
        # init data
        vout_key = "Voltage"
        psu_highvout = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_highvout
            # Get PSU power status.
            outputs = self.psu_info.get("Outputs")
            if outputs is None:
                return psu_highvout
            psu_highvout = outputs[vout_key]["Max"]/1000

        except:
            print("Error: Unable to access PSU voltage high thershold")
            return psu_highvout
            
        return psu_highvout


    def get_current(self):
        """
        psu current supplied
        """
        # init data
        iout_key = "Current"
        psu_iout = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_iout
            # Get PSU power status.
            
            outputs = self.psu_info.get("Outputs")
            if outputs is None:
                return psu_iout
            psu_iout = outputs[iout_key]["Value"]/1000

        except:
            print("Error: Unable to access PSU current")

            return psu_iout
        return psu_iout

    def get_input_voltage(self):
        """
        Retrieves intput current PSU voltage input

        Returns:
            A float number, the impu voltage in volts,
            e.g. 12.1
        """
        iput_key = "Voltage"
        psu_iput = 0.0
        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_iout
            # Get PSU power status.
            
            inputs = self.psu_info.get("Inputs")
            if inputs is None:
                return psu_iput
            psu_iput = inputs[iput_key]["Value"]/1000

        except:
            print("Error: Unable to access PSU input current")

            return psu_iput

        return psu_iput

    def get_input_current(self):
        """
        Retrieves intput current draw of the power supply

        Returns:
            A float number, the electric current in amperes,
            e.g. 15.4
        """
        iput_key = "Current"
        psu_iput = 0.0
        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_iout
            # Get PSU power status.
            
            inputs = self.psu_info.get("Inputs")
            if inputs is None:
                return psu_iput
            psu_iput = inputs[iput_key]["Value"]/1000

        except:
            print("Error: Unable to access PSU input current")

            return psu_iput

        return psu_iput

    def get_power(self):
        """
        psu power supplied
        """
        # init data
        pout_key = "Power"
        psu_pout = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_pout
            # Get PSU power status.
            outputs = self.psu_info.get("Outputs")
            if outputs is None:
                return psu_pout
            psu_pout = outputs[pout_key]["Value"]/1000000

        except:
            print("Error: Unable to access PSU power")
            return psu_pout
        
        return psu_pout
           
    def get_maximum_supplied_power(self):
        """
        psu maximum power supplied
        """
        # init data
        pout_key = "Power"
        psu_mpower = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_mpower
            # Get PSU power status.
            outputs = self.psu_info.get("Outputs")
            if outputs is None:
                return psu_mpower
            psu_mpower = outputs[pout_key]["Max"]/1000000

        except:
            print("Error: Unable to access PSU max supplied power")
            return psu_mpower
        
        return psu_mpower
           
    def get_powergood_status(self):
        """
        Retieves the powergood status of psu
        """

        return self.get_status()


    def get_temperature(self):
        """
        psu temperature 
        """
        
        # init data
        temp_key = "Temperature"
        psu_temp = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_temp
            # Get PSU power status.
            temp = self.psu_info[temp_key]
            if temp is None:
                return psu_temp

            temp1 = temp['TEMP1']["Value"]/1000
            temp2 = temp['TEMP2']["Value"]/1000
            temp3 = temp['TEMP3']['Value']/1000

            psu_temp = (temp1 + temp2 + temp3)/3

        except:
            print("Error: Unable to access PSU temperature")
            return psu_temp
        
        return psu_temp

    def get_temperature_high_threshold(self):
        """
        psu temperature 
        """
        
        # init data
        temp_key = "Temperature"
        psu_mtemp = 0.0

        try:
            # Request and validate sensor's information
            self.psu_info = self.request_data()
            if self.psu_info is None:
                return psu_mtemp
            # Get PSU power status.
            temp = self.psu_info[temp_key]
            if temp is None:
                return psu_mtemp
            
            psu_mtemp = temp['TEMP1']["Max"]/1000

        except:
            print("Error: Unable to access PSU temperature high threshold")
            return psu_mtemp
        
        return psu_mtemp

    def get_num_fans(self):
        """
        Retrieves the number of fan modules available on this PSU
            
        Returns:
            An integer, the number of fan modules available on this PSU
        """
        return len(self._fan_list)

    def get_all_fans(self):
        """
        Retrieves all fan modules available on this PSU
                                         
        Returns:
            A list of objects derived from FanBase representing all fan
            modules available on this PSU
        """
        return self._fan_list

    def get_fan(self, index):
        """
        Retrieves fan module represented by (0-based) index <index>
        
        Args:
            index: An integer, the index (0-based) of the fan module to
            retrieve
        
        Returns:
            An object dervied from FanBase representing the specified fan  
            module
        """
        fan = None
        try:
            fan = self._fan_list[index]
        except IndexError:
            sys.stderr.write("Fan index {} out of range (0-{})\n".format(index, len(self._fan_list)-1))
            
        return fan
