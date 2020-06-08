from natsort import natsorted
from swsssdk import SonicV2Connector
from .health_checker import checker, HealthChecker


class HardwareChecker(HealthChecker):
    CHASSIS_TABLE_NAME = 'CHASSIS_INFO'
    CHASSIS_KEY = '{}|chassis 1'.format(CHASSIS_TABLE_NAME)
    FAN_TABLE_NAME = 'FAN_INFO'
    PSU_TABLE_NAME = 'PSU_INFO'

    def __init__(self):
        HealthChecker.__init__(self)
        self._db = SonicV2Connector(host="127.0.0.1")
        self._db.connect(self._db.STATE_DB)

    def get_category(self):
        return 'Hardware'

    def check(self, config):
        self.reset()
        self._check_asic_status(config)
        self._check_fan_status(config)
        self._check_psu_status(config)

    def _check_asic_status(self, config):
        if config.ignore_devices and 'asic' in config.ignore_devices:
            return

        temperature = self._db.get(self._db.STATE_DB, HardwareChecker.CHASSIS_KEY, 'temp')
        temperature_threshold = self._db.get(self._db.STATE_DB, HardwareChecker.CHASSIS_KEY, 'temp_th')
        if not temperature:
            self._error_info['ASIC'] = 'Failed to get ASIC temperature'
        elif not temperature_threshold:
            self._error_info['ASIC'] = 'Failed to get ASIC temperature threshold'
        else:
            temperature = float(temperature)
            temperature_threshold = float(temperature_threshold)
            if temperature > temperature_threshold:
                self._error_info['ASIC'] = 'ASIC temperature is too hot, temperature={}, threshold={}'.format(temperature,
                                                                                                           temperature_threshold)

    def _check_fan_status(self, config):
        if config.ignore_devices and 'fan' in config.ignore_devices:
            return

        keys = self._db.keys(self._db.STATE_DB, HardwareChecker.FAN_TABLE_NAME + '*')
        if not keys:
            self._error_info['fan'] = 'Failed to get fan information'
            return

        for key in natsorted(keys):
            key_list = key.split('|')
            if len(key_list) != 2:  # error data in DB, log it and ignore
                self._error_info[key] = 'Invalid key for FAN_INFO: {}'.format(key)
                continue

            name = key_list[1]
            if config.ignore_devices and name in config.ignore_devices:
                continue
            data_dict = self._db.get_all(self._db.STATE_DB, key)
            presence = bool(data_dict['presence'])
            if not presence:
                self._error_info[name] = '{} is missing'.format(name)
                continue

            status = bool(data_dict['status'])
            if not status:
                self._error_info[name] = '{} is broken'.format(name)
                continue

            if not self._ignore_check(config.ignore_devices, 'fan', name, 'speed'):
                speed = data_dict.get('speed', None)
                speed_target = data_dict.get('speed_target', None)
                speed_tolerance = data_dict.get('speed_tolerance', None)
                if not speed:
                    self._error_info[name] = 'Failed to get actual speed data for {}'.format(name)
                elif not speed_target:
                    self._error_info[name] = 'Failed to get target speed date for {}'.format(name)
                elif not speed_tolerance:
                    self._error_info[name] = 'Failed to get speed tolerance for {}'.format(name)
                else:
                    speed = float(speed)
                    speed_target = float(speed_target)
                    speed_tolerance = float(speed_tolerance)
                    speed_min_th = speed_target * (1 - float(speed_tolerance) / 100)
                    speed_max_th = speed_target * (1 + float(speed_tolerance) / 100)
                    if speed < speed_min_th or speed > speed_max_th:
                        self._error_info[name] = '{} speed is out of range, speed={}, range=[{},{}]'.format(name, speed, speed_min_th, speed_max_th)

    def _check_psu_status(self, config):
        if config.ignore_devices and 'psu' in config.ignore_devices:
            return

        keys = self._db.keys(self._db.STATE_DB, HardwareChecker.PSU_TABLE_NAME + '*')
        if not keys:
            self._error_info['PSU'] = 'Failed to get PSU information'
            return

        for key in natsorted(keys):
            key_list = key.split('|')
            if len(key_list) != 2:  # error data in DB, log it and ignore
                self._error_info[key] = 'Invalid key for PSU_INFO: {}'.format(key)
                continue

            name = key_list[1]
            if config.ignore_devices and name in config.ignore_devices:
                continue

            data_dict = self._db.get_all(self._db.STATE_DB, key)
            presence = bool(data_dict['presence'])
            if not presence:
                self._error_info[name] = '{} is missing'.format(name)
                continue

            status = bool(data_dict['status'])
            if not status:
                self._error_info[name] = '{} is out of power'.format(name)
                continue

            if not self._ignore_check(config.ignore_devices, 'psu', name, 'temperature'):
                temperature = data_dict['temp']
                temperature_threshold = data_dict['temp_th']
                if temperature is None:
                    self._error_info[name] = 'Failed to get temperature data for {}'.format(name)
                elif temperature_threshold is None:
                    self._error_info[name] = 'Failed to get temperature threshold data for {}'.format(name)
                else:
                    temperature = float(temperature)
                    temperature_threshold = float(temperature_threshold)
                    if temperature > temperature_threshold:
                        self._error_info[name] = '{} temperature is too hot, temperature={}, threshold={}'.format(name, temperature,
                                                                                             temperature_threshold)

            if not self._ignore_check(config.ignore_devices, 'psu', name, 'voltage'):
                voltage = data_dict.get('voltage', None)
                voltage_min_th = data_dict.get('voltage_min_th', None)
                voltage_max_th = data_dict.get('voltage_max_th', None)
                if voltage is None:
                    self._error_info[name] = 'Failed to get voltage data for {}'.format(name)
                elif voltage_min_th is None:
                    self._error_info[name] = 'Failed to get voltage minimum threshold data for {}'.format(name)
                elif voltage_max_th is None:
                    self._error_info[name] = 'Failed to get voltage maximum threshold data for {}'.format(name)
                else:
                    voltage = float(voltage)
                    voltage_min_th = float(voltage_min_th)
                    voltage_max_th = float(voltage_max_th)
                    if voltage < voltage_min_th or voltage > voltage_max_th:
                        self._error_info[name] = '{} voltage is out of range, voltage={}, range=[{},{}]'.format(name, voltage, voltage_min_th,
                                                                                           voltage_max_th)

    def reset(self):
        self._error_info = {}

    @classmethod
    def _ignore_check(cls, ignore_set, category, object_name, check_point):
        if not ignore_set:
            return False

        if '{}.{}'.format(category, check_point) in ignore_set:
            return True
        elif '{}.{}'.format(object_name, check_point) in ignore_set:
            return True
        return False
