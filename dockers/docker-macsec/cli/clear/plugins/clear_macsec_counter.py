import os
import click

import show.plugins.macsec as show_macsec
import utilities_common.cli as clicommon


@click.group(cls=clicommon.AliasedGroup)
def macsec():
    pass


@macsec.command('macsec')
@click.option('--clean-cache', type=bool, required=False, default=False, help="If the option of clean cache is true, next show commands will show the raw counters which based on the service booted instead of the last clear command.")
def macsec_clear_counters(clean_cache):
    """ 
        Clear MACsec counts.
        This clear command will generated a cache for next show commands which will base on this cache as the zero baseline to show the increment of counters.
    """

    if clean_cache:
        os.remove(show_macsec.CACHE_FILE)
        print("Clean cache {}".format(show_macsec.CACHE_FILE))
        return

    clicommon.run_command("show macsec --dump-file {}".format(show_macsec.CACHE_FILE))
    print("Clear MACsec counters")


def register(cli):
    cli.add_command(macsec_clear_counters)


if __name__ == '__main__':
    macsec_clear_counters(None)