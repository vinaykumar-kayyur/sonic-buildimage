from setuptools import setup

setup(
    name = 'sonic-host-services',
    version = '1.0',
    description = 'Python services which run in the SONiC host OS',
    license = 'Apache 2.0',
    author = 'SONiC Team',
    author_email = 'linuxnetdev@microsoft.com',
    url = 'https://github.com/Azure/sonic-buildimage',
    maintainer = 'Joe LeVeque',
    maintainer_email = 'jolevequ@microsoft.com', #TODO invalid e-mail
    packages = [
        'host_modules'
    ],
    scripts = [
        'scripts/caclmgrd',
        'scripts/hostcfgd',
        'scripts/aaastatsd',
        'scripts/procdockerstatsd',
        'scripts/determine-reboot-cause',
        'scripts/process-reboot-cause',
        'scripts/sonic-host-server',
        'scripts/pcied'
    ],
    install_requires = [
        'dbus-python',
        'Jinja2>=2.10',
        'PyGObject',
        'sonic-py-common',
        'enum34; python_version < "3.4"'
    ],
    setup_requires = [
        'pytest-runner',
        'wheel'
    ],
    tests_require = [
        'parameterized',
        'pytest',
        'pyfakefs',
        'sonic-py-common',
        'deepdiff',
        'mock>=2.0.0; python_version < "3.3"',
        'pytest-cov'#,
        #'sonic-platform-common'
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Topic :: System',
    ],
    keywords = 'sonic SONiC host services',
    test_suite = 'setup.get_test_suite'
)
