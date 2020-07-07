import os
import json
import subprocess

from sonic_daemon_base.daemon_base import DaemonBase


class Common:

    DEVICE_PATH = '/usr/share/sonic/device/'
    CONFIG_DIR = 'sonic_platform_config'

    OUTPUT_SOURCE_IPMI = 'ipmitool'
    # OUTPUT_SOURCE_IPMI_RAW = 'ipmitool_raw'
    OUTPUT_SOURCE_GIVEN_LIST = 'value_list'
    OUTPUT_SOURCE_GIVEN_VALUE = 'value'

    SET_METHOD_IPMI = 'ipmitool'
    NULL_VAL = 'N/A'

    def __init__(self):
        (self.platform, self.hwsku) = DaemonBase().get_platform_and_hwsku()

    def _run_command(self, command):
        status = False
        result = ""
        try:
            proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            output = proc.communicate()[0]
            proc.wait()
            if not proc.returncode:
                status = True
                result = output.rstrip('\n')
        except:
            pass
        return status, result

    def _clean_input(self, input, config):
        cleaned_input = input

        ai = config.get('avaliable_input')
        if ai and input not in ai:
            raise ValueError("Invalid input")

        input_translator = config.get('input_translator')
        return eval(input_translator.format(input)) if input_translator else input

    def _clean_output(self, output, config):
        output_translator = config.get('output_translator')
        return eval(output_translator.format(output)) if output_translator else output

    def _ipmi_get(self, index, config):
        status, output = self._run_command(
            config['command'].format(config['argument'][index]))
        return output if status else NULL_VAL

    def _ipmi_set(self, index, config, input):
        arg = config['argument'][index].format(input)
        return self.run_command(config['command'].format(arg))

    # def get_ipmitool_raw_output(self, command):
    #     """
    #     Returns a list the elements of which are the individual bytes of
    #     ipmitool raw <cmd> command output.
    #     """
    #     status, result = self._run_command(command)
    #     return [int(i, 16) for i in result.split()] if status else None

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
        return os.path.join(DEVICE_PATH, self.platform, CONFIG_DIR, config_name)

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
        output = {
            self.OUTPUT_SOURCE_IPMI_GET: self._ipmi_get(index, config),
            self.OUTPUT_SOURCE_GIVEN_VALUE: config["value"],
            self.OUTPUT_SOURCE_GIVEN_LIST: config["value_list"][index]
        }.get(config.get('output_source'), default)

        return self._clean_output(output)

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
        cleaned_input = self._clean_input(input)
        return {
            self.SET_METHOD_IPMI: self._ipmi_set(index, config, cleaned_input)[0]
        }.get(config.get('set_method'), False)
