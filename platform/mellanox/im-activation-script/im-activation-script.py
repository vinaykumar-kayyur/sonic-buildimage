#!/usr/bin/env python3
#
# Copyright (c) 2021-2022 NVIDIA CORPORATION & AFFILIATES.
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

import shutil
import click
import re
import os


class IMActivator:
    PARAMS = {
        "sai_profile": {
            "file_name": "sai.profile"
            "enabled_param": "SAI_INDEPENDENT_MODULE_MODE=1",
            "disabled_param": ""
        },
        "pmon_daemon_control": {
            "file_name": "pmon_daemon_control.json"
            "enabled_param": "\"skip_xcvrd_cmis_mgr\": false",
            "disabled_param": "\"skip_xcvrd_cmis_mgr\": true",
        },
        "sai_xml": {
            "file_name": "sai_<>.xml", # will be filled at main, since we can't know the sku here 
            "enabled_param": "<late-create-all-ports>1</late-create-all-ports>",
            "disabled_param": "<late-create-all-ports>1</late-create-all-ports>" # TODO: think about solution
        }
    }

    @staticmethod
    def disable_param(path):
        file_path = '{path}/{}'.format(PARAMS[param]["file_name"])
        lines = None
        with open(file_path, 'r') as param_file:
            lines = param_file.readlines()

        if lines:
            lines = re.sub(PARAMS[param]["enabled_param"],
                           PARAMS[param]["disabled_param"],
                           lines)
            
        with open(file_path, 'w') as param_file:
            param_file.write(lines)


    @staticmethod
    def parse_show_platform_summary():
        summary = subprocess.check_output(['show', 'platform', 'summary'])
        summary = summary.split('\n')

        for field in summary:
            key, value = field.split(": ")
            
            if key == 'Platform':
                platform = value

            elif key == 'HwSKU':
                sku = value

        return platform, sku


    @staticmethod
    def remove_im_file(file_path):
        if os.path.isfile(file_path):
            os.remove(file_path)


    @staticmethod
    def disable_im():
        platform, sku = parse_show_platform_summary()
        sku_path = '/usr/share/sonic/device/{0}/{1}'.format(platform, sku)
        platform_path = '/usr/share/sonic/device/{0}'.format(platform)
        im_sai_profile(sku_path, 'disable')
        skip_cmis_mgr(sku_path, 'disable')
        late_create(sku_path, 'disable')
        
        remove_im_file('{sku_path}/{}'.format('media_settings.json'))
        remove_im_file('{sku_path}/{}'.format('optics_si_setting.json'))
        remove_im_file('{platform_path}/{}'.format('media_setting.json'))
        remove_im_file('{platform_path}/{}'.format('optics_si_setting.json'))
        

@click.command()
@click.option('--disable', is_flag=True, help='Disable IM')
def main(disable):

    if disable:
        IMActivator.disable_im()

if __name__ == '__main__':
    main()