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
    import sys, getopt
    import logging
    import logging.config
    import time  # this is only being used as part of the example
    import signal
except ImportError as e:
    raise ImportError('%s - required module not found' % str(e))

# Deafults
VERSION = '1.0'
FUNCTION_NAME = 'accton_as7535_32xb_monitor'

# Make a class we can use to capture stdout and sterr in the log
class accton_as7535_32xb_monitor(object):

    LM75_1_IDX = 1  # LM75_1_TEMP.
    LM75_2_IDX = 2  # LM75_2_TEMP.
    LM75_3_IDX = 3  # LM75_3_TEMP.
    LM75_4_IDX = 4  # LM75_4_TEMP.
    LM75_5_IDX = 5  # LM75_5_TEMP.
    LM75_6_IDX = 6  # LM75_6_TEMP.
    LM75_7_IDX = 7  # LM75_7_TEMP.
    LM75_8_IDX = 8  # LM75_8_TEMP.
    LM75_9_IDX = 9  # LM75_9_TEMP.
    LM75_10_IDX = 10 # LM75_10_TEMP.
    LM75_NUM_MAX = LM75_10_IDX

    thermal_sysfspath ={
    LM75_1_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp1_input"],
    LM75_2_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp2_input"],
    LM75_3_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp4_input"],
    LM75_4_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp5_input"],
    LM75_5_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp6_input"],
    LM75_6_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp7_input"],
    LM75_7_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp8_input"],
    LM75_8_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp9_input"],
    LM75_9_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp10_input"],
    LM75_10_IDX: ["/sys/devices/platform/as7535_32xb_thermal/temp11_input"]
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

    def _get_cpu_thermal_val(self, thermal_num):
        if thermal_num < self.LM75_1_IDX or thermal_num > self.LM75_5_IDX:
            logging.debug('GET. Parameter error. thermal_num, %d', thermal_num)
            return None

        content = None
        device_path = self.get_thermal_to_device_path(thermal_num)
        try:
            with open(device_path, 'r') as val_file:
                content = val_file.readline().rstrip()
        except IOError as e:
            logging.error('GET. unable to open file: %s', str(e))
            return None

        if content == '':
            logging.debug('GET. content is NULL. device_path:%s', device_path)
            return None

        return int(content)

    def manage_thermal(self):
        # Set CPU core temp to CPLD
        for id in range(self.LM75_1_IDX, self.LM75_5_IDX+1):
            value = self._get_cpu_thermal_val(id)
            if value is None:
                continue

            device_path = self.get_thermal_to_device_path(id+5)
            try:
                with open(device_path, 'w') as val_file:
                    val_file.write(str(int(value/1000)))
            except IOError as e:
                logging.error('GET. unable to open file: %s', str(e))
                continue

        return True

def handler(signum, frame):
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
    monitor = accton_as7535_32xb_monitor(log_file, log_level)

    # Loop forever, doing something useful hopefully:
    while True:
        monitor.manage_thermal()
        time.sleep(10)

if __name__ == '__main__':
    main(sys.argv[1:])
