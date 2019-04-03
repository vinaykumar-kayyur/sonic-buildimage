from setuptools import setup

setup(
    name='cel-platform-api',
    version='0.1',
    description='SONiC platform management API implementation for Celestica platform',
    license='Apache 2.0',
    author='SONiC Team',
    author_email='linuxnetdev@microsoft.com',
    url='https://github.com/Azure/sonic-buildimage',
    maintainer='Wirut Getbamrung',
    maintainer_email='wgetbumr@celestica.com',
    packages=[
         'sonic_platform_api',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
    ],
    keywords='sonic SONiC platform-api PLATFORM-API',
)
