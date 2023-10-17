#
# Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES.
# Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from . import utils
from sonic_py_common import logger

import time

SFP_TEMPERATURE_SCALE = 1000
ASIC_TEMPERATURE_SCALE = 125
ASIC_DEFAULT_TEMP_WARNNING_THRESHOLD = 105000
ASIC_DEFAULT_TEMP_CRITICAL_THRESHOLD = 120000

TC_CONFIG_FILE = '/run/hw-management/config/tc_config.json'
logger = logger.Logger('thermal-updater')


class ThermalUpdater:
    def __init__(self, sfp_list):
        self._sfp_list = sfp_list
        self._sfp_status = {}
        self._timer = utils.Timer()

    def load_tc_config(self):
        asic_poll_interval = 1
        sfp_poll_interval = 10
        data = utils.load_json_file(TC_CONFIG_FILE)
        if not data:
            logger.log_notice(f'{TC_CONFIG_FILE} does not exist, use default polling interval')

        if data:
            dev_parameters = data.get('dev_parameters')
            if dev_parameters is not None:
                asic_parameter = dev_parameters.get('asic')
                if asic_parameter is not None:
                    asic_poll_interval_config = asic_parameter.get('poll_time')
                    if asic_poll_interval_config:
                        asic_poll_interval = int(asic_poll_interval_config) / 2
                module_parameter = dev_parameters.get('module\\d+')
                if module_parameter is not None:
                    sfp_poll_interval_config = module_parameter.get('poll_time')
                    if sfp_poll_interval_config:
                        sfp_poll_interval = int(sfp_poll_interval_config) / 2

        logger.log_notice(f'ASIC polling interval: {asic_poll_interval}')
        self._timer.schedule(asic_poll_interval, self.update_asic)
        logger.log_notice(f'Module polling interval: {sfp_poll_interval}')
        self._timer.schedule(sfp_poll_interval, self.update_module)

    def start(self):
        if not self.wait_all_sfp_ready():
            logger.log_error('Failed to wait for all SFP ready, will put hw-management-tc to suspend')
            self.control_tc(True)
            return
        self.control_tc(False)
        self.load_tc_config()
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.control_tc(True)

    def control_tc(self, suspend):
        logger.log_notice(f'Set hw-management-tc to {"suspend" if suspend else "resume"}')
        utils.write_file('/run/hw-management/config/suspend', 1 if suspend else 0)

    def wait_all_sfp_ready(self):
        logger.log_notice('Waiting for all SFP modules ready...')
        max_wait_time = 60
        ready_set = set()
        while len(ready_set) != len(self._sfp_list):
            for sfp in self._sfp_list:
                try:
                    sfp.is_sw_control()
                    ready_set.add(sfp)
                except:
                    continue
            max_wait_time -= 1
            if max_wait_time == 0:
                return False
            time.sleep(1)

        logger.log_notice('All SFP modules are ready')
        return True

    def get_asic_temp(self):
        temperature = utils.read_int_from_file('/sys/module/sx_core/asic0/temperature/input', default=None)
        return temperature * ASIC_TEMPERATURE_SCALE if temperature is not None else ASIC_DEFAULT_TEMP_WARNNING_THRESHOLD

    def get_asic_temp_warning_threashold(self):
        emergency = utils.read_int_from_file('/sys/module/sx_core/asic0/temperature/emergency', default=None, log_func=None)
        return emergency * ASIC_TEMPERATURE_SCALE if emergency is not None else ASIC_DEFAULT_TEMP_WARNNING_THRESHOLD

    def get_asic_temp_critical_threashold(self):
        critical = utils.read_int_from_file('/sys/module/sx_core/asic0/temperature/critical', default=None, log_func=None)
        return critical * ASIC_TEMPERATURE_SCALE if  critical is not None else ASIC_DEFAULT_TEMP_CRITICAL_THRESHOLD

    def update_single_module(self, sfp):
        try:
            presence = sfp.get_presence()
            pre_presence = self._sfp_status.get(sfp.sdk_index)
            if presence:
                temperature = sfp.get_temperature()
                if temperature == 0:
                    warning_thresh = 0
                    critical_thresh = 0
                else:
                    warning_thresh = sfp.get_temperature_warning_threashold()
                    critical_thresh = sfp.get_temperature_critical_threashold()

                self.set_thermal_data(sfp.sdk_index + 1, 'input', int(temperature * SFP_TEMPERATURE_SCALE))
                self.set_thermal_data(sfp.sdk_index + 1, 'emergency', int(warning_thresh * SFP_TEMPERATURE_SCALE))
                self.set_thermal_data(sfp.sdk_index + 1, 'crit', int(critical_thresh * SFP_TEMPERATURE_SCALE))
            else:
                if pre_presence != presence:
                    self.remove_thermal_data(sfp.sdk_index + 1, 'input')
                    self.remove_thermal_data(sfp.sdk_index + 1, 'emergency')
                    self.remove_thermal_data(sfp.sdk_index + 1, 'crit')

            if pre_presence != presence:
                self._sfp_status[sfp.sdk_index] = presence
        except Exception as e:
            logger.log_error('Failed to update module {sfp.sdk_index} thermal data - {e}')
            self.set_thermal_data(sfp.sdk_index + 1, 'input', 'invalid')

    def set_thermal_data(self, index, type, value):
        if index == 0:
            print(f'set ASIC {type} {value}')
        else:
            print(f'set module {index} {type} {value}')

    def remove_thermal_data(self, index, type):
        if index == 0:
            print(f'remove ASIC {type}')
        else:
            print(f'remove module {index} {type}')

    def update_module(self):
        for sfp in self._sfp_list:
            self.update_single_module(sfp)

    def update_asic(self):
        try:
            self.set_thermal_data(0, 'input', self.get_asic_temp())
            self.set_thermal_data(0, 'emergency', self.get_asic_temp_warning_threashold())
            self.set_thermal_data(0, 'crit', self.get_asic_temp_critical_threashold())
        except Exception as e:
            logger.log_error('Failed to update ASIC thermal data - {e}')
            self.set_thermal_data(0, 'input', 'invalid')
