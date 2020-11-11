#!/usr/bin/env python3

from __future__ import print_function
import json
import argparse


def get_filename():
    """ Read the name of the file from the command line """
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    return args.filename

def get_json(filename):
    """ Open the file and parse json from it """
    js = ''
    json_started = False
    with open(filename) as fp:
        for line in fp:
            s_line = line.strip()
            if s_line == '{':
                json_started = True
            if json_started:
                js += s_line
    data = json.loads(js)
    return data

def convert_to_raw(value):
    """
    Convert from a value from suffix to raw value
    Example:
    '1 KB/s' -> 10240.0
    """
    conversion = {
        ' MB/s': 1024*1024*10,
        ' KB/s': 1024*10,
        ' B/s' : 1,
    }
    for suffix, multiplier in conversion.items():
        if value.endswith(suffix):
            no_suffix_value = value.replace(suffix, '')
            float_value = float(no_suffix_value)
            return float_value * multiplier
    raise RuntimeError("Can't convert value '%s'" % value)

def main():
    """
    Main function. Read the data and output result
    """
    filename = get_filename()
    data = get_json(filename)
    rx_bps_total = 0.0
    tx_bps_total = 0.0
    for _, obj in data.items():
        rx_bps_total += convert_to_raw(obj['RX_BPS'])
        tx_bps_total += convert_to_raw(obj['TX_BPS'])
    print("Total RX = %d b/s" % int(rx_bps_total))
    print("Total TX = %d b/s" % int(tx_bps_total))

if __name__ == '__main__':
    main()
