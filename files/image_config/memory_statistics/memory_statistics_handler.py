import os
import signal
import threading
import configparser
from swsscommon.swsscommon import ConfigDBConnector

class MemoryStatisticsDaemon:
    """
    Memory Statistics Daemon
    Responsible for collecting and storing memory usage statistics.
    1) Handle enabling or disabling the daemon via ConfigDB.
    2) Collect memory statistics at a configurable sampling interval.
    3) Handle retention of memory logs, deleting old logs when necessary.
    4) Respond to signals for reloading config (SIGHUP) and shutdown (SIGTERM).
    """

    def __init__(self):
        """git
        Initialize the MemoryStatisticsDaemon.
        Sets up directories, log files, and loads default settings.
        Also sets up signal handling for reloading and shutdown events.
        """
        self.hdir = "/var/log/memory_statistics"
        self.filename = os.path.join(self.hdir, "memory-statistics.log.gz")
        self.log_file = "/var/log/memory_statistics_daemon.log"
        self.initial_enable_state = False  # Initial enable state (default: disabled)
        self.logger = Logger(self.log_file, log_console=False)  # Initialize logger
        os.makedirs(self.hdir, exist_ok=True)  # Ensure memory statistics directory exists

        # Set up threading events to control running, reloading, and shutdown behavior
        self.running = threading.Event()
        self.reloading = threading.Event()
        self.shutdown_event = threading.Event()

        # Setup signal handlers for SIGHUP (reload) and SIGTERM (shutdown)
        signal.signal(signal.SIGHUP, self.handle_sighup)
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def load_default_settings(self):
        """
        Load default settings from the config file.
        If no config file is found, fallback values are used.
        """
        config = configparser.ConfigParser()
        config.read('/etc/memory_statistics.conf')  # Read configuration from the config file
        self.retention_period = config.getint('default', 'retention_period', fallback=15)  # Default retention period
        self.sampling_interval = config.getint('default', 'sampling_interval', fallback=5)  # Default sampling interval

    def load_config_from_db(self):
        """
        Load runtime configuration from the ConfigDB.
        Retrieves enable/disable state, retention period, and sampling interval.
        """
        self.config_db = ConfigDBConnector()
        self.config_db.connect()  # Connect to ConfigDB

        try:
            config = self.config_db.get_table('MEMORY_STATISTICS_TABLE')  # Get memory statistics config table

            # Update retention period and sampling interval with values from the database
            self.retention_period = int(config.get('retention-period', self.retention_period))
            self.sampling_interval = int(config.get('sampling-interval', self.sampling_interval))

            # Check if the daemon should be enabled or disabled
            enable_state = config.get('enable', 'false').lower() == 'true'
            if not enable_state:
                self.logger.log("Received disable command, shutting down daemon.", logging.INFO)
                self.handle_sigterm(None, None)

            self.logger.log("Configuration reloaded from ConfigDB.", logging.INFO)
        except Exception as e:
            self.logger.log(f"Error loading configuration from ConfigDB: {e}", logging.ERROR)
            raise

    def handle_sighup(self, signum, frame):
        """
        Handle the SIGHUP signal for reloading configuration.
        This sets the reloading flag to reload settings from the ConfigDB.
        """
        self.logger.log("Received SIGHUP, reloading configuration.", logging.INFO)
        self.reloading.set()  # Trigger reload

    def handle_sigterm(self, signum, frame):
        """
        Handle the SIGTERM signal for graceful shutdown.
        This sets the shutdown event to stop the daemon's operation cleanly.
        """
        self.logger.log("Received SIGTERM, shutting down gracefully.", logging.INFO)
        self.shutdown_event.set()  # Trigger shutdown

