"""Show techsupport command handler"""

import host_service
import subprocess
import re

MOD_NAME = 'showtech'

class Showtech(host_service.HostModule):
    """DBus endpoint that executes the "show techsupport" command
    """
    @host_service.method(host_service.bus_name(MOD_NAME), in_signature='s', out_signature='is')
    def info(self, date):

        ERROR_TAR_FAILED = 5
        ERROR_PROCFS_SAVE_FAILED = 6
        ERROR_INVALID_ARGUMENT = 10

        err_dict = {ERROR_INVALID_ARGUMENT: 'Invalid input: Incorrect DateTime format',
                    ERROR_TAR_FAILED: 'Failure saving information into compressed output file',
                    ERROR_PROCFS_SAVE_FAILED: 'Saving of process information failed'}

        cmd = ['/usr/local/bin/generate_dump']
        if date:
            cmd.append("-s")
            cmd.append(date)

        try:
            rc = 0
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    check=True)

        except subprocess.CalledProcessError as err:
            rc = err.returncode
            errmsg = err_dict.get(rc)

            if errmsg is None:
                output = 'Error: Failure code {:-5}'.format(rc)
            else:
                output = errmsg

            print("%Error: Host side: Failed: " + str(rc))
            return rc, output

        return rc, result.stdout

def register():
    """Return the class name"""
    return Showtech, MOD_NAME

