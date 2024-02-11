#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock, Mock, mock_open
import sys
from get_component_versions import *


class TestGetComponentVersions(unittest.TestCase):
    @patch('fwutil.lib.ComponentStatusProvider.get_status')
    def test_get_platform_component_versions(self, mock_csp):
        status_result = """Chassis    Module    Component    Version                  Description
        ---------  --------  -----------  -----------------------  ----------------------------------------
        MSN4410    N/A       ONIE         2022.08-5.3.0010-9600    ONIE - Open Network Install Environment
                             SSD          0202-000                 SSD - Solid-State Drive
                             BIOS         0ACLH004_02.02.010_9600  BIOS - Basic Input/Output System
                             CPLD1        CPLD000120_REV0900       CPLD - Complex Programmable Logic Device
                             CPLD2        CPLD000254_REV0600       CPLD - Complex Programmable Logic Device
                             CPLD3        CPLD000191_REV0102       CPLD - Complex Programmable Logic Device"""

        mock_csp.return_value = status_result
        result = get_platform_component_versions()

        expected_dict = {
        "ONIE": "2022.08-5.3.0010-9600",
        "SSD": "0202-000",
        "BIOS": "0ACLH004_02.02.010_9600",
        "CPLD1": "CPLD000120_REV0900",
        "CPLD2": "CPLD000254_REV0600",
        "CPLD3": "CPLD000191_REV0102"
    }

        self.assertEqual(result, expected_dict)


    @patch('fwutil.lib.ComponentStatusProvider')
    def test_unavailable_platform_component(self, mock_csp):
        mock_csp.get_status.return_value = ""
        expected_table = {
            "SSD": "N/A",
            "BIOS": "N/A",
            "CPLD": "N/A"
        }
        
        component_table = get_platform_component_versions()
        assert component_table == expected_table

    
    @patch('os.path.exists')
    def test_parse_compiled_components_file(self, mock_path):
        # Mock the open function and simulate the file content
        mock_file_content = """SDK 4.6.2134
        FW 2012.2134
        SAI SAIBuild2311.26.0.28
        HW-MGMT 7.0030.2008
        MFT 4.25.0
        Kernel 5.10.0-23-2"""

        mock_path.return_value = True

        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = parse_compiled_components_file()
            expected_dict = {
                "SDK": "4.6.2134",
                "FW": "2012.2134",
                "SAI": "SAIBuild2311.26.0.28",
                "HW-MGMT": "7.0030.2008",
                "MFT": "4.25.0",
                "Kernel": "5.10.0-23-2"
            }

            self.assertEqual(result, expected_dict)

    @patch('fwutil.lib.ComponentStatusProvider')
    def test_plaform_components_empty_output(self, mock_csp):
        # Mock the ComponentStatusProvider class to return an empty string
        mock_csp.get_status.return_value = ""

        # Expected result
        expected_result = {
            "SSD": "N/A",
            "BIOS": "N/A",
            "CPLD": "N/A"
        }

        # Test
        self.assertEqual(get_platform_component_versions(), expected_result)

    @patch('os.path.exists')
    def test_missing_compiled_versions(self, mock_os_path):
        mock_os_path.return_value = False
        
        expected_dict = {
            "SDK": "N/A",
            "FW": "N/A",
            "SAI": "N/A",
            "HW-MGMT": "N/A",
            "MFT": "N/A",
            "Kernel": "N/A"
        }

        self.assertEqual(parse_compiled_components_file(), expected_dict)

    @patch('os.path.exists')
    def test_invalid_compiled_versions(self, mock_path_exists):
        # Mock the open function and simulate the file content
        mock_file_content = """SDK 4.6.2134
        FW 2012.2134
        Kernel 5.10.0-23-2"""
        mock_path_exists.return_value = True

        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = parse_compiled_components_file()
            expected_dict = {
                "SDK": "4.6.2134",
                "FW": "2012.2134",
                "SAI": "N/A",
                "HW-MGMT": "N/A",
                "MFT": "N/A",
                "Kernel": "5.10.0-23-2"
            }

            self.assertEqual(result, expected_dict)


if __name__ == '__main__':
    unittest.main()