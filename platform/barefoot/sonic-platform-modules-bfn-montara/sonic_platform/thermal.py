try:
    import subprocess

    from sonic_platform.bfn_extensions.platform_sensors import platform_sensors_get
    from sonic_platform_base.thermal_base import ThermalBase
    from collections import namedtuple
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")


Threshold = namedtuple('Threshold', ['high_crit', 'high_err', 'high_warn',
                       'low_warn', 'low_err', 'low_crit'], defaults=[0]*6)


'''
data argument is in "sensors -A -u" format, example:
coretemp-isa-0000
Package id 0:
  temp1_input: 37.000
  temp1_max: 82.000
  temp1_crit: 104.000
  temp1_crit_alarm: 0.000
Core 0:
  temp2_input: 37.000
  ...
'''
def _sensors_chip_parsed(data: str):
    def kv(line):
        k, v, *_ = [t.strip(': ') for t in line.split(':') if t] + ['']
        return k, v

    chip, *data = data.strip().split('\n')
    chip = chip.strip(': ')

    sensors = []
    for line in data:
        if not line.startswith(' '):
            sensor_label = line.strip(': ')
            sensors.append((sensor_label, {}))
            continue

        if len(sensors) == 0:
            raise RuntimeError(f'invalid data to parse: {data}')

        attr, value = kv(line)
        sensor_label, sensor_data = sensors[-1]
        sensor_data.update({attr: value})

    return chip, dict(sensors)

'''
Example of returned dict:
{
    'coretemp-isa-0000': {
        'Core 1': { "temp1_input": 40, ...  },
        'Core 2': { ... }
    }
}
'''
def _sensors_get() -> dict:
    data = platform_sensors_get(['-A', '-u']) or ''
    data += subprocess.check_output("/usr/bin/sensors -A -u",
                shell=True, text=True)
    data = data.split('\n\n')
    data = [_sensors_chip_parsed(chip_data) for chip_data in data if chip_data]
    data = dict(data)
    return data

def _value_get(d: dict, key_prefix, key_suffix=''):
    for k, v in d.items():
        if k.startswith(key_prefix) and k.endswith(key_suffix):
            return v
    return None

# Thermal -> ThermalBase -> DeviceBase
class Thermal(ThermalBase):
    _thresholds = {
        "com_e_driver-i2c-4-33:memory-temp": Threshold(85.0, 80.75, 76.5),
        "com_e_driver-i2c-4-33:cpu-temp":    Threshold(105.0, 99.75, 94.5),
        "pfe1100-i2c-7-59:temp1":            Threshold(50.0, 47.5, 45.0),
        "pfe1100-i2c-7-59:temp2":            Threshold(90.0, 85.5, 81.0),
        "pfe1100-i2c-7-5a:temp1":            Threshold(50.0, 47.5, 45.0),
        "pfe1100-i2c-7-5a:temp2":            Threshold(90.0, 85.5, 81.0),
        "tmp75-i2c-3-48:outlet-middle-temp": Threshold(80.0, 76.0, 72.0),
        "tmp75-i2c-3-49:inlet-middle-temp":  Threshold(60.0, 57.0, 54.0),
        "tmp75-i2c-3-4a:inlet-left-temp":    Threshold(60.0, 57.0, 54.0),
        "tmp75-i2c-3-4b:switch-temp":        Threshold(105.0, 99.75, 94.5),
        "tmp75-i2c-3-4c:inlet-right-temp":   Threshold(60.0, 57.0, 54.0),
        "tmp75-i2c-8-48:outlet-right-temp":  Threshold(80.0, 76.0, 72.0),
        "tmp75-i2c-8-49:outlet-left-temp":   Threshold(80.0, 76.0, 72.0),
    }

    def __init__(self, chip, label):
        self.__chip = chip
        self.__label = label
        self.__name = f"{chip}:{label}".lower().replace(' ', '-')

    def __get(self, attr_prefix, attr_suffix):
        sensor_data = _sensors_get().get(self.__chip, {}).get(self.__label, {})
        value = _value_get(sensor_data, attr_prefix, attr_suffix)
        if value is not None: return value
        raise NotImplementedError

    # ThermalBase interface methods:
    def get_temperature(self) -> float:
        return float(self.__get('temp', 'input'))

    def get_high_warning_threshold(self) -> float:
        if self.get_name() in self._thresholds:
            return self._thresholds[self.get_name()].high_warn
        return float(self.__get('temp', 'max'))

    def get_high_threshold(self) -> float:
        if self.get_name() in self._thresholds:
            return self._thresholds[self.get_name()].high_err
        #cpu core case
        temp_warn = self.get_high_warning_threshold()
        temp_crit = self.get_high_critical_threshold()
        return (temp_warn + temp_crit) / 2

    def get_high_critical_threshold(self) -> float:
        if self.get_name() in self._thresholds:
            return self._thresholds[self.get_name()].high_crit
        return float(self.__get('temp', 'crit'))

    def get_low_warning_threshold(self) -> float:
        if self.get_name() in self._thresholds:
            return self._thresholds[self.get_name()].low_warn
        return 0

    def get_low_threshold(self) -> float:
        if self.get_name() in self._thresholds:
            return self._thresholds[self.get_name()].low_err
        return 0

    def get_low_critical_threshold(self) -> float:
        if self.get_name() in self._thresholds:
            return self._thresholds[self.get_name()].low_crit
        return 0

    # DeviceBase interface methods:
    def get_name(self):
        return self.__name

    def get_presence(self):
        return True

    def get_status(self):
        return True

def thermal_list_get():
    l = []
    for chip, chip_data in _sensors_get().items():
        for sensor, sensor_data in chip_data.items():
            # add only temperature sensors
            if _value_get(sensor_data, "temp") is not None:
                l.append(Thermal(chip, sensor))
    return l
