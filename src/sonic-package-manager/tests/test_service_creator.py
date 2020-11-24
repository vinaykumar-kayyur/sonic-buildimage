#!/usr/bin/env python
import os
from unittest.mock import Mock

import pytest

from sonic_package_manager.database import PackageEntry
from sonic_package_manager.manifest import Manifest
from sonic_package_manager.package import Package
from sonic_package_manager.service_creator.creator import (
    ServiceCreator,
    ETC_SONIC_PATH, DOCKER_CTL_SCRIPT_LOCATION,
    SERVICE_MGMT_SCRIPT_LOCATION, SYSTEMD_LOCATION, MONIT_CONF_LOCATION
)
from sonic_package_manager.service_creator.feature import FeatureRegistry


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


def test_feature_registration(mock_sonic_db, manifest):
    mock_feature_table = Mock()
    mock_feature_table.get = Mock(return_value=(False, ()))
    mock_sonic_db.initial_table = Mock(return_value=mock_feature_table)
    mock_sonic_db.persistent_table = Mock(return_value=mock_feature_table)
    mock_sonic_db.running_table = Mock(return_value=mock_feature_table)
    feature_registry = FeatureRegistry(mock_sonic_db)
    feature_registry.register('test', manifest)
    mock_feature_table.set.assert_called_with('test', [
        ('state', 'disabled'),
        ('auto_restart', 'enabled'),
        ('high_mem_alert', 'disabled'),
        ('has_per_asic_scope', 'False'),
        ('has_global_scope', 'True'),
        ('has_timer', 'False')
    ])


def test_feature_registration_with_timer(mock_sonic_db, manifest):
    manifest['service']['delayed'] = True
    mock_feature_table = Mock()
    mock_feature_table.get = Mock(return_value=(False, ()))
    mock_sonic_db.initial_table = Mock(return_value=mock_feature_table)
    mock_sonic_db.persistent_table = Mock(return_value=mock_feature_table)
    mock_sonic_db.running_table = Mock(return_value=mock_feature_table)
    feature_registry = FeatureRegistry(mock_sonic_db)
    feature_registry.register('test', manifest)
    mock_feature_table.set.assert_called_with('test', [
        ('state', 'disabled'),
        ('auto_restart', 'enabled'),
        ('high_mem_alert', 'disabled'),
        ('has_per_asic_scope', 'False'),
        ('has_global_scope', 'True'),
        ('has_timer', 'True')
    ])
