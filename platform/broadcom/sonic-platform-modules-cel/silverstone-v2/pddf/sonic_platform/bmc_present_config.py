#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @Time    : 2023/7/25 15:04
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao
# @Function: get bmc status. present(True) or absent(False)

def get_bmc_status():
    bmc_present_path = r"/usr/local/bin/bmc_present"
    bmc_status = None
    with open(bmc_present_path, "r") as f:
        bmc_status = f.read().strip()
    return True if bmc_status == "True" else False


