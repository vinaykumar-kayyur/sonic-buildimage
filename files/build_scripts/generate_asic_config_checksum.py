#!/usr/bin/env python

import syslog
import os
import hashlib

SYSLOG_IDENTIFIER = 'asic_config_checksum'

CHUNK_SIZE = 8192

CONFIG_FILES = {
    os.path.abspath('./src/sonic-swss/swssconfig/sample/'): ['netbouncer.json', '00-copp.config.json']
}

OUTPUT_FILE = os.path.abspath('./asic_config_checksum')

def log_info(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()

def log_error(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()

def get_config_files():
    '''
    Gathers up ASIC config file names from the appropriately named 'sample'
    directory in SWSS
    '''
    checksum_files = []
    for path, files in CONFIG_FILES.items():
        for file in files:
            checksum_files.append(os.path.join(path, file))
    return checksum_files

def generate_checksum(checksum_files):
    '''
    Iterates through all of the given ASIC config file, reads their contents,
    and generates a checksum. NOTE: The checksum is performed in the order
    provided. This function does NOT do any re-ordering of the files before
    creating the checksum.
    '''
    checksum = hashlib.sha1()
    for file in checksum_files:
        try:
            with open(file, 'r') as f:
                for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                    checksum.update(chunk)
        except IOError as e:
            log_error('Error processing ASIC config file ' + file + ':' + e.strerror)
            return None

    return checksum.hexdigest()

def main():
    config_files = sorted(get_config_files())
    checksum = generate_checksum(config_files)
    if checksum == None:
        exit(1)

    with open(OUTPUT_FILE, 'w') as output:
        output.write(checksum + '\n')

if __name__ == '__main__':
    main()
