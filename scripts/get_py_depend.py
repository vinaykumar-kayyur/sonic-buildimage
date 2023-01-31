#!/usr/bin/python3

import setuptools
from distutils import core

def setup(**kwargs):
        ret=[]
        a=kwargs.get('setup_requires')
        b=kwargs.get('tests_require')
        c=kwargs.get('install_requires')
        if a:
            ret+=a
        if b:
            ret+=b
        if c:
            ret+=c
        for i,x in enumerate(ret):
            print("'"+x+"'")


if __name__ == "__main__":
  setuptools.setup=setup
  core.setup=setup
  content = open('setup.py').read()
  exec(content)
