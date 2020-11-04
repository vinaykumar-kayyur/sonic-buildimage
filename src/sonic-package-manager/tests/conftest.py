#!/usr/bin/env python
from unittest.mock import Mock, MagicMock

import pytest

from sonic_package_manager.database import PackageDatabase, PackageEntry
from sonic_package_manager.manager import DockerApi, PackageManager
from sonic_package_manager.manifest import Manifest
from sonic_package_manager.manifest_resolver import ManifestResolver
from sonic_package_manager.registry import RegistryResolver
from sonic_package_manager.version import Version


@pytest.fixture
def mock_docker_api():
    yield MagicMock(DockerApi)


@pytest.fixture
def mock_registry_resolver():
    yield Mock(RegistryResolver)


@pytest.fixture
def mock_manifest_resolver():
    yield Mock(ManifestResolver)


@pytest.fixture
def fake_manifest_resolver():
    class TestManifestResolver(ManifestResolver):
        def __init__(self):
            self.manifests = {
                ('database', '1.0.0'): Manifest.marshal({
                    'package': {
                        'version': '1.0.0',
                    },
                    'service': {
                        'name': 'database',
                    },
                }),
                ('swss', '1.0.0'): Manifest.marshal({
                    'package': {
                        'version': '1.0.0',
                    },
                    'service': {
                        'name': 'swss',
                    },
                }),
                ('test-package', '1.6.0'): Manifest.marshal({
                    'package': {
                        'version': '1.6.0',
                    },
                    'service': {
                        'name': 'test-package',
                    },
                }),
                ('test-package-2', '1.5.0'): Manifest.marshal({
                    'package': {
                        'version': '1.5.0',
                    },
                    'service': {
                        'name': 'test-package-2',
                    },
                }),
                ('test-package-3', '1.5.0'): Manifest.marshal({
                    'package': {
                        'version': '1.5.0',
                    },
                    'service': {
                        'name': 'test-package-3',
                    },
                }),
                ('test-package-3', '1.6.0'): Manifest.marshal({
                    'package': {
                        'version': '1.6.0',
                    },
                    'service': {
                        'name': 'test-package-3',
                    },
                }),
                ('test-package-4', '1.5.0'): Manifest.marshal({
                    'package': {
                        'version': '1.5.0',
                    },
                    'service': {
                        'name': 'test-package-4',
                    },
                }),
                ('test-package-5', '1.5.0'): Manifest.marshal({
                    'package': {
                        'version': '1.5.0',
                    },
                    'service': {
                        'name': 'test-package-5',
                    },
                }),
                ('test-package-5', '1.9.0'): Manifest.marshal({
                    'package': {
                        'version': '1.9.0',
                    },
                    'service': {
                        'name': 'test-package-5',
                    },
                }),
                ('test-package-6', '1.5.0'): Manifest.marshal({
                    'package': {
                        'version': '1.5.0',
                    },
                    'service': {
                        'name': 'test-package-6',
                    },
                }),
                ('test-package-6', '2.0.0'): Manifest.marshal({
                    'package': {
                        'version': '2.0.0',
                    },
                    'service': {
                        'name': 'test-package-6',
                    },
                }),
            }

        def get_manifest(self, package_info: PackageEntry, ref: str) -> Manifest:
            return self.manifests[(package_info.name, ref)]

    yield TestManifestResolver()


@pytest.fixture
def mock_service_creator():
    return Mock()


@pytest.fixture
def package_manager(mock_docker_api,
                    mock_registry_resolver,
                    mock_service_creator,
                    fake_manifest_resolver,
                    fake_db):
    return PackageManager(mock_docker_api, mock_registry_resolver,
                          fake_db, fake_manifest_resolver,
                          mock_service_creator)


@pytest.fixture
def fake_db(mock_docker_api, mock_registry_resolver):
    content = {
        'database': PackageEntry(name='database',
                                 repository='docker-database',
                                 description='SONiC database service',
                                 default_reference='1.0.0',
                                 version=Version(1, 0, 0),
                                 installed=True, built_in=True),
        'swss': PackageEntry(name='swss',
                             repository='docker-orchagent',
                             description='SONiC switch state service',
                             default_reference='1.0.0',
                             version=Version(1, 0, 0),
                             installed=True, built_in=True),
        'test-package': PackageEntry(name='test-package',
                                     repository='Azure/docker-test',
                                     description='SONiC Package Manager Test Package',
                                     default_reference='1.6.0',
                                     installed=False, built_in=False),
        'test-package-2': PackageEntry(name='test-package-2',
                                       repository='Azure/docker-test-2',
                                       description='SONiC Package Manager Test Package #2',
                                       default_reference='1.5.0',
                                       installed=False, built_in=False),
        'test-package-3': PackageEntry(name='test-package-3',
                                       repository='Azure/docker-test-3',
                                       description='SONiC Package Manager Test Package #3',
                                       default_reference='1.5.0',
                                       version=Version(1, 5, 0),
                                       installed=True, built_in=False),
        'test-package-5': PackageEntry(name='test-package-5',
                                       repository='Azure/docker-test-5',
                                       description='SONiC Package Manager Test Package #5',
                                       default_reference='1.9.0',
                                       version=Version(1, 9, 0),
                                       installed=False, built_in=False),
        'test-package-6': PackageEntry(name='test-package-6',
                                       repository='Azure/docker-test-6',
                                       description='SONiC Package Manager Test Package #6',
                                       default_reference='1.5.0',
                                       installed=False, built_in=False),
    }

    yield PackageDatabase(content)


@pytest.fixture
def fake_db_for_migration(mock_docker_api, mock_registry_resolver):
    content = {
        'database': PackageEntry(name='database',
                                 repository='docker-database',
                                 description='SONiC database service',
                                 default_reference='1.0.0',
                                 version=Version(1, 0, 0),
                                 installed=True, built_in=True),
        'swss': PackageEntry(name='swss',
                             repository='docker-orchagent',
                             description='SONiC switch state service',
                             default_reference='1.0.0',
                             version=Version(1, 0, 0),
                             installed=True, built_in=True),
        'test-package': PackageEntry(name='test-package',
                                     repository='Azure/docker-test',
                                     description='SONiC Package Manager Test Package',
                                     default_reference='1.6.0',
                                     installed=False, built_in=False),
        'test-package-2': PackageEntry(name='test-package-2',
                                       repository='Azure/docker-test-2',
                                       description='SONiC Package Manager Test Package #2',
                                       default_reference='2.0.0',
                                       installed=False, built_in=False),
        'test-package-3': PackageEntry(name='test-package-3',
                                       repository='Azure/docker-test-3',
                                       description='SONiC Package Manager Test Package #2',
                                       default_reference='1.6.0',
                                       version=Version(1, 6, 0),
                                       installed=True, built_in=False),
        'test-package-4': PackageEntry(name='test-package-4',
                                       repository='Azure/docker-test-4',
                                       description='SONiC Package Manager Test Package #4',
                                       default_reference='1.5.0',
                                       version=Version(1, 5, 0),
                                       installed=True, built_in=False),
        'test-package-5': PackageEntry(name='test-package-5',
                                       repository='Azure/docker-test-5',
                                       description='SONiC Package Manager Test Package #5',
                                       default_reference='1.5.0',
                                       version=Version(1, 5, 0),
                                       installed=True, built_in=False),
        'test-package-6': PackageEntry(name='test-package-6',
                                       repository='Azure/docker-test-6',
                                       description='SONiC Package Manager Test Package #6',
                                       default_reference='1.5.0',
                                       version=Version(2, 0, 0),
                                       installed=True, built_in=False),
    }

    yield PackageDatabase(content)


@pytest.fixture
def anything():
    """ Fixture that returns Any object that can be used in
    assert_called_*_with to match any object passed. """

    class Any:
        def __eq__(self, other):
            return True

    yield Any()
