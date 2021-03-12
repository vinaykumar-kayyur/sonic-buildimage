import importlib.machinery
import importlib.util
import os
import sys
import swsssdk

from parameterized import parameterized
from unittest import TestCase, mock
from tests.hostcfgd.test_vectors import hostcfgdTestVector
from tests.hostcfgd.mock_configdb import MockConfigDb


swsssdk.ConfigDBConnector = MockConfigDb
test_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, "scripts")
sys.path.insert(0, modules_path)

# Load the file under test
hostcfgd_path = os.path.join(scripts_path, 'hostcfgd')
loader = importlib.machinery.SourceFileLoader('hostcfgd', hostcfgd_path)
spec = importlib.util.spec_from_loader(loader.name, loader)
hostcfgd = importlib.util.module_from_spec(spec)
loader.exec_module(hostcfgd)
sys.modules['hostcfgd'] = hostcfgd


class TestHostcfgd(TestCase):
    """
        Test hostcfd daemon - feature
    """
    def __verify_table(self, table, expected_table):
        """
            verify config db tables

            Compares Config DB table (FEATURE) with expected output table

            Args:
                table(dict): Current Config Db table
                expected_table(dict): Expected Config Db table

            Returns:
                None
        """
        isEqual = len(table) == len(expected_table)
        if isEqual:
            for key, fields in expected_table.items():
                isEqual = isEqual and key in table
                if isEqual:
                    for field, value in fields.items():
                        isEqual = isEqual and value == table[key][field]
                        if not isEqual:
                            break;
                else:
                    break
        return isEqual

    @parameterized.expand(hostcfgdTestVector)
    def test_hostcfgd(self, name, testData):
        """
            Test hostcfd daemon initialization

            Args:
                name(str): test name
                test_data(dict): test data which contains initial Config Db tables, and expected results

            Returns:
                None
        """
        MockConfigDb.set_config_db(testData["config_db"])
        with mock.patch("hostcfgd.subprocess") as mockSubprocess:
            hostConfigDaemon = hostcfgd.HostConfigDaemon()
            hostConfigDaemon.update_all_feature_states()
            assert self.__verify_table(
                MockConfigDb.get_config_db()["FEATURE"],
                testData["expected_config_db"]["FEATURE"]
            ), "Test failed for test data: {0}".format(testData)
            mockSubprocess.check_call.assert_has_calls(testData["expected_subprocess_calls"], any_order=True)
