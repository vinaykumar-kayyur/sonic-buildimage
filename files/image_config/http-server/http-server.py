#!/usr/bin/env python3
# 
###########################################################################
# http-server.py
# 
# Python HTTP Server service.
# This service should run only when /etc/sonic/http_server.yaml file is
# available.
#
# http_server.yaml provides following parameters:
#     http_server_port: Port to bind to, default: 8000
#     http_server_dir:  HTTP server home directory path, default: /var/www/
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
import http.server
import logging
import socketserver
import yaml

from pathlib import Path

HTTP_DEFAULT_CONFIG_FILE = '/etc/sonic/http_config.yaml'
HTTP_DEFAULT_BIND_PORT = 8000
HTTP_DEFAULT_DIR_PATH = '/var/www'
http_dir = None

class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=http_dir, **kwargs)

class HttpServer():
    def __init__(self, args, **kw):
        self.http_config = None
        logger.info('HTTP Server config file:{}'.format(args.config_file))

        with open(args.config_file) as f:
            # Load http server config from config_file
            self.http_config = yaml.safe_load(f)
            # Get Server directory path from config
            global http_dir
            http_dir = self.http_config.get('http_server_dir', HTTP_DEFAULT_DIR_PATH)

            # Get Server port from config
            self.http_server_port = self.http_config.get('http_server_port', HTTP_DEFAULT_BIND_PORT)

            # Create HTTP home dir path if not present
            path = Path(http_dir)
            path.mkdir(parents=True, exist_ok=True)

    def run(self):
        if self.http_config:
            with socketserver.TCPServer(('http-server', self.http_server_port), HTTPRequestHandler) as httpd:
                logger.info('HTTP Server Port:{} home:{}'.format(self.http_server_port, http_dir))
                httpd.serve_forever()

def main():
    parser = argparse.ArgumentParser(description='Python3 HTTP Server')
    parser.add_argument('--config-file', help='HTTP Server config yaml file', default=HTTP_DEFAULT_CONFIG_FILE)
    args = parser.parse_args()

    global logger
    logger = logging.getLogger(__name__)

    HttpServer(args).run()

if __name__ == '__main__':
    main()
