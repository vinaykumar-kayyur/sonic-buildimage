#!/usr/bin/env python
#
# Copyright (C) 2019 Accton Technology Corporation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# ------------------------------------------------------------------
# HISTORY:
#    mm/dd/yyyy (A.D.)
#    11/13/2017: Polly Hsu, Create
#    05/08/2019: Roy Lee, changed for as5812-54x.
#    05/29/2019: Brandon Chuang, changed for as5835-54x.
#    06/11/2019: Brandon Chuang, changed for as5835-54t.
# ------------------------------------------------------------------

try:
    import os
    import sys, getopt
    import logging
    import logging.config
    import time  # this is only being used as part of the example
    import signal
    import glob
except ImportError as e:
    raise ImportError('%s - required module not found' % str(e))

# Deafults
VERSION = '1.0'
FUNCTION_NAME = 'accton_as7926_40xfb_monitor'

# Make a class we can use to capture stdout and sterr in the log
class accton_as7926_40xfb_monitor(object):

    CPU_CORE_1_IDX = 1  # 1_CPU_CORE_1_TEMP.
    CPU_CORE_2_IDX = 2  # 2_CPU_CORE_2_TEMP.
    CPU_CORE_3_IDX = 3  # 3_CPU_CORE_3_TEMP.
    CPU_CORE_4_IDX = 4  # 4_CPU_CORE_4_TEMP.
    CPU_CORE_5_IDX = 5  # 5_CPU_CORE_5_TEMP.
    CPU_CORE_6_IDX = 6  # 6_CPU_CORE_6_TEMP.
    CPU_CORE_7_IDX = 7  # 7_CPU_CORE_7_TEMP.
    CPU_CORE_8_IDX = 8  # 8_CPU_CORE_8_TEMP.
    CPU_CORE_NUM_MAX = CPU_CORE_8_IDX

    thermal_sysfspath ={
    CPU_CORE_1_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp2_input"],
    CPU_CORE_2_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp3_input"],
    CPU_CORE_3_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp4_input"],
    CPU_CORE_4_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp5_input"],
    CPU_CORE_5_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp6_input"],
    CPU_CORE_6_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp7_input"],
    CPU_CORE_7_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp8_input"],
    CPU_CORE_8_IDX: ["/sys/devices/platform/coretemp.0/hwmon/hwmon0/temp9_input"],
    }

    def __init__(self, log_file, log_level):
        """Needs a logger and a logger level."""
        # set up logging to file
        logging.basicConfig(
            filename=log_file,
            filemode='w',
            level=log_level,
            format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        # set up logging to console
        if log_level == logging.DEBUG:
            console = logging.StreamHandler()
            console.setLevel(log_level)
            formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)

        logging.debug('SET. logfile:%s / loglevel:%d', log_file, log_level)

    def get_thermal_to_device_path(self, thermal_num):
        return self.thermal_sysfspath[thermal_num][0]

    def _get_thermal_val(self, thermal_num):
        if thermal_num < self.CPU_CORE_1_IDX or thermal_num > self.CPU_CORE_NUM_MAX:
            logging.debug('GET. Parameter error. thermal_num, %d', thermal_num)
            return None

        device_path = self.get_thermal_to_device_path(thermal_num)
        if(os.path.isfile(device_path)):
            for filename in glob.glob(device_path):
                try:
                    val_file = open(filename, 'r')
                except IOError as e:
                    logging.error('GET. unable to open file: %s', str(e))
                    return None
            content = val_file.readline().rstrip()
            val_file.close()

            if content == '':
                logging.debug('GET. content is NULL. device_path:%s', device_path)
                return None

            return int(content)
        else:
            print "No such device_path=%s"%device_path
            return 0

    def manage_cpu_thermal(self):
        max_value = 0
        # Set CPU core temp to CPLD
        for id in self.thermal_sysfspath:
            value = self._get_thermal_val(id)

            if (id == 1):
                max_value = value
            elif (value > max_value):
                max_value = value

        device_path = "/sys/devices/platform/as7926_40xfb_thermal/temp1_input"
        try:
            val_file = open(device_path, 'w')
        except IOError as e:
            logging.error('GET. unable to open file: %s', str(e))
            return None

        val_file.write(str(int(max_value/1000)))
        val_file.close()

        return True

def handler(signum, frame):
        logging.debug('INFO:Cause signal %d, set fan speed max.', signum)
        sys.exit(0)

def main(argv):
    log_file = '%s.log' % FUNCTION_NAME
    log_level = logging.INFO
    if len(sys.argv) != 1:
        try:
            opts, args = getopt.getopt(argv,'hdl:',['lfile='])
        except getopt.GetoptError:
            print 'Usage: %s [-d] [-l <log_file>]' % sys.argv[0]
            return 0
        for opt, arg in opts:
            if opt == '-h':
                print 'Usage: %s [-d] [-l <log_file>]' % sys.argv[0]
                return 0
            elif opt in ('-d', '--debug'):
                log_level = logging.DEBUG
            elif opt in ('-l', '--lfile'):
                log_file = arg

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    monitor = accton_as7926_40xfb_monitor(log_file, log_level)

    # Loop forever, doing something useful hopefully:
    while True:
        monitor.manage_cpu_thermal()
        time.sleep(10)

if __name__ == '__main__':
    main(sys.argv[1:])