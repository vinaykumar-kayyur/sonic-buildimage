from unittest.mock import MagicMock, patch

import os
from bgpcfgd.directory import Directory
from bgpcfgd.template import TemplateFabric
from . import swsscommon_test
from .util import load_constants
import bgpcfgd.managers_device_global

TEMPLATE_PATH = os.path.abspath('../../dockers/docker-fpm-frr/frr')
BASE_PATH = os.path.abspath('../sonic-bgpcfgd/tests/data/general/peer-group.conf/')

def constructor():
    cfg_mgr = MagicMock()
    def get_text():
        return cfg_mgr.changes
    def update():
        cfg_mgr.changes = get_string_from_file("/result_all.conf")
    def push(cfg):
        cfg_mgr.changes += cfg + "\n"
    cfg_mgr.get_text = get_text
    cfg_mgr.update = update
    cfg_mgr.push = push

    constants = load_constants()['constants']
    common_objs = {
        'directory': Directory(),
        'cfg_mgr':   cfg_mgr,
        'tf':        TemplateFabric(TEMPLATE_PATH),
        'constants': constants
    }
    mgr = bgpcfgd.managers_device_global.DeviceGlobalCfgMgr(common_objs, "CONFIG_DB", "BGP_DEVICE_GLOBAL")
    cfg_mgr.update()
    return mgr


@patch('bgpcfgd.managers_device_global.log_debug')
def test_isolate_device(mocked_log_info): 
    m = constructor()
    res = m.set_handler("STATE", {"tsa_enabled": "true"})
    assert res, "Expect True return value for set_handler"
    mocked_log_info.assert_called_with("DeviceGlobalCfgMgr::Done")
    assert m.cfg_mgr.get_text() == get_string_from_file("/result_all_isolate.conf")

@patch('bgpcfgd.managers_device_global.log_debug')
def test_unisolate_device(mocked_log_info): 
    m = constructor()
    res = m.set_handler("STATE", {"tsa_enabled": "false"})
    assert res, "Expect True return value for set_handler"
    mocked_log_info.assert_called_with("DeviceGlobalCfgMgr::Done")
    assert m.cfg_mgr.get_text() == get_string_from_file("/result_all_unisolate.conf")

def test_check_state_and_get_tsa_routemaps():
    m = constructor()
    m.set_handler("STATE", {"tsa_enabled": "true"})
    res = m.check_state_and_get_tsa_routemaps(m.cfg_mgr.get_text())
    assert res == get_string_from_file("/result_isolate.conf")

    m.set_handler("STATE", {"tsa_enabled": "false"})
    res = m.check_state_and_get_tsa_routemaps(m.cfg_mgr.get_text())
    assert res == ""
    
def test_get_tsa_routemaps(): 
    m = constructor()
    res = m.get_tsa_routemaps(m.cfg_mgr.get_text())
    expected_res = get_string_from_file("/result_isolate.conf")
    assert res == expected_res

def test_get_tsb_routemaps(): 
    m = constructor()
    res = m.get_tsb_routemaps(m.cfg_mgr.get_text())
    expected_res = get_string_from_file("/result_unisolate.conf")
    assert res == expected_res

def get_string_from_file(filename):
    fp = open(BASE_PATH + filename, "r")
    cfg = fp.read()
    fp.close()

    return cfg

@patch('bgpcfgd.managers_device_global.log_err')
def test_set_handler_failure_case(mocked_log_info): 
    m = constructor()
    res = m.set_handler("STATE", {})
    assert res == False, "Expect False return value for invalid data passed to set_handler"
    mocked_log_info.assert_called_with("DeviceGlobalCfgMgr:: data is None")

def test_del_handler(): 
    m = constructor()
    res = m.del_handler("STATE")
    assert res, "Expect True return value for del_handler"

