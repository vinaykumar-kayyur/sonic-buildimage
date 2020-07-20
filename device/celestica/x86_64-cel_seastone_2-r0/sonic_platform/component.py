#!/usr/bin/env python

#############################################################################
# Celestica
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

import json
import os.path
import inspect

try:
    from sonic_platform_base.component_base import ComponentBase
    from common import Common
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Component(ComponentBase):
    """Platform-specific Component class"""

    COMPONENT_CONFIG = 'component.json'

    def __init__(self, component_index, conf):
        ComponentBase.__init__(self)

        self._index = component_index
        self._config = conf
        self._api_common = Common(conf=self._config)
        self._name = self.get_name()

    def get_name(self):
        """
        Retrieves the name of the component
        Returns:
            A string containing the name of the component
        """
        default = 'N/A'
        config = self._config["get_name"]
        return self._api_common.get_output(self._index, config, default)

    def get_description(self):
        """
        Retrieves the description of the component
        Returns:
            A string containing the description of the component
        """
        default = 'N/A'
        config = self._config["get_description"]
        return self._api_common.get_output(self._index, config, default)

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component
        Note: the firmware version will be read from HW
        Returns:
            A string containing the firmware version of the component
        """
        default = 'N/A'
        config = self._config["get_firmware_version"]
        return self._api_common.get_output(self._index, config, default)

    def get_available_firmware_version(self, image_path):
        """
        Retrieves the available firmware version of the component
        Note: the firmware version will be read from image
        Args:
            image_path: A string, path to firmware image
        Returns:
            A string containing the available firmware version of the component
        """
        raise NotImplementedError

    def get_firmware_update_notification(self, image_path):
        """
        Retrieves a notification on what should be done in order to complete
        the component firmware update
        Args:
            image_path: A string, path to firmware image
        Returns:
            A string containing the component firmware update notification if required.
            By default 'None' value will be used, which indicates that no actions are required
        """
        return None

    def install_firmware(self, image_path):
        """
        Installs firmware to the component
        This API performs firmware installation only: this may/may not be the same as firmware update.
        In case platform component requires some extra steps (apart from calling Low Level Utility)
        to load the installed firmware (e.g, reboot, power cycle, etc.) - this must be done manually by user
        Note: in case immediate actions are required to complete the component firmware update
        (e.g., reboot, power cycle, etc.) - will be done automatically by API and no return value provided
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install was successful, False if not
        """
        raise NotImplementedError

    def update_firmware(self, image_path):
        """
        Updates firmware of the component
        This API performs firmware update: it assumes firmware installation and loading in a single call.
        In case platform component requires some extra steps (apart from calling Low Level Utility)
        to load the installed firmware (e.g, reboot, power cycle, etc.) - this will be done automatically by API
        Args:
            image_path: A string, path to firmware image
        Raises:
            RuntimeError: update failed
        """
        raise NotImplementedError
