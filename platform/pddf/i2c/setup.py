#!/usr/bin/env python

from setuptools import setup
import os

setup(
   name='pddf-platform',
   version='%s' % os.environ.get('PLATFORM_MODULE_VERSION', '1.0'),
   description='Module consisting of generic drivers to initialize platform',
   packages=[
      'modules',
   ],
)

