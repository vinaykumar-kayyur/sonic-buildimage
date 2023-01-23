#!/usr/bin/python3

import yaml

from build_img_metadata import get_bld_config

EXCL_CFG_PATH = 'src/sonic-utilities/exclude-cfg/exclude-cfg.yaml'

#get configuration with excluded components only

def get_excl_config():
    bld_cfg = {}
    excl_cfg = {}

    bld_cfg = get_bld_config()

    for key, val in bld_cfg.items():
        if str(key).startswith("INCLUDE_") and val == "n":
            excl_cfg[key] = val

    return excl_cfg

# Write build metadata into yaml file

def write_data(path:str, data_dict:dict):
    with open(path, 'w') as file:
        yaml.dump(data_dict, file)

def build_excl_cfg():
    excl_data = get_excl_config()
    write_data(EXCL_CFG_PATH, excl_data)

if __name__ == '__main__':
    build_excl_cfg()
