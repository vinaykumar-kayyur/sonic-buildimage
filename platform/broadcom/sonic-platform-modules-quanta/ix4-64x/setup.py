#!/usr/bin/env python

import os
import sys
from setuptools import setup
os.listdir

setup(
   name='ix4_64x',
   version='1.0',
   description='Module to initialize Quanta IX4-64X platforms',
   
   packages=['ix4_64x'],
   package_dir={'ix4_64x': 'ix4-64x/classes'},
)

