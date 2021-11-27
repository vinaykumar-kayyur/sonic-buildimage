#!/usr/bin/env python3
# 
###########################################################################
# config-chassis.py
# 
# Chassis preconfiguration service.
# This module provides preconfiguration service for chassis based system
# based on data provided by
# /use/share/sonic/devices/<platform>/chassis.yaml file
#
###########################################################################
# Copyright (c) 2021 Cisco Systems, Inc. and its affiliates.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###########################################################################

import argparse
import logging
import os.path
import subprocess
import yaml

ETC_HOSTS_FILE = '/etc/hosts'
HTTP_CONFIG_FILE = '/etc/sonic/http_config.yaml'

class ChassisConfig():
    def __init__(self, args, **kw):
        self.chassis_conf = None
        self.http_config = None
        if args.config_file:
            chassis_yaml = args.config_file
        else:
            # get chassis.yaml path based on platform type
            self.get_platform()
            chassis_yaml=os.path.join('/usr/share/sonic/device', self.platform, 'chassis.yaml')

        if os.path.isfile(chassis_yaml):
            with open(chassis_yaml) as f:
                self.chassis_conf = yaml.safe_load(f)

            # Extract http config
            self.http_config = self.chassis_conf.get('http_config')
        else:
            logger.info('chassis config file {} not present - skip config'.format(chassis_yaml))

    def get_platform(self):
        ''' Get the platform type from DEVICE_METADATA '''
        SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
        PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'

        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-H', '-v', PLATFORM_KEY],
                            stdout=subprocess.PIPE,
                            shell=False,
                            stderr=subprocess.STDOUT)
        outp = proc.communicate()[0]
        proc.wait()
        self.platform = outp.decode().rstrip('\n')

    def config_http(self):
        ''' Setup HTTP server configuration.
            if http_config is not none:
              if start_http_server is 'yes' or '1',
                 create HTTP_CONFIG_FILE file with the config. 
                 This file is a pre-requisite to run HTTP server service.
              if http_server_ip is not None, Set 'http-server' hostname with provided IP.
                HTTP server shall bind to this hostname.'''
        if self.http_config:
            start_http_server = self.http_config.get('start_http_server')
            if start_http_server == 'yes' or start_http_server == '1':
                # Create HTTP_CONFIG_FILE with http_config, generally on the Supervisor card.
                logger.info('start_http_server is set, creating {}'.format(HTTP_CONFIG_FILE))
                with open(HTTP_CONFIG_FILE, 'w') as f:
                    yaml.dump(self.http_config, f)
            http_server_ip = self.http_config.get('http_server_ip')
            if http_server_ip:
                # write 'httpd_server' hostname mapping in ETC_HOSTS_FILE if the hostname is not present
                logger.info('write http-server hostname entry to {}'.format(ETC_HOSTS_FILE))
                with open(ETC_HOSTS_FILE) as f:
                    if 'http-server' not in f.read():
                        etc_hosts_data = '{} {}\n'.format(self.http_config['http_server_ip'], 'http-server')
                        f = open(ETC_HOSTS_FILE, 'a')
                        f.write(etc_hosts_data)
        else:
            logger.info('http config is not available, skip server configuration.')

    def run(self):
        # HTTP config is provided, configure the service.
        self.config_http()

def main():
    parser = argparse.ArgumentParser(description='Chassis configuration service')
    parser.add_argument('--config-file', help='Chassis config yaml file', default=None)
    args = parser.parse_args()

    global logger
    logger = logging.getLogger(__name__)

    ChassisConfig(args).run()


if __name__ == '__main__':
    main()
