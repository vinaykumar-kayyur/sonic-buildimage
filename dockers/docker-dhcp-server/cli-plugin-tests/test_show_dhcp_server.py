import sys
from unittest import mock

from click.testing import CliRunner

sys.path.append('../cli/show/plugins/')
import show_dhcp_server

class TestShowDHCPServer(object):
    def test_plugin_registration(self):
        cli = mock.MagicMock()
        show_dhcp_server.register(cli)

    def test_show_dhcp_server_ipv4_lease_without_dhcpintf(self, mock_db):
        runner = CliRunner()
        db = Db()
        db.db = mock_db()
        result = runner.invoke(show_dhcp_server.dhcp_server.ipv4.lease, [])
        assert result.exit_code == 0, "exit code: {}, Exception: {}, Traceback: {}".format(result.exit_code, result.exception, result.exc_info)

    def test_show_dhcp_server_ipv4_lease_with_dhcpintf(self, mock_db):
        runner = CliRunner()
        db = Db()
        db.db = mock_db()
        result = runner.invoke(show_dhcp_server.dhcp_server.ipv4.lease, ["Vlan1000"])
        assert result.exit_code == 0, "exit code: {}, Exception: {}, Traceback: {}".format(result.exit_code, result.exception, result.exc_info)

    def test_show_dhcp_server_ipv4_lease_client_not_in_fdb(self, mock_db):
        runner = CliRunner()
        db = Db()
        db.db = mock_db()
        result = runner.invoke(show_dhcp_server.dhcp_server.ipv4.lease, ["Vlan1001"])
        assert result.exit_code == 0, "exit code: {}, Exception: {}, Traceback: {}".format(result.exit_code, result.exception, result.exc_info)
