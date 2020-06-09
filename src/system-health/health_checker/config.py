import os
import json
from sonic_device_util import get_machine_info
from sonic_device_util import get_platform_info


class Config(object):
    DEFAULT_INTERVAL = 60
    DEFAULT_LED_CONFIG = {
        'fault': 'red',
        'normal': 'green',
    }
    GET_PLATFORM_CMD = 'sonic-cfggen -d -v DEVICE_METADATA.localhost.platform'
    CONFIG_FILE = 'system_health_monitoring_config.json'

    def __init__(self):
        mi = get_machine_info()
        if mi is not None:
            self.platform_name = get_platform_info(mi)
        else:
            self.platform_name = self._get_platform_name()
        self._config_file = os.path.join('/usr/share/sonic/device/', self.platform_name, Config.CONFIG_FILE) 
        self._last_mtime = None
        self.config_data = None
        self.interval = Config.DEFAULT_INTERVAL
        self.ignore_services = None
        self.ignore_devices = None
        self.external_checkers = None

    def load_config(self):
        if not os.path.exists(self._config_file):
            if self._last_mtime is not None:
                self._reset()
            return

        mtime = os.stat(self._config_file)
        if mtime != self._last_mtime:
            try:
                self._last_mtime = mtime
                with open(self._config_file, 'r') as f:
                    self.config_data = json.load(f)

                self.interval = self.config_data.get('interval', Config.DEFAULT_INTERVAL)
                if 'services_to_ignore' in self.config_data:
                    self.ignore_services = set(self.config_data['services_to_ignore'])
                if 'devices_to_ignore' in self.config_data:
                    self.ignore_devices = set(self.config_data['devices_to_ignore'])
                if 'external_checkers' in self.config_data:
                    self.external_checkers = set(self.config_data['external_checkers'])
            except Exception as e:
                self._reset()

    def _reset(self):
        self._last_mtime = None
        self.config_data = None
        self.interval = Config.DEFAULT_INTERVAL
        self.ignore_services = None
        self.ignore_devices = None
        self.external_checkers = None

    def get_led_color(self, status):
        if self.config_data and 'led_color' in self.config_data:
            if status in self.config_data['led_color']:
                return self.config_data['led_color'][status]
        
        return self.DEFAULT_LED_CONFIG[status]

    def _get_platform_name(self):
        from .utils import run_command
        output = run_command(Config.GET_PLATFORM_CMD)
        return output.strip()

