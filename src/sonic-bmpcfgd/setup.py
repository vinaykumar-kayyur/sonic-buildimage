from __future__ import print_function
import sys
from setuptools import setup
import pkg_resources
from packaging import version

# sonic_dependencies, version requirement only supports '>='
sonic_dependencies = ['sonic-py-common', 'sonic-utilities']
for package in sonic_dependencies:
    try:
        package_dist = pkg_resources.get_distribution(package.split(">=")[0])
    except pkg_resources.DistributionNotFound:
        print(package + " is not found!", file=sys.stderr)
        print("Please build and install SONiC python wheels dependencies from sonic-buildimage", file=sys.stderr)
        exit(1)
    if ">=" in package:
        if version.parse(package_dist.version) >= version.parse(package.split(">=")[1]):
            continue
        print(package + " version not match!", file=sys.stderr)
        exit(1)

setup(
    name = 'sonic-bmpcfgd-services',
    version = '1.0',
    description = 'Python services which run in the bmp container',
    license = 'Apache 2.0',
    author = 'SONiC Team',
    author_email = 'linuxnetdev@microsoft.com',
    url = 'https://github.com/Azure/sonic-buildimage',
    maintainer = 'Feng Pan',
    maintainer_email = 'fenpan@microsoft.com',
    packages = [
        'host_modules'
    ],
    scripts = [
        'scripts/bmpcfgd'
    ],
    install_requires = [
        'dbus-python',
        'systemd-python',
        'Jinja2>=2.10',
        'PyGObject',
        'psutil'
    ] + sonic_dependencies,
    setup_requires = [
        'pytest-runner',
        'wheel'
    ],
    tests_require = [
        'parameterized',
        'pytest',
        'pyfakefs',
        'sonic-py-common',
        'deepdiff==6.2.2',
        'psutil'
    ],
    extras_require = {
        "testing": [
            'parameterized',
            'pytest',
            'pyfakefs',
            'sonic-py-common',
            'deepdiff==6.2.2'
        ]
    },
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Topic :: System',
    ],
    keywords = 'sonic SONiC bmp services',
    test_suite = 'setup.get_test_suite'
)
