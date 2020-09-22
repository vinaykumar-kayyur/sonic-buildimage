from app.allow_list import BGPAllowListMgr
from app.directory import Directory
from app.template import TemplateFabric

from mock import MagicMock, patch
import pytest


def new_run_command(cmd):
    return 0, "", ""

global_constants = {
    "bgp": {
        "allow_list": {
            "enabled": True,
            "default_pl_rules": {
                "v4": [ "deny 0.0.0.0/0 le 17" ],
                "v6": [
                    "deny 0::/0 le 59",
                    "deny 0::/0 ge 65"
                ]
            }
        }
    }
}

#@pytest.mark.skip()
@patch('app.allow_list.run_command', side_effect=new_run_command)
def test_set_handler_with_community(mock_run_command):
    test_set_handler_with_community.push_list_called = False
    def push_list(args):
        test_set_handler_with_community.push_list_called = True
        assert args == [
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 10 deny 0.0.0.0/0 le 17',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 20 permit 10.20.30.0/24 ge 25',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 30 permit 30.50.0.0/16 ge 17',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 10 deny 0::/0 le 59',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 20 deny 0::/0 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 30 permit fc00:20::/64 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 40 permit fc00:30::/64 ge 65',
            'bgp community-list standard COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020 permit 1010:2020',
            'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 10',
            ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4',
            ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
            'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 10',
            ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6',
            ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        ]
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.push_list = push_list
    cfg_mgr.get_text.return_value = []
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.set_handler("DEPLOYMENT_ID|5|1010:2020", {
        "prefixes_v4": "10.20.30.0/24,30.50.0.0/16",
        "prefixes_v6": "fc00:20::/64,fc00:30::/64",
    })
    assert test_set_handler_with_community.push_list_called, "cfg_mgr.push_list wasn't called"

#@pytest.mark.skip()
@patch('app.allow_list.run_command', side_effect=new_run_command)
def test_set_handler_no_community(mock_run_command):
    test_set_handler_no_community.push_list_called = False
    def push_list(args):
        test_set_handler_no_community.push_list_called = True
        assert args == [
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 10 deny 0.0.0.0/0 le 17',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 20 permit 20.20.30.0/24 ge 25',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 30 permit 40.50.0.0/16 ge 17',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 10 deny 0::/0 le 59',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 20 deny 0::/0 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 30 permit fc01:20::/64 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 40 permit fc01:30::/64 ge 65',
            'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 30000',
            ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4',
            'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 30000',
            ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6',
        ]
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.push_list = push_list
    cfg_mgr.get_text.return_value = []
    common_objs = {
            'directory': Directory(),
            'cfg_mgr': cfg_mgr,
            'tf': TemplateFabric(),
            'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.set_handler("DEPLOYMENT_ID|5", {
        "prefixes_v4": "20.20.30.0/24,40.50.0.0/16",
        "prefixes_v6": "fc01:20::/64,fc01:30::/64",
    })
    assert test_set_handler_no_community.push_list_called, "cfg_mgr.push_list wasn't called"

#@pytest.mark.skip()
@patch('app.allow_list.run_command', side_effect=new_run_command)
def test_del_handler_with_community(mock_run_command):
    test_del_handler_with_community.push_list_called = False
    def push_list(args):
        test_del_handler_with_community.push_list_called = True
        assert args == [
            'no route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 10',
            'no route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 10',
            'no ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4',
            'no ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6',
            'no bgp community-list standard COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        ]
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.push_list = push_list
    cfg_mgr.get_text.return_value = [
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 10 deny 0.0.0.0/0 le 17',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 20 permit 10.20.30.0/24 ge 25',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 30 permit 30.50.0.0/16 ge 17',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 10 deny 0::/0 le 59',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 20 deny 0::/0 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 30 permit fc00:20::/64 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 40 permit fc00:30::/64 ge 65',
        'bgp community-list standard COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020 permit 1010:2020',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 10',
        ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4',
        ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 10',
        ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6',
        ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        ""
    ]
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.del_handler("DEPLOYMENT_ID|5|1010:2020")
    assert test_del_handler_with_community.push_list_called, "cfg_mgr.push_list wasn't called"

#@pytest.mark.skip()
@patch('app.allow_list.run_command', side_effect=new_run_command)
def test_del_handler_no_community(mock_run_command):
    test_del_handler_no_community.push_list_called = False
    def push_list(args):
        test_del_handler_no_community.push_list_called = True
        assert args == [
            'no route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 30000',
            'no route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 30000',
            'no ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4',
            'no ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6',
        ]
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.push_list = push_list
    cfg_mgr.get_text.return_value = [
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 10 deny 0.0.0.0/0 le 17',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 20 permit 20.20.30.0/24 ge 25',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 30 permit 40.50.0.0/16 ge 17',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 10 deny 0::/0 le 59',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 20 deny 0::/0 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 30 permit fc01:20::/64 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 40 permit fc01:30::/64 ge 65',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 30000',
        ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 30000',
        ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6',
        " "
    ]
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.del_handler("DEPLOYMENT_ID|5")
    assert test_del_handler_no_community.push_list_called, "cfg_mgr.push_list wasn't called"

#@pytest.mark.skip()
def test_set_handler_with_community_data_is_already_presented():
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.get_text.return_value = [
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 10 deny 0.0.0.0/0 le 17',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 20 permit 10.20.30.0/24 ge 25',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 30 permit 30.50.0.0/16 ge 17',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 10 deny 0::/0 le 59',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 20 deny 0::/0 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 30 permit fc00:20::/64 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 40 permit fc00:30::/64 ge 65',
        'bgp community-list standard COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020 permit 1010:2020',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 10',
        ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4',
        ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 10',
        ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6',
        ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        ""
    ]
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.set_handler("DEPLOYMENT_ID|5|1010:2020", {
        "prefixes_v4": "10.20.30.0/24,30.50.0.0/16",
        "prefixes_v6": "fc00:20::/64,fc00:30::/64",
    })
    assert not cfg_mgr.push_list.called, "cfg_mgr.push_list was called, but it shouldn't have been"

#@pytest.mark.skip()
def test_set_handler_no_community_data_is_already_presented():
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.get_text.return_value = [
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 10 deny 0.0.0.0/0 le 17',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 20 permit 20.20.30.0/24 ge 25',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 30 permit 40.50.0.0/16 ge 17',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 10 deny 0::/0 le 59',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 20 deny 0::/0 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 30 permit fc01:20::/64 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 40 permit fc01:30::/64 ge 65',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 30000',
        ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 30000',
        ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6',
        ""
    ]
    common_objs = {
            'directory': Directory(),
            'cfg_mgr': cfg_mgr,
            'tf': TemplateFabric(),
            'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.set_handler("DEPLOYMENT_ID|5", {
        "prefixes_v4": "20.20.30.0/24,40.50.0.0/16",
        "prefixes_v6": "fc01:20::/64,fc01:30::/64",
    })
    assert not cfg_mgr.push_list.called, "cfg_mgr.push_list was called, but it shouldn't have been"

#@pytest.mark.skip()
def test_del_handler_with_community_no_data():
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.get_text.return_value = [""]
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.del_handler("DEPLOYMENT_ID|5|1010:2020")
    assert not cfg_mgr.push_list.called, "cfg_mgr.push_list was called, but it shouldn't have been"

#@pytest.mark.skip()
def test_del_handler_no_community_no_data():
    cfg_mgr = MagicMock()
    cfg_mgr.update.return_value = None
    cfg_mgr.get_text.return_value = [""]
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.del_handler("DEPLOYMENT_ID|5")
    assert not cfg_mgr.push_list.called, "cfg_mgr.push_list was called, but it shouldn't have been"

#@pytest.mark.skip()
def test_set_handler_with_community_update_prefixes_add():
    test_set_handler_with_community_update_prefixes_add.push_list_called = False
    def push_list(args):
        test_set_handler_with_community_update_prefixes_add.push_list_called = True
        assert args == [
            'no ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 10 deny 0.0.0.0/0 le 17',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 20 permit 10.20.30.0/24 ge 25',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 30 permit 30.50.0.0/16 ge 17',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 40 permit 80.90.0.0/16 ge 17',
            'no ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 10 deny 0::/0 le 59',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 20 deny 0::/0 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 30 permit fc00:20::/64 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 40 permit fc00:30::/64 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 50 permit fc02::/64 ge 65',
        ]
    cfg_mgr = MagicMock()
    cfg_mgr.push_list = push_list
    cfg_mgr.update.return_value = None
    cfg_mgr.get_text.return_value = [
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 10 deny 0.0.0.0/0 le 17',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 20 permit 10.20.30.0/24 ge 25',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4 seq 30 permit 30.50.0.0/16 ge 17',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 10 deny 0::/0 le 59',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 20 deny 0::/0 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 30 permit fc00:20::/64 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6 seq 40 permit fc00:30::/64 ge 65',
        'bgp community-list standard COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020 permit 1010:2020',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 10',
        ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V4',
        ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 10',
        ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020_V6',
        ' match community COMMUNITY_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_1010:2020',
        ""
    ]
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.set_handler("DEPLOYMENT_ID|5|1010:2020", {
        "prefixes_v4": "10.20.30.0/24,30.50.0.0/16,80.90.0.0/16",
        "prefixes_v6": "fc00:20::/64,fc00:30::/64,fc02::/64",
    })
    assert test_set_handler_with_community_update_prefixes_add.push_list_called, "cfg_mgr.push_list wasn't called"

#@pytest.mark.skip()
def test_set_handler_no_community_update_prefixes_add():
    test_set_handler_no_community_update_prefixes_add.push_list_called = False
    def push_list(args):
        test_set_handler_no_community_update_prefixes_add.push_list_called = True
        assert args == [
            'no ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 10 deny 0.0.0.0/0 le 17',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 20 permit 20.20.30.0/24 ge 25',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 30 permit 40.50.0.0/16 ge 17',
            'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 40 permit 80.90.0.0/16 ge 17',
            'no ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 10 deny 0::/0 le 59',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 20 deny 0::/0 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 30 permit fc01:20::/64 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 40 permit fc01:30::/64 ge 65',
            'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 50 permit fc02::/64 ge 65',
        ]
    cfg_mgr = MagicMock()
    cfg_mgr.push_list = push_list
    cfg_mgr.update.return_value = None
    cfg_mgr.get_text.return_value = [
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 10 deny 0.0.0.0/0 le 17',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 20 permit 20.20.30.0/24 ge 25',
        'ip prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4 seq 30 permit 40.50.0.0/16 ge 17',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 10 deny 0::/0 le 59',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 20 deny 0::/0 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 30 permit fc01:20::/64 ge 65',
        'ipv6 prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6 seq 40 permit fc01:30::/64 ge 65',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V4 permit 30000',
        ' match ip address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V4',
        'route-map ALLOW_LIST_DEPLOYMENT_ID_5_V6 permit 30000',
        ' match ipv6 address prefix-list PL_ALLOW_LIST_DEPLOYMENT_ID_5_COMMUNITY_empty_V6',
        ""
    ]
    common_objs = {
            'directory': Directory(),
            'cfg_mgr': cfg_mgr,
            'tf': TemplateFabric(),
            'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    mgr.set_handler("DEPLOYMENT_ID|5", {
        "prefixes_v4": "20.20.30.0/24,40.50.0.0/16,80.90.0.0/16",
        "prefixes_v6": "fc01:20::/64,fc01:30::/64,fc02::/64",
    })
    assert test_set_handler_no_community_update_prefixes_add.push_list_called, "cfg_mgr.push_list wasn't called"

def test___set_handler_validate():
    cfg_mgr = MagicMock()
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(),
        'constants': global_constants,
    }
    mgr = BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES")
    data = {
        "prefixes_v4": "20.20.30.0/24,40.50.0.0/16",
        "prefixes_v6": "fc01:20::/64,fc01:30::/64",
    }
    assert not mgr._BGPAllowListMgr__set_handler_validate("DEPLOYMENT_ID|5|1010:2020", None)
    assert not mgr._BGPAllowListMgr__set_handler_validate("DEPLOYMENT_ID1|5|1010:2020", data)
    assert not mgr._BGPAllowListMgr__set_handler_validate("DEPLOYMENT_ID|z|1010:2020", data)

# FIXME: more testcases for coverage
