#!/usr/bin/env python

import os
import re
import json
import struct
import subprocess
from sonic_daemon_base.daemon_base import DaemonBase
from mmap import *

# HOST_CHK_CMD = "docker > /dev/null 2>&1"
# EMPTY_STRING = ""

CONFIG_PATH = '/usr/share/sonic/device/{}/sonic_platform_config'


class Common:

    NULL_VAL = 'N/A'

    OPER_IMPI = 'ipmi'
    OPER_FIXED_LIST = 'fixed_list'
    OPER_FIXED = 'fixed'

    def __init__(self):

        (self.platform, self.hwsku) = DaemonBase().get_platform_and_hwsku()

    def get_config_path(self):
        return CONFIG_PATH.format(self.platform)

    def load_json_file(self, path):
        json_data = {}
        try:
            json_data = json.load(open(path))
        except IOError:
            pass
        return json_data

    def run_command(self, cmd):
        status = False
        result = ""
        try:
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                status, result = True, raw_data.strip()
        except Exception as e:
            print(e)
            status = False
        return status, result

    def get_val(self, index, config, default_val):
        ret_val = default_val

        if config.get('oper_type') == Common.OPER_IMPI:
            status, result = self.ipmi_get(index, config)
            ret_val = result if status else ret_val
        elif config.get('oper_type') == Common.OPER_FIXED:
            ret_val = config["value"]
        elif config.get('oper_type') == Common.OPER_FIXED_LIST:
            ret_val = config["value"][index]

        return ret_val

    def set_val(self, index, input, config):
        ret_val = False
        if config.get('oper_type') == Common.OPER_IMPI:
            transformed_input = eval(config['input_transform'].format(input))
            ret_val, result = self.ipmi_set(index, transformed_input, config)
        return ret_val

    def ipmi_get(self, index, config):
        cmd = config['command'][index]
        full_cmd = config['command_template'].format(config['command'][index])
        status, result = self.run_command(full_cmd)
        if config.get('output_transform'):
            ret_val = config['output_transform'].get(
                result, config['default_output'])
        elif config.get('output_formula'):
            ret_val = eval(config['output_formula'][index].format(result))
        else:
            ret_val = eval(config['formula'].format(result))
        return status, ret_val

    def ipmi_set(self, index, input, config):
        cmd = config['command'][index].format(input)
        full_cmd = config['command_template'].format(cmd)
        status, ret_val = self.run_command(full_cmd)
        return status, ret_val

    # def is_host(self):
    #     return os.system(HOST_CHK_CMD) == 0

    # def pci_get_value(self, resource, offset):
    #     status = True
    #     result = ""
    #     try:
    #         fd = os.open(resource, os.O_RDWR)
    #         mm = mmap(fd, 0)
    #         mm.seek(int(offset))
    #         read_data_stream = mm.read(4)
    #         result = struct.unpack('I', read_data_stream)
    #     except:
    #         status = False
    #     return status, result

    # def run_interactive_command(self, cmd):
    #     try:
    #         os.system(cmd)
    #     except:
    #         return False
    #     return True

    # def read_txt_file(self, file_path):
    #     try:
    #         with open(file_path, 'r') as fd:
    #             data = fd.read()
    #             return data.strip()
    #     except IOError:
    #         pass
    #     return None

    # def read_one_line_file(self, file_path):
    #     try:
    #         with open(file_path, 'r') as fd:
    #             data = fd.readline()
    #             return data.strip()
    #     except IOError:
    #         pass
    #     return None

    # def ipmi_raw(self, netfn, cmd):
    #     status = True
    #     result = ""
    #     try:
    #         cmd = "ipmitool raw {} {}".format(str(netfn), str(cmd))
    #         p = subprocess.Popen(
    #             cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         raw_data, err = p.communicate()
    #         if err == '':
    #             result = raw_data.strip()
    #         else:
    #             status = False
    #     except:
    #         status = False
    #     return status, result

    # def ipmi_fru_id(self, id, key=None):
    #     status = True
    #     result = ""
    #     try:
    #         cmd = "ipmitool fru print {}".format(str(
    #             id)) if not key else "ipmitool fru print {0} | grep '{1}' ".format(str(id), str(key))

    #         p = subprocess.Popen(
    #             cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         raw_data, err = p.communicate()
    #         if err == '':
    #             result = raw_data.strip()
    #         else:
    #             status = False
    #     except:
    #         status = False
    #     return status, result

    # def ipmi_set_ss_thres(self, id, threshold_key, value):
    #     status = True
    #     result = ""
    #     try:
    #         cmd = "ipmitool sensor thresh '{}' {} {}".format(
    #             str(id), str(threshold_key), str(value))
    #         p = subprocess.Popen(
    #             cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         raw_data, err = p.communicate()
    #         if err == '':
    #             result = raw_data.strip()
    #         else:
    #             status = False
    #     except:
    #         status = False
    #     return status, result
