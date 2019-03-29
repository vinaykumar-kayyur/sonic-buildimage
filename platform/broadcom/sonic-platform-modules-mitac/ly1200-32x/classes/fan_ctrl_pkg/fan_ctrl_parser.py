#! /usr/bin/env python
# coding:utf-8

try:
    import argparse
    import os
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


def fan_ctrl_parser(base_dir):
    # get the current path
    config_dir = base_dir + "/conf_file/"

    parser = argparse.ArgumentParser(usage='./fan-ctrl [-h help] [-z zone_file] [-t thermal_file] [-o log_file] [-d] [-s]')
    parser.add_argument('-z', '--zone-config', metavar='', help='Fan zone configuration file (default: conf_file/fan-zone.conf)')
    parser.add_argument('-t', '--temp-config', metavar='', help='Fan zone thermal configuration file (default: conf_file/fan-zone-thermal.conf)')
    parser.add_argument('-o', '--log-file', metavar='', help='Log file (default: /var/log/syslog)')
    parser.add_argument('-d', '--debug', help='Debug mode (default: off)', action='store_true')
    parser.add_argument('-s', '--simulate', help='Simulate mode (default: off)', action='store_true')

    args = parser.parse_args()

    if args.zone_config is None:
        zone_conf = config_dir + "fan-zone.conf"
    else:
        zone_conf = args.zone_config
        if not os.path.exists(zone_conf):
            raise OSError('zone config \'%s\' is not exist' % (zone_conf))

    if args.temp_config is None:
        temp_conf = config_dir + "fan-zone-thermal.conf"
    else:
        temp_conf =  args.temp_config
        if not os.path.exists(temp_conf):
            raise OSError('temp config \'%s\' is not exist' % (temp_conf))

    if args.log_file is None:
        log_file = "/var/log/syslog"
    else:
        log_file = args.log_file

    if args.debug is True:
        # default debug mode (0: OFF, 1: ON)
        debug_mode = args.debug
    else:
        debug_mode = False

    if args.simulate is True:
        simulate_mode = args.simulate
    else:
        simulate_mode = False

    return zone_conf, temp_conf, log_file, debug_mode, simulate_mode
