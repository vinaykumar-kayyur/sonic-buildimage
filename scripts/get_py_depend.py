#!/usr/bin/python3

import setuptools
from distutils import core

def setup(**kwargs):
  ret=kwargs.get('tests_require')
  if ret:
    for i,x in enumerate(ret):
      print("'"+x+"'")


if __name__ == "__main__":
  setuptools.setup=setup
  core.setup=setup
  content = open('setup.py').read()
  exec(content)
