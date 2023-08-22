#######################################################################
# Asterfusion CX-T Devices Components                                 #
#                                                                     #
# Component contains an implementation of SONiC Platform Base API and #
# provides the components firmware management function                #
#                                                                     #
#######################################################################

try:
    import os
    import time

    from .constants import *
    from .helper import APIHelper

    from sonic_platform_base.component_base import ComponentBase
except ImportError as err:
    raise ImportError(str(err) + "- required module not found")

BMC_GET = os.path.join(os.path.dirname(os.path.realpath(__file__)), "utils", "bmc_get")
LOCK_FILE = "/tmp/.bmc_get.lock"
READ_TIMEOUT = 5
COMPONENT_LIST = (
    {
        "name": "BIOS",
        "description": "Basic Input/Output System",
        "version": "/sys/class/dmi/id/bios_version",
        "typeget": "file",
    },
    {
        "name": "BMC",
        "description": "Baseboard Management Controller",
        "version": [BMC_GET, "0xd", "0xaa", "0xaa"],
        "typeget": "cmd",
    },
)


class Component(ComponentBase):
    """Platform-specific Component class"""

    def __init__(self, component_index, helper, hwver, hwsku, platform):
        ComponentBase.__init__(self)
        self._api_helper = helper  # type: APIHelper
        # Init device
        self.board = hwver
        self.hwsku = hwsku
        self.platform = platform
        # Init index
        self.component_index = component_index + 1
        self._init_version()

    def _init_version(self):
        self._version = "Unknown"
        if COMPONENT_LIST[self.component_index - 1].get("typeget") == "file":
            self._version = self._api_helper.get_file_content(
                COMPONENT_LIST[self.component_index - 1].get("version")
            )
        elif COMPONENT_LIST[self.component_index - 1].get("typeget") == "cmd":
            with self._api_helper.file_lock(LOCK_FILE):
                while True:
                    output = self._api_helper.get_cmd_output(
                        COMPONENT_LIST[self.component_index - 1].get("version")
                    ).split()[1:]
                    if len(output) == 3 and "failed" not in output:
                        self._version = ".".join(map(lambda ver: str(int(ver)), output))
                        break
                    time.sleep(READ_TIMEOUT)

    def get_name(self):
        """
        Retrieves the name of the component

        Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.component_index - 1].get("name")

    def get_description(self):
        """
        Retrieves the description of the component

        Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.component_index - 1].get("description")

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Note: the firmware version will be read from HW

        Returns:
            A string containing the firmware version of the component
        """
        return self._version

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

    def auto_update_firmware(self, image_path, boot_type):
        """
        Updates firmware of the component

        This API performs firmware update automatically based on boot_type: it assumes firmware installation
        and/or creating a loading task during the reboot, if needed, in a single call.
        In case platform component requires some extra steps (apart from calling Low Level Utility)
        to load the installed firmware (e.g, reboot, power cycle, etc.) - this will be done automatically during the reboot.
        The loading task will be created by API.

        Args:
            image_path: A string, path to firmware image
            boot_type: A string, reboot type following the upgrade
                         - none/fast/warm/cold

        Returns:
            Output: A return code
                return_code: An integer number, status of component firmware auto-update
                    - return code of a positive number indicates successful auto-update
                        - status_installed = 1
                        - status_updated = 2
                        - status_scheduled = 3
                    - return_code of a negative number indicates failed auto-update
                        - status_err_boot_type = -1
                        - status_err_image = -2
                        - status_err_unknown = -3

        Raises:
            RuntimeError: auto-update failure cause
        """
        raise NotImplementedError
