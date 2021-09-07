import subprocess
import show.main as show
from click.testing import CliRunner

expected_table = """\
--------  ------------
Vlan1000  fc02:2000::1
--------  ------------

"""
class TestDhcpRelayHelper(object):

    def test_show_dhcpv6_helper(self):
        runner = CliRunner()
        subprocess.run('sonic-db-cli CONFIG_DB hmset "DHCP_RELAY|Vlan1000" "fc02:2000::1"', shell=True)
        result = runner.invoke(show.cli.commands["dhcp_relay_helper"].commands["ipv6"], [])
        print(result.output)
        assert result.output == expected_table

