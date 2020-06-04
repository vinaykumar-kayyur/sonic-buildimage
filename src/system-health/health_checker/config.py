import os
import json


class Config(object):
    DEFAULT_INTERVAL = 60

    def __init__(self):
        self._config_file = ''  # TODO: init
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

    def _reset(self):
        self._last_mtime = None
        self.interval = Config.DEFAULT_INTERVAL
        self.ignore_services = None
        self.ignore_devices = None
        self.external_checkers = None
