from natsort import natsorted
from swsssdk import SonicV2Connector
from .health_checker import checker, HealthChecker


@checker()
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
        if 'asic' in config.ignore_devices:
            return

        temperature = self._db.get(self._db.STATE_DB, HardwareChecker.CHASSIS_KEY, 'temperature')
        temperature_threshold = self._db.get(self._db.STATE_DB, HardwareChecker.CHASSIS_KEY, 'temperature_threshold')
        if not temperature:
            self._error_list.append('Failed to get ASIC temperature')
        elif not temperature_threshold:
            self._error_list.append('Failed to get ASIC temperature threshold')
        else:
            temperature = float(temperature)
            temperature_threshold = float(temperature_threshold)
            if temperature > temperature_threshold:
                self._error_list.append('ASIC temperature is too hot, temperature={}, threshold={}'.format(temperature,
                                                                                                           temperature_threshold))

    def _check_fan_status(self, config):
        if 'fan' in config.ignore_devices:
            return

        keys = self._db.keys(self._db.STATE_DB, HardwareChecker.FAN_TABLE_NAME + '*')
        if not keys:
            self._error_list.append('Failed to get fan information')
            return

        for key in natsorted(keys):
            key_list = key.split('|')
            if len(key_list) != 2:  # error data in DB, log it and ignore
                self._error_list.append('Invalid key for FAN_INFO: {}'.format(key))
                continue

            name = key_list[1]
            if name in config.ignore_devices:
                continue
            data_dict = self._db.get_all(self._db.STATE_DB, key)
            presence = bool(data_dict['presence'])
            if not presence:
                self._error_list.append('{} is missing'.format(name))
                continue

            status = bool(data_dict['status'])
            if not status:
                self._error_list.append('{} is broken'.format(name))
                continue

            if not self._ignore_check(config.ignore_devices, 'fan', name, 'speed'):
                speed = data_dict['speed']
                speed_threshold = data_dict['target_speed']
                if not speed:
                    self._error_list.append('Failed to get speed data for {}'.format(name))
                elif not speed_threshold:
                    self._error_list.append('Failed to get speed threshold for {}'.format(name))
                else:
                    speed = float(speed)
                    thresholds = speed_threshold.split(',')
                    min_speed = float(thresholds[0])
                    max_speed = float(thresholds[1])
                    if speed < min_speed or speed > max_speed:
                        self._error_list.append(
                            '{} speed is out of range, speed={}, range=[{},{}]'.format(name, speed, min_speed, max_speed))

    def _check_psu_status(self, config):
        if 'psu' in config.ignore_devices:
            return

        keys = self._db.keys(self._db.STATE_DB, HardwareChecker.PSU_TABLE_NAME + '*')
        if not keys:
            self._error_list.append('Failed to get PSU information')
            return

        for key in natsorted(keys):
            key_list = key.split('|')
            if len(key_list) != 2:  # error data in DB, log it and ignore
                self._error_list.append('Invalid key for PSU_INFO: {}'.format(key))
                continue

            name = key_list[1]
            if name in config.ignore_devices:
                continue

            data_dict = self._db.get_all(self._db.STATE_DB, key)
            presence = bool(data_dict['presence'])
            if not presence:
                self._error_list.append('{} is missing'.format(name))
                continue

            status = bool(data_dict['status'])
            if not status:
                self._error_list.append('{} is out of power'.format(name))
                continue

            if not self._ignore_check(config.ignore_devices, 'psu', name, 'temperature'):
                temperature = data_dict['temperature']
                temperature_threshold = data_dict['temperature_threshold']
                if temperature is None:
                    self._error_list.append('Failed to get temperature data for {}'.format(name))
                elif temperature_threshold is None:
                    self._error_list.append('Failed to get temperature threshold data for {}'.format(name))
                else:
                    temperature = float(temperature)
                    temperature_threshold = float(temperature_threshold)
                    if temperature > temperature_threshold:
                        self._error_list.append(
                            '{} temperature is too hot, temperature={}, threshold={}'.format(name, temperature,
                                                                                             temperature_threshold))
            if not self._ignore_check(config.ignore_devices, 'psu', name, 'voltage'):
                voltage = data_dict['voltage']
                voltage_threshold = data_dict['voltage_threshold']
                if voltage is None:
                    self._error_list.append('Failed to get voltage data for {}'.format(name))
                elif voltage_threshold is None:
                    self._error_list.append('Failed to get voltage threshold data for {}'.format(name))
                else:
                    voltage = float(voltage)
                    thresholds = voltage_threshold.split(',')
                    min_voltage = float(thresholds[0])
                    max_voltage = float(thresholds[1])
                    if voltage < min_voltage or voltage > max_voltage:
                        self._error_list.append(
                            '{} voltage is out of range, voltage={}, range=[{},{}]'.format(name, voltage, min_voltage,
                                                                                           max_voltage))

    def reset(self):
        self._error_list = []

    @classmethod
    def _ignore_check(cls, ignore_set, category, object_name, check_point):
        if not ignore_set:
            return False

        if '{}.{}'.format(category, check_point) in ignore_set:
            return True
        elif '{}.{}'.format(object_name, check_point) in ignore_set:
            return True
        return False
