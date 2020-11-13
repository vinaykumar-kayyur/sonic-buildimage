#!/usr/bin/env python3

import signal
import os
import sys
import syslog

SCRIPT_PATH = '/usr/share/sonic/scripts/'

name = None

def mark_end():
    if os.path.exists(os.path.join(SCRIPT_PATH, "container_state.py")):
        sys.path.append('/usr/share/sonic/scripts/')
        import container_state
        container_state.container_down(name)
        syslog.syslog(syslog.LOG_INFO, "Marking end of docker {}".format(name))


def handler(signum, frame):
    syslog.syslog(syslog.LOG_ERR, "Received signal {}".format(signum))
    mark_end()


def main():
    global name

    if (len(sys.argv) < 2):
        print("Usage {} <container name>".format(sys.argv[0]))
        syslog.syslog(syslog.LOG_ERR, "Usage {} <container name>".format(sys.argv[0]))
        sys.exit(-1)

    name = sys.argv[1]
    signal.signal(signal.SIGTERM, handler)

    syslog.syslog(syslog.LOG_INFO, "Sleep until signal for {}".format(name))
    signal.pause()


if __name__ == "__main__":
    main()
