import os
import syslog

"""
Logging functionality for SONiC Python applications
"""


class Logger(object):
    """
    Logger class for SONiC Python applications
    """
    FACILITY_USER = syslog.LOG_USER
    FACILITY_DAEMON = syslog.LOG_DAEMON

    PRIORITY_ERROR = syslog.LOG_ERR
    PRIORITY_WARNING = syslog.LOG_WARNING
    PRIORITY_NOTICE = syslog.LOG_NOTICE
    PRIORITY_INFO = syslog.LOG_INFO
    PRIORITY_DEBUG = syslog.LOG_DEBUG

    def __init__(self, log_identifier=None, log_facility=FACILITY_USER):
        self.syslog = syslog

        if not log_identifier:
            log_identifier = os.path.basename(sys.argv[0])
            
        self.syslog.openlog(ident=log_identifier,
                            logoption=(syslog.LOG_PID | syslog.LOG_NDELAY),
                            facility=log_facility)

        # Set the default minimum log priority to PRIORITY_NOTICE
        self.set_min_log_priority(self.PRIORITY_NOTICE)

    def __del__(self):
        self.syslog.closelog()

    #
    # Methods for setting minimum log priority
    #

    def set_min_log_priority(self, priority):
        """
        Sets the minimum log priority level to <priority>. All log messages
        with a priority lower than <priority> will not be logged

        Args:
            priority: The minimum priority at which to log messages
        """
        self.syslog.setlogmask(self.syslog.LOG_UPTO(priority))

    def set_min_log_priority_error(self):
        """
        Convenience function to set minimum log priority to PRIORITY_ERROR
        """
        self.set_min_log_priority(self.PRIORITY_ERROR)

    def set_min_log_priority_warning(self):
        """
        Convenience function to set minimum log priority to PRIORITY_WARNING
        """
        self.set_min_log_priority(self.PRIORITY_WARNING)

    def set_min_log_priority_notice(self):
        """
        Convenience function to set minimum log priority to PRIORITY_NOTICE
        """
        self.set_min_log_priority(self.PRIORITY_NOTICE)

    def set_min_log_priority_info(self):
        """
        Convenience function to set minimum log priority to PRIORITY_INFO
        """
        self.set_min_log_priority(self.PRIORITY_INFO)

    def set_min_log_priority_debug(self):
        """
        Convenience function to set minimum log priority to PRIORITY_DEBUG
        """
        self.set_min_log_priority(self.PRIORITY_DEBUG)

    #
    # Methods for logging messages
    #

    def log(self, priority, msg, also_print_to_console=False):
        self.syslog.syslog(priority, msg)

        if also_print_to_console:
            print(msg)

    def log_error(self, msg, also_print_to_console=False):
        self.log(self.PRIORITY_ERROR, msg, also_print_to_console)

    def log_warning(self, msg, also_print_to_console=False):
        self.log(self.PRIORITY_WARNING, msg, also_print_to_console)

    def log_notice(self, msg, also_print_to_console=False):
        self.log(self.PRIORITY_NOTICE, msg, also_print_to_console)

    def log_info(self, msg, also_print_to_console=False):
        self.log(self.PRIORITY_INFO, msg, also_print_to_console)

    def log_debug(self, msg, also_print_to_console=False):
        self.log(self.PRIORITY_DEBUG, msg, also_print_to_console)
