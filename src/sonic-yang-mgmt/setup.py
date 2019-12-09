#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from os import system
from sys import exit

# important reuirements parameters
build_requirements = ['../../target/debs/stretch/libyang_1.0.73_amd64.deb',
                      '../../target/debs/stretch/libyang-cpp_1.0.73_amd64.deb',
                      '../../target/debs/stretch/python2-yang_1.0.73_amd64.deb']

install_requirements = []

setup_requirements = ['pytest-runner',]

test_requirements = ['pytest>=3',]

# read me
with open('README.rst') as readme_file:
    readme = readme_file.read()

# class for prerequisites to build this package
class pkgBuild(build_py):
    """Custom Build PLY"""

    def run (self):
        # install libyang, it will be used for testing a build time
        for req in build_requirements:
            if 'target/debs'in req:
                pkg_install_cmd = "sudo dpkg -i {}".format(req)
                if (system(pkg_install_cmd)):
                    print("{} installed failed".format(req))
                else:
                    print("{} installed".format(req))

        # Continue usual build steps
        build_py.run(self)


setup(
    cmdclass={
        'build_py': pkgBuild,
    },
    author="lnos-coders",
    author_email='lnos-coders@linkedin.com',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Package contains YANG models for sonic.",
    install_requires=install_requirements,
    tests_require = test_requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n',
    include_package_data=True,
    keywords='sonic_yang_mgmt',
    name='sonic_yang_mgmt',
    # py_modules=['sonic_yang'],
    packages=find_packages(),
    setup_requires=setup_requirements,
    version='1.0',
    zip_safe=False,
)
