#!/usr/bin/python3

import os
import sys
import setuptools
from distutils import core

def setup(**kwargs):
  ret=kwargs.get('tests_require')
  if ret:
    for i,x in enumerate(ret):
      os.system("pip" + str(sys.version_info.major) + " install " + '"' + x + '"')


if __name__ == "__main__":
  setuptools.setup=setup
  core.setup=setup
  content = open('setup.py').read()
  exec(content)
