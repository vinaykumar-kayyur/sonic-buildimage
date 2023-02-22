import subprocess
import sys
from setuptools import setup

def secure_setup(**kwargs):
    install_list = ['requires', 'tests_require', 'install_requires' ]
    for keyword in install_list:
        packages = kwargs.get(keyword)
        if packages:
            for package in packages:
                proc = subprocess.Popen([sys.executable, '-m', 'pip', 'show', package.split("=")[0].split(">")[0].split("<")[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    sys.stdout.write(stdout)
                    sys.stderr.write(stderr)
                    sys.stderr.write("Please build and install SONiC python wheels dependencies from github.com/sonic-net/sonic-buildimage\n")
                    sys.stderr.write("Then install other dependencies from Pypi\n")
                    exit(1)
    setup(**kwargs)
