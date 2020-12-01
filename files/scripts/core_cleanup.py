#!/usr/bin/python3
import argparse
from argparse import RawTextHelpFormatter
from stat import ST_CTIME
import os, time
from datetime import datetime, timedelta
from sonic_py_common.logger import Logger
import sys

CORE_FILE_DIR=r'/var/core'
DEFAULT_INTERVAL=0
DEFAULT_MAX_DUMPS=4
SYSLOG_IDENTIFIER = 'core_cleanup.py'

def exe_name(filename):
    try:
        return filename.split('.')[1]
    except:
        return filename

def corefile_cleanup(input_dir, max_dumps, logger):
    core_files = (os.path.join(input_dir, fn) for fn in os.listdir(input_dir))
    core_file_info = ((os.stat(path), path) for path in core_files)
    core_file_detailed_info = ((stat[ST_CTIME], path) for stat, path in core_file_info)
    # Groups core files based on the executable program name to identify duplicate core files
    exe_groups = dict()
    for cdate, path in core_file_detailed_info:
        if exe_groups.get(exe_name(os.path.basename(path))) is None:
            exe_groups[exe_name(os.path.basename(path))] = [(cdate, path)]
        else:
            exe_groups.get(exe_name(os.path.basename(path))).append((cdate, path))

    for exe, core_files in exe_groups.items():
        if len(core_files) > 1:
            idx = 0
            last_idx = len(core_files) - 1
            for cdate, path in sorted(core_files, reverse=True):
                if idx >= (max_dumps - 1) and idx != last_idx:
                    logger.log_info('Deleting the core file {}'.format(path))
                    try:
                        os.remove(path)
                    except FileNotFoundError:
                        pass
                    except Exception as e:
                        logger.log_error('Exception [{}] while deleting the core file {}'.format(e, path))
                idx += 1

def main():
    logger = Logger(SYSLOG_IDENTIFIER)
    logger.set_min_log_priority_info()

    # Add allowed arguments
    parser = argparse.ArgumentParser(description="Core file garbage collector:\n\n"
                                                 "Duplicate core files generated for the same exectable program are deleted.\n"
                                                 "Only the oldest and n-1 latest duplicate core files are saved, rest of them are deleted.",
                                     formatter_class=RawTextHelpFormatter)

    # Directory to clean-up
    parser.add_argument("-d", "--input-dir",
                        metavar='DIR', default=CORE_FILE_DIR,
                        help="core files directory to cleanup")

    # Maximum number of duplicate core files stored
    parser.add_argument("-n", "--max-dumps", type=int,
                        default=DEFAULT_MAX_DUMPS, choices=range(1, 11),
                        help='maximum number of core files saved for a given executable program. Default: 4')

    # Parse command arguments
    options = parser.parse_args()

    if not os.path.isdir(options.input_dir):
        logger.log_error("Error! Directory {} does not exist".format(options.input_dir))
        sys.exit(1)

    logger.log_info('Cleaning up core files')
    corefile_cleanup(options.input_dir, options.max_dumps, logger)
    logger.log_info('Finished cleaning up core files')

if __name__== "__main__":
    main()
