#!/usr/bin/env python3

import re
import os
import subprocess
import time
from sonic_py_common.logger import Logger
from swsscommon.swsscommon import ConfigDBConnector

SYSLOG_IDENTIFIER = os.path.basename(__file__)

# Global logger instance
logger = Logger(SYSLOG_IDENTIFIER)
logger.log_info("Starting DHCP DoS logger...")

# Connect to config db
config_db = ConfigDBConnector()
config_db.connect()

# Initialize
drop_pkts = {}

# Get list of ports
ports = config_db.get_table('PORT').keys()

drop_pkts = {port: 0 for port in get_ports()}

# Main handler function
def handler():
    while True:
        for port in drop_pkts.keys():

            output = subprocess.run(["tc", "-s", "qdisc", "show", "dev", str(port), "handle", "ffff:"], shell=False, capture_output=True)

            #output = subprocess.run(["tc -s qdisc show dev {} handle ffff:".format(str(port))], shell=True, capture_output=True)
            if output is not None:
                match = re.search(r'dropped (\d+)', output.stdout)

                if int(match) > drop_pkts[port]:
                        logger.log_info(f"Port {port}: Current DHCP drop counter is {int(match)}")
                        drop_pkts[port] = int(match)
                else:
                    logger.log_warning(f"No dropped packets found on port {port}")