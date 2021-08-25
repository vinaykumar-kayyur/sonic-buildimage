import click
sys.path.insert(0, '../../show/plugins/')
import show_dhcp6relay_counters


# sonic-clear dhcp6relay_counters
@click.command()
@click.option('-i', '--interface', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def dhcp6relay_counter_clear(interface, verbose):
    """Clear dhcp6relay message counts"""
    
    counter = DHCPv6_Counter()
    counter_intf = counter.get_interface()

    if interface:
        counter.clear_table(interface)
    else:
        for intf in counter_intf:
                counter.clear_table(intf)

def register(cli):
    cli.add_command(dhcp6relay_counter_clear)