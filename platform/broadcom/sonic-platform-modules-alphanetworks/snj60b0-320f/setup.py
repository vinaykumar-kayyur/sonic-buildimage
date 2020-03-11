#!/usr/bin/env python

import os
import sys
from setuptools import setup
os.listdir

setup(
   name='snj60b0_320f',
   version='1.0',
   description='Module to initialize Alphanetworks SNJ60B0-320F platforms',
   
   packages=['snj60b0_320f'],
   package_dir={'snj60b0_320f': 'snj60b0-320f/classes'},
)

