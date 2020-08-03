import os
import json
from sonic_py_common import device_info


class Config(object):
    DEFAULT_INTERVAL = 60
    DEFAULT_BOOTUP_TIMEOUT = 300
    DEFAULT_LED_CONFIG = {
        'fault': 'red',
        'normal': 'green',
        'booting': 'orange_blink'
    }
    GET_PLATFORM_CMD = 'sonic-cfggen -d -v DEVICE_METADATA.localhost.platform'
    CONFIG_FILE = 'system_health_monitoring_config.json'
    MONIT_CONFIG_FILE = '/etc/monit/monitrc'
    MONIT_START_DELAY_CONFIG = 'with start delay'

    def __init__(self):
        self.platform_name = device_info.get_platform()
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

                self.interval = self.config_data.get('polling_interval', Config.DEFAULT_INTERVAL)
                self.ignore_services = self._get_list_data('services_to_ignore')
                self.ignore_devices = self._get_list_data('devices_to_ignore')
                self.external_checkers = self._get_list_data('external_checkers')
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

    def get_bootup_timeout(self):
        if not os.path.exists(Config.MONIT_CONFIG_FILE):
            return self.DEFAULT_BOOTUP_TIMEOUT

        try:
            with open(Config.MONIT_CONFIG_FILE) as f:
                lines = f.readlines()
                for line in lines:
                    if not line:
                        continue

                    line = line.strip()
                    if not line:
                        continue

                    pos = line.find('#')
                    if pos == 0:
                        continue

                    line = line[:pos]
                    pos = line.find(Config.MONIT_START_DELAY_CONFIG)
                    if pos != -1:
                        return int(line[pos+len(Config.MONIT_START_DELAY_CONFIG):].strip())
        except Exception:
            return self.DEFAULT_BOOTUP_TIMEOUT

    def _get_list_data(self, key):
        if key in self.config_data:
            data = self.config_data[key]
            if isinstance(data, list):
                return set(data)
        return None
