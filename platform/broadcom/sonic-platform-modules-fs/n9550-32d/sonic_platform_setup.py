#!/usr/bin/env pytho

import os
import sys
from setuptools import setup
os.listdir

setup(
   name='sonic_platform',
   version='1.0',
   description='SONiC platform API implementation on FS Platforms',
   
   packages=['sonic-platform'],
   package_dir={'sonic_platform': 'n9550-32d/sonic_platform'},
)

