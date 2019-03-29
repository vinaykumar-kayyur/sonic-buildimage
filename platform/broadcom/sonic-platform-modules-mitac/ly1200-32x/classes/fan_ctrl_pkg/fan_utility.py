#! /usr/bin/env python
# coding:utf-8

try:
    import subprocess
    import logging
    import socket
    import os
    import sys
    import glob
    import json
    import ast
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


def DEBUG(arg): FanUtility.log_message(logging.DEBUG, arg)
def INFO(arg): FanUtility.log_message(logging.INFO, arg)
def WARN(arg): FanUtility.log_message(logging.WARNING, arg)
def ERR(arg): FanUtility.log_message(logging.ERROR, arg)
def CRITICAL(arg): FanUtility.log_message(logging.CRITICAL, arg)


class ReadonlyDict(dict):
    def __setitem__(self, key, value):
        raise TypeError("__setitem__ is not supported")

    def __delitem__(self, key):
        raise TypeError("__delitem__ is not supported")


class FanUtility(object):
    """ fan-ctrl FanUtility class """

    _log_file = "/var/log/syslog"

    def __new__(cls, *args):
        if len(args) != 5:
            raise TypeError("it needs five arguments")
        cls._log_file = args[2]
        return object.__new__(cls)

    def __init__(self, *args):
        """ The *args is list of [zone_conf, temp_conf, log_file, debug_mode, simulate_mode] """
        self.__debug_mode = args[3]
        self.__simulate_mode = args[4]
        _sim_zone_dict = self.__create_zone_dict(args[0])
        if self.__simulate_mode is True:
            for name in _sim_zone_dict['TEMP_LIST']:
                _sim_zone_dict[name]['cmd'] = 'cat /tmp/simulate' + name + '.txt'
                with open('/tmp/simulate' + name + '.txt', 'w+') as f:
                    f.write('60.0')

            for i in range(len(_sim_zone_dict['FAN_CMD'])):
                _sim_zone_dict['FAN_CMD'][i] = '/tmp/simulate_fan_pwm'
            with open('/tmp/simulate_fan_pwm', 'w+') as f:
                f.write('0')

        self.__fan_zone = ReadonlyDict(_sim_zone_dict)
        self.__fan_zone_thermal = ReadonlyDict(self.__create_zone_thermal_dict(args[1]))
        self.__current_pwm = 0

    @property
    def debug_mode(self):
        return self.__debug_mode

    @property
    def simulate_mode(self):
        return self.__simulate_mode

    @property
    def fan_zone(self):
        return self.__fan_zone

    @property
    def fan_zone_thermal(self):
        return self.__fan_zone_thermal

    @property
    def pwm_value(self):
        return self.__current_pwm

    @pwm_value.setter
    def pwm_value(self, current_pwm):
        for file_path in self.fan_zone['FAN_CMD']:
            file_path = glob.glob(file_path)[0]
            try:
                with open(file_path, 'w+') as f:
                    f.write(str(current_pwm))
            except EnvironmentError:
                ERR("Open file fail. reason = " + file_path + " is not exist.")

        self.__current_pwm = current_pwm

    @classmethod
    def log_message(cls, msg_lvl, msg):
        """ Log wrappers """

        hostname = socket.gethostname()
        log_file = cls._log_file
        date_fmt = '%b %_d %T'
        msg_format = '%(asctime)s ' + hostname + ' %(filename)s[%(process)d]: <%(levelname)s>:%(message)s'

        logging.basicConfig(filename=log_file, format=msg_format, datefmt=date_fmt, level=logging.DEBUG)

        # DEBUG:10 INFO:20 WARNING:30 ERROR:40
        if msg_lvl >= logging.WARNING:
            print(msg)

        if msg_lvl == logging.DEBUG:
            logging.debug(msg)
        elif msg_lvl == logging.INFO:
            logging.info(msg)
        elif msg_lvl == logging.WARNING:
            logging.warning(msg)
        elif msg_lvl == logging.ERROR:
            logging.error(msg)
            sys.exit(os.EX_USAGE)
        elif msg_lvl == logging.CRITICAL:
            logging.critical(msg)
            sys.exit(os.EX_USAGE)
        else:
            raise ValueError("Unsupported message level" + str(msg_lvl))

    def dump_runtime_info(self, *args):
        """ Debug for showing system current fan level and PWM """
        if self.debug_mode is True:
            if len(args) == 0:
                print("********* Sensor Group *********")
                for name in self.fan_zone['TEMP_LIST']:
                    print(name + '\t' + self.fan_zone[name]['cmd'] + '\t' + self.fan_zone[name]['max_temp'])

                print("********* Sensor Table *********")
                for name in self.fan_zone_thermal['TEMP_LIST']:
                    sensor_list = ''
                    for pwm in self.fan_zone_thermal['PWM']:
                        sensor_list += str(self.fan_zone_thermal[str(pwm)][name]) + " "
                    print(name + '\t' + sensor_list)
            else:
                print("********* Sensor Reading *********")
                temp = args[0]
                current_pwm = args[1]
                for name in self.fan_zone['TEMP_LIST']:
                    print(name + "\t" + str(temp[name]))

                current_level = self.fan_zone_thermal['PWM'].index(current_pwm) + 1
                # For human readable, the representation of fan level will start from 1.
                print("Current Level" + "\t " + str(current_level) + ", PWM" + "\t " + str(current_pwm))

        if self.simulate_mode is True:
            print("********* Simulate mode *********")
            print('please modify the contents of following files.')
            for name in self.fan_zone['TEMP_LIST']:
                print('/tmp/simulate' + name + '.txt')

    @staticmethod
    def platform_init(conf_dir, zone_conf, temp_conf, simulate_mode):
        """ Getting board type and create symbolic link """

        file_path = conf_dir + "/conf_file"

        if os.path.basename(zone_conf).find("fan-zone.conf") == -1:
            forward_sensor_conf = "ln -sf " + zone_conf + " " + file_path + "/fan-zone.conf"
            reverse_sensor_conf = "ln -sf " + zone_conf + " " + file_path + "/fan-zone.conf"
        else:
            forward_sensor_conf = "ln -sf " + file_path + "/fan-zone_F2B.conf " + file_path + "/fan-zone.conf"
            reverse_sensor_conf = "ln -sf " + file_path + "/fan-zone_B2F.conf " + file_path + "/fan-zone.conf"

        if os.path.basename(temp_conf).find("fan-zone-thermal.conf") == -1:
            forward_pwm_conf = "ln -sf " + temp_conf + " " + file_path + "/fan-zone-thermal.conf"
            reverse_pwn_conf = "ln -sf " + temp_conf + " " + file_path + "/fan-zone-thermal.conf"
        else:
            forward_pwm_conf = "ln -sf " + file_path + "/fan-zone-thermal_F2B.conf " + file_path + "/fan-zone-thermal" \
                                                                                                   ".conf "
            reverse_pwn_conf = "ln -sf " + file_path + "/fan-zone-thermal_B2F.conf " + file_path + "/fan-zone-thermal" \
                                                                                                   ".conf "

        # board_type_cmd_dic
        board_type_list1 = ("0x0", "0x2")
        board_type_list2 = ("0x1", "0x3")
        cmd_list1 = (forward_sensor_conf, forward_pwm_conf)
        cmd_list2 = (reverse_sensor_conf, reverse_pwn_conf)

        # get board type
        if simulate_mode is True:
            board_type = "0x1"
        else:
            get_board_type_cmd = "cat /sys/bus/i2c/devices/1-0032/brd_type"
            board_type = subprocess.check_output(["/bin/bash", "-c", get_board_type_cmd]).decode('utf8').strip()

        # create symbolic
        if board_type in board_type_list1:
            for cmd in cmd_list1:
                subprocess.check_output(["/bin/bash", "-c", cmd])
        elif board_type in board_type_list2:
            for cmd in cmd_list2:
                subprocess.check_output(["/bin/bash", "-c", cmd])
        else:
            print(board_type + "is not exist")
            sys.exit(os.EX_DATAERR)

    @staticmethod
    def __create_zone_dict(file_path):
        """ Create zone dictionary """

        zone_dic = {}
        temp_grp = []
        fan_grp = []
        list1 = ('INTERVAL', 'HYTERESIS', 'MIN_PWM')

        # get temp list
        cmd = "cat " + file_path + " | grep '^TEMP_'| awk -F ',' {'print$1'}"
        temp_list = subprocess.check_output(["/bin/bash", "-c", cmd]).decode('utf8').split()
        zone_dic['TEMP_LIST'] = temp_list

        # get sensor name cmd max_temp
        for i in range(len(temp_list)):
            # Processing ascii code for degree sign
            cmd = "cat " + file_path + " | grep '^TEMP_' | awk NR==" + str(i + 1) + ">/tmp/fan_ctrl.BAK"
            os.system(cmd)
            cmd = "cat /tmp/fan_ctrl.BAK|sed 's/^+\|\\xc2\\xb0C//g'"
            line = subprocess.check_output(["/bin/bash", "-c", cmd]).decode('utf8').strip()
            items = line.split(', ')
            temp_grp += [str(item).strip() for item in items]

        while len(temp_grp) > 0:
            name, cmd, max_temp = temp_grp[:3]
            cmd = cmd.strip('"')
            zone_dic[name] = {'cmd': cmd, 'max_temp': max_temp}
            del temp_grp[:3]

        # get default value INTERVAL:10, HYSTERESIS:2, MIN_PWM:39, ZONE_ID:0
        for list_name in list1:
            cmd = "cat " + file_path + " | grep ^" + list_name + " | awk -F '=' {'print$2'} | tail"
            value = subprocess.check_output(["/bin/bash", "-c", cmd]).strip()
            if not value:
                ERR("config: status = invalid. reason = no " + list_name + " defined.")
            else:
                try:
                    zone_dic[list_name] = int(value) if int(value) >= 0 else None
                except TypeError:
                    ERR("config: status = invalid. reason = the value of " + list_name + " is not integer.")

        zone_dic['ZONE_ID'] = 0

        # get fan command and fan numbers
        cmd = "cat " + file_path + "| grep '^FAN_' | awk {'print$2'} | wc -l"
        fan_num = subprocess.check_output(["/bin/bash", "-c", cmd]).strip()

        for i in range(int(fan_num)):
            cmd = "cat " + file_path + " | grep '^FAN_' | awk NR==" + str(i + 1) + "{'print$2'}"
            line = subprocess.check_output(["/bin/bash", "-c", cmd]).decode('utf8').strip('\n')
            fan_grp += line.split(',')

        zone_dic['FAN_CMD'] = fan_grp
        zone_dic = ast.literal_eval(json.dumps(zone_dic))
        return zone_dic

    @staticmethod
    def __create_zone_thermal_dict(file_path):
        """ Create zone thermal dictionary """

        zone_thermal_dic = {}
        sensor_temp = {}

        #  get temp list
        cmd = "cat " + file_path + " | grep '^TEMP_'| awk {'print$1'}"
        temp_list = subprocess.check_output(["/bin/bash", "-c", cmd]).decode('utf8').split()
        zone_thermal_dic['TEMP_LIST'] = temp_list

        # get fan_level_list
        cmd = "cat " + file_path + "| grep '^PWM' | awk -F 'PWM' {'print$2'}"
        pwm_list = list(map(int, subprocess.check_output(["/bin/bash", "-c", cmd]).split()))
        zone_thermal_dic['PWM'] = pwm_list

        # get sensor fan level
        for sensor_name in temp_list:
            cmd = "cat " + file_path + "| grep ^" + sensor_name + "| awk -F " + sensor_name + " {'print$2'}"
            s_fan_level_list = list(map(float, subprocess.check_output(["/bin/bash", "-c", cmd]).split()))
            zone_thermal_dic[sensor_name] = list(zip(s_fan_level_list, pwm_list))
            sensor_temp[sensor_name] = s_fan_level_list

        # get pre_pwn
        pre_pwm_list = pwm_list[0:len(pwm_list) - 1]
        pre_pwm_list.insert(0, 0)
        sensor_temp['PRE_PWM'] = pre_pwm_list

        for i in range(len(pwm_list)):
            list1 = []
            name_list = []
            for name in sensor_temp:
                list1.append(sensor_temp[name][i])
                name_list.append(name)
            zone_thermal_dic[pwm_list[i]] = dict(zip(name_list, list1))

        zone_thermal_dic = ast.literal_eval(json.dumps(zone_thermal_dic))
        return zone_thermal_dic

    def validate_configuration(self):
        """ Initialization """

        # validate zone config
        if len(self.fan_zone['TEMP_LIST']) == 0:
            ERR("config: status = invalid. reason = no TEMPERATURE SENSORS defined.")

        if len(self.fan_zone['FAN_CMD']) == 0:
            ERR("config: status = invalid. reason = no FAN defined.")

        # validate thermal config 
        if len(self.fan_zone_thermal['PWM']) == 0:
            ERR("config: status = invalid. reason = no FAN LEVELS defined.")

        if len(self.fan_zone_thermal['TEMP_LIST']) != len(self.fan_zone['TEMP_LIST']):
            ERR("config: status = invalid. reason = the number of temperature sensors is inconsistent.")

        # compare temperature sensor name between configuration files
        for i in range(len(self.fan_zone['TEMP_LIST'])):
            if self.fan_zone['TEMP_LIST'][i] != self.fan_zone_thermal['TEMP_LIST'][i]:
                ERR("config: status = invalid. reason = the name of temperature sensors is inconsistent.")

        # validate pwm values 
        for pwm in self.fan_zone_thermal['PWM']:
            if pwm < self.fan_zone['MIN_PWM']:
                ERR("config: status=invalid. reason=the value of fan level is less than MIN_PWM({0}).".format(
                        str(self.fan_zone["MIN_PWM"])))
