#!/usr/bin/env python3
"""This is rsylog output plugin for streaming structured data from logs with error handling.

This plugin parses the log messages on o/p to identify events for reporting.
The *_parse.rc.json files provide the list of regex expressions to identify
the events. Each identified event is reported with its tag (unique within a
process), the name of the process sending the event and parsed dynamic data
as expressed in the regex.

Sample:
        {
            "tag": "bgp_admin_up",
            "regex": "^ Peer 'default.([0-9a-f:.]*)' admin state is set to 'up'",
            "params": [ "peer_ip" ]
        },

The log message " Peer 'default|10.10.10.10' admin state is set to 'up'" will
send following event to an UDP listener.

    "{'tag': 'admin_up', 'program': 'bgpcfgd', 'peer_ip': '10.0.0.1'}"

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

# Global values that are static for life of the plugin instance.
outfile = None                  # Handle to o/p file for debug o/p 
logfile = "/tmp/{}_logfile"     # Name of the log file for logs from this plugin
telemetry_client_h = None       # UDP client socket handle
reglst = []                     # List of regex
pgm_name = ""                   # Name of the process that spawned this plugin instance.

err_reported_tags = set()       # Error reported on these tags.
                                # Cache to avoid duplicates

server_port = TELEMETRY_SERVER_PORT # Configurable via args


class RecoverableError(Exception):
    """An error that has caused the processing of the current message to
    fail, but does not require restarting the plugin.

    Recoverable errors will cause the 'omprog' action to be temporarily
    suspended by rsyslog, during a period that can be configured using the
    "action.resumeInterval" action parameter. When the action is resumed,
    rsyslog will resend the failed message to your plugin.
    """


# Loads the regex list, once upon init
#
def load_reglist(rc_path, pgm_name):
    global reglst

    rcfile = os.path.join(rc_path, PARSER_CFG_FILE.format(pgm_name))
    with open(rcfile) as s:
        reglst = json.load(s)
    logging.info("load_reglist: file:{} len={}".format(rcfile, len(reglst)))


# Matches msg against the list and return the match if found, else return false
#
def do_regex_match(msg):
    global reglst, pgm_name

    to_log = {}
    match = False

    for entry in reglst:
        res = re.search(entry["regex"], msg)
        if res:
            groups = res.groups()
            params = entry["params"]
            tag = entry["tag"]
            to_log = {
                    "tag": tag,
                    "program": pgm_name }
            if (len(params) != len(groups)) and (tag not in err_reported_tags):
                # Report only once for each tag, as it is static error.
                err_reported_tags.add(tag)
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
    """Process one log message received from rsyslog.
    If matches an event, send the parsed data to UDP listener.

    Args:
        msg (str): the log message. Does NOT include a trailing newline.

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
        bytesToSend = str.encode(str(to_log))
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
    This is the main loop that receives messages from rsyslog via stdin,
    invokes the above entrypoints, and provides status codes to rsyslog
    via stdout.
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
                # to be temporarily suspended.  (If debugging is enabled in rsyslog,
                # this line will appear in the debug logs.)
                #
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
    parser.add_argument("-d", "--debug", action="store_true", default=False,
            help="Run with debug log level")
    parser.add_argument("-n", "--port-number", type=int,
            help="Listening port", default=TELEMETRY_SERVER_PORT)
    parser.add_argument("-p", "--pgm-name", required=True,
            help="Name of the program dumping the message")
    parser.add_argument("-r", "--rc-path", default="/etc/rsyslog.d",
            help="Dir of the rc file")
    parser.add_argument("-s", "--skip-send", action="store_true", default=False,
            help="Send data to UDP listene")
    args = parser.parse_args()

    pgm_name = args.pgm_name

    try:
        onInit(is_debug=args.debug, port=args.port_number, rc_path=args.rc_path,
                do_send = not args.skip_send)
        run()
    except Exception as e:
        # If an error occurs during initialization, log it and terminate. The
        # 'omprog' action will eventually restart the program.
        logging.exception("Initialization error, exiting program")
        sys.exit(1)


if __name__ == "__main__":
    main()

