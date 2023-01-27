import yaml
import re
import os

PATH_BUILD_METADATA = "/etc/sonic/build_metadata.yaml"
PATH_CONFIG = "/sonic/rules/config"
PATH_CONFIG_USER = PATH_CONFIG + ".user"
PATH_FLAG_TO_KEY_MAP = "/etc/sonic/flags_to_keys_map.yaml"
PATH_DIST_FLAG_TO_KEY_MAP = os.path.dirname(os.path.abspath(__file__)) + "/.." + PATH_FLAG_TO_KEY_MAP
PATH_CFGGEN_KEYS_CLEANER = "/tmp/keys_to_clean"

def read_rules_config(path = None):
    '''
    Read config file (e.g. rules/config) and
    return in dictionary format
    '''
    
    if path is None:
        path = PATH_CONFIG
    
    if os.path.exists(path) is False:
        return {}
    
    with open(path) as file:
        file = file.read().split("\n")

    dict = {}

    for line in file:
        # non empty line and not comment
        if re.search("^$", line) is None and \
            re.search("^#", line) is None:
            line = line.replace("?=", "=", 1)
            # clear from spaces
            line = line.replace(" ", "")
            key_value = line.split("=")
            dict[key_value[0]] = key_value[1]

    return dict

def read_metadata_conifg(key_pattern = "", value_pattern = "", path = None):
    '''
    pattern: default is any string. "^$" - empty string
    "word" - substring, "^word$" - definite string

    return value: dict from metadata
    '''

    if path is None:
        path = PATH_BUILD_METADATA
    
    # Check if path exists
    if os.path.exists(path) is True:
        with open(path) as file:
            config = yaml.safe_load(file)
        config = config['Configuration']
    # probably this is build unit test
    # read rules/config from sonic-buildimage
    else:
        config = {}
        config = read_rules_config(PATH_CONFIG)
        config_user = read_rules_config(PATH_CONFIG_USER)
        if config_user is not None:
            config.update(config_user)

    for key in list(config):
        if re.search(key_pattern, key) is None or \
            (re.search(key_pattern, key) is not None and \
            re.search(value_pattern, config[key]) is None):
            del config[key]

    return config

def read_map(keys, path = None):
    '''
    Get list of values from key list
    '''

    if path is None:
        path = PATH_DIST_FLAG_TO_KEY_MAP

    if keys is None or os.path.exists(path) is False:
        return []

    with open(path) as file:
        map = yaml.safe_load(file)

    values = []
    for key in keys:
        values.extend(map[key])

    # remove empty strings
    values = list(filter(None, values))

    return values

def rm_top_nested_key(dict, key):
    '''
    provide dot separated key string to go through path and remove top nested key from dictionary
    e.g. DEVICE_METADATA.localhost.bgp_asn
    e.g. BGP_NEIGHBOR
    '''

    if "." in key:
        keys_splitted = key.split(".", 1)
        if keys_splitted[0] in dict:
            dict = dict[keys_splitted[0]]
            key = keys_splitted[1]
            rm_top_nested_key(dict, key)
    else:
        dict.pop(key, None)

def clean_cfggen_dict(dict, keys):
    '''
    Helper function for sonic-cfggen. Clear keys for
    disabled build flags (e.g. for INCLUDE_FRR_BGP).
    dict: sonic-cfggen dictionary
    keys: dot separated keys (see rm_top_nested_key)
    '''

    if keys is None:
        return

    for key in keys:
        rm_top_nested_key(dict, key)
