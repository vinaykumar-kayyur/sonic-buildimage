#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# sensorutil.py
# Platform-specific SENSOR status interface for SONiC
#

import os
import sys
import collections
import json

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from baseutil import *

try:
    from sonic_mon.mon_base import MonBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

SENSOR_CONFIG = {
    "num":58,
    "attr_list":[
        [   {"attr":"name","data":"vol1", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol1/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol1/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol1/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol1/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol1/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol2", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol2/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol2/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol2/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol2/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol2/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol3", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol3/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol3/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol3/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol3/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol3/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol4", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol4/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol4/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol4/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol4/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol4/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol5", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol5/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol5/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol5/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol5/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol5/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol6", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol6/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol6/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol6/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol6/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol6/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol7", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol7/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol7/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol7/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol7/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol7/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol8", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol8/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol8/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol8/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol8/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol8/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol9", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol9/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol9/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol9/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol9/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol9/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol10", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol10/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol10/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol10/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol10/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol10/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol11", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol11/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol11/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol11/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol11/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol11/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol12", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol12/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol12/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol12/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol12/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol12/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol13", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol13/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol13/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol13/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol13/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol13/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol14", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol14/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol14/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol14/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol14/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol14/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol15", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol15/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol15/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol15/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol15/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol15/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol16", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol16/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol16/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol16/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol16/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol16/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol17", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol17/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol17/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol17/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol17/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol17/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol18", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol18/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol18/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol18/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol18/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol18/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol19", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol19/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol19/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol19/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol19/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol19/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol20", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol20/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol20/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol20/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol20/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol20/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol21", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol21/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol21/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol21/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol21/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol21/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol22", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol22/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol22/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol22/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol22/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol22/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol23", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol23/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol23/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol23/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol23/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol23/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol24", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol24/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol24/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol24/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol24/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol24/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol25", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol25/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol25/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol25/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol25/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol25/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol26", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol26/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol26/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol26/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol26/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol26/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol27", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol27/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol27/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol27/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol27/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol27/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol28", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol28/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol28/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol28/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol28/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol28/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol29", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol29/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol29/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol29/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol29/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol29/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"vol30", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/vol_sensor/vol30/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/vol_sensor/vol30/alias", "gettype":"sysfs"},
            {"attr":"type","data":"vol", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/vol_sensor/vol30/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"min", "loc":"/sys_switch/vol_sensor/vol30/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
            {
                "attr":"value", "loc":"/sys_switch/vol_sensor/vol30/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision": 3, "unit":"V"
            },
        ],
        [   {"attr":"name","data":"temp1", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp1/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp1/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp1/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp1/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp1/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp2", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp2/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp2/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp2/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp2/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp2/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp3", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp3/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp3/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp3/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp3/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp3/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp4", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp4/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp4/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp4/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp4/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp4/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp5", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp5/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp5/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp5/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp5/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp5/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp6", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp6/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp6/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp6/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp6/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp6/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp7", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp7/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp7/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp7/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp7/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp7/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp8", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp8/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp8/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp8/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp8/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp8/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp9", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp9/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp9/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp9/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp9/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp9/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp10", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp10/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp10/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp10/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp10/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp10/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp11", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp11/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp11/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp11/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp11/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp11/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp12", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp12/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp12/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp12/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp12/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp12/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp13", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp13/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp13/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp13/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp13/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp13/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp14", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp14/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp14/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp14/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp14/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp14/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp15", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp15/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp15/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp15/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp15/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp15/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp16", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp16/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp16/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp16/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp16/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp16/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp17", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp17/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp17/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp17/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp17/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp17/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp18", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp18/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp18/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp18/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp18/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp18/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp19", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp19/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp19/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp19/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp19/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp19/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp20", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp20/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp20/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp20/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp20/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp20/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"temp21", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/temp_sensor/temp21/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/temp_sensor/temp21/alias", "gettype":"sysfs"},
            {"attr":"type","data":"temp", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/temp_sensor/temp21/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"min", "loc":"/sys_switch/temp_sensor/temp21/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
            {
                "attr":"value", "loc":"/sys_switch/temp_sensor/temp21/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C"
            },
        ],
        [   {"attr":"name","data":"curr1", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/curr_sensor/curr1/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/curr_sensor/curr1/alias", "gettype":"sysfs"},
            {"attr":"type","data":"curr", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/curr_sensor/curr1/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"min", "loc":"/sys_switch/curr_sensor/curr1/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"value", "loc":"/sys_switch/curr_sensor/curr1/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
        ],
        [   {"attr":"name","data":"curr2", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/curr_sensor/curr2/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/curr_sensor/curr2/alias", "gettype":"sysfs"},
            {"attr":"type","data":"curr", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/curr_sensor/curr2/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"min", "loc":"/sys_switch/curr_sensor/curr2/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"value", "loc":"/sys_switch/curr_sensor/curr2/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
        ],
        [   {"attr":"name","data":"curr3", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/curr_sensor/curr3/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/curr_sensor/curr3/alias", "gettype":"sysfs"},
            {"attr":"type","data":"curr", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/curr_sensor/curr3/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"min", "loc":"/sys_switch/curr_sensor/curr3/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"value", "loc":"/sys_switch/curr_sensor/curr3/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
        ],
        [   {"attr":"name","data":"curr4", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/curr_sensor/curr4/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/curr_sensor/curr4/alias", "gettype":"sysfs"},
            {"attr":"type","data":"curr", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/curr_sensor/curr4/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"min", "loc":"/sys_switch/curr_sensor/curr4/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"value", "loc":"/sys_switch/curr_sensor/curr4/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
        ],
        [   {"attr":"name","data":"curr5", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/curr_sensor/curr5/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/curr_sensor/curr5/alias", "gettype":"sysfs"},
            {"attr":"type","data":"curr", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/curr_sensor/curr5/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"min", "loc":"/sys_switch/curr_sensor/curr5/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"value", "loc":"/sys_switch/curr_sensor/curr5/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
        ],
        [   {"attr":"name","data":"curr6", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/curr_sensor/curr6/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/curr_sensor/curr6/alias", "gettype":"sysfs"},
            {"attr":"type","data":"curr", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/curr_sensor/curr6/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"min", "loc":"/sys_switch/curr_sensor/curr6/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"value", "loc":"/sys_switch/curr_sensor/curr6/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
        ],
        [   {"attr":"name","data":"curr7", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/curr_sensor/curr7/type", "gettype":"sysfs"},
            {"attr":"alias", "loc":"/sys_switch/curr_sensor/curr7/alias", "gettype":"sysfs"},
            {"attr":"type","data":"curr", "gettype":"direct_config"},
            {
                "attr":"max", "loc":"/sys_switch/curr_sensor/curr7/max", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"min", "loc":"/sys_switch/curr_sensor/curr7/min", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
            {
                "attr":"value", "loc":"/sys_switch/curr_sensor/curr7/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":3, "unit":"A"
            },
        ],
    ],
}

class SensorUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(SENSOR_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)