#!/usr/bin/env python
import os

import pytest

from sonic_package_manager.database import PackageEntry
from sonic_package_manager.manifest import Manifest
from sonic_package_manager.package import Package
from sonic_package_manager.service_creator.creator import (
    ServiceCreator,
    ETC_SONIC_PATH, DOCKER_CTL_SCRIPT_LOCATION,
    SERVICE_MGMT_SCRIPT_LOCATION, SYSTEMD_LOCATION, MONIT_CONF_LOCATION
)


@pytest.fixture
def manifest():
    return Manifest.marshal({
        'package': {
            'name': 'test',
            'version': '1.0.0',
        },
        'service': {
            'name': 'test',
            'requires': ['database'],
            'after': ['database', 'swss', 'syncd'],
            'before': ['ntp-config'],
            'dependent-of': ['swss'],
            'asic-service': False,
            'host-service': True,
        },
        'container': {
            'privileged': True,
            'volumes': [
                '/etc/sonic:/etc/sonic:ro'
            ]
        }
    })


def test_service_creator(sonic_fs, manifest, mock_feature_registry):
    creator = ServiceCreator(mock_feature_registry)
    entry = PackageEntry('test', 'azure/sonic-test')
    package = Package(entry, '1.0.0', manifest)
    creator.create(package)

    assert sonic_fs.exists(os.path.join(ETC_SONIC_PATH, 'swss_dependent'))
    assert sonic_fs.exists(os.path.join(DOCKER_CTL_SCRIPT_LOCATION, 'test.sh'))
    assert sonic_fs.exists(os.path.join(SERVICE_MGMT_SCRIPT_LOCATION, 'test.sh'))
    assert sonic_fs.exists(os.path.join(SYSTEMD_LOCATION, 'test.service'))
    assert sonic_fs.exists(os.path.join(MONIT_CONF_LOCATION, 'monit_test'))


def test_service_creator_with_timer_unit(sonic_fs, manifest, mock_feature_registry):
    creator = ServiceCreator(mock_feature_registry)
    entry = PackageEntry('test', 'azure/sonic-test')
    package = Package(entry, '1.0.0', manifest)
    creator.create(package)

    assert not sonic_fs.exists(os.path.join(SYSTEMD_LOCATION, 'test.timer'))

    manifest['service']['delayed'] = True
    package = Package(entry, '1.0.0', manifest)
    creator.create(package)

    assert sonic_fs.exists(os.path.join(SYSTEMD_LOCATION, 'test.timer'))
