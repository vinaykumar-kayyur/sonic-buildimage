import subprocess
import sys
from setuptools import setup

def secure_setup(**kwargs):
    install_list = ['requires', 'tests_require', 'install_requires' ]
    for keyword in install_list:
        packages = kwargs.get(keyword)
        if packages:
            for package in packages:
                r = subprocess.call([sys.executable, '-m', 'pip', 'show', package.split("=")[0].split(">")[0].split("<")[0]], stdout=sys.stderr.fileno())
                if r != 0:
                    sys.stderr.write("Please build and install SONiC python wheels dependencies from github.com/sonic-net/sonic-buildimage\n")
                    sys.stderr.write("Then install other dependencies from Pypi\n")
                    exit(1)
    setup(**kwargs)
