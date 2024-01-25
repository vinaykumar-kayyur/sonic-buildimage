#!/usr/bin/env python3

import os
import subprocess

def is_eventd_running():
    try:
        output = subprocess.check_output(['systemctl', 'is-active', "eventd"], text=True)
        return output.strip() == 'active'
    except subprocess.CalledProcessError:
        return False

def start_rsyslog_plugin(parse_json, yang_module):
    command = ["/usr/bin/rsyslog_plugin", "-r" f"/etc/rsyslog.d/{parse_json}", "-m", yang_module]
    try:
        subprocess.run(command, check=True)
        logger.info("rsyslog_plugin started running")
    except subprocess.CalledProcessError as e:
        logger.info("An error occurred while executing rsyslog_plugin: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", nargs='?', const='', default='', help="Regex file for rsyslog plugin binary")
    parser.add_argument("-t", "--tag", nargs='?', const='', default='', help="Tag used by rsyslog plugin binary to publish events")
    args = parser.parse_args()
    if(args.file == '' or args.tag == ''):
        logging.error("Invalid or empty regex file/tag")
        return
    if(is_eventd_running):
        start_rsyslog_plugin(file, tag)
