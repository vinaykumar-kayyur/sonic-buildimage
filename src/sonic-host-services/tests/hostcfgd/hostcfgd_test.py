import os
import sys
import swsscommon as swsscommon_package
from sonic_py_common import device_info
from swsscommon import swsscommon

from parameterized import parameterized
from sonic_py_common.general import load_module_from_source
from unittest import TestCase, mock

from .test_vectors import HOSTCFGD_TEST_VECTOR, HOSTCFG_DAEMON_CFG_DB
from tests.common.mock_configdb import MockConfigDb, MockDBConnector

from pyfakefs.fake_filesystem_unittest import patchfs
from deepdiff import DeepDiff
from unittest.mock import call

test_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, 'scripts')
sys.path.insert(0, modules_path)

# Load the file under test
hostcfgd_path = os.path.join(scripts_path, 'hostcfgd')
hostcfgd = load_module_from_source('hostcfgd', hostcfgd_path)
hostcfgd.ConfigDBConnector = MockConfigDb
hostcfgd.DBConnector = MockDBConnector
hostcfgd.Table = mock.Mock()

class TestFeatureHandler(TestCase):
    """Test methods of `FeatureHandler` class. 
    """
    def checks_config_table(self, feature_table, expected_table):
        """Compares `FEATURE` table in `CONFIG_DB` with expected output table.

        Args:
            feature_table: A dictionary indicates current `FEATURE` table in `CONFIG_DB`.
            expected_table A dictionary indicates the expected `FEATURE` table in `CONFIG_DB`.

        Returns:
            Returns True if `FEATURE` table in `CONFIG_DB` was not modified unexpectedly;
            otherwise, returns False.
        """
        ddiff = DeepDiff(feature_table, expected_table, ignore_order=True)

        return True if not ddiff else False

    def checks_systemd_config_file(self, feature_table, feature_systemd_name_map=None):
        """Checks whether the systemd configuration file of each feature was created or not
        and whether the `Restart=` field in the file is set correctly or not.

        Args:
            feature_table: A dictionary indicates `Feature` table in `CONFIG_DB`.

        Returns: Boolean value indicates whether test passed or not.
        """

        truth_table = {'enabled': 'always',
                       'disabled': 'no'}

        systemd_config_file_path = os.path.join(hostcfgd.FeatureHandler.SYSTEMD_SERVICE_CONF_DIR,
                                                'auto_restart.conf')

        for feature_name in feature_table:
            auto_restart_status = feature_table[feature_name].get('auto_restart', 'disabled')
            if "enabled" in auto_restart_status:
                auto_restart_status = "enabled"
            elif "disabled" in auto_restart_status:
                auto_restart_status = "disabled"

            feature_systemd_list = feature_systemd_name_map[feature_name] if feature_systemd_name_map else [feature_name]

            for feature_systemd in feature_systemd_list:
                feature_systemd_config_file_path = systemd_config_file_path.format(feature_systemd)
                is_config_file_existing = os.path.exists(feature_systemd_config_file_path)
                assert is_config_file_existing, "Systemd configuration file of feature '{}' does not exist!".format(feature_systemd)

                with open(feature_systemd_config_file_path) as systemd_config_file:
                    status = systemd_config_file.read().strip()
                assert status == '[Service]\nRestart={}'.format(truth_table[auto_restart_status])

    def get_state_db_set_calls(self, feature_table):
        """Returns a Mock call objects which recorded the `set` calls to `FEATURE` table in `STATE_DB`.

        Args:
            feature_table: A dictionary indicates `FEATURE` table in `CONFIG_DB`.

        Returns:
            set_call_list: A list indicates Mock call objects.
        """
        set_call_list = []

        for feature_name in feature_table.keys():
            feature_state = ""
            if "enabled" in feature_table[feature_name]["state"]:
                feature_state = "enabled"
            elif "disabled" in feature_table[feature_name]["state"]:
                feature_state = "disabled"
            else:
                feature_state = feature_table[feature_name]["state"]

            set_call_list.append(mock.call(feature_name, [("state", feature_state)]))

        return set_call_list

    @parameterized.expand(HOSTCFGD_TEST_VECTOR)
    @patchfs
    def test_sync_state_field(self, test_scenario_name, config_data, fs):
        """Tests the method `sync_state_field(...)` of `FeatureHandler` class.

        Args:
            test_secnario_name: A string indicates different testing scenario.
            config_data: A dictionary contains initial `CONFIG_DB` tables and expected results.

        Returns:
            Boolean value indicates whether test will pass or not.
        """
        # add real path of sesscommon for database_config.json
        fs.add_real_paths(swsscommon_package.__path__)
        fs.create_dir(hostcfgd.FeatureHandler.SYSTEMD_SYSTEM_DIR)

        MockConfigDb.set_config_db(config_data['config_db'])
        feature_state_table_mock = mock.Mock()
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            with mock.patch("sonic_py_common.device_info.get_device_runtime_metadata", return_value=config_data['device_runtime_metadata']):
                with mock.patch("sonic_py_common.device_info.is_multi_npu", return_value=True if 'num_npu' in config_data else False):
                    with mock.patch("sonic_py_common.device_info.get_num_npus", return_value=config_data['num_npu'] if 'num_npu' in config_data else 1):
                        with mock.patch("sonic_py_common.device_info.get_namespaces", return_value=["asic{}".format(a) for a in  range(config_data['num_npu'])] if 'num_npu' in config_data else []):
                            popen_mock = mock.Mock()
                            attrs = config_data['popen_attributes']
                            popen_mock.configure_mock(**attrs)
                            mocked_subprocess.Popen.return_value = popen_mock

                            device_config = {}
                            device_config['DEVICE_METADATA'] = MockConfigDb.CONFIG_DB['DEVICE_METADATA']
                            device_config.update(config_data['device_runtime_metadata'])

                            feature_handler = hostcfgd.FeatureHandler(MockConfigDb(), feature_state_table_mock, device_config)
                            feature_table = MockConfigDb.CONFIG_DB['FEATURE']
                            feature_handler.sync_state_field(feature_table)

                            feature_systemd_name_map = {}
                            for feature_name in feature_table.keys():
                                feature = hostcfgd.Feature(feature_name, feature_table[feature_name], device_config)
                                feature_names, _ = feature_handler.get_multiasic_feature_instances(feature)
                                feature_systemd_name_map[feature_name] = feature_names

                            is_any_difference = self.checks_config_table(MockConfigDb.get_config_db()['FEATURE'],
                                                                         config_data['expected_config_db']['FEATURE'])
                            assert is_any_difference, "'FEATURE' table in 'CONFIG_DB' is modified unexpectedly!"

                            if 'num_npu' in config_data:
                                for ns in range(config_data['num_npu']):
                                    namespace = "asic{}".format(ns)
                                    is_any_difference = self.checks_config_table(feature_handler.ns_cfg_db[namespace].get_config_db()['FEATURE'],
                                                                                 config_data['expected_config_db']['FEATURE'])
                                    assert is_any_difference, "'FEATURE' table in 'CONFIG_DB' in namespace {} is modified unexpectedly!".format(namespace)

                            feature_table_state_db_calls = self.get_state_db_set_calls(feature_table)

                            self.checks_systemd_config_file(config_data['config_db']['FEATURE'], feature_systemd_name_map)
                            mocked_subprocess.check_call.assert_has_calls(config_data['enable_feature_subprocess_calls'],
                                                                          any_order=True)
                            mocked_subprocess.check_call.assert_has_calls(config_data['daemon_reload_subprocess_call'],
                                                                          any_order=True)
                            feature_state_table_mock.set.assert_has_calls(feature_table_state_db_calls)
                            self.checks_systemd_config_file(config_data['config_db']['FEATURE'], feature_systemd_name_map)

    @parameterized.expand(HOSTCFGD_TEST_VECTOR)
    @patchfs
    def test_handler(self, test_scenario_name, config_data, fs):
        """Tests the method `handle(...)` of `FeatureHandler` class.

        Args:
            test_secnario_name: A string indicates different testing scenario.
            config_data: A dictionary contains initial `CONFIG_DB` tables and expected results.

        Returns:
            Boolean value indicates whether test will pass or not.
        """
        # add real path of sesscommon for database_config.json
        fs.add_real_paths(swsscommon_package.__path__)
        fs.create_dir(hostcfgd.FeatureHandler.SYSTEMD_SYSTEM_DIR)

        MockConfigDb.set_config_db(config_data['config_db'])
        feature_state_table_mock = mock.Mock()
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            with mock.patch("sonic_py_common.device_info.get_device_runtime_metadata", return_value=config_data['device_runtime_metadata']):
                with mock.patch("sonic_py_common.device_info.is_multi_npu", return_value=True if 'num_npu' in config_data else False):
                    with mock.patch("sonic_py_common.device_info.get_num_npus", return_value=config_data['num_npu'] if 'num_npu' in config_data else 1):
                        popen_mock = mock.Mock()
                        attrs = config_data['popen_attributes']
                        popen_mock.configure_mock(**attrs)
                        mocked_subprocess.Popen.return_value = popen_mock

                        device_config = {}
                        device_config['DEVICE_METADATA'] = MockConfigDb.CONFIG_DB['DEVICE_METADATA']
                        device_config.update(config_data['device_runtime_metadata'])
                        feature_handler = hostcfgd.FeatureHandler(MockConfigDb(), feature_state_table_mock, device_config)

                        feature_table = MockConfigDb.CONFIG_DB['FEATURE']

                        feature_systemd_name_map = {}
                        for feature_name, feature_config in feature_table.items():
                            feature_handler.handler(feature_name, 'SET', feature_config)
                            feature = hostcfgd.Feature(feature_name, feature_table[feature_name], device_config)
                            feature_names, _ = feature_handler.get_multiasic_feature_instances(feature)
                            feature_systemd_name_map[feature_name] = feature_names

                        self.checks_systemd_config_file(config_data['config_db']['FEATURE'], feature_systemd_name_map)
                        mocked_subprocess.check_call.assert_has_calls(config_data['enable_feature_subprocess_calls'],
                                                                      any_order=True)
                        mocked_subprocess.check_call.assert_has_calls(config_data['daemon_reload_subprocess_call'],
                                                                      any_order=True)

    def test_feature_config_parsing(self):
        swss_feature = hostcfgd.Feature('swss', {
            'state': 'enabled',
            'auto_restart': 'enabled',
            'has_timer': 'True',
            'has_global_scope': 'False',
            'has_per_asic_scope': 'True',
        })

        assert swss_feature.name == 'swss'
        assert swss_feature.state == 'enabled'
        assert swss_feature.auto_restart == 'enabled'
        assert swss_feature.has_timer
        assert not swss_feature.has_global_scope
        assert swss_feature.has_per_asic_scope

    def test_feature_config_parsing_defaults(self):
        swss_feature = hostcfgd.Feature('swss', {
            'state': 'enabled',
        })

        assert swss_feature.name == 'swss'
        assert swss_feature.state == 'enabled'
        assert swss_feature.auto_restart == 'disabled'
        assert not swss_feature.has_timer
        assert swss_feature.has_global_scope
        assert not swss_feature.has_per_asic_scope

    @mock.patch('hostcfgd.FeatureHandler.update_systemd_config', mock.MagicMock())
    @mock.patch('hostcfgd.FeatureHandler.update_feature_state', mock.MagicMock())
    @mock.patch('hostcfgd.FeatureHandler.sync_feature_asic_scope', mock.MagicMock())
    def test_feature_resync(self):
        mock_db = mock.MagicMock()
        mock_db.get_entry = mock.MagicMock()
        mock_db.mod_entry = mock.MagicMock()
        mock_feature_state_table = mock.MagicMock()

        feature_handler = hostcfgd.FeatureHandler(mock_db, mock_feature_state_table, {})
        feature_table = {
            'sflow': {
                'state': 'enabled',
                'auto_restart': 'enabled',
                'delayed': 'True',
                'has_global_scope': 'False',
                'has_per_asic_scope': 'True',
            }
        }
        mock_db.get_entry.return_value = None
        feature_handler.sync_state_field(feature_table)
        mock_db.mod_entry.assert_called_with('FEATURE', 'sflow', {'state': 'enabled'})
        mock_db.mod_entry.reset_mock()

        feature_handler = hostcfgd.FeatureHandler(mock_db, mock_feature_state_table, {})
        mock_db.get_entry.return_value = {
            'state': 'disabled',
        }
        feature_handler.sync_state_field(feature_table)
        mock_db.mod_entry.assert_not_called()

        feature_handler = hostcfgd.FeatureHandler(mock_db, mock_feature_state_table, {})
        feature_table = {
            'sflow': {
                'state': 'always_enabled',
                'auto_restart': 'enabled',
                'delayed': 'True',
                'has_global_scope': 'False',
                'has_per_asic_scope': 'True',
            }
        }
        feature_handler.sync_state_field(feature_table)
        mock_db.mod_entry.assert_called_with('FEATURE', 'sflow', {'state': 'always_enabled'})
        mock_db.mod_entry.reset_mock()

        feature_handler = hostcfgd.FeatureHandler(mock_db, mock_feature_state_table, {})
        mock_db.get_entry.return_value = {
            'state': 'some template',
        }
        feature_table = {
            'sflow': {
                'state': 'enabled',
                'auto_restart': 'enabled',
                'delayed': 'True',
                'has_global_scope': 'False',
                'has_per_asic_scope': 'True',
            }
        }
        feature_handler.sync_state_field(feature_table)
        mock_db.mod_entry.assert_called_with('FEATURE', 'sflow', {'state': 'enabled'})


class TesNtpCfgd(TestCase):
    """
        Test hostcfd daemon - NtpCfgd
    """
    def setUp(self):
        MockConfigDb.CONFIG_DB['NTP'] = {'global': {'vrf': 'mgmt', 'src_intf': 'eth0'}}
        MockConfigDb.CONFIG_DB['NTP_SERVER'] = {'0.debian.pool.ntp.org': {}}

    def tearDown(self):
        MockConfigDb.CONFIG_DB = {}

    def test_ntp_global_update_with_no_servers(self):
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            popen_mock = mock.Mock()
            attrs = {'communicate.return_value': ('output', 'error')}
            popen_mock.configure_mock(**attrs)
            mocked_subprocess.Popen.return_value = popen_mock

            ntpcfgd = hostcfgd.NtpCfg()
            ntpcfgd.ntp_global_update('global', MockConfigDb.CONFIG_DB['NTP']['global'])

            mocked_subprocess.check_call.assert_not_called()

    def test_ntp_global_update_ntp_servers(self):
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            popen_mock = mock.Mock()
            attrs = {'communicate.return_value': ('output', 'error')}
            popen_mock.configure_mock(**attrs)
            mocked_subprocess.Popen.return_value = popen_mock

            ntpcfgd = hostcfgd.NtpCfg()
            ntpcfgd.ntp_global_update('global', MockConfigDb.CONFIG_DB['NTP']['global'])
            ntpcfgd.ntp_server_update('0.debian.pool.ntp.org', 'SET')
            mocked_subprocess.check_call.assert_has_calls([call('systemctl restart ntp-config', shell=True)])

    def test_loopback_update(self):
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            popen_mock = mock.Mock()
            attrs = {'communicate.return_value': ('output', 'error')}
            popen_mock.configure_mock(**attrs)
            mocked_subprocess.Popen.return_value = popen_mock

            ntpcfgd = hostcfgd.NtpCfg()
            ntpcfgd.ntp_global = MockConfigDb.CONFIG_DB['NTP']['global']
            ntpcfgd.ntp_servers.add('0.debian.pool.ntp.org')

            ntpcfgd.handle_ntp_source_intf_chg('eth0')
            mocked_subprocess.check_call.assert_has_calls([call('systemctl restart ntp-config', shell=True)])


class TestHostcfgdDaemon(TestCase):

    def setUp(self):
        MockConfigDb.set_config_db(HOSTCFG_DAEMON_CFG_DB)

    def tearDown(self):
        MockConfigDb.CONFIG_DB = {}

    @patchfs
    def test_feature_events(self, fs):
        fs.create_dir(hostcfgd.FeatureHandler.SYSTEMD_SYSTEM_DIR)
        MockConfigDb.event_queue = [('FEATURE', 'dhcp_relay'),
                                ('FEATURE', 'mux'),
                                ('FEATURE', 'telemetry')]
        daemon = hostcfgd.HostConfigDaemon()
        daemon.register_callbacks()
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            popen_mock = mock.Mock()
            attrs = {'communicate.return_value': ('output', 'error')}
            popen_mock.configure_mock(**attrs)
            mocked_subprocess.Popen.return_value = popen_mock
            try:
                daemon.start()
            except TimeoutError:
                pass
            expected = [call('sudo systemctl daemon-reload', shell=True),
                        call('sudo systemctl unmask dhcp_relay.service', shell=True),
                        call('sudo systemctl enable dhcp_relay.service', shell=True),
                        call('sudo systemctl start dhcp_relay.service', shell=True),
                        call('sudo systemctl daemon-reload', shell=True),
                        call('sudo systemctl unmask mux.service', shell=True),
                        call('sudo systemctl enable mux.service', shell=True),
                        call('sudo systemctl start mux.service', shell=True),
                        call('sudo systemctl daemon-reload', shell=True),
                        call('sudo systemctl unmask telemetry.service', shell=True),
                        call('sudo systemctl unmask telemetry.timer', shell=True),
                        call('sudo systemctl enable telemetry.timer', shell=True),
                        call('sudo systemctl start telemetry.timer', shell=True)]
            mocked_subprocess.check_call.assert_has_calls(expected)

            # Change the state to disabled
            MockConfigDb.CONFIG_DB['FEATURE']['telemetry']['state'] = 'disabled'
            MockConfigDb.event_queue = [('FEATURE', 'telemetry')]
            try:
                daemon.start()
            except TimeoutError:
                pass
            expected = [call('sudo systemctl stop telemetry.timer', shell=True),
                        call('sudo systemctl disable telemetry.timer', shell=True),
                        call('sudo systemctl mask telemetry.timer', shell=True),
                        call('sudo systemctl stop telemetry.service', shell=True),
                        call('sudo systemctl disable telemetry.timer', shell=True),
                        call('sudo systemctl mask telemetry.timer', shell=True)]
            mocked_subprocess.check_call.assert_has_calls(expected)

    def test_loopback_events(self):
        MockConfigDb.set_config_db(HOSTCFG_DAEMON_CFG_DB)
        MockConfigDb.event_queue = [('NTP', 'global'),
                                  ('NTP_SERVER', '0.debian.pool.ntp.org'),
                                  ('LOOPBACK_INTERFACE', 'Loopback0|10.184.8.233/32')]
        daemon = hostcfgd.HostConfigDaemon()
        daemon.register_callbacks()
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            popen_mock = mock.Mock()
            attrs = {'communicate.return_value': ('output', 'error')}
            popen_mock.configure_mock(**attrs)
            mocked_subprocess.Popen.return_value = popen_mock
            try:
                daemon.start()
            except TimeoutError:
                pass
            expected = [call('systemctl restart ntp-config', shell=True),
            call('iptables -t mangle --append PREROUTING -p tcp --tcp-flags SYN SYN -d 10.184.8.233 -j TCPMSS --set-mss 1460', shell=True),
            call('iptables -t mangle --append POSTROUTING -p tcp --tcp-flags SYN SYN -s 10.184.8.233 -j TCPMSS --set-mss 1460', shell=True)]
            mocked_subprocess.check_call.assert_has_calls(expected, any_order=True)

    def test_kdump_event(self):
        MockConfigDb.set_config_db(HOSTCFG_DAEMON_CFG_DB)
        daemon = hostcfgd.HostConfigDaemon()
        daemon.register_callbacks()
        MockConfigDb.event_queue = [('KDUMP', 'config')]
        with mock.patch('hostcfgd.subprocess') as mocked_subprocess:
            popen_mock = mock.Mock()
            attrs = {'communicate.return_value': ('output', 'error')}
            popen_mock.configure_mock(**attrs)
            mocked_subprocess.Popen.return_value = popen_mock
            try:
                daemon.start()
            except TimeoutError:
                pass
            expected = [call('sonic-kdump-config --disable', shell=True),
                        call('sonic-kdump-config --num_dumps 3', shell=True),
                        call('sonic-kdump-config --memory 0M-2G:256M,2G-4G:320M,4G-8G:384M,8G-:448M', shell=True)]
            mocked_subprocess.check_call.assert_has_calls(expected, any_order=True)
