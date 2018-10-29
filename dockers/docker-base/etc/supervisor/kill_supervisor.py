#!/usr/bin/python

# Please follow the link for documentation: http://supervisord.org/events.html
# SupervisorD exits immediately if one of its managed process get crashed as it subscribes to "EVENT Listener" process.

import sys
import os
import signal
import subprocess

from supervisor.childutils import listener

def write_stdout(s):
    # only eventlistener protocol messages may be sent to stdout
    sys.stdout.write(s)
    sys.stdout.flush()

def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()

def main():
    while True:
        all_service_list = []
        proc = subprocess.Popen(["supervisorctl avail | cut -d' ' -f1"], shell=True, stdout=subprocess.PIPE)
        (out, err) = proc.communicate()

        all_service_list = out.split()

        # "exception_service_list" contains all the program excluded  from event listener process.
        exception_service_list = ["start.sh", "enable_counters", "swssconfig", "arp_update", "ledinit", "fancontrol", "lm-sensors", "ledd", "xcvrd", "configdb-load.sh", "snmpd-config-updater"]

        service_list =  [x for x in all_service_list if x not in exception_service_list]
        headers, body = listener.wait(sys.stdin, sys.stdout)
        body = dict([pair.split(":") for pair in body.split(" ")])

        write_stderr("Headers: %r\n" % repr(headers))
        write_stderr("Body: %r\n" % repr(body))

        process = body["processname"];
        state = headers["eventname"].split('_')[2];
        if process in service_list:
            write_stderr("Process {} got {} !!! Time to kill Supervisord !!!\n".format(process,state))
            try:
                pidfile = open('/var/run/supervisord.pid','r')
                pid = int(pidfile.readline());
                os.kill(pid, signal.SIGQUIT)
            except Exception as e:
                write_stdout('Could not kill supervisor: ' + e.strerror + '\n')
        else:
            write_stderr("Process {} got {} !!! But no need to kill Supervisor !!!\n".format(process,state))

        # # transition from READY to ACKNOWLEDGED
        write_stdout("RESULT 2\nOK")


if __name__ == "__main__":
    main()

