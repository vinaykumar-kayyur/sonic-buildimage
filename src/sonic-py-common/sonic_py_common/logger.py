import os
import syslog

"""
Logging functionality for SONiC Python applications
"""

FACILITY_USER = syslog.LOG_USER
FACILITY_DAEMON = syslog.LOG_DAEMON

class Logger(object):
    """
    Logger class for SONiC Python applications
    """
    def __init__(self, log_identifier=None, log_facility=FACILITY_USER):
        self.syslog = syslog

        if not log_identifier:
            log_identifier = os.path.basename(sys.argv[0])
            
        self.syslog.openlog(ident=log_identifier,
                            logoption=(syslog.LOG_PID | syslog.LOG_NDELAY),
                            facility=log_facility)

    def __del__(self):
        self.syslog.closelog()

    def log_error(self, msg, also_print_to_console=False):
        self.syslog.syslog(self.syslog.LOG_ERR, msg)

        if also_print_to_console:
            print(msg)

    def log_warning(self, msg, also_print_to_console=False):
        self.syslog.syslog(self.syslog.LOG_WARNING, msg)

        if also_print_to_console:
            print(msg)

    def log_notice(self, msg, also_print_to_console=False):
        self.syslog.syslog(self.syslog.LOG_NOTICE, msg)

        if also_print_to_console:
            print(msg)

    def log_info(self, msg, also_print_to_console=False):
        self.syslog.syslog(self.syslog.LOG_INFO, msg)

        if also_print_to_console:
            print(msg)

    def log_debug(self, msg, also_print_to_console=False):
        self.syslog.syslog(self.syslog.LOG_DEBUG, msg)

        if also_print_to_console:
            print(msg)
