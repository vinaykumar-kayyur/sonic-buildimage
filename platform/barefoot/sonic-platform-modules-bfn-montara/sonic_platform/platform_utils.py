#!/usr/bin/env python

try:
    import os
    import subprocess
    import signal
    from functools import wraps

except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

def file_create(path, mode=None):
    def run_cmd(cmd):
        if os.geteuid() != 0:
            cmd.insert(0, 'sudo')
        subprocess.check_output(cmd)

    file_path = os.path.dirname(path)
    if not os.path.exists(file_path):
        run_cmd(['mkdir', '-p', file_path])
    if not os.path.isfile(path):
        run_cmd(['touch', path])
    if (mode is not None):    
        run_cmd(['chmod', mode, path])

def cancel_on_sigterm(func):
    """
    Wrapper for a function which has to be cancel on SIGTERM
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        def handler(sig, frame):
            if sigterm_handler:
                sigterm_handler(sig, frame)
            raise Exception("Canceling {}() execution...".format(func.__name__))

        sigterm_handler = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, handler)
        result = None
        try:
            result = func(*args, **kwargs)
        finally:
            signal.signal(signal.SIGTERM, sigterm_handler)
        return result
    return wrapper