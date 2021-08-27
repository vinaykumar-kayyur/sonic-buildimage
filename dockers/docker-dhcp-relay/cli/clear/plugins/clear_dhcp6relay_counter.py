import sys
import click
sys.path.insert(0, '../../show/plugins/')
from show_dhcp6relay_counters import DHCPv6_Counter


# sonic-clear dhcp6relay_counters
@click.command('dhcp6relay_counters')
@click.option('-i', '--interface', required=False)
def dhcp6relay_clear_counters(interface):
    """ Clear dhcp6relay message counts """
    
    counter = DHCPv6_Counter()
    counter_intf = counter.get_interface()

    if interface:
        counter.clear_table(interface)
    else:
        for intf in counter_intf:
                counter.clear_table(intf)

def register(cli):
    cli.add_command(dhcp6relay_clear_counters)

if __name__ == '__main__':
    dhcp6relay_clear_counters()
