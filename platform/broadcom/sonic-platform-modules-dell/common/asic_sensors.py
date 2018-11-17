#! /usr/bin/python
# Retrieve the maximum number of thermal sensors supported on
# the ASIC from the flex counter DB and print the readings
# along wtih the average.

import swsssdk
import json
import sys
import os
import pickle
from subprocess import Popen, PIPE

# temp files to cache constants
SENSORS_DIR = "/tmp/dell/sensors"
SWITCH_OID = "switch_oid"
MAX_SENSORS = "max_sensors"

# Load a value from a given file
def load_from_file(file):
    if os.path.isfile(file):
        try:
            value = pickle.load(open(file, 'r'))
        except IOError as e:
            print e.errno, e
            sys.exit(e.errno)
    return value

# Dump a value into a given file
def dump_to_file(file, value):
    if value:
        try:
            pickle.dump(value, open(file, 'w'))
        except IOError as e:
            print e.errno, e
            sys.exit(e.errno)

# Get the switch OID should the ASIC support sensors
def get_switch_sensors_oid():
    switch_oid_file = SENSORS_DIR + "/" + SWITCH_OID

    # Check if we saved it in the tmp file already
    if os.path.isfile(switch_oid_file):
        return load_from_file(switch_oid_file)

    if not os.path.exists(SENSORS_DIR):
        try:
            os.makedirs(SENSORS_DIR)
        except IOError as e:
            print e.errno, e
            sys.exit(1)

    # Retrieve the switch oid from the flex counter DB
    # and save it in the file cache
    proc = Popen("docker exec -i database redis-cli \
                 --raw -n 5 KEYS FLEX_COUNTER_TABLE:SWITCH_SENSORS*", \
                 stdout=PIPE, stderr=PIPE, shell=True)
    out, err = proc.communicate()

    for key in out.splitlines() or [None]:
        if key:
            id = key.replace('FLEX_COUNTER_TABLE:SWITCH_SENSORS:oid:', '')
            if id:
                dump_to_file(switch_oid_file, id)
                return id
    return None

# Get the number of sensor values that will be dumped to counters DB
def get_switch_max_sensors(sensors):
    max_sensors_file = SENSORS_DIR + "/" + MAX_SENSORS

    if os.path.isfile(max_sensors_file):
        return load_from_file(max_sensors_file)

    temp_list = [sensors[key] for key in sensors
                 if key.startswith('SAI_SWITCH_ATTR_TEMP_')]
    max_sensors = len(temp_list)
    if max_sensors:
        dump_to_file(max_sensors_file, max_sensors)
        return max_sensors

    return 0

# Print the ASIC sensors from the counter DB
def print_asic_sensors():

    countersdb = swsssdk.SonicV2Connector(host='127.0.0.1')
    countersdb.connect(countersdb.COUNTERS_DB)

    id = get_switch_sensors_oid()
    if id:
        sensors = countersdb.get_all(countersdb.COUNTERS_DB,
                                     'COUNTERS:oid:' + id)
        max_sensors = get_switch_max_sensors(sensors)

        average_temp = sensors.get('SAI_SWITCH_ATTR_AVERAGE_TEMP')
        max_temp = sensors.get('SAI_SWITCH_ATTR_MAX_TEMP')
        temp_list = []

        # Retrieve the list of individual sensor values
        for i in range(max_sensors):
            temp_list.append(sensors.get('SAI_SWITCH_ATTR_TEMP_%d' % i))

        if (average_temp is not None) and \
           (max_temp is not None) and \
           (temp_list is not None):
            print '\nBCM Internal: ' \
                + str(average_temp) + ' C' \
                + ' (max ' + str(max_temp) + ' C)' \
                + ' (' + ' '.join(str(x) for x in temp_list) + ' C)'
        else:
            print '\nBCM Internal: ' + 'NA'

    else:
        print '\nBCM Internal: ' + 'NA'

    countersdb.close(countersdb.COUNTERS_DB)

