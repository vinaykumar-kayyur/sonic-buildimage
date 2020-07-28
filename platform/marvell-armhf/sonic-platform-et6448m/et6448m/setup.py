#!/usr/bin/env python
import os
import sys
from setuptools import setup
os.listdir
setup(
    name='sonic_platform',
    version='1.0',
    description='Module to initialize et6448m platforms',
    packages=['sonic_platform'],
    package_dir={'sonic_platform': 'et6448m/sonic_platform'},
     )
