from setuptools import setup, find_packages

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
    packages=find_packages(),
    data_files=[
        ('pit-sysdiag/src', ['pit-sysdiag/src/banner.py',
                             'pit-sysdiag/src/errcode.py',
                             'pit-sysdiag/src/sysdiag.py',
                             'pit-sysdiag/src/pit_util_common.py',
                             'pit-sysdiag/src/function.py',
                             'pit-sysdiag/src/syslogger.py',
                             'pit-sysdiag/src/test_case.py',
                             'pit-sysdiag/src/psu_tc.py',
                             'pit-sysdiag/src/fan_tc.py']),
        ('pit-sysdiag/cases/fan_tc', ['pit-sysdiag/cases/fan_tc/config.json']),
        ('pit-sysdiag/cases/psu_tc', ['pit-sysdiag/cases/psu_tc/config.json']),
        ('pit-sysdiag/config/platform/x86_64-alibaba_as14-40d-cl-r0', ['pit-sysdiag/config/platform/x86_64-alibaba_as14-40d-cl-r0/case_config.json', 'pit-sysdiag/config/platform/x86_64-alibaba_as14-40d-cl-r0/platform_config.json']),
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Utilities',
    ],
    keywords='SONiC Platform Integration Test'
)
