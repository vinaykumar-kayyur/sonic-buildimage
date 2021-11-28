#!/usr/bin/env python3

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

        if csp.is_modular_chassis(): 
            _, parent_name, comp_name = key.split('/')
        else: 
            parent_name, comp_name = key.split('/')
            
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
    
