from sonic_py_common.task_base import ThreadTaskBase

from . import utils
from .device_data import DeviceDataManager


class CPUThermalControl(ThreadTaskBase):
    CPU_COOLING_STATE = '/var/run/hw-management/thermal/cooling2_cur_state'
    CPU_TEMP_FILE = '/var/run/hw-management/thermal/cpu_pack'
    MAX_COOLING_STATE = 10
    MIN_COOLING_STATE = 2
    INTERVAL = 3

    def __init__(self):
        super(CPUThermalControl, self).__init__()
        self.temp_low, self.temp_high = DeviceDataManager.get_cpu_thermal_threshold()

    def task_worker(self):
        last_temp = 0
        while not self.task_stopping_event.wait(self.INTERVAL):
            last_temp = self.run(last_temp)

    def run(self, last_temp):
        current_temp = self.read_cpu_temp()
        if current_temp < self.temp_low:
            self.set_cooling_state(self.MIN_COOLING_STATE)
        elif current_temp > self.temp_high:
            self.set_cooling_state(self.MAX_COOLING_STATE)
        else:
            cooling_state = self.get_cooling_state()
            if current_temp > last_temp:
                self.set_cooling_state(min(cooling_state + 1, self.MAX_COOLING_STATE))
            elif current_temp < last_temp:
                self.set_cooling_state(max(cooling_state - 1, self.MIN_COOLING_STATE))
        return current_temp

    def set_cooling_state(self, state):
        utils.write_file(self.CPU_COOLING_STATE, state, log_func=None)

    def get_cooling_state(self):
        return utils.read_int_from_file(self.CPU_COOLING_STATE, default=self.MAX_COOLING_STATE, log_func=None)

    def read_cpu_temp(self):
        cpu_temp = utils.read_int_from_file(self.CPU_TEMP_FILE, default=self.temp_high, log_func=None)
        return cpu_temp if cpu_temp <= 1000 else int(cpu_temp / 1000)
  