from setuptools import setup

dependencies = [
]

setup(
    name='sonic-pit',
    version='1.0',
    description='Platform Integration Test',
    license='Apache 2.0',
    author='S3IP PIT dev-team',
    author_email='guizhao.lh@alibaba-inc.com',
    maintainer='S3IP PIT dev-team',
    maintainer_email='guizhao.lh@alibaba-inc.com',
    install_requires=dependencies,
    packages=["pit-sysdiag",
              "pit-sysdiag.src",
              "pit-sysdiag.cases",
              "pit-sysdiag.config",
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
        'Programming Language :: Python :: 3.7',
        'Topic :: System :: Utilities',
    ],
    keywords='SONiC Platform Integration Test'
)
