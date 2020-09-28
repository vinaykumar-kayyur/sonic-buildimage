from swsscommon import swsscommon

from bgpcfgd.config import ConfigMgr
from bgpcfgd.directory import Directory
from bgpcfgd.managers_allow_list import BGPAllowListMgr
from bgpcfgd.managers_bgp import BGPPeerMgrBase
from bgpcfgd.managers_db import BGPDataBaseMgr
from bgpcfgd.managers_intf import InterfaceMgr
from bgpcfgd.managers_setsrc import ZebraSetSrc
from bgpcfgd.runner import Runner
from bgpcfgd.template import TemplateFabric
from bgpcfgd.utils import wait_for_daemons, read_constants


def main():
    """ Main function """
    wait_for_daemons(["bgpd", "zebra", "staticd"], seconds=20)
    #
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   ConfigMgr(),
        'tf':        TemplateFabric(),
        'constants': read_constants(),
    }
    managers = [
        # Config DB managers
        BGPDataBaseMgr(common_objs, "CONFIG_DB", swsscommon.CFG_DEVICE_METADATA_TABLE_NAME),
        BGPDataBaseMgr(common_objs, "CONFIG_DB", swsscommon.CFG_DEVICE_NEIGHBOR_METADATA_TABLE_NAME),
        # Interface managers
        InterfaceMgr(common_objs, "CONFIG_DB", swsscommon.CFG_INTF_TABLE_NAME),
        InterfaceMgr(common_objs, "CONFIG_DB", swsscommon.CFG_LOOPBACK_INTERFACE_TABLE_NAME),
        InterfaceMgr(common_objs, "CONFIG_DB", swsscommon.CFG_VLAN_INTF_TABLE_NAME),
        InterfaceMgr(common_objs, "CONFIG_DB", swsscommon.CFG_LAG_INTF_TABLE_NAME),
        # State DB managers
        ZebraSetSrc(common_objs, "STATE_DB", swsscommon.STATE_INTERFACE_TABLE_NAME),
        # Peer Managers
        BGPPeerMgrBase(common_objs, "CONFIG_DB", swsscommon.CFG_BGP_NEIGHBOR_TABLE_NAME, "general", True),
        BGPPeerMgrBase(common_objs, "CONFIG_DB", "BGP_MONITORS", "monitors", True),
        BGPPeerMgrBase(common_objs, "CONFIG_DB", "BGP_PEER_RANGE", "dynamic", False),
        # AllowList Managers
        BGPAllowListMgr(common_objs, "CONFIG_DB", "BGP_ALLOWED_PREFIXES"),
    ]
    runner = Runner()
    for mgr in managers:
        runner.add_manager(mgr)
    runner.run()