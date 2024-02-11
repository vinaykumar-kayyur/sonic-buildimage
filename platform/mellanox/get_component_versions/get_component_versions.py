#!/usr/bin/env python3
#
# Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES.
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

from fwutil.lib import ComponentStatusProvider
from tabulate import tabulate
import os
import subprocess
import re

COMPONENT_VERSIONS_FILE = "/etc/mlnx/component-versions"
HEADERS = ["COMPONENT", "COMPILATION", "ACTUAL"]
COMMANDS_FOR_ACTUAL = {
    "MFT": ["dpkg -l | grep -e 'mft '", "mft *([0-9.]*)"],
    "HW-MGMT": ["dpkg -l | grep hw", ".*1\\.mlnx\\.([0-9.]*)"],
    "SDK": ["docker exec -it syncd bash -c 'dpkg -l | grep sdk'", ".*1\\.mlnx\\.([0-9.]*)"],
    "SAI": ["docker exec -it syncd bash -c 'dpkg -l | grep mlnx-sai'", ".*1\\.mlnx\\.([A-Za-z0-9.]*)"],
    "FW": ["mlxfwmanager --query | grep -e 'FW *[0-9.]*'", "FW * [0-9]{2}\\.([0-9.]*)"],
    "Kernel": ["uname -r", "([0-9][0-9.-]*)-.*"]
}
UNAVAILABLE_PLATFORM_VERSIONS = {
    "SSD": "N/A",
    "BIOS": "N/A",
    "CPLD": "N/A"
}

UNAVAILABLE_COMPILED_VERSIONS = {
    "SDK": "N/A",
    "FW": "N/A",
    "SAI": "N/A",
    "HW-MGMT": "N/A",
    "MFT": "N/A",
    "Kernel": "N/A"
}


def parse_compiled_components_file():
    compiled_versions = {}

    if not os.path.exists(COMPONENT_VERSIONS_FILE):
        return UNAVAILABLE_COMPILED_VERSIONS

    with open(COMPONENT_VERSIONS_FILE, 'r') as component_versions:
        for line in component_versions.readlines():
            comp, version = line.split()
            compiled_versions[comp] = version

    if len(compiled_versions.keys()) < len(UNAVAILABLE_COMPILED_VERSIONS.keys()):
        for component in UNAVAILABLE_COMPILED_VERSIONS.keys():
            if not compiled_versions.get(component):
                compiled_versions[component] = "N/A"

    return compiled_versions


def get_platform_component_versions():
    csp = ComponentStatusProvider()
    version_table = csp.get_status()

    if not version_table or version_table == "":
        return UNAVAILABLE_PLATFORM_VERSIONS

    lines = version_table.split("\n")
    lines = lines[2:]

    parsed_lines = []
    for line in lines:
        """
        The fields are separated by whitespaces, so split by whitespace.
        The number of whitespaces between fields varies, so after spliting we filter the columns to get rid of the empty values.
        """
        columns = line.split(" ")
        parsed_lines.append([column for column in columns if column])

    platform_versions = {}

    # In the first line (ONIE version), the 'chassis' and 'module' fields have values,
    # so the version we actually need (ONIE) is the third value and not he first value like in the rest.
    platform_versions[parsed_lines[0][2]] = parsed_lines[0][3]
    parsed_lines = parsed_lines[1:]

    # Adding the rest of the versions
    for line in parsed_lines:
        platform_versions[line[0]] = line[1]

    return platform_versions


def get_current_version(comp):
    version = subprocess.run(COMMANDS_FOR_ACTUAL[comp][0], shell=True, executable="/usr/bin/bash", stdout=subprocess.PIPE)
    parsed_version = re.search(COMMANDS_FOR_ACTUAL[comp][1], str(version.stdout))
    return parsed_version.group(1) if parsed_version else "N/A"


def format_output_table(table):
    return tabulate(table, HEADERS)


def main():

    if os.getuid() != 0:
        print("Error: Root privileges are required")
        return

    compiled_versions = parse_compiled_components_file()
    platform_versions = get_platform_component_versions()

    output_table = []
    for comp in compiled_versions.keys():
        actual = get_current_version(comp)
        output_table.append([comp, compiled_versions[comp], actual])

    for comp in platform_versions.keys():
        output_table.append([comp, "-", platform_versions[comp]])

    print(format_output_table(output_table))


if __name__ == "__main__":
    main()
