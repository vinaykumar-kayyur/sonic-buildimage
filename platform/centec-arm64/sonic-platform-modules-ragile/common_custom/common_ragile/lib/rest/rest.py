#!/usr/bin/python
# -*- coding: utf-8 -*-

import redis
import urllib
import urllib2
import json
import ssl
import requests
import cookielib
import time
import os
import re
import collections
import pickle
import binascii
import base64
import subprocess
import imp
import pexpect
from logutil.logutil import *
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {'Content-type': 'application/json'}
context = ssl._create_unverified_context()
__DEBUG__ = "N"
LOGIN_TRY_TIME = 3
RESTRETURNKEY = "status"
RESTRETURNSUCCESSKEY = "OK"
SYSLOG_IDENTIFIER = "rest"

def d_print(debug_info):
    if(__DEBUG__ == "Y"):
        print(debug_info)


class BMCMessage():
    _session = None
    _diagToBmcCmdPrefix = "/usr/local/bin/rj_rawcmd_cli diag cmd "
    _sessionFile = "bmcsession"  
    BMC_LOGIN_PATH = "/login"
    BMC_URLPRE_PATH = "http://240.1.1.1:8080"
    FANS_PRE_STRING = "/xyz/openbmc_project/inventory/system/chassis/motherboard/fan" 
    FANS_STATE_STRING = "/xyz/openbmc_project/state/fan0"
    FANS_PATH = "/xyz/openbmc_project/sensors/fan_tach/enumerate"
    FAN_FRU_PATH = "/xyz/openbmc_project/inventory/system/chassis/motherboard/enumerate"
    SENSORS_PATH = "/xyz/openbmc_project/sensors/enumerate"
    BMC_STATE_PATH = '/xyz/openbmc_project/state/bmc0'
    
    def getBmcUrl(self, name):
        return self.BMC_URLPRE_PATH + name
    
    def getBmcValue(self, path):
        return self.bmcget(self.getBmcUrl(path));
      
    @property
    def getSessionConfigfile(self):
        filename = self._sessionFile
        direct = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(direct, filename)
        return filename
    
    def saveSessionToFile(self):
        configfile = self.getSessionConfigfile
        with open(configfile, 'wb') as f:
            pickle.dump(self.session.cookies, f)
      
    @property
    def getsessionvalue(self):
        configfile = self.getSessionConfigfile;
        if os.path.exists(configfile) == False:
            d_print("file no exists")
            return False
        self.session = requests.session()
        self.session.keep_alive = False
        with open(configfile, 'rb') as f:
            self.session.cookies.update(pickle.load(f))
        return True

    def __init__(self):
        d_print("bmcmessage init...")
        self.session = requests.session()
        self.session.keep_alive = False
        #if self.getsessionvalue == False:
        #    d_print("init value...")
        #    self.login_times()
        #if self.getsessionvalue == False:
        #    raise Exception("connect failed")
        pass

    def __del__(self):
        pass

    def bmcget(self, url):
        d_print(url)
        for i in range(3):
            try:
                response = self.session.get(url, verify=False, timeout=60)
                if self.isReturnSuccess(response.text):
                    return json.loads(response.text)['data']
                bmc_restful_logger("bmcget:%s,status:%s,text:%s" %(url,response.status_code,response.text))
            except Exception as e:
                bmc_restful_logger("bmcget:%s,Exception:%s" %(url,str(e)))
        return None

    def bmcput(self, url, data):
        d_print(url)
        d_print(data)
        request = {}
        request["data"] = data
        data_json = json.dumps(request)
        d_print(data_json)
        try:
            response = self.session.put(
                url, data=data_json, headers=headers, verify=False, timeout=60)
            if self.isReturnSuccess(response.text):
                return 1
            else:
                bmc_restful_logger("data:%s,bmcput:%s,status:%s,text:%s" %(data,url,response.status_code,response.text))
                return 0
        except Exception as e:
            bmc_restful_logger("data:%s,bmcput:%s,Exception:%s" %(data,url,str(e)))
            return 0
      
    def bmcpost(self, url, data,maytimeout=120):
        d_print(url)
        d_print(data)
        request = {}
        request = data
        data_json = json.dumps(request)
        d_print(data_json)
        
        for i in range(3):
            try:
                response = self.session.post(
                    url, data=data_json, headers=headers, verify=False, timeout=maytimeout)
                if self.isReturnSuccess(response.text):
                    if json.loads(response.text)['data'] != None and json.loads(response.text)['data']['Outputs'] != None:
                        return json.loads(response.text)['data']['Outputs']
                    else:
                        return "Success"
                bmc_restful_logger("data:%s,bmcpost:%s,status:%s,text:%s" %(data,url,response.status_code,response.text))
            except Exception as e:
                bmc_restful_logger("bmcpost:%s,Exception:%s" %(url,str(e)))
        return None

    def postSffTemp(self, data):
        url = "/xyz/openbmc_project/sensors/temperature/ODM_SSF_Temp/attr/Scale"
        return self.bmcput(self.getBmcUrl(url), data)
        
    def isNeedLogin(self, val):
        if RESTRETURNKEY in json.loads(val) and json.loads(val)[RESTRETURNKEY] == "error" and json.loads(val)['data']['description'] == 'Login required':
            return True
        else:
            return False

    def isReturnSuccess(self, val):
        if RESTRETURNKEY in json.loads(val) and json.loads(val)[RESTRETURNKEY] == RESTRETURNSUCCESSKEY:
            return True
        else:
            return False

    def getfansList(self):
        fan_ret = self.bmcget(self.getBmcUrl(self.FANS_PATH))
        return fan_ret

    def getfanFruList(self):
        fanfru_ret = self.bmcget(self.getBmcUrl(self.FAN_FRU_PATH))
        return fanfru_ret

    def getFansMsg(self):
        curFanList = self.getfansList()
        fanfru_ret = self.getfanFruList()
        if fanfru_ret == None:
            return None
        curfanFruLists = [it for it in fanfru_ret  if "fan" in it]
        d_print(curFanList)
        fan_state = self.bmcget(self.getBmcUrl(self.FANS_STATE_STRING))
        if fan_state == None:
            return None
        if curFanList == None:
            return None
        curFanLists = [elem for elem in curFanList if  elem.split("/")[-1].startswith("FAN")]
        curFanLists = sorted(curFanLists)
        result = dict()
        result["Number"] = len(curFanLists)
        d_print("fan num:%d" % len(curFanLists))
        for item in curFanLists:
            rest1 = item.split("/")
            ret = rest1[-1]#.replace("ODM_", "").upper()
            d_print("ret: %s fan index:%s"%(ret, str(int(ret[3:4]) - 1)))
            fansreadNamevalue = self.FANS_PRE_STRING + str(int(ret[3:4]) - 1)
            dict1 = curFanList.get(item, None)
            dict2 = fanfru_ret.get(fansreadNamevalue, None)
            if dict1 == None:
                dict_t = dict2
            elif dict2 == None:
                dict_t = dict1
            else:
                dict_t = dict(dict1, **dict2)

            d_print("dict:")
            d_print(dict_t)
            
            fanPresentKey = "Fan%dPresent" % (int(ret[3:4]))
            fanStateKey = "Fan%dState" % (int(ret[3:4]))
            fanAirFlow = "Fan%dAirFlow"% (int(ret[3:4]))
            fanMotor1= "Fan%dMotor1"% (int(ret[3:4]))
            fanMotor2= "Fan%dMotor2"% (int(ret[3:4]))
            
            ret_ttt = False
            if fan_state != None  and fan_state.get(fanPresentKey, None) == "xyz.openbmc_project.State.ODM_Fan.CurrentState.Ready":
                dict_t["Present"] = True 
            else:
                dict_t["Present"] = False
            
            if fan_state != None and fan_state.get(fanStateKey, None) == "xyz.openbmc_project.State.ODM_Fan.CurrentState.Ready":
                dict_t["Running"] = True 
            else:
                dict_t["Running"] = False
            
            if fan_state.get(fanMotor1, None) == "xyz.openbmc_project.State.ODM_Fan.CurrentState.Ready" and fan_state.get(fanMotor2, None) == "xyz.openbmc_project.State.ODM_Fan.CurrentState.Ready":
                ret_ttt =  True
            
            airflowtmp = fan_state.get(fanAirFlow, "").split('.')[-1]
            if airflowtmp == "NA":
                dict_t["AirFlow"] = None
            else:
                dict_t["AirFlow"]= airflowtmp
            dict_t["Status"]= ret_ttt
            
            dict_t["PN"] = dict_t.get("Model", None) 
            dict_t["SN"] = dict_t.get("SerialNumber", None)
            dict_t["Speed"] = dict_t.get("Value", None)
            dict_t["LowThd"] = dict_t.get("CriticalLow", None)
            dict_t["HighThd"] = dict_t.get("CriticalHigh", None) 
            result[ret] = dict_t
        return collections.OrderedDict(sorted(result.items(), key=lambda t: t[0]))

    def login_times(self):
        n = 0
        while True:
            if n > LOGIN_TRY_TIME:
                return False
            if self.login() == True:
                return True
            n += 1
        return False

    def login(self):
        try:
            url = self.getBmcUrl(self.BMC_LOGIN_PATH)
            self.session = requests.session()
            data_json = json.dumps(LOGIN_REQUEST_DATA)
            response = self.session.post(
                url, data=data_json, headers=headers, verify=False, timeout=60)
            if self.isReturnSuccess(response.text):
                self.saveSessionToFile()
                return True
            else:
                return False
        except Exception:
            return False

    def getPsuNum(self):
        return len(self.getPsuValues())
    
    def getPsuMsg(self):
        PSU_FAN_PATH = "/xyz/openbmc_project/sensors/fan_tach/enumerate"
        PSU_FRU_PATH = "/xyz/openbmc_project/inventory/system/chassis/motherboard/enumerate"
        PSU_PRESENCE_STR = "/xyz/openbmc_project/state/psu0"
        STATE_STR = "xyz.openbmc_project.State.ODM_PSU.CurrentState.Ready"
        STATE_TRUE = 'xyz.openbmc_project.State.ODM_PSU.CurrentState.True'
        PSU_PRE_STR ="/xyz/openbmc_project/inventory/system/chassis/motherboard/powersupply"
         
        psuNums = self.bmcget(self.getBmcUrl(PSU_FAN_PATH))
        if psuNums == None:
            return None
        psuNumStrs = [psu_item for psu_item in psuNums if "PSU" in psu_item]
        d_print(psuNumStrs)
        ret = self.bmcget(self.getBmcUrl(PSU_FRU_PATH))
        value = self.bmcget(self.getBmcUrl(PSU_PRESENCE_STR))
        if ret == None:
            return None
        psuRestult = dict()
        psuRestult["Number"] = len(psuNumStrs)
        PSUNAME = "PSU"
        for psu_child in range(len(psuNumStrs)):
            index = psu_child + 1
            psuNames = PSU_PRE_STR + str(index - 1)
            psuDict = dict()
            psuPresentKey = "PSU%dPresent" % (index )
            psuStateKey = "PSU%dState" % (index )
            psuInputStatus ="PSU%dInputState" % (index )
            psuInputType  ="PSU%dInputType"% (index )
            psuOutputStatus= "PSU%dOutputState"% (index )
            AirFlow  = "PSU%dAirFlow"% (index )
            psuName = PSUNAME + str(index )
            itemdict = ret.get(psuNames, {})
            psuDict = itemdict
            if value.get(psuPresentKey, None) == STATE_STR:
                psuDict["Present"] = True
            else:
                psuDict["Present"] = False
            if value.get(psuStateKey, None) == STATE_STR:
                psuDict["PowerStatus"] = True
            else:
                psuDict["PowerStatus"] = False
            if value.get(psuInputStatus, None) == STATE_TRUE:
                psuDict["InputStatus"] = True
            else:
                psuDict["InputStatus"] = False
            if value.get(psuOutputStatus, None) == STATE_TRUE:
                psuDict["OutputStatus"] = True
            else:
                psuDict["OutputStatus"] = False
            psuinputtypetmp = value.get(psuInputType, "").split('.')[-1]
            if psuinputtypetmp == 'NA':
                psuDict["InputType"] = None
            else:
                psuDict["InputType"] = psuinputtypetmp
            ariflowtmp = value.get(AirFlow, "").split('.')[-1]
            if ariflowtmp == 'NA':
                psuDict["AirFlow"] = None
            else:
                psuDict["AirFlow"] = ariflowtmp
            psuDict["PN"] = itemdict.get("Model", None)
            psuDict["SN"] = itemdict.get("SerialNumber", None)
            psuRestult[psuName] = psuDict
        return collections.OrderedDict(sorted(psuRestult.items(), key=lambda t: t[0]))

    def getSensorsNum(self):
        return len(self.getSensorsNames())

    def getSensorsName(self, index):
        result = self.getSensorsNames()[index]
        rest1 = result.split(":")
        return "".join(rest1[-1:])

    def getSensorsFullName(self, index):
        return self.getSensorsNames()[index]

    def getSensorsInputNumsByIndex(self, index):
        name = self.getSensorsFullName(index)
        return self.getSensorsinputNumByName(name)
 
    def getsensorLists(self):  
        ret_t = self.bmcget(self.getBmcUrl(self.SENSORS_PATH))
        bmcstate = self.bmcget(self.getBmcUrl(self.BMC_STATE_PATH))
        #lc1 = ["Dvdd0v8_V1","Dvdd0v8_C1","Avdd0v8_V1","Avdd0v8_C1","Cq1v2_V1","Cq1v2_C1","Cq1v8_V1","Cq1v8_C1","ODM_Cq3v3_V1","ODM_Cq3v3_C1","ODM_Cq5v0_V1","ODM_Cq5v0_C1","ODM_Cq3v3Qs_V11","ODM_Cq3v3Qs_C11","ODM_Cq3v3Qs_V21","ODM_Cq3v3Qs_C21","ODM_LC1_Temp"]
        #lc2 = ["Dvdd0v8_V2","Dvdd0v8_C2","Avdd0v8_V2","Avdd0v8_C2","Cq1v2_V2","Cq1v2_C2","Cq1v8_V2","Cq1v8_C2","ODM_Cq3v3_V2","ODM_Cq3v3_C2","ODM_Cq5v0_V2","ODM_Cq5v0_C2","ODM_Cq3v3Qs_V12","ODM_Cq3v3Qs_C12","ODM_Cq3v3Qs_V22","ODM_Cq3v3Qs_C22","ODM_LC2_Temp"]
        #lc3 = ["Dvdd0v8_V3","Dvdd0v8_C3","Avdd0v8_V3","Avdd0v8_C3","Cq1v2_V3","Cq1v2_C3","Cq1v8_V3","Cq1v8_C3","ODM_Cq3v3_V3","ODM_Cq3v3_C3","ODM_Cq5v0_V3","ODM_Cq5v0_C3","ODM_Cq3v3Qs_V13","ODM_Cq3v3Qs_C13","ODM_Cq3v3Qs_V23","ODM_Cq3v3Qs_C23","ODM_LC3_Temp"]
        #lc4 = ["Dvdd0v8_V4","Dvdd0v8_C4","Avdd0v8_V4","Avdd0v8_C4","Cq1v2_V4","Cq1v2_C4","Cq1v8_V4","Cq1v8_C4","ODM_Cq3v3_V4","ODM_Cq3v3_C4","ODM_Cq5v0_V4","ODM_Cq5v0_C4","ODM_Cq3v3Qs_V14","ODM_Cq3v3Qs_C14","ODM_Cq3v3Qs_V24","ODM_Cq3v3Qs_C24","ODM_LC4_Temp"]

        if ret_t == None:
            return None
        result = dict()
        result['Sys'] = {"Sys_AirFlow":bmcstate.get('AirFlow',"").split('.')[-1]}
        for item in ret_t:
            childitem = dict()
            rest1 = item.split("/")
            ret = rest1[-1]
            psus = ret.split("_")[0]
            value1 = ret
            if ret == "ODM_SSF_Temp":
                continue
            elif "_TEMP" in ret:
                psus = "temperature".upper()
                value1 = ret.upper()
            ret_tmp = ret_t.get(item, None)
            if ret_tmp == None:
                continue
            typename = self.getInputTypes(value1)
            ret_tmp["Type"] = typename
            ret_tmp["CriticalLow"] = self.getFinalValueByType(typename, ret_tmp.get("CriticalLow", 0))
            ret_tmp["LowThd"] = ret_tmp.get("CriticalLow", 0)
            ret_tmp["CriticalHigh"] = self.getFinalValueByType(typename, ret_tmp.get("CriticalHigh", 0)) 
            ret_tmp["HighThd"] = ret_tmp.get("CriticalHigh", 0)
            ret_tmp["Value"] = self.getFinalValueByType(typename, ret_tmp.get("Value", 0))
            if result.__contains__(psus):
                result.get(psus)[value1] = ret_tmp
            else:
                childitem[value1] = ret_tmp
                result[psus] = childitem
        return collections.OrderedDict(sorted(result.items(), key=lambda t: t[0]))

    def getInputTypes(self, name):
        if "TEMP" in name:
            return "temperature"
        elif "SYS_" in name and name.endswith("_V"):
            return "voltage"
        elif "SYS_" in name and name.endswith("_C"):
            return "amp"
        elif name.endswith("_V") or name.endswith("_V1") or name.endswith("_V2") or name.endswith("_V3") or name.endswith("_V4"):
            return "voltage"
        elif name.endswith("_C") or name.endswith("_C1") or name.endswith("_C2") or name.endswith("_C3") or name.endswith("_C4"):
            return "amp"
        elif name.endswith("_V11") or name.endswith("_V21") or name.endswith("_V12") or name.endswith("_V22") or name.endswith("_V13")  or name.endswith("_V23")  or name.endswith("_V14")  or name.endswith("_V24") :
            return "voltage"
        elif name.endswith("_C11") or name.endswith("_C21") or name.endswith("_C12") or name.endswith("_C22") or name.endswith("_C13")  or name.endswith("_C23")  or name.endswith("_C14")  or name.endswith("_C24") :
            return "amp"
        elif name.endswith("_C") :
            return "amp"
        elif name.endswith("_P") :
            return "power"
        elif "FAN" in name:
            return "RPM"
        elif "_CURR" in name:
            return "amp"
        elif "_VOL" in name:
            return "voltage"
        elif "POWER" in name:
            return "power"
        elif name == "SWITCH_VANALOG" or name == "SWITCH_VCORE":
            return "voltage"
        elif name == "SWITCH_CCORE" or name == "SWITCH_CANALOG":
            return "amp"
        else: 
            return "voltage"
        return None

    def getSensorInputType(self, name):
        if "TEMP" in name:
            return "temperature"
        elif "SYS_" in name and name.endswith("_V"):
            return "voltage"
        elif "SYS_" in name and name.endswith("_C"):
            return "amp"
        elif "FAN" in name:
            return "RPM"
        elif "_CURR" in name:
            return "amp"
        elif "_VOL" in name:
            return "voltage"
        elif "POWER" in name:
            return "power"
        else: 
            return "voltage"
        return None

    def getFinalValueByType(self, inputtype, value):
        if inputtype == "voltage" or inputtype == "temperature" or inputtype == "power" or inputtype == "wattage" or inputtype == "amp":
            return float(value) / 1000  
        else:
            return value

    def getDealValueByType(self, inputtype, value):
        inputtype = self.getSensorInputType(inputtype)
        if inputtype == "voltage" or inputtype == "temperature" or inputtype == "power" or inputtype == "wattage" or inputtype == "amp":
            return float(value) / 1000  
        else:
            return value

    @property
    def session(self):
        return self._session

    def send_diag_cmd_t_bmc(self, str):
        PSU_PRESENCE_STR = "/api/hw/rawcmd"
        fun_name_full = self._diagToBmcCmdPrefix + str
        data_post = {"Command": fun_name_full}
        realurl = self.getBmcUrl(PSU_PRESENCE_STR)
        return self.bmcpost(realurl, data_post)

    def get_macrov_value(self):
        data_post = {"Command": "/usr/local/bin/rj_rawcmd_cli get mac_rov"}
        PSU_PRESENCE_STR = "/api/hw/rawcmd"
        realurl = self.getBmcUrl(PSU_PRESENCE_STR)
        return self.bmcpost(realurl, data_post)

    def get_current_bmc_version(self):
        dataval = self.getBmcValue("/api/bmc/info")
        if dataval == None:
            return ""
        else:
            return "\"BmcVersion\": \""+dataval["Version"]+"\""

    def get_bmc_version_flash(self):
        dataval = self.getBmcValue("/api/bmc/info")
        if dataval == None:
            return "N/A","N/A"
        else:
            return str(dataval["Version"]),str(dataval["Flash"])

class MonitorMessage():

    def __init__(self):
        print ("test")

    def test(self):
        print ("Monitor")


class x86Message(MonitorMessage):
    MAILBOX_DIR = "/sys/bus/i2c/devices/"
    PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
    module_product    = None
    
    def __init__(self):
        platform = Osutil.get_platform_info(Osutil.get_machine_info())
        platform_path = "/".join([self.PLATFORM_ROOT_PATH, platform])
        try:
            module_file_config = "/".join([platform_path, "plugins", "config.py"])
            self.module_product = imp.load_source("config", module_file_config)
        except IOError, e:
            log_error("Failed to load platform module '%s': %s" % ("config", str(e)), True)
        d_print('x86 init...')

    def test(self):
        print ("x86Message")

    def getFanNum(self):
        return len(self.getFanNames())

    def getFanName(self, index):
        x = self.getFanNames()
        name = x[index]
        return name

    # Get a mailbox register
    def get_pmc_register(self, reg_name):
        retval = 'ERR'
        mb_reg_file = self.MAILBOX_DIR + reg_name

        if (not os.path.isfile(mb_reg_file)):
            # print mb_reg_file,  'not found !'
            return "%s %s  notfound" % (retval , mb_reg_file)
        try:
            with open(mb_reg_file, 'r') as fd:
                retval = fd.read()
        except Exception as error:
            pass

        retval = retval.rstrip('\r\n')
        retval = retval.lstrip(" ")
        return retval

    def getValue(self, location, bit , type):
        value_t = self.get_pmc_register(location)
        if value_t.startswith("ERR"):
            return value_t
        if (type == 1):
            return float(value_t) / 1000
        elif (type == 2):
            return float(value_t) / 100
        elif (type == 3):
            psu_status = int(value_t, 16)
            return (psu_status & (1 << bit)) >> bit
        else:
            return value_t;
                        
    def getFanFru(self, name):
        print (name)
        return self.getFanStatus(name)
        # ret = RedisUtil.grtFanFruValue(name)   
        # return self.bmcget(RedisUtil.getRedisPreValue(ret))

    def tlve2set(self,bin_data):
        RAGILE_CARDID = self.module_product.RAGILE_CARDID
        machine_vars=Osutil.get_machine_info()
        machine_vars_onie_version=machine_vars.get("onie_version")
        _value = {}
        _value[boardTLV._TLV_CODE_VENDOR_EXT]     = self.getTLVcardidBin()
        _value[boardTLV._TLV_CODE_PRODUCT_NAME]   = self.module_product.RAGILE_PRODUCTNAME
        _value[boardTLV._TLV_CODE_PART_NUMBER]    = self.module_product.RAGILE_PART_NUMBER
        _value[boardTLV._TLV_CODE_LABEL_REVISION] = self.module_product.RAGILE_LABEL_REVISION
        _value[boardTLV._TLV_CODE_PLATFORM_NAME]  = DeviceMessage().getplatform()
        _value[boardTLV._TLV_CODE_ONIE_VERSION]   = machine_vars_onie_version
        _value[boardTLV._TLV_CODE_MAC_SIZE]       = self.module_product.RAGILE_MAC_SIZE
        _value[boardTLV._TLV_CODE_MANUF_NAME]     = self.module_product.RAGILE_MANUF_NAME
        _value[boardTLV._TLV_CODE_MANUF_COUNTRY]  = self.module_product.RAGILE_MANUF_COUNTRY
        _value[boardTLV._TLV_CODE_VENDOR_NAME]    = self.module_product.RAGILE_VENDOR_NAME
        _value[boardTLV._TLV_CODE_DIAG_VERSION]   = self.module_product.RAGILE_DIAG_VERSION
        _value[boardTLV._TLV_CODE_SERVICE_TAG]    = self.module_product.RAGILE_SERVICE_TAG
        _value[boardTLV._TLV_CODE_MANUF_DATE] =time.strftime('%m/%d/%Y %H:%M:%S', time.localtime())  # 自动添加setmac时
        _value[boardTLV._TLV_CODE_PRODUCT_NAME]   = bin_data.get(boardTLV._TLV_CODE_PRODUCT_NAME)
        _value[boardTLV._TLV_CODE_SERIAL_NUMBER]  = bin_data.get(boardTLV._TLV_CODE_SERIAL_NUMBER)
        _value[boardTLV._TLV_CODE_DEVICE_VERSION]= bin_data.get(boardTLV._TLV_CODE_DEVICE_VERSION)
        _value[boardTLV._TLV_CODE_MAC_BASE] = bin_data.get(boardTLV._TLV_CODE_MAC_BASE)  
        rst, ret = boardTLV().generate_value(_value)
        boardTLV().writeToEEprom(rst , self.module_product.E2_LOC)

    def getCPUeeprom(self):
        e2loc = self.module_product.CPUEEPROMS
        name = self.dumpValueByI2c(e2loc.get('bus'),e2loc.get('loc'))
        return name

    def setCPUeeprom(self,bindata):
        e2loc = self.module_product.CPUEEPROMS
        Osutil.writeToE2(e2loc.get('bus'),e2loc.get('loc'), bindata)

    def dumpValueByI2c(self, bus, loc):
        str = ""
        for i in range(256):
            ret,val = Osutil.rji2cget(bus, loc, i)
            str += chr(Osutil.strtoint(val))
        return str

    def geteepromLocation(self,bus, devno):
        location = "%d-00%02x/eeprom" % (bus,devno)
        return location

    def getTlvLoc(self):
        e2loc = self.module_product.E2_LOC
        location = "%d-00%02x/eeprom" % (e2loc.get('bus'),e2loc.get('devno') )
        return location

    def getTLVe2(self):
        name = self.get_pmc_register(self.getTlvLoc())
        if name == None:
            return name
        return boardTLV().decode_eeprom(name)

    def getcardid(self):
        return self.module_product.RAGILE_CARDID

    def getproductname(self):
        return self.module_product.RAGILE_PRODUCTNAME

    def getTLVproductname(self):
        name = self.get_pmc_register(self.getTlvLoc())
        if name == None:
            return name
        return boardTLV().getcardName(name)

    def getTLVcardidBin(self):
        return boardTLV().generate_e2_cardid(self.module_product.RAGILE_CARDID) 

    def resetTLVe2(self):
        cardidbin = self.getTLVcardidBin()
        _value = {}
        _value[boardTLV._TLV_CODE_VENDOR_EXT]  = cardidbin
        rst, ret = boardTLV().generate_value(_value)
        print (boardTLV().writeToEEprom(rst, self.module_product.E2_LOC))


    def getPsuNum(self):
        # TODO
        pass

    def getPsuValues(self):
        # TODO
        pass

    def getPsuValue(self, index):
        # TODO
        pass

    def getSensorsNum(self):
        # TODO
        pass

    def getSensorsNames(self):
        # TODO
        pass

    def getSensorsName(self, index):
        # TODO
        pass

    def getSensorsFullName(self, index):
        # TODO
        pass

    def getSensorsinputNumByName(self, title):
        # TODO
        pass

    def getSensorsInputNumsByIndex(self, index):
        # TODO
        pass

    def getSensorsInputNameByIndex(self, sensorindex, inputindex):
        # TODO
        pass

    def getSensorsinputs(self, title):
        # TODO
        pass

    def getSensorsInputValue(self, index, index2):
        # TODO
        pass

    pass

class boardTLV():
    _TLV_INFO_ID_STRING = "TlvInfo\x00"
    _TLV_INFO_VERSION = 0x01
    _TLV_INFO_LENGTH = 0x00
    _TLV_INFO_LENGTH_VALUE = 0xba
    _TLV_CODE_PRODUCT_NAME = 0x21
    _TLV_CODE_PART_NUMBER = 0x22
    _TLV_CODE_SERIAL_NUMBER = 0x23
    _TLV_CODE_MAC_BASE = 0x24
    _TLV_CODE_MANUF_DATE = 0x25
    _TLV_CODE_DEVICE_VERSION = 0x26
    _TLV_CODE_LABEL_REVISION = 0x27
    _TLV_CODE_PLATFORM_NAME = 0x28
    _TLV_CODE_ONIE_VERSION = 0x29
    _TLV_CODE_MAC_SIZE = 0x2A
    _TLV_CODE_MANUF_NAME = 0x2B
    _TLV_CODE_MANUF_COUNTRY = 0x2C
    _TLV_CODE_VENDOR_NAME = 0x2D
    _TLV_CODE_DIAG_VERSION = 0x2E
    _TLV_CODE_SERVICE_TAG = 0x2F
    _TLV_CODE_VENDOR_EXT = 0xFD
    _TLV_CODE_CRC_32 = 0xFE
    _TLV_DISPLAY_VENDOR_EXT = 1
    _TLV_CODE_RJ_CARID = 0x01
    _TLV_INFO_HDR_LEN = 11

    def _crc32(self,v):
        return '0x%08x' % (binascii.crc32(v) & 0xffffffff)

    def getTLV_BODY(self, type, productname):
        x = []
        temp_t = ""
        if type == self._TLV_CODE_MAC_BASE:
            arr = productname.split(':')
            for tt in arr:
                temp_t += chr(int(tt, 16))
        elif type == self._TLV_CODE_DEVICE_VERSION:
            temp_t = chr(productname)
        elif type == self._TLV_CODE_MAC_SIZE:
            temp_t = chr(productname >> 8) + chr(productname & 0x00ff)
        else:
            temp_t = productname
        x.append(chr(type))
        x.append(chr(len(temp_t)))
        for i in temp_t:
            x.append(i)
        return x

    def generate_value(self,_t):
        ret = []
        for i in self._TLV_INFO_ID_STRING:
            ret.append(i)
        ret.append(chr(self._TLV_INFO_VERSION))
        ret.append(chr(self._TLV_INFO_LENGTH))
        ret.append(chr(self._TLV_INFO_LENGTH_VALUE))

        total_len = 0
        for key in _t:
            x = self.getTLV_BODY(key, _t[key])
            ret += x
            total_len += len(x)
        ret[10] = chr(total_len + 6)

        ret.append(chr(0xFE))
        ret.append(chr(0x04))
        s = self._crc32(''.join(ret))
        for t in range(0, 4):
            ret.append(chr(int(s[2 * t + 2:2 * t + 4], 16)))
        totallen = len(ret)
        if (totallen < 256):
            for left_t in range(0, 256 - totallen):
                ret.append(chr(0x00))
        return (ret, True)

    def generate_e2_cardid(self, cardid):
        s = "%08x" % cardid
        ret = ""
        for t in range(0, 4):
            ret += chr(int(s[2 * t:2 * t + 2], 16))
        ret = chr(0x01) + chr(len(ret)) + ret
        return ret

    def decode_eeprom(self, e):
        total_len = (ord(e[9]) << 8) | ord(e[10])
        tlv_index = self._TLV_INFO_HDR_LEN
        tlv_end = self._TLV_INFO_HDR_LEN + total_len
        ret = []
        while (tlv_index + 2) < len(e) and tlv_index < tlv_end:
            rt = self.decoder(None, e[tlv_index:tlv_index + 2 + ord(e[tlv_index + 1])])
            ret.append(rt)
            if ord(e[tlv_index]) == self._TLV_CODE_CRC_32:
                break
            tlv_index += ord(e[tlv_index + 1]) + 2
        for item in ret:
            if item['code'] == self._TLV_CODE_VENDOR_EXT:
                rt = self.decoder(None, item["value"]
                             [0: 0 + 2 + ord(item["value"][0 + 1])])
                ret.append(rt)
        return ret

    def getcardid(self, eeprom):
        ret = self.decode_eeprom(eeprom)
        for item in ret:
            if item['code'] == self._TLV_CODE_RJ_CARID:
                return item.get('value',None)
        return None

    def getcardName(self,eeprom):
        ret = self.decode_eeprom(eeprom)
        for item in ret:
            if item['code'] == self._TLV_CODE_PRODUCT_NAME:
                return item.get('value',None)
        return None

    def decoder(self,s, t):
        if ord(t[0]) == self._TLV_CODE_PRODUCT_NAME:
            name = "Product Name"
            value = str(t[2:2 + ord(t[1])])
        elif ord(t[0]) == self._TLV_CODE_PART_NUMBER:
            name = "Part Number"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_SERIAL_NUMBER:
            name = "Serial Number"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_MAC_BASE:
            name = "Base MAC Address"
            value = ":".join([binascii.b2a_hex(T) for T in t[2:8]]).upper()
        elif ord(t[0]) == self._TLV_CODE_MANUF_DATE:
            name = "Manufacture Date"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_DEVICE_VERSION:
            name = "Device Version"
            value = str(ord(t[2]))
        elif ord(t[0]) == self._TLV_CODE_LABEL_REVISION:
            name = "Label Revision"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_PLATFORM_NAME:
            name = "Platform Name"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_ONIE_VERSION:
            name = "ONIE Version"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_MAC_SIZE:
            name = "MAC Addresses"
            value = str((ord(t[2]) << 8) | ord(t[3]))
        elif ord(t[0]) == self._TLV_CODE_MANUF_NAME:
            name = "Manufacturer"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_MANUF_COUNTRY:
            name = "Manufacture Country"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_VENDOR_NAME:
            name = "Vendor Name"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_DIAG_VERSION:
            name = "Diag Version"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_SERVICE_TAG:
            name = "Service Tag"
            value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_VENDOR_EXT:
            name = "Vendor Extension"
            value = ""
            if self._TLV_DISPLAY_VENDOR_EXT:
                value = t[2:2 + ord(t[1])]
        elif ord(t[0]) == self._TLV_CODE_CRC_32 and len(t) == 6:
            name = "CRC-32"
            value = "0x%08X" % (((ord(t[2]) << 24) | (
                ord(t[3]) << 16) | (ord(t[4]) << 8) | ord(t[5])),)
        elif ord(t[0]) == self._TLV_CODE_RJ_CARID:
            name = "rj_cardid"
            value = ""
            for c in t[2:2 + ord(t[1])]:
                value += "%02X" % (ord(c),)
        else:
            name = "Unknown"
            value = ""
            for c in t[2:2 + ord(t[1])]:
                value += "0x%02X " % (ord(c),)
        return {"name": name, "code": ord(t[0]), "value": value}

    def writeToEEprom(self,rst_arr , E2_LOC):
        index = 0
        for item in rst_arr:
            Osutil.rji2cset(E2_LOC["bus"], E2_LOC["devno"], index, ord(item))
            index += 1
        os.system("rmmod at24 ")
        os.system("modprobe at24 ")
        os.system("rm -f /var/cache/sonic/decode-syseeprom/syseeprom_cache")

class Osutil():
    SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
    HWSKU_KEY = "DEVICE_METADATA['localhost']['hwsku']"
    PLATFORM_KEY = "DEVICE_METADATA['localhost']['platform']"

    @staticmethod
    def writeToE2(bus, loc, rst_arr):
        index = 0
        for item in rst_arr:
            Osutil.rji2cset(bus, loc, index, ord(item))
            index += 1
    @staticmethod
    def strtoint(str):  # The hexadecimal string is converted to int, "4040"/"0x4040"/"0X4040" = 16448
        value = 0
        rest_v = str.replace("0X", "").replace("0x", "")
        for index in range(len(rest_v)):
            value |= int(rest_v[index], 16) << ((len(rest_v) - index - 1) * 4)
        return value
    # Compare strings regardless of size
    @staticmethod
    def astrcmp(str1,str2):
        return str1.lower()==str2.lower()
    @staticmethod
    def rj_os_system(cmd):
        status, output = subprocess.getstatusoutput(cmd)
        if status:
            log_error('Failed :%s msg:%s status:%s'%(cmd,output,status))
        return status, output
    @staticmethod
    def log_os_system(cmd, show,log_file=SYSLOG_IDENTIFIER):
        d_print ('         Run :'+ cmd)
        status, output = subprocess.getstatusoutput(cmd)
        d_print (" with result :" + str(status))
        d_print ("      output :" + output)
        if status:
            log_error('Failed :%s msg:%s status:%s'%(cmd,output,status),log_file)
            if show:
                print ('Failed :'+ cmd)
        return  status, output

    @staticmethod
    def rji2cset(bus, devno, address, byte):
        command_line = "i2cset -f -y %d 0x%02x 0x%02x 0x%02x" % (
            bus, devno, address, byte)
        retrytime = 6
        ret_t = ""
        for i in range(retrytime):
            ret, ret_t = Osutil.rj_os_system(command_line)
            if ret == 0:
                return True, ret_t
        log_error('command_line:%s ret :%d ret_t:%s'%(command_line,ret,ret_t))
        return False, ret_t

    @staticmethod
    def rji2cget(bus, devno, address, word=None):
        if word == None:
            command_line = "i2cget -f -y %d 0x%02x 0x%02x " % (bus, devno, address)
        else:
            command_line = "i2cget -f -y %d 0x%02x 0x%02x %s" % (bus, devno, address, word)
        retrytime = 6
        ret_t = ""
        for i in range(retrytime):
            ret, ret_t = Osutil.rj_os_system(command_line)
            if ret == 0:
                return True, ret_t
            time.sleep(0.1)
        log_error('command_line:%s ret :%d ret_t:%s'%(command_line,ret,ret_t))
        return False, ret_t
    @staticmethod
    def isValidMac(mac):
        if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$", mac):
            return True
        return False

    @staticmethod
    def seteth0mac(eth, mac):
        rulefile = "/etc/udev/rules.d/70-persistent-net.rules"
        if Osutil.isValidMac(mac) == False:
            return False, "MAC非法"

        # Temporarily change the local ETH0 to the value after setMAC
        ifconfigcmd = "ifconfig eth0 down"
        log_debug(ifconfigcmd,SYSLOG_IDENTIFIER)
        ret, status = Osutil.rj_os_system(ifconfigcmd)
        if ret:
            return False, "软件停用eth0出错"
        ifconfigcmd = "ifconfig eth0 hw ether %s" % mac
        log_debug(ifconfigcmd,SYSLOG_IDENTIFIER)
        ret, status = Osutil.rj_os_system(ifconfigcmd)
        if ret:
            return False, "软件设置网卡MAC出错"
        ifconfigcmd = "ifconfig eth0 up"
        log_debug(ifconfigcmd,SYSLOG_IDENTIFIER)
        ret, status = Osutil.rj_os_system(ifconfigcmd)
        if ret:
            return False, "软件启用eth0出错"
        if os.path.exists(rulefile):
            os.remove(rulefile)
        print ("MGMT MAC【%s】" % mac)
        return True, "success"

    @staticmethod
    def get_machine_info():
        if not os.path.isfile('/host/machine.conf'):
            return None
        machine_vars = {}
        with open('/host/machine.conf') as machine_file:
            for line in machine_file:
                tokens = line.split('=')
                if len(tokens) < 2:
                    continue
                machine_vars[tokens[0]] = tokens[1].strip()
        return machine_vars

    @staticmethod
    def get_platform_info(machine_info):
        if machine_info != None:
            if machine_info.__contains__('onie_platform'):
                return  machine_info['onie_platform']
            elif machine_info.__contains__('aboot_platform'):
                return machine_info['aboot_platform']
        return None

    @staticmethod
    def get_platform_and_hwsku():
        try:
            proc = subprocess.Popen([Osutil.SONIC_CFGGEN_PATH, '-H', '-v', Osutil.PLATFORM_KEY],
                                    stdout=subprocess.PIPE,
                                    shell=False,
                                    stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            platform = stdout.rstrip('\n')
    
            proc = subprocess.Popen([Osutil.SONIC_CFGGEN_PATH, '-d', '-v', Osutil.HWSKU_KEY],
                                    stdout=subprocess.PIPE,
                                    shell=False,
                                    stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            hwsku = stdout.rstrip('\n')
        except OSError, e:
            raise OSError("Cannot detect platform")

        return (platform, hwsku)

class DeviceMessage():
    _message = None

    def __init__(self, GLObalSelectBmc=True):
        if GLObalSelectBmc:
            # d_print("before BMCMessage init")
            self._message = BMCMessage()
        else:
            # d_print("before x86 init")
            self._message = x86Message()

    @property
    def message(self):
        return self._message

    def getFRUList(self):
        str = "bmc_get_e2_show_list"
        ret_info = BMCMessage().send_diag_cmd_t_bmc(str)
        return ret_info[0]

    def getSETFRUList(self):
        str1 = "bmc_get_e2_set_list"
        ret_info = BMCMessage().send_diag_cmd_t_bmc(str1)
        return ret_info[0]

    def getFRUeeprom(self, e2type, index):
        strtmp = "bmc_get_e2_bin -json \"%s\""
        param = {}
        param["e2type"] = e2type
        param["index"] = index
        paramtmp = strtmp % str(param)
        ret_info = BMCMessage().send_diag_cmd_t_bmc(paramtmp)
        ret_dict = eval(ret_info[0])
        if ret_dict.get("status") == "ok":
            return ret_dict.get('ret_info')
        else:
            return None

    def setFRUeeprom(self, e2type, index, bindata):
        strtmp  = "bmc_write_e2_bin -json \"%s\""
        param1 = []
        param = {}
        param["e2type"] = e2type
        param["index"] = index
        ret_t = base64.b64encode(bindata)
        param["bin"] = ret_t
        param1.append(param)
        paramtmp = strtmp % str(param1)
        ret_info = BMCMessage().send_diag_cmd_t_bmc(paramtmp)
        ret_dict = eval(ret_info[0])
        if ret_dict.get("status") == "ok":
            return True
        else:
            print (ret_dict.get("ret_info"))
            return False

    def getplatform(self):
        '''Obtain the sonic system platform information'''
        (platform, hwsku) = Osutil.get_platform_and_hwsku()
        return platform

    def settlve2(self, bin_data):
        '''set TLV E2'''
        return x86Message().tlve2set(bin_data)

    def getTLVe2(self):
        '''get TLV E2'''
        return x86Message().getTLVe2();

    def getTLVe2Dict(self):
        '''get TLV E2 dict'''
        ret = self.getTLVe2()
        ret_t = {}
        for item in ret:
            ret_t[item['code']] = item['value']
        return ret_t

    def resetTLVE2(self):
        return x86Message().resetTLVe2();

    def getfannum(self):
        return self.message.getFanNum()

    def getcardid(self):
        '''set TLV board crad ID'''
        return x86Message().getcardid();

    def getproductname(self, readtype):
        '''Read the product name  0 is read from configs，1 is read from tlv'''
        if readtype == 0:
            return x86Message().getproductname()
        elif readtype == 1:
            return x86Message().getTLVproductname()
        else:
            return None

    def getCPUeeprom(self):
        return x86Message().getCPUeeprom();

    def setCPUEEPROM(self,bindata):
        return x86Message().setCPUeeprom(bindata)

    def getFanNames(self):
        return self.message.getFanNames()

    def getFanName(self, index):
        return self.message.getFanName(index)

    def getFanStatus(self, name):
        return self.message.getFanStatus(name)
    
    def getFanFru(self, name):
        return self.message.getFanFru(name)
    
    def getFanAll(self):
        return self.message.getFansMsg()

    def getPsuNum(self):
        return self.message.getPsuNum()

    def getPsuValue(self, index):
        return self.message.getPsuValue(index)
    
    def getPsuPresence(self, index):
        return self.message.getPsuPresence(index)

    def getPsuStatus(self, index):
        return self.message.getPsuStatus(index)

    def getPsuAll(self):
        return self.message.getPsuMsg();

    def getfanList(self):
        return self.message.getfansList()

    def getSensorsNum(self):
        return self.message.getSensorsNum()

    def getSensorsName(self, index):
        return self.message.getSensorsName(index)

    def getSensorsinputNumByName(self, title):
        return self.message.getSensorsinputNumByName(title)

    def getSensorsInputNumsByIndex(self, index):
        return self.message.getSensorsInputNumsByIndex(index)

    def getSensorsInputNameByIndex(self, sensorindex, inputindex):
        return self.message.getSensorsInputNameByIndex(sensorindex, inputindex)

    def getSensorsInputValue(self, index, index2):
        return self.message.getSensorsInputValue(index, index2)

    def getsensorList(self):
        return self.message.getsensorList()

    def getsensorAll(self):
        return self.message.getsensorLists()

    def getSensorInputType(self, name):
        return self.message.getSensorInputType(name)
    
    def getRealUnitByType(self, name):
        return self.message.getRealUnitByType(name)
        
    def getDealValueByType(self, name, value):
        return self.message.getDealValueByType(name, value)

    def util_setmac(self,eth, mac):
        return Osutil.seteth0mac(eth, mac)

    def getDmiSysByType(self, type_t):
        ret, log = Osutil.rj_os_system("which dmidecode ")
        if ret != 0 or len(log) <= 0:
            error = "cmd find dmidecode"
            return False, error
        cmd = log + " -t %s" % type_t
        ret1, log1 = Osutil.rj_os_system(cmd)
        if ret != 0 or len(log1) <= 0:
            return False, "命令执行出错[%s]" % cmd
        its = log1.replace("\t", "").strip().split("\n")
        ret = {}
        for it in its:
            if ":" in it:
                key = it.split(":")[0].lstrip()
                value = it.split(":")[1].lstrip()
                ret[key] = value
        return True, ret

    pass
