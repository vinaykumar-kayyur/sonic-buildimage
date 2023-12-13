import sys
from unittest import mock

from click.testing import CliRunner

import utilities_common.cli as clicommon

sys.path.append('../cli/config/plugins/')
import config_dhcp_server


class TestConfigDHCPServer(object):
    def test_plugin_registration(self):
        cli = mock.MagicMock()
        config_dhcp_server.register(cli)

    def test_config_dhcp_server_ipv4_add(self, mock_db):
        expected_value = {
            "gateway": "100.10.10.10",
            "lease_time": "1000",
            "mode": "PORT",
            "netmask": "255.255.254.0",
            "state": "disabled"
        }
        runner = CliRunner()
        db = clicommon.Db()
        db.db = mock_db
        result = runner.invoke(config_dhcp_server.dhcp_server.commands["ipv4"].commands["add"], \
                ["Vlan200", "--mode=PORT", "--lease_time=1000", "--gateway=10.10.10.10", "--netmask=255.255.254.0"], obj=db)
        assert result.exit_code == 0, "exit code: {}, Exception: {}, Traceback: {}".format(result.exit_code, result.exception, result.exc_info)
        assert mock_db.get_all("CONFIG_DB", "DHCP_SERVER_IPV4|Vlan200") == expected_value

