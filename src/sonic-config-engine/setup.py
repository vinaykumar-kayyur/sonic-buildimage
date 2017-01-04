#!/usr/bin/env python

from distutils.core import setup

setup(name='sonic-config-engine',
      version='1.0',
      description='Utilities for generating SONiC configuration files',
      author='Taoyu Li',
      author_email='taoyl@microsoft.com',
      url='https://github.com/Azure/sonic-buildimage',
      py_modules=['minigraph'],
      scripts=['render_config'],
     )
