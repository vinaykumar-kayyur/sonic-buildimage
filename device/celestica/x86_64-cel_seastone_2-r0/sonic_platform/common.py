import os
import json
import subprocess

from sonic_daemon_base.daemon_base import DaemonBase


class Common:

    DEVICE_PATH = '/usr/share/sonic/device/'
    CONFIG_DIR = 'sonic_platform_config'

    OUTPUT_SOURCE_IPMI = 'ipmitool'
    OUTPUT_SOURCE_GIVEN_LIST = 'value_list'
    OUTPUT_SOURCE_GIVEN_VALUE = 'value'
    OUTPUT_SOURCE_SYSFS = 'sysfs_value'

    SET_METHOD_IPMI = 'ipmitool'
    NULL_VAL = 'N/A'

    def __init__(self):
        (self.platform, self.hwsku) = DaemonBase().get_platform_and_hwsku()

    def _run_command(self, command):
        status = False
        output = ""
        try:
            p = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                status, output = True, raw_data.strip()
        except:
            pass
        return status, output

    def _clean_input(self, input, config):
        cleaned_input = input

        ai = config.get('avaliable_input')
        if ai and input not in ai:
            return None

        input_translator = config.get('input_translator')
        if type(input_translator) is dict:
            input = input_translator.get(input)

        elif type(input_translator) is unicode:
            input = eval(input_translator.format(input))

        return input

    def _clean_output(self, index, output, config):
        output_translator = config.get('output_translator')

        if type(output_translator) is dict:
            output = output_translator.get(output)
        elif type(output_translator) is unicode:
            output = eval(output_translator.format(output))
        elif type(output_translator) is list:
            output = eval(output_translator[index].format(output))

        return output

    def _ipmi_get(self, index, config):
        argument = config.get('argument')
        cmd = config['command'].format(
            config['argument'][index]) if argument else config['command']
        status, output = self._run_command(cmd)
        return output if status else None

    def _sysfs_read(self,index,config):
        sysfs_path = config.get('sysfs_path')

        #### Remaining Design Warning : Check argument type
        argument = config['argument'][index].split(',')
        sysfs_path = sysfs_path.format(*argument)
        content = ""
        try:
            content = open(sysfs_path)
            content = content.readline().rstrip()
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False
        
        return content
    
    def _sysfs_write(self,index,config,input):
        sysfs_path = config.get('sysfs_path')
        #### Remaining Design Warning : Check argument type
        argument = config['argument'][index].split(',')
        sysfs_path = sysfs_path.format(*argument)
        #### Remaining Design Warning : Validate write_offset
        write_offset = int(config.get('write_offset'))
        output = ""
        try:
            open_file = open(sysfs_path,"r+")
            open_file.seek(write_offset)
            open_file.write(input)
            open_file.close()
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False , output
        return True , output

    def _ipmi_set(self, index, config, input):
        arg = config['argument'][index].format(input)
        return self._run_command(config['command'].format(arg))

    def load_json_file(self, path):
        """
        Retrieves the json object from json file path

        Returns:
            A json object
        """
        with open(path, 'r') as f:
            json_data = json.load(f)

        return json_data

    def get_config_path(self, config_name):
        """
        Retrieves the path to platform api config directory

        Args:
            config_name: A string containing the name of config file.

        Returns:
            A string containing the path to json file
        """
        return os.path.join(self.DEVICE_PATH, self.platform, self.CONFIG_DIR, config_name)

    def get_output(self, index, config, default):
        """
        Retrieves the output for each function base on config

        Args:
            index: An integer containing the index of device.
            config: A dict object containing the configuration of specified function.
            default: A string containing the default output of specified function.

        Returns:
            A string containing the output of specified function in config
        """
        output_source = config.get('output_source')

        if output_source == self.OUTPUT_SOURCE_IPMI:
            output = self._ipmi_get(index, config)

        elif output_source == self.OUTPUT_SOURCE_GIVEN_VALUE:
            output = config["value"]

        elif output_source == self.OUTPUT_SOURCE_GIVEN_LIST:
            output = config["value_list"][index]

        elif output_source == self.OUTPUT_SOURCE_SYSFS:
            output = self._sysfs_read(index,config)

        else:
            output = default

        return self._clean_output(index, output, config) or default

    def set_output(self, index, input, config):
        """
        Sets the output of specified function on config

        Args:
            config: A dict object containing the configuration of specified function.
            index: An integer containing the index of device.
            input: A string containing the input of specified function.

        Returns:
            bool: True if set function is successfully, False if not
        """
        cleaned_input = self._clean_input(input, config)
        if not cleaned_input:
            return False

        set_method = config.get('set_method')
        if set_method == self.SET_METHOD_IPMI:
            output = self._ipmi_set(index, config, cleaned_input)[0]
        elif set_method == self.OUTPUT_SOURCE_SYSFS:
            output = self._sysfs_write(index,config,cleaned_input)[0]
        else:
            output = False

        return output
