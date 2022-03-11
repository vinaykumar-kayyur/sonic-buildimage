#!/usr/bin/env python3
"""A skeleton for a Python rsyslog output plugin with error handling.
Requires Python 3.

To integrate a plugin based on this skeleton with rsyslog, configure an
'omprog' action like the following:
    action(type="omprog"
        binary="/usr/bin/myplugin.py"
        output="/var/log/myplugin.log"
        confirmMessages="on"
        ...)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0
     -or-
     see COPYING.ASL20 in the source distribution

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import json
import logging
import os
import re
import socket
import sys


TELEMETRY_SERVER_IP = "127.0.0.1"
TELEMETRY_SERVER_PORT = 20001

PARSER_CFG_FILE = "{}_parse.rc.json"

# Global definitions specific to your plugin
outfile = None
logfile = "/tmp/{}_logfile"
telemetry_client_h = None
reglst = []
pgm_name = ""

server_port = TELEMETRY_SERVER_PORT


class RecoverableError(Exception):
    """An error that has caused the processing of the current message to
    fail, but does not require restarting the plugin.

    An example of such an error would be a temporary loss of connection to
    a database or a server. If such an error occurs in the onMessage function,
    your plugin should wrap it in a RecoverableError before raising it.
    For example:

        try:
            # code that connects to a database
        except DbConnectionError as e:
            raise RecoverableError from e

    Recoverable errors will cause the 'omprog' action to be temporarily
    suspended by rsyslog, during a period that can be configured using the
    "action.resumeInterval" action parameter. When the action is resumed,
    rsyslog will resend the failed message to your plugin.
    """


def load_reglist(rc_path, pgm_name):
    global reglst

    rcfile = os.path.join(rc_path, PARSER_CFG_FILE.format(pgm_name))
    with open(rcfile) as s:
        reglst = json.load(s)
    logging.info("load_reglist: file:{} len={}".format(rcfile, len(reglst)))


def do_regex_match(msg):
    global reglst, pgm_name

    to_log = {}
    match = False

    for entry in reglst:
        res = re.search(entry["regex"], msg)
        if res:
            groups = res.groups()
            params = entry["params"]
            to_log = {
                    "tag": entry["tag"],
                    "program": pgm_name }
            if len(params) != len(groups):
                logging.error("{}:params mismatch: params:{} groups:{} msg:{}".format(
                    pgm_name, params, groups, msg))
                to_log["parsed"] = groups
            else:
                for i in range(len(params)):
                    to_log[params[i]] = groups[i]
            match = True
            break
    return match, to_log


def onInit(is_debug, port, rc_path, do_send):
    global pgm_name

    # Set up plugin here. This is called once at the start of run.
    # This plugin reports its own logs via rsyslog. This will facilitate
    # diagnosing problems and debugging this plugin.Here we set up the standard
    # Python logging system to output the logs to stderr. In the rsyslog
    # configuration, configure the 'omprog' action to capture the stderr
    # of this plugin by specifying the action's "output" parameter.
    #
    #    action(type="omprog"
    #       binary="/usr/share/sonic/scripts/rsyslog_plugin.py -p bgpcfgd -d -r /root/try -s"
    #       output="/var/log/myplugin.log"
    #       confirmMessages="on"
    #       template="prog_msg")
    #
    logging.basicConfig(stream=sys.stderr,
                        level=logging.DEBUG if is_debug else logging.WARNING,
                        format='%(asctime)s %(levelname)s %(message)s')

    logging.debug("onInit called")

    # load regex list
    load_reglist(rc_path, pgm_name)

    if is_debug:
        # For debug purposes, this plugin skeleton appends the received logs
        # to a file.
        global outfile, logfile
        outfile = open(logfile.format(pgm_name), "w")

    if do_send:
        # Open client socket, if enabled to send
        global telemetry_client_h, server_port

        telemetry_client_h = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        server_port = port


def onMessage(msg):
    """Process one log message received from rsyslog (e.g. send it to a
    database). If this function raises an error, the message will be retried
    by rsyslog.

    Args:
        msg (str): the log message. Does NOT include a trailing newline.

    Raises:
        RecoverableError: If a recoverable error occurs. The message will be
            retried without restarting the plugin.
        Exception: If a non-recoverable error occurs. The plugin will be
            restarted before retrying the message.
    """

    # Do regex match
    match, to_log = do_regex_match(msg)

    global outfile
    if outfile:
        # In debug mode, write all messages into a file.
        outfile.write("match:{} to_log:{} msg:{}".format(match, to_log, msg))
        outfile.write("\n")
        outfile.flush()

    # Send msg to server
    global telemetry_client_h, server_port

    if match and telemetry_client_h:
        bytesToSend = str.encode("match:{} to_log:{} msg:{}".format(match, to_log, msg))
        telemetry_client_h.sendto(bytesToSend, (TELEMETRY_SERVER_IP, server_port))


def onExit():
    """Do everything that is needed to finish processing (e.g. close files,
    handles, disconnect from systems...). This is being called immediately
    before exiting.

    This function should not raise any error. If it does, the error will be
    logged as a warning and ignored.
    """
    logging.debug("onExit called")

    # For illustrative purposes, this plugin skeleton appends the received logs
    # to a file. When implementing your plugin, remove the following code.
    global outfile
    if outfile:
        outfile.close()


def run():
    """
    -------------------------------------------------------
    This is plumbing that DOES NOT need to be CHANGED
    -------------------------------------------------------
    This is the main loop that receives messages from rsyslog via stdin,
    invokes the above entrypoints, and provides status codes to rsyslog
    via stdout. In most cases, modifying this code should not be necessary.
    """
    # Tell rsyslog we are ready to start processing messages:
    print("OK", flush=True)

    endedWithError = False
    try:
        line = sys.stdin.readline()
        while line:
            line = line.rstrip('\n')
            try:
                onMessage(line)
                status = "OK"
            except RecoverableError as e:
                # Any line written to stdout that is not a status code will be
                # treated as a recoverable error by 'omprog', and cause the action
                # to be temporarily suspended. In this skeleton, we simply return
                # a one-line representation of the Python exception. (If debugging
                # is enabled in rsyslog, this line will appear in the debug logs.)
                status = repr(e)
                # We also log the complete exception to stderr (or to the logging
                # handler(s) configured in doInit, if any).
                logging.exception(e)

            # Send the status code (or the one-line error message) to rsyslog:
            print(status, flush=True)
            line = sys.stdin.readline()

    except Exception:
        # If a non-recoverable error occurs, log it and terminate. The 'omprog'
        # action will eventually restart the program.
        logging.exception("Unrecoverable error, exiting program")
        endedWithError = True

    try:
        onExit()
    except Exception:
        logging.warning("Exception ignored in onExit", exc_info=True)

    if endedWithError:
        sys.exit(1)
    else:
        sys.exit(0)


def main():
    global pgm_name

    parser=argparse.ArgumentParser(description="rsyslog plugin for events")
    parser.add_argument("-d", "--debug", action="store_true", default=True,
            help="Run with debug log level")
    parser.add_argument("-n", "--port-number", type=int,
            help="Listening port", default=TELEMETRY_SERVER_PORT)
    parser.add_argument("-p", "--pgm-name", required=True,
            help="Name of the program dumping the message")
    parser.add_argument("-r", "--rc-path", required=True,
            help="Dir of the rc file")
    parser.add_argument("-s", "--send", action="store_true", default=False,
            help="Send data to UDP listene")
    args = parser.parse_args()

    pgm_name = args.pgm_name

    try:
        onInit(is_debug=args.debug, port=args.port_number, rc_path=args.rc_path,
                do_send = args.send)
        run()
    except Exception as e:
        # If an error occurs during initialization, log it and terminate. The
        # 'omprog' action will eventually restart the program.
        logging.exception("Initialization error, exiting program")
        sys.exit(1)


if __name__ == "__main__":
    main()

