#!/usr/bin/env python

__author__ = 'BinbinXie'
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Development"

import requests
import re

try:
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    def __init__(self):
        PsuBase.__init__(self)
        self.psu_info_url = "http://240.1.1.1:8080/api/psu/info"

        self.psu_info_list = None

    def request_data(self):
        # Reqest data from BMC if not exist.
        if self.psu_info_list is None:
            psu_info_req = requests.get(self.psu_info_url)
            psu_info_json = psu_info_req.json()
            self.psu_info_list = psu_info_json.get('data')
        
        return self.psu_info_list

    def airflow_selector(self, pn):
        # Set airflow type
        airflow = "Unknown"
        return airflow

    def get_num_psus(self):
        """
        Retrieves the number of PSUs available on the device
        :return: An integer, the number of PSUs available on the device
        """

        num_psus = 2

        return num_psus

    def get_psu_status(self, index):
        """
        Retrieves the oprational status of power supply unit (PSU) defined
                by 1-based index <index>
        :param index: An integer, 1-based index of the PSU of which to query status
        :return: Boolean, True if PSU is operating properly, False if PSU is faulty
        """

        
        # init data
        psu_key = "PSU" + str(index)
        psu_status_key = "Status"
        psu_power_status = False

        try:
            # Request and validate sensor's information
            self.psu_info_list = self.request_data()
            # Get PSU power status.
            is_psu = self.psu_info_list.get(psu_key)
            
            outputs = is_psu.get("Outputs")
            psu_status = str(outputs.get(psu_status_key)).strip()
            if is_psu is not None and psu_status == "True":
                psu_power_status = True

        except:
            print("Error: Unable to access PSU power status")
            return False

        return psu_power_status

    def get_psu_presence(self, index):
        """
        Retrieves the presence status of power supply unit (PSU) defined
                by 1-based index <index>
        :param index: An integer, 1-based index of the PSU of which to query status
        :return: Boolean, True if PSU is plugged, False if not
        """
        # Init data
        psu_key = "PSU" + str(index)
        psu_presence_key = "Present"
        psu_presence_status = False
        
        try:
            # Request and validate sensor's information.
            #self.psu_status_list, self.psu_info_list = self.request_data()
            self.psu_info_list = self.request_data()
            
            is_psu = self.psu_info_list.get(psu_key)
            psu_status = str(is_psu.get(psu_presence_key)).strip()
            if is_psu is not None and psu_status == "yes":
                psu_presence_status = True
                
            # Get PSU present status.

        except:
            print("Error: Unable to access PSU presence status")
            return False

        return psu_presence_status

    def get_psu_sn(self, index):
        """
        Get the serial number of the psu,

        :param index: An integer, 1-based index of the PSU.
        :return: Serial number
        """
        serial_number = "N/A"
        psu_key = "PSU" + str(index)
        psu_sn_key = "SN"

        try:
            # Request and validate sensor's information.
            #self.psu_status_list, self.psu_info_list = self.request_data()
            self.psu_info_list = self.request_data()

            is_psu = self.psu_info_list.get(psu_key)
            psu_sn = str(is_psu.get(psu_sn_key)).strip()
            if is_psu is not None and psu_sn is not None:
                serial_number = psu_sn if psu_sn.strip() != "" else "N/A"

        except:
            return "N/A"

        return serial_number

    def get_psu_pn(self, index):
        """
        Get the product name of the psu

        :param index: An integer, 1-based index of the PSU.
        :return: Product name
        """
        product_name = "N/A"
        psu_key = "PSU" + str(index)
        psu_pn_key = "PN"

        try:
            # Request and validate sensor's information
            self.fru_status_list, self.psu_info_list = self.request_data()

            is_psu = self.psu_info_list.get(psu_key)
            psu_pn = str(is_psu.get(psu_pn_key)).strip()
            if is_psu is not None and psu_pn is not None:
                product_name = psu_pn if psu_pn.strip() != "" else "N/A"

        except:
            return "N/A"

        return product_name

    def get_all(self):
        """
            Number: mandatory, max number of PSU, integer
            PSU1, PSU2, ...: mandatory, PSU name, string
            Present: mandatory for each PSU, present status, boolean, True for present, False for NOT present
            PowerStatus: conditional, if PRESENT is True, power status of PSU,boolean, True for powered, False for NOT powered
            PN, conditional, if PRESENT is True, PN of the PSU, string
            SN, conditional, if PRESENT is True, SN of the PSU, string
        """

        # Init data
        all_psu_dict = dict()
        all_psu_dict["Number"] = self.get_num_psus()
        psu_sn_key_1 = "Serial Number"
        psu_sn_key_2 = "Product Serial"
        psu_pn_key = "Product Name"

        # Request and validate sensor's information.
        self.fru_status_list, self.psu_info_list = self.request_data()

        # Set PSU FRU data.
        psu_info_dict = dict()
        for psu_fru in self.psu_info_list:
            psu_data = dict()
            pn = psu_fru.get(psu_pn_key)
            sn = psu_fru.get(psu_sn_key_1) or psu_fru.get(psu_sn_key_2)
            psu_data["PN"] = "N/A" if not pn or str(
                pn).strip() == "" else str(pn).strip()
            psu_data["SN"] = "N/A" if not pn or str(
                pn).strip() == "" else str(sn).strip()

            fru_check = [psu_fru[v] for v in psu_fru.keys() if 'FRU Info' in v]
            non_fru_check = [v for v in psu_fru.keys() if 'PSU' in v]

            if len(non_fru_check) > 0:
                psu_idx = int(re.findall('\d+', non_fru_check[0])[0])
                psu_info_dict[psu_idx] = psu_data
            elif len(fru_check) > 0:
                psu_idx = int(re.findall('\d+', fru_check[0])[0])
                psu_info_dict[psu_idx] = psu_data

        # Set PSU status.
        for fru_status in self.fru_status_list:
            psu_status_dict = dict()
            find_psu = [v for v in fru_status.keys() if "PSU" in v]
            if len(find_psu) > 0:
                psu_idx = int(re.findall('\d+', find_psu[0])[0])
                psu_ps_status = True if str(fru_status.get(
                    "Present")).strip() == "Present" else False
                psu_pw_status = True if str(fru_status.get(
                    "Power Status")).strip() == "OK" else False
                psu_pw_type = str(fru_status.get(
                    "Power Type")).strip()
                ac_status = True if str(fru_status.get(
                    "AC Status")).strip().upper() == "OK" else False

                psu_status_dict["Present"] = psu_ps_status
                if psu_ps_status:
                    psu_status_dict["PowerStatus"] = psu_pw_status
                    psu_status_dict["PN"] = psu_info_dict[psu_idx]["PN"]
                    psu_status_dict["SN"] = psu_info_dict[psu_idx]["SN"]
                    psu_status_dict["InputType"] = psu_pw_type
                    psu_status_dict["InputStatus"] = True if psu_pw_status and psu_ps_status else False
                    psu_status_dict["OutputStatus"] = ac_status
                    psu_status_dict["AirFlow"] = self.airflow_selector(
                        psu_status_dict["PN"])
                all_psu_dict[find_psu[0]] = psu_status_dict

        return all_psu_dict
