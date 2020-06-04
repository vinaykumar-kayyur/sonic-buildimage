from setuptools import setup

setup(
    name='system-health',
    version='1.0',
    description='SONiC system health package',
    license='Apache 2.0',
    author='SONiC Team',
    author_email='linuxnetdev@microsoft.com',
    url='https://github.com/Azure/sonic-buildimage',
    maintainer='Junchao Chen',
    maintainer_email='junchaow@mellanox.com',
    packages=[
        'health_checker',
    ],
    scripts=[
        'scripts/healthd',
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
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Hardware',
    ],
    keywords='SONiC sonic HEALTH health',
)

