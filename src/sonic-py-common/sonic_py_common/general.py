import sys
from subprocess import Popen, STDOUT, PIPE, CalledProcessError, check_output


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
    try:
        output = check_output(cmd, text=True, stderr=STDOUT)
        exitcode = 0
    except CalledProcessError as ex:
        output = ex.output
        exitcode = ex.returncode
    if output[-1:] == '\n':
        output = output[:-1]
    return exitcode, output


def getstatusoutput_noshell_pipe(cmd1, cmd2):
    """
    This function implements getstatusoutput API from subprocess module
    but using shell=False to prevent shell injection. Input command includes
    pipe command.
    """
    with Popen(cmd1, universal_newlines=True, stdout=PIPE) as p1:
        with Popen(cmd2, universal_newlines=True, stdin=p1.stdout, stdout=PIPE) as p2:
            output = p2.communicate()[0]
            p1.wait()
            if p1.returncode != 0 or p2.returncode != 0:
                return ([p1.returncode, p2.returncode], output)
    if output[-1:] == '\n':
        output = output[:-1]
    return ([0, 0], output)


def check_output_pipe(cmd1, cmd2):
    """
    This function implements check_output API from subprocess module.
    Input command includes pipe command.
    """
    cmd = ' '.join(cmd1) + ' | ' + ' '.join(cmd2)
    with Popen(cmd1, universal_newlines=True, stdout=PIPE) as p1:
        with Popen(cmd2, universal_newlines=True, stdin=p1.stdout, stdout=PIPE) as p2:
            output = p2.communicate()[0]
            p1.wait()
            if p1.returncode != 0 or p2.returncode != 0:
                if p1.returncode != 0:
                    raise CalledProcessError(returncode=p1.returncode, cmd=cmd, output=output)
                else:
                    raise CalledProcessError(returncode=p2.returncode, cmd=cmd, output=output)
    return output

