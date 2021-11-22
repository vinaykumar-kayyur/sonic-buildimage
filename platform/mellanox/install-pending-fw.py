#!/usr/bin/env python

from config.fwutil.lib import PlatformDataProvider, PlatformComponentsParser

# Init platform chassis helper classes
pdp = PlatformDataProvider()
pcp = PlatformComponentsParser(pdp.is_modular_chassis())
csp = ComponentStatusProvider()

# Parse update status file
update_status = csp.read_au_status_file_if_exists()

# Parse platform components file
pcp.parse_platform_components()


# Iterate each component in the status file
for key, status in update_status.items():

    if len(key.split('/')) == 3:
        chassis_name, mod_name, comp_name = key.split('/')
        component = pcp.module_component_map[mod_name][comp_name]
    else:
        chassis_name, comp_name = key.split('/')
        component = pcp.chassis_component_map[chassis_name][comp_name]


# Check status file for "installed" firmware


# Run install_firmware function for these


# IF CPLD run update last after all other installs. 
