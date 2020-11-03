#!/usr/bin/env python

import signal
import syslog
import sys

sys.path.append('/usr/share/sonic/scripts/')
import container_state

name = None

def mark_end():
    container_state.down(name)
    syslog.syslog(syslog.LOG_INFO, "Marking end of docker {}".format(name))


def handler(signum, frame):
    syslog.syslog(syslog.LOG_ERR, "Received signal {}".format(signum))
    mark_end()


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
