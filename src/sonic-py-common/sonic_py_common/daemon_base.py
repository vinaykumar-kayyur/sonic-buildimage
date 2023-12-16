import logging
import signal
import sys
import syslog

from . import device_info
from .general import load_module_from_source
from .logger import Logger
from .syslogger import SysLogger

#
# Constants ====================================================================
#

REDIS_TIMEOUT_MSECS = 0

EEPROM_MODULE_NAME = 'eeprom'
EEPROM_CLASS_NAME = 'board'

# The empty namespace refers to linux host namespace.
EMPTY_NAMESPACE = ''

#
# Helper functions =============================================================
#


def db_connect(db_name, namespace=EMPTY_NAMESPACE):
    from swsscommon import swsscommon
    return swsscommon.DBConnector(db_name, REDIS_TIMEOUT_MSECS, True, namespace)


#
# DaemonBase ===================================================================
#


class DaemonBase(Logger):
    def __init__(self, log_identifier, use_syslogger=False):
        super().__init__()
        if use_syslogger:
            super().__init__()
            self.logger_instance = SysLogger(log_identifier)
        else:
            super().__init__(
                log_identifier=log_identifier,
                log_facility=Logger.LOG_FACILITY_DAEMON,
                log_option=(Logger.LOG_OPTION_NDELAY | Logger.LOG_OPTION_PID)
            )
        self.use_syslogger = use_syslogger

        # Register our default signal handlers, unless the signal already has a
        # handler registered, most likely from a subclass implementation
        if not signal.getsignal(signal.SIGHUP):
            signal.signal(signal.SIGHUP, self.signal_handler)
        if not signal.getsignal(signal.SIGINT):
            signal.signal(signal.SIGINT, self.signal_handler)
        if not signal.getsignal(signal.SIGTERM):
            signal.signal(signal.SIGTERM, self.signal_handler)

    def log(self, priority, msg, also_print_to_console=False):
        if self._min_log_priority >= priority:
            if self.use_syslogger:
                # Using SysLogger.
                self.logger_instance.log(priority, msg)
            else:
                # Using parent Logger class's log method.
                super().log(priority, msg)

            # Send message to console
            if also_print_to_console:
                print(msg)

    # Default signal handler; can be overridden by subclass
    def signal_handler(self, sig, frame):
        if sig == signal.SIGHUP:
            self.log_info("DaemonBase: Caught SIGHUP - ignoring...")
        elif sig == signal.SIGINT:
            self.log_info("DaemonBase: Caught SIGINT - exiting...")
            sys.exit(128 + sig)
        elif sig == signal.SIGTERM:
            self.log_info("DaemonBase: Caught SIGTERM - exiting...")
            sys.exit(128 + sig)
        else:
            self.log_warning("DaemonBase: Caught unhandled signal '{}'".format(sig))

    # Loads platform specific platform module from source
    def load_platform_util(self, module_name, class_name):
        platform_util = None

        # Get path to platform and hwsku
        (platform_path, hwsku_path) = device_info.get_paths_to_platform_and_hwsku_dirs()

        try:
            module_file = "/".join([platform_path, "plugins", module_name + ".py"])
            module = load_module_from_source(module_name, module_file)
        except IOError as e:
            raise IOError("Failed to load platform module '%s': %s" % (module_name, str(e)))

        try:
            platform_util_class = getattr(module, class_name)
            # board class of eeprom requires 4 paramerters, need special treatment here.
            if module_name == EEPROM_MODULE_NAME and class_name == EEPROM_CLASS_NAME:
                platform_util = platform_util_class('','','','')
            else:
                platform_util = platform_util_class()
        except AttributeError as e:
            raise AttributeError("Failed to instantiate '%s' class: %s" % (class_name, str(e)))

        return platform_util

    # Runs daemon
    def run(self):
        raise NotImplementedError()
