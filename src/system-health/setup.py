from setuptools import setup
import sys
import subprocess

dependencies = [
    'natsort',
    'sonic_py_common',
    'docker'
]

def setup_fake(**kwargs):
    install_list = ['requires', 'tests_require', 'install_requires' ]
    for keyword in install_list:
        packages = kwargs.get(keyword)
        if packages:
            for package in packages:
                r = subprocess.call([sys.executable, '-m', 'pip', 'show', package.split("==")[0]])
                if r != 0:
                    sys.stderr.write("\033[33mPlease build and install SONiC python wheels dependencies from github.com/sonic-net/sonic-buildimage\033[0m\n")
                    sys.stderr.write("\033[33mThen install other dependencies from Pypi\033[0m\n")
                    exit(1)
    setup(**kwargs)

setup_fake(
    name='system-health',
    version='1.0',
    description='SONiC system health package',
    license='Apache 2.0',
    author='SONiC Team',
    author_email='linuxnetdev@microsoft.com',
    url='https://github.com/Azure/sonic-buildimage',
    maintainer='Junchao Chen',
    maintainer_email='junchaow@mellanox.com',
    install_requires=dependencies,
    packages=[
        'health_checker',
        'tests'
    ],
    scripts=[
        'scripts/healthd',
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest',
        'mock>=2.0.0'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Topic :: System :: Hardware',
    ],
    keywords='SONiC sonic HEALTH health',
    test_suite='setup.get_test_suite'
)
