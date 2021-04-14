import os
import select
import sys

from mock import MagicMock

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

class TestSfpEvent(object):
    @classmethod
    def setup_class(cls):
        os.environ["MLNX_PLATFORM_API_UNIT_TESTING"] = "1"
        select.select = MagicMock(return_value=([99], None, None))

    def test_check_sfp_status(self):
        from sonic_platform.sfp_event import SDK_SFP_STATE_IN, SDK_SFP_STATE_OUT, SDK_SFP_STATE_ERR
        from sonic_platform.sfp_event import STATUS_PLUGIN, STATUS_PLUGOUT
        from sonic_platform.sfp_event import sdk_sfp_err_type_dict

        self.executor(SDK_SFP_STATE_IN, None, STATUS_PLUGIN)
        self.executor(SDK_SFP_STATE_OUT, None, STATUS_PLUGOUT)
        for error_type, error_status in sdk_sfp_err_type_dict.items():
            self.executor(SDK_SFP_STATE_ERR, error_type, error_status)

    def executor(self, mock_module_state, mock_error_type, expect_status):
        from sonic_platform.sfp_event import sfp_event

        event = sfp_event()
        event.on_pmpe = MagicMock(return_value=(True, [0,1], mock_module_state, mock_error_type))
        port_change = {}
        found = event.check_sfp_status(port_change, 0)
        assert found
        assert 1 in port_change and port_change[1] == expect_status
        assert 2 in port_change and port_change[2] == expect_status
