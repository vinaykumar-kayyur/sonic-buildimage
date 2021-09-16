import sys
import os
from unittest import mock
sys.path.append('../cli/show/plugins/')
import show_dhcpv6_helper as show
from click.testing import CliRunner

try:
    modules_path = os.path.join(os.path.dirname(__file__), "../../../src/sonic-utilities")
    test_path = os.path.join(modules_path, "tests")
    mock_table_path = os.path.join(test_path, "mock_tables")
    sys.path.insert(0, modules_path)
    sys.path.insert(0, test_path)
    sys.path.insert(0, mock_table_path)
    import dbconnector
except KeyError:
    pass
    
expected_table = """\
--------  ------------
Vlan1000  fc02:2000::1
          fc02:2000::2
--------  ------------

"""
class TestDhcpRelayHelper(object):

    def test_show_dhcpv6_helper(self):
        runner = CliRunner()
        result = runner.invoke(show.dhcp_relay_helper.commands["ipv6"], [])
        assert result.output == expected_table

