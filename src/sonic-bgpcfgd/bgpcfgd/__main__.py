import sys
import syslog
import signal
import traceback
import os

from .main import main
from .vars import g_debug
from .log import log_notice, log_crit


def signal_handler(_, __):  # signal_handler(signum, frame)
    """ signal handler """
    global g_run
    g_run = False


if __name__ == '__main__':
    rc = 0
    try:
        syslog.openlog('bgpcfgd')
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        main()
    except KeyboardInterrupt:
        log_notice("Keyboard interrupt")
    except RuntimeError as exc:
        log_crit(str(exc))
        rc = -2
        if g_debug:
            raise
    except Exception as exc:
        log_crit("Got an exception %s: Traceback: %s" % (str(exc), traceback.format_exc()))
        rc = -1
        if g_debug:
            raise
    finally:
        syslog.closelog()
    try:
        sys.exit(rc)
    except SystemExit:
        os._exit(rc)
