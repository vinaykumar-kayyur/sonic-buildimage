# TODO Add support for running different dhcrelay processes for each dhcp interface
# Currently if we run multiple dhcrelay processes, except for the last running process,
# others will not relay dhcp_release packet.
import psutil
import subprocess
import sys
import syslog
import time
from swsscommon import swsscommon
from .dhcp_server_utils import DhcpDbConnector

REDIS_SOCK_PATH = "/var/run/redis/redis.sock"
DHCP_SERVER_IPV4_SERVER_IP = "DHCP_SERVER_IPV4_SERVER_IP"
DHCP_SERVER_IPV4 = "DHCP_SERVER_IPV4"
VLAN = "VLAN"
DEFAULT_SELECT_TIMEOUT = 5000  # millisecond
DHCP_SERVER_INTERFACE = "eth0"
DEFAULT_REFRESH_INTERVAL = 2

KILLED_OLD = 1
NOT_KILLED = 2
NOT_FOUND_PROC = 3


class DhcpRelayd(object):
    sel = None
    subscribe_dhcp_server_table = None
    subscribe_vlan_table = None
    dhcp_interfaces_state = {}

    def __init__(self, db_connector, select_timeout=DEFAULT_SELECT_TIMEOUT):
        """
        Args:
            db_connector: db connector obj
            select_timeout: timeout setting for subscribe db change
        """
        self.db_connector = db_connector
        self.last_refresh_time = None
        self.select_timeout = select_timeout

    def start(self):
        """
        Start function
        """
        self.refresh_dhcrelay()
        self._subscribe_config_db()

    def refresh_dhcrelay(self):
        """
        To refresh dhcrelay/dhcpmon process (start or restart)
        """
        syslog.syslog(syslog.LOG_INFO, "Start to refresh dhcrelay related processes")
        dhcp_server_ip = self._get_dhcp_server_ip()
        dhcp_server_ipv4_table = self.db_connector.get_config_db_table(DHCP_SERVER_IPV4)
        vlan_table = self.db_connector.get_config_db_table(VLAN)

        dhcp_interfaces = set()
        self.dhcp_interfaces_state = {}
        for dhcp_interface, config in dhcp_server_ipv4_table.items():
            self.dhcp_interfaces_state[dhcp_interface] = config["state"]
            if dhcp_interface not in vlan_table:
                continue
            if config["state"] == "enabled":
                dhcp_interfaces.add(dhcp_interface)
        self._start_dhcrelay_process(dhcp_interfaces, dhcp_server_ip)
        self._start_dhcpmon_process(dhcp_interfaces)

    def wait(self):
        """
        Wait function, check db change here
        """
        while True:
            self._config_db_update_event()

    def _subscribe_config_db(self):
        self.sel = swsscommon.Select()
        self.subscribe_dhcp_server_table = swsscommon.SubscriberStateTable(self.db_connector.config_db,
                                                                           DHCP_SERVER_IPV4)
        self.subscribe_vlan_table = swsscommon.SubscriberStateTable(self.db_connector.config_db, VLAN)
        # Subscribe dhcp_server_ipv4 and vlan table. No need to subscribe vlan_member table
        self.sel.addSelectable(self.subscribe_dhcp_server_table)
        self.sel.addSelectable(self.subscribe_vlan_table)

    def _config_db_update_event(self):
        state, _ = self.sel.select(self.select_timeout)
        if state == swsscommon.Select.TIMEOUT or state != swsscommon.Select.OBJECT:
            return

        need_refresh = self._check_dhcp_server_update()
        need_refresh |= self._check_vlan_update()
        if need_refresh:
            self.refresh_dhcrelay()

    def _check_dhcp_server_update(self):
        need_refresh = False
        while not self.subscribe_dhcp_server_table.empty():
            key, op, entry = self.subscribe_dhcp_server_table.pop()
            if op == "SET":
                for field, value in entry:
                    if field != "state":
                        continue
                    # Only if new state is disabled and old state is disabled, we can skip. Other scenarios need refres
                    if not (value == "disabled" and (key not in self.dhcp_interfaces_state
                                                     or self.dhcp_interfaces_state[key] == "disabled")):
                        need_refresh = True
            # For del operation, we can skip disabled change
            if op == "DEL":
                if key in self.dhcp_interfaces_state:
                    if self.dhcp_interfaces_state[key] == "enabled":
                        need_refresh = True
                    else:
                        del self.dhcp_interfaces_state[key]
        return need_refresh

    def _check_vlan_update(self):
        need_refresh = False
        while not self.subscribe_vlan_table.empty():
            key, op, _ = self.subscribe_vlan_table.pop()
            # For vlan doesn't have related dhcp entry, not need to refresh dhcrelay process
            if key not in self.dhcp_interfaces_state:
                continue
            if self.dhcp_interfaces_state[key] == "disabled":
                if op == "DEL":
                    del self.dhcp_interfaces_state[key]
            else:
                need_refresh = True
        return need_refresh

    def _start_dhcrelay_process(self, new_dhcp_interfaces, dhcp_server_ip):
        # To check whether need to kill dhcrelay process
        kill_res = self._kill_exist_relay_releated_process(new_dhcp_interfaces, "dhcrelay")
        if kill_res == NOT_KILLED:
            # Means old running status consistent with the new situation, no need to run new
            return

        # No need to start new dhcrelay process
        if len(new_dhcp_interfaces) == 0:
            return

        cmds = ["/usr/sbin/dhcrelay", "-d", "-m", "discard", "-a", "%h:%p", "%P", "--name-alias-map-file",
                "/tmp/port-name-alias-map.txt"]
        for dhcp_interface in new_dhcp_interfaces:
            cmds += ["-id", dhcp_interface]
        cmds += ["-iu", "docker0", dhcp_server_ip]
        subprocess.Popen(cmds)
        syslog.syslog(syslog.LOG_INFO, "dhcrelay process started successfully, cmds: {}".format(cmds))

    def _start_dhcpmon_process(self, new_dhcp_interfaces):
        # To check whether need to kill dhcrelay process
        kill_res = self._kill_exist_relay_releated_process(new_dhcp_interfaces, "dhcpmon")
        if kill_res == NOT_KILLED:
            # Means old running status consistent with the new situation, no need to run new
            return

        # No need to start new dhcrelay process
        if len(new_dhcp_interfaces) == 0:
            return

        for dhcp_interface in new_dhcp_interfaces:
            cmds = ["/usr/sbin/dhcpmon", "-id", dhcp_interface, "-iu", "docker0", "-im", "eth0"]
            subprocess.Popen(cmds)
            syslog.syslog(syslog.LOG_INFO, "dhcpmon process started successfully, cmds: {}".format(cmds))

    def _kill_exist_relay_releated_process(self, new_dhcp_interfaces, process_name):
        old_dhcp_interfaces = set()
        target_proc = None

        # Get old dhcrelay process and get old dhcp interfaces
        for proc in psutil.process_iter():
            if proc.name() == process_name:
                cmds = proc.cmdline()
                index = 0
                target_proc = proc
                while index < len(cmds):
                    if cmds[index] == "-id":
                        old_dhcp_interfaces.add(cmds[index + 1])
                        index += 2
                    else:
                        index += 1
        if target_proc is None:
            return NOT_FOUND_PROC

        # No need to kill
        if process_name == "dhcrelay" and old_dhcp_interfaces == new_dhcp_interfaces or \
           process_name == "dhcpmon" and old_dhcp_interfaces == (new_dhcp_interfaces):
            return NOT_KILLED

        target_proc.terminate()
        target_proc.wait()
        syslog.syslog(syslog.LOG_INFO, "Kill process: {}".format(process_name))
        return KILLED_OLD

    def _get_dhcp_server_ip(self):
        dhcp_server_ip_table = swsscommon.Table(self.db_connector.state_db, DHCP_SERVER_IPV4_SERVER_IP)
        for _ in range(10):
            state, ip = dhcp_server_ip_table.hget(DHCP_SERVER_INTERFACE, "ip")
            if state:
                return ip
            else:
                syslog.syslog(syslog.LOG_INFO, "Cannot get dhcp server ip")
                time.sleep(10)
        syslog.syslog(syslog.LOG_ERR, "Cannot get dhcp_server ip from state_db")
        sys.exit(1)


def main():
    dhcp_db_connector = DhcpDbConnector(redis_sock=REDIS_SOCK_PATH)
    dhcprelayd = DhcpRelayd(dhcp_db_connector)
    dhcprelayd.start()
    dhcprelayd.wait()


if __name__ == "__main__":
    main()
