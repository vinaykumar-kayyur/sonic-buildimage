#!/usr/bin/env python

import setuptools

setuptools.setup(
        name='sonic-ctrmgrd',
        version='1.0.0',
        author='Renuka Manavalan',
        author_email='remanava@microsoft.com',
        description='Collection all scripts required to support remote container management',
        url='https://github.com/Azure/sonic-buildimage',
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        python_requires='>=3.6',
        install_requires=['netaddr', 'pyyaml'],
        scripts=['container_action', 'kube_commands.py', 'ctrmgrd.py'],
)
