
# pcieutil.py
# Platform-specific PCIE status interface for SONIC
#

import os
import yaml
import subprocess

try:
    from pcie_base import PcieBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")
    


class PcieUtil():
    """Platform-specific PCIEutil class"""
    
    def __init__(self):
        self.Dict = {}
  

    # input the hwsku path 
    def get_pcie_id(self, hwsku_path):
        _dict_temp = {}
    # get the device message
        config_path = hwsku_path + '/pcie.yaml'
        with open(config_path) as pcie_file:
            pcieInfo = yaml.safe_load(pcie_file)
            devSpd = pcieInfo['devSpd']
            devId = pcieInfo['devId']
    # get the device id info        
        command = "sudo lspci -n | grep " + devId
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output = proc.stdout.readlines()
        (out, err) = proc.communicate()

        if proc.returncode > 0:
            for line in output:
                print(line.strip())
            return
        else:
            for line in output:
                busId = line.strip()
                venderId = line.split(":")[2].strip()
                deviceId = line.split(":")[3].split()[0].strip()
                _dict_temp['venderId'] = venderId
                _dict_temp['deviceId'] = deviceId
                self.Dict[busId] = _dict_temp
        return self.Dict
    # input the hwsku path 
    def get_pcie_speed(self ,hwsku_path):
        _keyDict = {}
    # get the device message        
        config_path = hwsku_path + '/pcie.yaml'
        with open(config_path) as pcie_file:
            pcieInfo = yaml.safe_load(pcie_file)
            devSpd = pcieInfo['devSpd']
            devId = pcieInfo['devId']
    #  get the device key              
        command = "sudo lspci"
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output = proc.stdout.readlines()
        (out, err) = proc.communicate()
    #shell cmd return failed
        if proc.returncode > 0:
            for line in output:
                click.echo(line.strip())
            return
        else:
            for line in output:
                if devId in line:
                    _keyDict[line.split()[0]] = line.strip()
    # get the devicr message
        for key, value in _keyDict.items():
            checkin = 0
            erroutput = open("/dev/null", "w")
            command = "sudo lspci -vvvv -s " + key
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=erroutput.fileno())
            proc.wait()
            output = proc.stdout.readlines()
            #shell cmd return failed
            if proc.returncode > 0:
                for line in output:
                    click.echo(line.strip())
                print("shell cmd return faild: {0}".format(proc.returncode))
                return
            else:
                for line in output:
                    if "LnkSta:" in line:
                        self.Dict[value] = line.strip()
                        speed = line.split()[2].split(',')[0]   #LnkSta: Speed 5GT/s, Width x4, TrErr- Train- SlotClk+ DLActive- BWMgmt- ABWMgmt-
                        if speed == devSpd:                        
                            checkin = 1
                        else:
                            print("LnkSta not match which is {0}".format(speed))
        return self.Dict
        
        
            



