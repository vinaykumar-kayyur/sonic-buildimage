#!/usr/bin/env python
import os
import yaml
import subprocess

DOCUMENTATION = '''
---
module: sonic_platform
version_added: "1.9"
short_description: Retrive platform related facts for a device.
description:
    - Retrieve platform related facts from config files.
'''

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
        if machine_info.has_key('onie_platform'):
            return  machine_info['onie_platform']
        elif machine_info.has_key('aboot_platform'):
            return machine_info['aboot_platform']
    return None

def get_sonic_version_info():
    if not os.path.isfile('/etc/sonic/sonic_version.yml'):
        return None
    data = {}
    with open('/etc/sonic/sonic_version.yml') as stream:
        data = yaml.load(stream)
    return data

def get_system_mac():
    get_mac_cmd = "ip link show eth0 | grep ether | awk '{print $2}'"
    version_info = get_sonic_version_info()

    if (version_info['asic_type'] == 'mellanox'):
        eeprom_file = "/sys/bus/i2c/devices/8-0051/eeprom"
        if (os.access(eeprom_file, os.R_OK)):
            get_mac_cmd = "od -vt x1 -An " + eeprom_file + "| xargs printf \"0x%s \" | xargs printf \"%02x:\" | awk 'BEGIN { FS=\":\"; i=8+1+2+1} {while(i<NF) {type=$i; len=(\"0x\"$(i+1));if(type!=\"24\") {i=i+2+len} else {print substr($0, (i+1)*3+1, len*3-1); break}}}'"

    proc = subprocess.Popen(get_mac_cmd, shell=True, stdout=subprocess.PIPE)
    (mac, err) = proc.communicate()
    mac = mac.strip()
    
    # Align last byte of MAC if necessary
    if version_info and (version_info['asic_type'] == 'mellanox' or version_info['asic_type'] == 'centec'):
        last_byte = mac[-2:]
        aligned_last_byte = format(int(int(last_byte, 16) & 0b11000000), '02x')
        mac = mac[:-2] + aligned_last_byte
    return mac

