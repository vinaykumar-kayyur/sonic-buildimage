#!/usr/bin/python3

import os
import os.path
import yaml
import re

RULES_CFG_PATH = 'rules/config'
RULES_CFG_USER_PATH = 'rules/config.user'
IMG_METADATA_FILE = 'build_metadata.yaml'

#
# Helper functions
#

# Get header info (version, date/time, commit/branch, kernel/distro)

def get_header_info():
    hdr_data = {}
    hdr_data ['SONiC_Software_Version'] = os.environ.get('build_version')
    hdr_data['Distribution'] = os.environ.get('debian_version')
    hdr_data['Kernel'] = os.environ.get('kernel_version')
    hdr_data['Build_branch'] = os.environ.get('branch')
    hdr_data['Build_commit'] = os.environ.get('commit_id')
    hdr_data['Build_date'] = os.environ.get('build_date')
    hdr_data['Architecture'] = os.environ.get('configured_arch')
    hdr_data['Platform'] = os.environ.get('configured_platform')

    return hdr_data

# Read config file by a given path, create dictionary

def read_cfg_file(cfg_path:str, cfg_dict:dict):
    if os.path.exists(cfg_path) is False:
        return

    #read config file
    with open(cfg_path) as cfg_fp:
        cfg_lines = cfg_fp.readlines()
        for line in cfg_lines:
            line = line.strip()
            if line.startswith('#') or re.search("^\s*$", line):
                #skip comments or empty lines
                continue
            else:
                #strip spaces, for pairs with ?= remove '?'
                key = line.split('=')[0].rstrip('?').strip()
                value = line.split('=')[1].strip()
                cfg_dict[key] = value

# Get build configuration
# read build configuration from config and config.user files
# config.user overwrites options from config, see slave.mk

def get_bld_config():
    bld_config = {}

    read_cfg_file(RULES_CFG_PATH, bld_config)
    read_cfg_file(RULES_CFG_USER_PATH, bld_config)

    return bld_config

# Get features list
# get features list and status according to build configuration

def get_features_list(features_list_path:str):
    feature_list = {}

    if os.path.exists(features_list_path) is False:
        return

    with open(features_list_path) as feature_yaml:
        feature_list = yaml.safe_load(feature_yaml)

    return feature_list

# Write build metadata into yaml file

def write_matadata(path:str):
    bld_metadata = {}

    bld_metadata['Version'] = get_header_info()
    bld_metadata['Configuration'] = get_bld_config()

    with open(path, 'w') as file:
        yaml.dump(bld_metadata, file)

def build_metadata():
    write_matadata(IMG_METADATA_FILE)

if __name__ == '__main__':
    build_metadata()
