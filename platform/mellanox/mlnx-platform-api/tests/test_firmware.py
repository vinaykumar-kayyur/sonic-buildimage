import os
import sys
import pytest
from mock import MagicMock
from .mock_platform import MockFan

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

from sonic_platform.component import Component, ComponentSSD

def mock_install_firmware_success(image_path):
    return True

def mock_install_firmware_fail(image_path):
    return False

def mock_update_notification_cold_boot(image_path):
    return "Immediate power cycle is required to complete NAME firmware update"

def mock_update_notification_warm_boot(image_path):
    return None

def mock_update_notification_error(image_path):
    raise RuntimeError("Failed to parse NAME firmware upgrade status")

test_data_default = [
        (None, False, None, -2),
        (None, True, 'warm', -1),
        (mock_install_firmware_fail, True, 'cold', -3),
        (mock_install_firmware_success, True, 'cold', 2)
        ]

test_data_ssd = [
        (None, None, False, None, -2),
        (None, mock_update_notification_error, True, None, -3),
        (mock_install_firmware_fail,    mock_update_notification_cold_boot, True, 'cold', -3),
        (mock_install_firmware_success, mock_update_notification_cold_boot, True, 'warm', -1),
        (mock_install_firmware_success, mock_update_notification_cold_boot, True, 'cold', 2),
        (mock_install_firmware_success, mock_update_notification_warm_boot, True, 'warm', 2),
        (mock_install_firmware_success, mock_update_notification_warm_boot, True, 'cold', 2)
        ]

@pytest.mark.parametrize('install_func, image_found, boot_type, expect', test_data_default)
def test_auto_update_firmware_default(monkeypatch, install_func, image_found, boot_type, expect):

    def mock_path_exists(path):
        return image_found

    test_component = Component()

    monkeypatch.setattr(test_component, 'install_firmware', install_func)
    monkeypatch.setattr(os.path, 'exists', mock_path_exists)

    result = test_component.auto_update_firmware(None, boot_type)

    assert result == expect


@pytest.mark.parametrize('install_func, notify, image_found, boot_type, expect', test_data_ssd)
def test_auto_update_firmware_default(monkeypatch, install_func, notify, image_found, boot_type, expect):

    def mock_path_exists(path):
        return image_found

    test_component_ssd = ComponentSSD()

    monkeypatch.setattr(test_component_ssd, 'install_firmware', install_func)
    monkeypatch.setattr(test_component_ssd, 'get_firmware_update_notification', notify)
    monkeypatch.setattr(os.path, 'exists', mock_path_exists)

    result = test_component_ssd.auto_update_firmware(None, boot_type)

    assert result == expect

