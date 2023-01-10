# -*- coding: UTF-8 -*-
import os

def get_machine_info():
    if not os.path.isfile('/host/machine.conf'):
        return None
    machine_vars = {}
    with open('/host/machine.conf') as machine_file:
        for line in machine_file:
            tokens = line.split('=')
            if len(tokens) < 2:
                continue
            machine_vars[tokens[0]] = tokens[1].strip()
    return machine_vars

def get_platform_info(machine_info):
    if machine_info != None:
        if machine_info.__contains__('onie_platform'):
            return  machine_info['onie_platform']
        elif machine_info.__contains__('aboot_platform'):
            return machine_info['aboot_platform']
    return None