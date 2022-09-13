import sys
import subprocess


def load_module_from_source(module_name, file_path):
    """
    This function will load the Python source file specified by <file_path>
    as a module named <module_name> and return an instance of the module
    """
    module = None

    # TODO: Remove this check once we no longer support Python 2
    if sys.version_info.major == 3:
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader(module_name, file_path)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
    else:
        import imp
        module = imp.load_source(module_name, file_path)

    sys.modules[module_name] = module

    return module


def getstatusoutput_noshell(cmd):
    """
    This function implements getstatusoutput API from subprocess module
    but using shell=False to prevent shell injection.
    """
    p = subprocess.run(cmd, capture_output=True, universal_newlines=True)
    status, output = p.returncode, p.stdout
    if output[-1:] == '\n':
        output = output[:-1]
    return (status, output)


def getstatusoutput_noshell_pipe(cmd1, cmd2):
    """
    This function implements getstatusoutput API from subprocess module
    but using shell=False to prevent shell injection. Input command includes
    pipe command.
    """
    status = 0
    with subprocess.Popen(cmd1, universal_newlines=True, stdout=subprocess.PIPE) as p1:
        with subprocess.Popen(cmd2, universal_newlines=True, stdin=p1.stdout, stdout=subprocess.PIPE) as p2:
            output = p2.communicate()[0]
            p1.wait()
            if p1.returncode != 0 and p2.returncode != 0:
                status = 1
    if output[-1:] == '\n':
        output = output[:-1]
    return (status, output)
