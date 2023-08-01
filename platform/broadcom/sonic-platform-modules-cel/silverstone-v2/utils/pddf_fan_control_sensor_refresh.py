#!/usr/bin/python
# -*- coding: utf-8 -*-#

# @Time   : 2023/7/31 13:15
# @Mail   : yajiang@celestica.com
# @Author : jiang tao

import sys
import os
sys.path.append(r"/usr/local/bin")
from FanControl import FanControl
import pddf_sensor_list_refresh


if os.popen("cat /usr/local/bin/bmc_present").read().strip() == "False":
    FanControl.main(sys.argv[1:])

if os.popen("cat /usr/local/bin/bmc_present").read().strip() == "True":
    pddf_sensor_list_refresh.main()
