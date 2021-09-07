import show.main as show
from click.testing import CliRunner


expected_counts = """\
  Message Type
--------------  --
       Solicit
     Advertise
       Request
       Confirm
         Renew
        Rebind
         Reply
       Release
       Decline
 Relay-Forward
   Relay-Reply

"""
class TestDhcp6RelayCounters(object):

    def test_show_counts(self):
        runner = CliRunner()
        #runner.invoke(clear.cli.commands["dhcp6relay-counters"], [])
        result = runner.invoke(show.cli.commands["dhcp6relay-counters"].commands["counts"], [])
        print(result.output)
        assert result.output == expected_counts

