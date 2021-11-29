#!/usr/bin/env python3
#
# Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES.
# Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from collections import namedtuple

from fwutil.lib import ComponentStatusProvider, PlatformComponentsParser
from sonic_platform.component import ComponentCPLD

# Globals
FW_STATUS_SCHEDULED = "scheduled"
CPLDRefresh = namedtuple("CPLDRefresh", ["cpld", "fw_file"])
CPLD_FLAG = None

# Init platform chassis helper classes
csp = ComponentStatusProvider()
pcp = PlatformComponentsParser(csp.is_modular_chassis())

# Parse update status file
update_status = csp.read_au_status_file_if_exists()

if update_status is None:
    exit(0)

# Parse platform components file
try:
    pcp.parse_platform_components()
except Exception as e:
    print("Error parsing platform components. Firmware update failed: {}".format(str(e)))
    print("System will reboot in 10 seconds please fix issue and run update command again.")
    time.sleep(10)
    exit(-1)

# Iterate each component in the status file
for boot_type, components in update_status.items():
    for comp in components:

        # Skip if fw isn't scheduled for install at reboot
        if comp["info"] != FW_STATUS_SCHEDULED: continue

        # Get component object and target firmware file
        key = comp["comp"]
        comp_path = key.split("/")

        if len(comp_path) == 3:
            # Module component
            _, parent_name, comp_name = comp_path
            fw_file = pcp.module_component_map[parent_name][comp_name]["firmware"]
            component = csp.module_component_map[parent_name][comp_name]
        else: 
            # Chassis component
            parent_name, comp_name = comp_path
            fw_file = pcp.chassis_component_map[parent_name][comp_name]["firmware"]
            component = csp.chassis_component_map[parent_name][comp_name]

        # Install firmware. If CPLD flag to be installed last due to force reboot during refresh
        if type(component) == ComponentCPLD:
            if CPLD_FLAG is not None:
                print("WARNING: Multiple CPLD firmwares defined. Some CPLD updates may not fully complete.")
            CPLD_FLAG = CPLDRefresh(component, fw_file)
        else:
            component.install_firmware(fw_file, allow_reboot=False)

# Run CPLD refresh last if needed
if CPLD_FLAG is not None:
    CPLD_FLAG.cpld.refresh_firmware(CPLD_FLAG.fw_file)
    
