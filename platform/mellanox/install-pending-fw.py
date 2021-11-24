#!/usr/bin/env python3

from fwutil.lib import ComponentStatusProvider, PlatformComponentsParser
from sonic_platform.component import ComponentCPLD

#Globals
CPLD_FLAG = None

# Init platform chassis helper classes
csp = ComponentStatusProvider()
pcp = PlatformComponentsParser(csp.is_modular_chassis())


# Parse update status file
update_status = csp.read_au_status_file_if_exists()

if update_status is None:
    exit(0)

# Parse platform components file
pcp.parse_platform_components()


# Iterate each component in the status file
for boot_type, components in update_status.items():
    for comp in components:

        if comp["info"] != "scheduled": continue

        key = comp['comp']

        if len(key.split('/')) == 3:
            chassis_name, mod_name, comp_name = key.split('/')
            comp_fw = pcp.module_component_map[mod_name][comp_name]
            component = csp.module_component_map[mod_name][comp_name]
        else:
            chassis_name, comp_name = key.split('/')
            comp_fw = pcp.chassis_component_map[chassis_name][comp_name]
            component = csp.chassis_component_map[chassis_name][comp_name]

        fw_file = comp_fw['firmware']

        if type(component) == ComponentCPLD:
            if CPLD_FLAG is not None:
                print("WARNING: Multiple CPLD firmwares defined. Some CPLD updates may not fully complete.")
            CPLD_FLAG = (component, fw_file)
        else:
            component.__install_firmware(fw_file, allow_reboot=False)

# Run CPLD refresh last if needed
if CPLD_FLAG is not None:
    CPLD_FLAG[0].__refresh_cpld(CPLD_FLAG[1])
    
