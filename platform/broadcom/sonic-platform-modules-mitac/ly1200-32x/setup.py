#!/usr/bin/env python

import os
import sys
from setuptools import setup
os.listdir

setup(
   name='ly1200_32x',
   version='1.0',
   description='Module to initialize Mitac LY1200-32X platforms',

   packages=['sys_serv_pkg'],
   package_dir={'sys_serv_pkg': 'ly1200-32x/classes/sys_serv_pkg'},
)

