# -*- coding: utf-8 -*-#

# @Time   : 2023/3/16 10:13
# @Mail   : J_Talong@163.com yajiang@celestica.com
# @Author : jiang tao


try:
    import abc
    from ..sonic_pcie.pcie_common import PcieUtil
except ImportError as e:
    raise ImportError(str(e) + " - required module not found")


class Pcie(PcieUtil):
    def __init__(self, path):
        PcieUtil.__init__(path)
# class Pcie(object):
#     def __init__(self, path):
#         """
#           Constructor
#           Args:
#             pcieutil file and config file path
#          """
#
#         self.pcie_util = PcieUtil(path)
#
#     @abc.abstractmethod
#     def get_pcie_device(self):
#         """
#          get current device pcie info
#
#           Returns:
#             A list including pcie device info
#          """
#         return self.pcie_util.get_pcie_device()
#
#     @abc.abstractmethod
#     def get_pcie_check(self):
#         """
#          Check Pcie device with config file
#          Returns:
#             A list including pcie device and test result info
#         """
#         return self.pcie_util.get_pcie_check()
