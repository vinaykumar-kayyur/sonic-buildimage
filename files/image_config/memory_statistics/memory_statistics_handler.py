import os
import time
import gzip
import json
import syslog
import socket
import threading
import signal
from datetime import datetime
import psutil
from swsssdk import ConfigDBConnector


# Logger class for syslog
class Logger:
    def __init__(self, syslog_identifier, syslog_console=False):
        syslog.openlog(ident=syslog_identifier, logoption=syslog.LOG_NDELAY, facility=syslog.LOG_DAEMON)
        self.syslog_console = syslog_console

    def log(self, msg, level=syslog.LOG_INFO):
        syslog.syslog(level, msg)
        if self.syslog_console:
            print(msg)


class MemoryStatsDaemon:
    def __init__(self):
        # Configuration Settings
        self.hdir = "/var/log/memory_statistics"
        self.filename = "/var/log/memory_statistics/mem-stats-total.log.gz"
        self.server_address = '/var/run/dbus/memstats.socket'
        self.syslog_id = "sysmon#mem"
        self.syslog_console = False

        # Dynamic configuration that may change at runtime
        self.enable = False
        self.retention_period = 7
        self.sampling_interval = 300

        # Setup logging
        self.logger = Logger(self.syslog_id, self.syslog_console)

        # Ensure logging directory exists
        os.makedirs(self.hdir, exist_ok=True)

        # Initialize ConfigDB connection
        self.config_db = ConfigDBConnector()
        self.config_db.connect()

        # Load initial configuration
        self.load_config()

        # Set the running flag
        self.running = True

        # Register SIGHUP signal handler for reloading config
        signal.signal(signal.SIGHUP, self.handle_sighup)

    def load_config(self):
        config = self.config_db.get_table('MEMORY_STATS')
        self.enable = config.get('enable', 'false').lower() == 'true'
        self.retention_period = int(config.get('retention-period', 7))
        self.sampling_interval = int(config.get('sampling-interval', 300))

        self.logger.log("Configuration loaded.", syslog.LOG_INFO)

    def handle_sighup(self, signum, frame):
        self.logger.log("Received SIGHUP, reloading configuration.", syslog.LOG_INFO)
        self.load_config()

    def collect_memory_usage(self):
        meminfo = psutil.virtual_memory()
        memdict = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total': meminfo.total,
            'used': meminfo.used,
            'free': meminfo.free,
            'buffers': meminfo.buffers,
            'cached': meminfo.cached,
            'available': meminfo.available
        }
        return memdict

    def store_memory_log(self, memdict):
        with gzip.open(self.filename, "ab") as f:
            f.write(json.dumps(memdict).encode('utf-8') + b'\n')
        self.logger.log("Stored memory log entry.", syslog.LOG_DEBUG)

    def collect_and_store_memory(self):
        while self.running:
            if self.enable:
                try:
                    mem_dict = self.collect_memory_usage()
                    self.store_memory_log(mem_dict)
                except Exception as e:
                    self.logger.log(f"Error collecting/storing memory usage: {str(e)}", syslog.LOG_ERR)
            time.sleep(self.sampling_interval)

    def handle_client_connection(self, client_socket):
        try:
            with open(self.filename, 'rb') as f:
                logs = f.read()
            client_socket.sendall(logs)
        except Exception as e:
            self.logger.log(f"Error handling client connection: {str(e)}", syslog.LOG_ERR)
        finally:
            client_socket.close()

    def start_socket_server(self):
        if os.path.exists(self.server_address):
            os.remove(self.server_address)

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.server_address)
        server.listen(5)
        self.logger.log("Socket server started.", syslog.LOG_INFO)

        while self.running:
            client_socket, _ = server.accept()
            client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_socket,)
            )
            client_handler.start()

    def run(self):
        self.logger.log("Memory statistics daemon started.", syslog.LOG_INFO)

        # Start the memory collection and storage thread
        memory_thread = threading.Thread(target=self.collect_and_store_memory)
        memory_thread.daemon = True
        memory_thread.start()

        # Start the socket server for CLI communication
        self.start_socket_server()


if __name__ == "__main__":
    daemon = MemoryStatsDaemon()
    daemon.run()
