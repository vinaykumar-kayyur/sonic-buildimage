import os
import click

import show.plugins.macsec as show_macsec
import utilities_common.cli as clicommon


@click.group(cls=clicommon.AliasedGroup)
def macsec():
    pass


@macsec.command('macsec')
@click.option('--clean-cache', type=bool, required=False, default=False)
def macsec_clear_counters(clean_cache):
    """ Clear MACsec counts """

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