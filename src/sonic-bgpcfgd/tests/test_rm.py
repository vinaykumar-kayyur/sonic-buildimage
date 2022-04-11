from unittest.mock import MagicMock

from bgpcfgd.managers_rm import RouteMapMgr
from swsscommon import swsscommon

def constructor():
    cfg_mgr = MagicMock()

    common_objs = {
        'cfg_mgr':   cfg_mgr,
        'constants': {},
    }

    mgr = RouteMapMgr(common_objs, "STATE_DB", swsscommon.STATE_ROUTE_MAP_TABLE_NAME)
    return mgr

def set_del_test(mgr, op, args, expected_ret, expected_cmds):
    set_del_test.push_list_called = False
    def push_list(cmds):
        set_del_test.push_list_called = True
        assert cmds in expected_cmds
        return True
    mgr.cfg_mgr.push_list = push_list

    if op == "SET":
        ret = mgr.set_handler(*args)
        assert ret == expected_ret
    elif op == "DEL":
        mgr.del_handler(*args)
    else:
        assert False, "Wrong operation"

    if expected_cmds:
        assert set_del_test.push_list_called, "cfg_mgr.push_list wasn't called"
    else:
        assert not set_del_test.push_list_called, "cfg_mgr.push_list was called"

def test_set_del():
    mgr = constructor()
    set_del_test(
        mgr,
        "SET",
        ("VXLAN_OV_ECMP_RM", {
            "community_id": "1234:1234"
        }),
        True,
        [
            ["route-map VXLAN_OV_ECMP_RM permit 100",
             " set community 1234:1234"]
        ]
    )

    set_del_test(
        mgr,
        "DEL",
        ("VXLAN_OV_ECMP_RM",),
        True,
        [
            ["no route-map VXLAN_OV_ECMP_RM permit 100"]
        ]
    )
