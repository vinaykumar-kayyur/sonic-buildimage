#!/usr/bin/env python
import sys
import json
import re
import argparse
import subprocess
import glob
import os
from jsonschema import validate


cache={}
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'

dirname=os.path.dirname(os.path.realpath(__file__))




class PddfParse():
    def __init__(self):
        if not os.path.exists("/usr/share/sonic/platform"):
            self.platform, self.hwsku = self.get_platform_and_hwsku()
            os.symlink("/usr/share/sonic/device/"+self.platform, "/usr/share/sonic/platform")

        try:
            with open('/usr/share/sonic/platform/pddf/pddf-device.json') as f:
                  self.data = json.load(f)
        except IOError:
            #print "Error - required JSON file not found"
            if os.path.exists('/usr/share/sonic/platform'):
                os.unlink("/usr/share/sonic/platform")


        self.data_sysfs_obj={}
        self.sysfs_obj={}


    # Returns platform and HW SKU
    def get_platform_and_hwsku(self):
        try:
            proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-H', '-v', PLATFORM_KEY],
                                    stdout=subprocess.PIPE,
                                    shell=False,
                                    stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            platform = stdout.rstrip('\n')

            proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-d', '-v', HWSKU_KEY],
                                    stdout=subprocess.PIPE,
                                    shell=False,
                                    stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            hwsku = stdout.rstrip('\n')
        except OSError, e:
            raise OSError("Cannot detect platform")

        return (platform, hwsku)

    #################################################################################################################################
    #   GENERIC DEFS
    #################################################################################################################################
    def runcmd(self, cmd):
        #print cmd
        if os.system(cmd)!=0:
            print "%s -- command failed"%cmd
        return

    def get_dev_idx(self, dev, ops):
            parent=dev['dev_info']['virt_parent']
            pdev=self.data[parent]
            
            return pdev['dev_attr']['dev_idx']


    def get_path(self, target, attr):
        aa = target + attr

        if aa in cache:
            return cache[aa]

        op={ "cmd": "show_attr", "target":target, "attr":attr }
        #print self.data[target]
        str = self.dev_parse(self.data[target], op)
        #print "[test] str is %s" %str
        str = str.rstrip('\n')
        cache[aa]=str
        return str


    def get_device_type(self, key):
        return self.data[key]['dev_info']['device_type']

    def get_platform(self):
        return self.data['PLATFORM']

    def get_num_psu_fans(self, dev):
        if not dev in self.data.keys():
            return 0

        if not 'num_psu_fans' in self.data[dev]['dev_attr']:
            return 0
        
        return self.data[dev]['dev_attr']['num_psu_fans']

    #################################################################################################################################
    #   CREATE DEFS
    #################################################################################################################################
    def create_device(self, attr, path, ops):

            for key in attr.keys():
                    cmd="echo '%s' > /sys/kernel/%s/%s"%(attr[key], path, key)
                    self.runcmd(cmd)

    def create_psu_i2c_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PSU']:
            self.create_device(dev['i2c']['topo_info'], "pddf/devices/psu/i2c", ops)
            cmd= "echo '%s' > /sys/kernel/pddf/devices/psu/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            cmd= "echo '%s'  > /sys/kernel/pddf/devices/psu/i2c/psu_idx"%( self.get_dev_idx(dev, ops))
            self.runcmd(cmd)
            for attr in dev['i2c']['attr_list']:
                    self.create_device(attr, "pddf/devices/psu/i2c", ops)
                    cmd= "echo 'add' > /sys/kernel/pddf/devices/psu/i2c/attr_ops"
                    self.runcmd(cmd)
                    #print ""

            cmd = "echo 'add' > /sys/kernel/pddf/devices/psu/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd = "echo %s 0x%x > /sys/bus/i2c/devices/i2c-%d/new_device" % (dev['i2c']['topo_info']['dev_type'], int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"


        ##os.system("sleep 1")


    def create_psu_bmc_device(self, dev, ops):
            print ""


    def create_psu_device(self, dev, ops):
            #if 'i2c' in dev:
                    self.create_psu_i2c_device(dev, ops )
                    return

            #if 'bmc' in dev:
                    #self.create_psu_bmc_device(dev)
                    
    def create_fan_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['FAN']:
            self.create_device(dev['i2c']['topo_info'], "pddf/devices/fan/i2c", ops)
            cmd= "echo '%s' > /sys/kernel/pddf/devices/fan/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            self.create_device(dev['i2c']['dev_attr'], "pddf/devices/fan/i2c", ops)
            for attr in dev['i2c']['attr_list']:
                self.create_device(attr, "pddf/devices/fan/i2c", ops)
                cmd= "echo 'add' > /sys/kernel/pddf/devices/fan/i2c/attr_ops"
                self.runcmd(cmd)
                #print ""

            cmd= "echo 'add' > /sys/kernel/pddf/devices/fan/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd= "echo %s 0x%x > /sys/bus/i2c/devices/i2c-%d/new_device" % (dev['i2c']['topo_info']['dev_type'], int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"

        #os.system("sleep 1")

    def create_temp_sensor_device(self, dev, ops):
        # NO PDDF driver for temp_sensors device
        #if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['TEMP_SENSOR']:
            #create_device(dev['i2c']['topo_info'], "pddf/devices/fan/i2c", ops)
            #create_device(dev['i2c']['dev_attr'], "pddf/devices/fan/i2c", ops)
            #for attr in dev['i2c']['attr_list']:
                #create_device(attr, "pddf/devices/fan/i2c", ops)
                #print "echo 'add' > /sys/kernel/pddf/devices/fan/i2c/attr_ops\n"

            #print "echo 'add' > /sys/kernel/pddf/devices/fan/i2c/dev_ops\n"
        #else:
            cmd= "echo %s 0x%x > /sys/bus/i2c/devices/i2c-%d/new_device" % (dev['i2c']['topo_info']['dev_type'], int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"

            #os.system("sleep 1")


    def create_cpld_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['CPLD']:
            self.create_device(dev['i2c']['topo_info'], "pddf/devices/cpld", ops)
            cmd= "echo '%s' > /sys/kernel/pddf/devices/cpld/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            #create_device(dev['i2c']['dev_attr'], "pddf/devices/cpld", ops)
            # TODO: If attributes are provided then, use 'self.create_device' for them too
            cmd= "echo 'add' > /sys/kernel/pddf/devices/cpld/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd= "echo %s 0x%x > /sys/bus/i2c/devices/i2c-%d/new_device" % (dev['i2c']['topo_info']['dev_type'], int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"

        #os.system("sleep 1")


    def create_mux_device(self, dev, ops):
            self.create_device(dev['i2c']['topo_info'], "pddf/devices/mux", ops)
            cmd= "echo '%s' > /sys/kernel/pddf/devices/mux/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            self.create_device(dev['i2c']['dev_attr'], "pddf/devices/mux", ops)
            cmd= "echo 'add' > /sys/kernel/pddf/devices/mux/dev_ops"
            self.runcmd(cmd)
            #print "\n"
            #os.system("sleep 1")

    def create_xcvr_i2c_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PORT_MODULE']:
            self.create_device(dev['i2c']['topo_info'], "pddf/devices/xcvr/i2c", ops)
            cmd= "echo '%s' > /sys/kernel/pddf/devices/xcvr/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            #create_device(dev['i2c']['dev_attr'], "pddf/devices/psu/i2c")
            cmd="echo '%s'  > /sys/kernel/pddf/devices/xcvr/i2c/dev_idx"%( self.get_dev_idx(dev, ops))
            self.runcmd(cmd)
            for attr in dev['i2c']['attr_list']:
                self.create_device(attr, "pddf/devices/xcvr/i2c", ops)
                cmd="echo 'add' > /sys/kernel/pddf/devices/xcvr/i2c/attr_ops"
                self.runcmd(cmd)
                #print ""

            cmd="echo 'add' > /sys/kernel/pddf/devices/xcvr/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd="echo %s 0x%x > /sys/bus/i2c/devices/i2c-%d/new_device" % (dev['i2c']['topo_info']['dev_type'], int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"

        #os.system("sleep 1")

    def create_xcvr_bmc_device(self, dev, ops):
            print ""

    def create_xcvr_device(self, dev, ops):
            #if 'i2c' in dev:
            self.create_xcvr_i2c_device(dev, ops )
            return
            #if 'bmc' in dev:
            #self.create_psu_bmc_device(dev)

    def create_sysstatus_device(self, dev, ops):
        for attr in dev['attr_list']:
            self.create_device(attr, "pddf/devices/sysstatus", ops)
            cmd= "echo 'add' > /sys/kernel/pddf/devices/sysstatus/attr_ops"
            self.runcmd(cmd)
            #print "\n"

    def create_eeprom_device(self, dev, ops):
        if "EEPROM" in self.data['PLATFORM']['drivers'] and dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['EEPROM']:
            self.create_device(dev['i2c']['topo_info'], "pddf/devices/eeprom/i2c", ops)
            cmd= "echo '%s' > /sys/kernel/pddf/devices/eeprom/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            self.create_device(dev['i2c']['dev_attr'], "pddf/devices/eeprom/i2c", ops)
            cmd = "echo 'add' > /sys/kernel/pddf/devices/eeprom/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"

        else:
            cmd= "echo %s 0x%x > /sys/bus/i2c/devices/i2c-%d/new_device" % (dev['i2c']['topo_info']['dev_type'], int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"

        #os.system("sleep 1")

    #################################################################################################################################
    #   DELETE DEFS
    #################################################################################################################################
    def delete_eeprom_device(self, dev, ops):
        if "EEPROM" in self.data['PLATFORM']['drivers'] and dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['EEPROM']:
            cmd= "echo '%s' > /sys/kernel/pddf/devices/eeprom/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            cmd = "echo 'delete' > /sys/kernel/pddf/devices/eeprom/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd= "echo 0x%x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"
        #os.system("sleep 1")

    def delete_sysstatus_device(self, dev, ops):
        # NOT A PHYSICAL DEVICE.... rmmod on module would remove all the artifacts
        pass

        #for attr in dev['attr_list']:
            #cmd= "echo '%s' > /sys/kernel/pddf/devices/sysstatus/i2c_name"%(dev['dev_info']['device_name'])
            #self.runcmd(cmd)
            #cmd= "echo 'delete' > /sys/kernel/pddf/devices/sysstatus/attr_ops"
            #self.runcmd(cmd)

    def delete_xcvr_i2c_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PORT_MODULE']:
            cmd= "echo '%s' > /sys/kernel/pddf/devices/xcvr/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            cmd="echo 'delete' > /sys/kernel/pddf/devices/xcvr/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd="echo 0x%x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"
        #os.system("sleep 1")

    def delete_xcvr_device(self, dev, ops):
        self.delete_xcvr_i2c_device(dev, ops)
        return

    def delete_mux_device(self, dev, ops):
            cmd= "echo '%s' > /sys/kernel/pddf/devices/mux/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            cmd= "echo 'delete' > /sys/kernel/pddf/devices/mux/dev_ops"
            self.runcmd(cmd)
            #print "\n"
            #os.system("sleep 1")

    def delete_cpld_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['CPLD']:
            cmd= "echo '%s' > /sys/kernel/pddf/devices/cpld/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            cmd= "echo 'delete' > /sys/kernel/pddf/devices/cpld/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd= "echo 0x%x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"
        #os.system("sleep 1")

    def delete_temp_sensor_device(self, dev, ops):
        # NO PDDF driver for temp_sensors device
        #if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['TEMP_SENSOR']:
            #cmd= "echo '%s' > /sys/kernel/pddf/devices/temp_sensor/i2c/i2c_name"%(dev['dev_info']['device_name'])
            #self.runcmd(cmd)
            #cmd= "echo 'add' > /sys/kernel/pddf/devices/temp_sensor/i2c/dev_ops"
            #self.runcmd(cmd)
        #else:
            cmd= "echo 0x%x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"

            #os.system("sleep 1")

    def delete_fan_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['FAN']:
            cmd= "echo '%s' > /sys/kernel/pddf/devices/fan/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            cmd= "echo 'delete' > /sys/kernel/pddf/devices/fan/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd= "echo 0x%x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"
        #os.system("sleep 1")


    def delete_psu_i2c_device(self, dev, ops):
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PSU']:
            cmd= "echo '%s' > /sys/kernel/pddf/devices/psu/i2c/i2c_name"%(dev['dev_info']['device_name'])
            self.runcmd(cmd)
            cmd = "echo 'delete' > /sys/kernel/pddf/devices/psu/i2c/dev_ops"
            self.runcmd(cmd)
            #print "\n"
        else:
            cmd = "echo 0x%x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (int(dev['i2c']['topo_info']['dev_addr'], 0), int(dev['i2c']['topo_info']['parent_bus'], 0))
            self.runcmd(cmd)
            #print "\n"
        #os.system("sleep 1")

    def delete_psu_device(self, dev, ops):
            #if 'i2c' in dev:
            self.delete_psu_i2c_device(dev, ops )
            return


    #################################################################################################################################
    #   SHOW ATTRIBIUTES DEFS
    #################################################################################################################################
    def is_led_device_configured(self, device_name, index):
            for key in self.data.keys():
                    if key != 'PLATFORM':
                            dev_info=self.data[key]['dev_info']
                            if dev_info['device_type'] == 'LED':
                                    attr=self.data[key]['dev_attr']
                                    if((device_name==dev_info['device_name']) and (index==attr['index'])):
                                            return(True)

            return (False)

    def show_device_sysfs(self, dev, ops):
        parent=dev['dev_info']['device_parent']
        #print parent
        pdev=self.data[parent]
        if pdev['dev_info']['device_parent'] == 'SYSTEM':
            return "/sys/bus/i2c/devices/"+"i2c-%d"%int(pdev['i2c']['topo_info']['dev_addr'], 0)
        return self.show_device_sysfs(pdev, ops) + "/" + "i2c-%d" % int(dev['i2c']['topo_info']['parent_bus'], 0)


    # This is alid for 'at24' type of EEPROM devices. Only one attribtue 'eeprom' 
    def show_attr_eeprom_device(self, dev, ops):
        str = ""
        attr_name=ops['attr']
        attr_list=dev['i2c']['attr_list']
        KEY="eeprom"
        dsysfs_path=""

        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]

        for attr in attr_list:
            if attr_name == attr['attr_name'] or attr_name == 'all':
                #print self.show_device_sysfs(dev, ops)+"/%d-00%x" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))+"/%s"%attr['attr_name']
                if 'drv_attr_name' in attr.keys():
                    real_name = attr['drv_attr_name']
                else:
                    real_name = attr['attr_name']

                dsysfs_path = self.show_device_sysfs(dev, ops)+"/%d-00%x" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))+"/%s"%real_name
                if not dsysfs_path in self.data_sysfs_obj[KEY]:
                    self.data_sysfs_obj[KEY].append(dsysfs_path)
                str += dsysfs_path+"\n"
        return str


    def show_attr_mux_device(self, dev, ops):
        ret = ""
        KEY="mux"
        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]

        return ret

    def show_attr_psu_i2c_device(self, dev, ops):
        target=ops['target']
        attr_name=ops['attr']
        str = ""
        KEY="psu"
        dsysfs_path=""

        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]

        if target == 'all' or target == dev['dev_info']['virt_parent'] :
            attr_list=dev['i2c']['attr_list']
            for attr in attr_list:
                if attr_name == attr['attr_name'] or attr_name == 'all' :
                    #print self.show_device_sysfs(dev, ops)+"/%d-00%x" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))+"/%s"%attr['attr_name']
                    if 'drv_attr_name' in attr.keys():
                        real_name = attr['drv_attr_name']
                    else:
                        real_name = attr['attr_name']

                    dsysfs_path = self.show_device_sysfs(dev, ops)+"/%d-00%x" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))+"/%s"%real_name
                    if not dsysfs_path in self.data_sysfs_obj[KEY]:
                        self.data_sysfs_obj[KEY].append(dsysfs_path)
                    str += dsysfs_path+"\n"
        return str


    def show_attr_psu_device(self, dev, ops):
        return self.show_attr_psu_i2c_device(dev, ops )


    def show_attr_fan_device(self, dev, ops):
        str = ""
        attr_name=ops['attr']
        attr_list=dev['i2c']['attr_list']
        KEY="fan"
        dsysfs_path=""

        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]


        for attr in attr_list:
            if attr_name == attr['attr_name'] or attr_name == 'all':
                #print self.show_device_sysfs(dev, ops)+"/%d-00%x" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))+"/%s"%attr['attr_name']
                if 'drv_attr_name' in attr.keys():
                    real_name = attr['drv_attr_name']
                else:
                    real_name = attr['attr_name']

                dsysfs_path= self.show_device_sysfs(dev, ops)+"/%d-00%x" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))+"/%s"%real_name
                if not dsysfs_path in self.data_sysfs_obj[KEY]:
                    self.data_sysfs_obj[KEY].append(dsysfs_path)
                str += dsysfs_path+"\n"
        return str

    # This is only valid for LM75
    def show_attr_temp_sensor_device(self, dev, ops):
        str = ""
        attr_name=ops['attr']
        attr_list=dev['i2c']['attr_list']
        KEY="temp-sensors"
        dsysfs_path=""

        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]


        for attr in attr_list:
            if attr_name == attr['attr_name'] or attr_name == 'all':
                path = self.show_device_sysfs(dev, ops)+"/%d-00%x/" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))
                #print  glob.glob(path+'hwmon/hwmon*/'+attr['attr_name'])
                if 'drv_attr_name' in attr.keys():
                    real_name = attr['drv_attr_name']
                else:
                    real_name = attr['attr_name']

                if (os.path.exists(path)):
                    full_path = glob.glob(path + 'hwmon/hwmon*/' + real_name)[0]
                    #full_path = path + 'hwmon/hwmon/' + attr['attr_name']
                    dsysfs_path=full_path
                    if not dsysfs_path in self.data_sysfs_obj[KEY]:
                        self.data_sysfs_obj[KEY].append(dsysfs_path)
                    str += full_path + "\n"
        return str

    def show_attr_sysstatus_device(self, dev, ops):
        ret = ""
        attr_name=ops['attr']
        attr_list=dev['attr_list']
        KEY="sys-status"
        dsysfs_path=""

        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]


        for attr in attr_list:
           if attr_name == attr['attr_name'] or attr_name == 'all':
              dsysfs_path = "/sys/kernel/pddf/devices/sysstatus/sysstatus_data/" + attr['attr_name']
              if not dsysfs_path in self.data_sysfs_obj[KEY]:
                  self.data_sysfs_obj[KEY].append(dsysfs_path)
              #print path
              ret += dsysfs_path+"\n"
        return ret


    def show_attr_xcvr_i2c_device(self, dev, ops):
        target=ops['target']
        attr_name=ops['attr']
        str = ""
        dsysfs_path = ""
        KEY="xcvr"
        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]

        if target == 'all' or target == dev['dev_info']['virt_parent'] :
            attr_list=dev['i2c']['attr_list']
            for attr in attr_list:
                if attr_name == attr['attr_name'] or attr_name == 'all' :
                    if 'drv_attr_name' in attr.keys():
                        real_name = attr['drv_attr_name']
                    else:
                        real_name = attr['attr_name']

                    dsysfs_path = self.show_device_sysfs(dev, ops)+"/%d-00%x" %(int(dev['i2c']['topo_info']['parent_bus'], 0), int(dev['i2c']['topo_info']['dev_addr'], 0))+"/%s"%real_name
                    if not dsysfs_path in self.data_sysfs_obj[KEY]:
                        self.data_sysfs_obj[KEY].append(dsysfs_path)
                    str += dsysfs_path+"\n"
        return str


    def show_attr_xcvr_device(self, dev, ops):
        return self.show_attr_xcvr_i2c_device(dev, ops )

    def show_attr_cpld_device(self, dev, ops):
        ret = ""
        KEY="cpld"
        if not KEY in self.data_sysfs_obj:
            self.data_sysfs_obj[KEY]=[]

        return ret


    #################################################################################################################################
    #   SHOW DEFS
    #################################################################################################################################
    def check_led_cmds(self, key, ops):
            name = ops['target']+'_LED'
            if (ops['target']=='config' or ops['attr']=='all') or (name==self.data[key]['dev_info']['device_name'] and ops['attr']==self.data[key]['dev_attr']['index']):
                return (True)
            else:
                return (False)

    def dump_sysfs_obj(self, obj, key_type):
            if (key_type == 'keys'):
                for key in obj.keys():	
                    print key
                return

            for key in obj:
                if (key == key_type or key_type == 'all'):
                    print key+":"
                    for entry in obj[key]:
                        print "\t"+entry

    def add_list_sysfs_obj(self, obj, KEY, list):
        for sysfs in list:
            if not sysfs in obj[KEY]:
                obj[KEY].append(sysfs)

    def sysfs_attr(self, key, value, path, obj, obj_key):
            sysfs_path="/sys/kernel/%s/%s"%(path, key)
            if not sysfs_path in obj[obj_key]:
                    obj[obj_key].append(sysfs_path)


    def sysfs_device(self, attr, path, obj, obj_key):
            for key in attr.keys():
                    sysfs_path="/sys/kernel/%s/%s"%(path, key)
                    if not sysfs_path in obj[obj_key]:
                            obj[obj_key].append(sysfs_path)

    def show_eeprom_device(self, dev, ops):
            return


    def show_mux_device(self, dev, ops):
            KEY ='mux'
            if not KEY in self.sysfs_obj:
                    self.sysfs_obj[KEY] = []
                    self.sysfs_device(dev['i2c']['topo_info'], "pddf/devices/mux", self.sysfs_obj, KEY)
                    self.sysfs_device(dev['i2c']['dev_attr'], "pddf/devices/mux", self.sysfs_obj, KEY)
                    sysfs_path= "/sys/kernel/pddf/devices/mux/dev_ops"
                    if not sysfs_path in self.sysfs_obj[KEY]:
                            self.sysfs_obj[KEY].append(sysfs_path)
                    list=['/sys/kernel/pddf/devices/mux/i2c_type',
                          '/sys/kernel/pddf/devices/mux/i2c_name',
                          '/sys/kernel/pddf/devices/mux/error']
                    self.add_list_sysfs_obj(self.sysfs_obj, KEY, list)


    def show_psu_i2c_device(self, dev, ops):
        KEY ='psu'
        path='pddf/devices/psu/i2c'
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PSU']:
            if not KEY in self.sysfs_obj:
                    self.sysfs_obj[KEY] = []
                    self.sysfs_device(dev['i2c']['topo_info'], path, self.sysfs_obj, KEY)
                    sysfs_path = "/sys/kernel/pddf/devices/psu/i2c/psu_idx"
                    self.sysfs_obj[KEY].append(sysfs_path)

                    for attr in dev['i2c']['attr_list']:
                            self.sysfs_device(attr, "pddf/devices/psu/i2c", self.sysfs_obj, KEY)
                            sysfs_path = "/sys/kernel/pddf/devices/psu/i2c/dev_ops"
                            if not sysfs_path in self.sysfs_obj[KEY]:
                                    self.sysfs_obj[KEY].append(sysfs_path)
                    list=['/sys/kernel/pddf/devices/psu/i2c/i2c_type',
                          '/sys/kernel/pddf/devices/fan/i2c/i2c_name',
                          '/sys/kernel/pddf/devices/psu/i2c/error',
                          '/sys/kernel/pddf/devices/psu/i2c/attr_ops']
                    self.add_list_sysfs_obj(self.sysfs_obj, KEY, list)


    def show_psu_device(self, dev, ops):
            self.show_psu_i2c_device(dev, ops )
            return

    def show_client_device(self):
        KEY ='client'
        if not KEY in self.sysfs_obj:
               self.sysfs_obj[KEY] = []
               list=['/sys/kernel/pddf/devices/showall']
               self.add_list_sysfs_obj(self.sysfs_obj, KEY, list)


    def show_fan_device(self, dev, ops):
        KEY ='fan'
        path='pddf/devices/fan/i2c'
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['FAN']:
            if not KEY in self.sysfs_obj:
                    self.sysfs_obj[KEY] = []

                    self.sysfs_device(dev['i2c']['topo_info'], path, self.sysfs_obj, KEY)
                    self.sysfs_device(dev['i2c']['dev_attr'], path, self.sysfs_obj, KEY)
                    for attr in dev['i2c']['attr_list']:
                            self.sysfs_device(attr, path, self.sysfs_obj, KEY)
                    list=['/sys/kernel/pddf/devices/fan/i2c/i2c_type',
                          '/sys/kernel/pddf/devices/fan/i2c/i2c_name',
                          '/sys/kernel/pddf/devices/fan/i2c/error',
                          '/sys/kernel/pddf/devices/fan/i2c/attr_ops',
                          '/sys/kernel/pddf/devices/fan/i2c/dev_ops']
                    self.add_list_sysfs_obj(self.sysfs_obj, KEY, list)


    def show_temp_sensor_device(self, dev, ops):
            #path= "/sys/bus/i2c/devices/i2c-%d/new_device\n" % (int(dev['i2c']['topo_info']['parent_bus'], 0))
            #print "temp: "+ path
            return

    def show_sysstatus_device(self, dev, ops):
        KEY ='sysstatus'
        if not KEY in self.sysfs_obj:
            self.sysfs_obj[KEY] = []
            for attr in dev['attr_list']:
                    self.sysfs_device(attr, "pddf/devices/sysstatus", self.sysfs_obj, KEY)
                    sysfs_path= "/sys/kernel/pddf/devices/sysstatus/attr_ops"
                    if not sysfs_path in self.sysfs_obj[KEY]:
                            self.sysfs_obj[KEY].append(sysfs_path)


    def show_xcvr_i2c_device(self, dev, ops):
        KEY ='xcvr'
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PORT_MODULE']:
            if not KEY in self.sysfs_obj:
                    self.sysfs_obj[KEY] = []
                    self.sysfs_device(dev['i2c']['topo_info'], "pddf/devices/xcvr/i2c", self.sysfs_obj, KEY)

                    for attr in dev['i2c']['attr_list']:
                            self.sysfs_device(attr, "pddf/devices/xcvr/i2c", self.sysfs_obj, KEY)
                            sysfs_path = "/sys/kernel/pddf/devices/xcvr/i2c/dev_ops"
                            if not sysfs_path in self.sysfs_obj[KEY]:
                                    self.sysfs_obj[KEY].append(sysfs_path)
                    list=['/sys/kernel/pddf/devices/xcvr/i2c/i2c_type',
                          '/sys/kernel/pddf/devices/xcvr/i2c/i2c_name',
                          '/sys/kernel/pddf/devices/xcvr/i2c/error',
                          '/sys/kernel/pddf/devices/xcvr/i2c/attr_ops']
                    self.add_list_sysfs_obj(self.sysfs_obj, KEY, list)


    def show_xcvr_device(self, dev, ops):
            self.show_xcvr_i2c_device(dev, ops )
            return

    def show_cpld_device(self, dev, ops):
        KEY ='cpld'
        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['CPLD']:
            if not KEY in self.sysfs_obj:
                    self.sysfs_obj[KEY] = []
                    self.sysfs_device(dev['i2c']['topo_info'], "pddf/devices/cpld", self.sysfs_obj, KEY)
                    sysfs_path= "/sys/kernel/pddf/devices/cpld/dev_ops"
                    if not sysfs_path in self.sysfs_obj[KEY]:
                            self.sysfs_obj[KEY].append(sysfs_path)
                    list=['/sys/kernel/pddf/devices/cpld/i2c_type',
                          '/sys/kernel/pddf/devices/cpld/i2c_name',
                          '/sys/kernel/pddf/devices/cpld/error']
                    self.add_list_sysfs_obj(self.sysfs_obj, KEY, list)

    def show_led_platform_device(self, key, ops):
            if ops['attr']=='all' or ops['attr']=='PLATFORM':
                    KEY='platform'
                    if not KEY in self.sysfs_obj:
                            self.sysfs_obj[KEY] = []
                            path='pddf/devices/platform'
                            self.sysfs_attr('num_psus', self.data['PLATFORM']['num_psus'], path, self.sysfs_obj, KEY)
                            self.sysfs_attr('num_fans', self.data['PLATFORM']['num_fans'], path, self.sysfs_obj, KEY)

    def show_led_device(self, key, ops):
            if self.check_led_cmds(key, ops):
                    KEY='led'
                    if not KEY in self.sysfs_obj:
                            self.sysfs_obj[KEY] = []
                            path="pddf/devices/led"
                            for attr in self.data[key]['i2c']['attr_list']:
                                    self.sysfs_attr('device_name', self.data[key]['dev_info']['device_name'], path, self.sysfs_obj, KEY)
                                    self.sysfs_attr('swpld_addr', self.data[key]['dev_info']['device_name'], path, self.sysfs_obj, KEY)
                                    self.sysfs_attr('swpld_addr_offset', self.data[key]['dev_info']['device_name'], path, self.sysfs_obj, KEY)
                                    self.sysfs_device(self.data[key]['dev_attr'], path, self.sysfs_obj, KEY)
                                    for attr_key in attr.keys():
                                            attr_path="pddf/devices/led/" + attr['attr_name']
                                            if (attr_key != 'attr_name' and attr_key != 'swpld_addr' and attr_key != 'swpld_addr_offset'):
                                                    self.sysfs_attr(attr_key, attr[attr_key], attr_path, self.sysfs_obj, KEY)
                            sysfs_path="/sys/kernel/pddf/devices/led/dev_ops"
                            if not sysfs_path in self.sysfs_obj[KEY]:
                                    self.sysfs_obj[KEY].append(sysfs_path)
                            list=['/sys/kernel/pddf/devices/led/cur_state/color',
                                    '/sys/kernel/pddf/devices/led/cur_state/color_state']
                            self.add_list_sysfs_obj(self.sysfs_obj, KEY, list)


    def validate_xcvr_device(self, dev, ops):
        devtype_list = ['optoe1', 'optoe2']
        dev_addr_list = ['0x50', '0x51', '0x53']
        dev_attribs = ['xcvr_present', 'xcvr_reset', 'xcvr_intr_status', 'xcvr_lpmode']
        ret_val = "xcvr validation failed"

        if dev['i2c']['topo_info']['dev_type'] in devtype_list:
            for attr in dev['i2c']['attr_list']:
                if 'attr_name' in attr.keys() and 'eeprom' in attr.values():
                    ret_val = "xcvr validation success"
                else:
                    print "xcvr validation Failed"
                    return

        elif dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PORT_MODULE']:
            for attr in dev['i2c']['attr_list']:
                #if 'attr_name' in attr.keys() and 'xcvr_present' in attr.values():
                if attr.get("attr_name") in dev_attribs:
                    ret_val = "Success"
                else:
                    print "xcvr validation Failed"
                    return
        print ret_val

    def validate_eeprom_device(self, dev, ops):
        devtype_list = ['24c02']
        dev_access_mode = ['BLOCK', 'BYTE']
        dev_attribs = ['eeprom']
        ret_val = "eeprom failed"

        if dev['i2c']['topo_info']['dev_type'] in devtype_list:
            if dev['i2c']['dev_attr']['access_mode'] in dev_access_mode:
                for attr in dev['i2c']['attr_list']:
                    if attr.get("attr_name") in dev_attribs:
                        ret_val = "eeprom success"
        print ret_val

    def validate_mux_device(self, dev, ops):
        devtype_list = ['pca9548', 'pca954x']
        dev_channels = ["0", "1", "2", "3", "4", "5", "6", "7"]
        ret_val = "mux failed"

        if dev['i2c']['topo_info']['dev_type'] in devtype_list:
            for attr in dev['i2c']['channel']:
                if attr.get("chn") in dev_channels:
                    ret_val = "Mux success"
        print ret_val

    def validate_cpld_device(self, dev, ops):
        devtype_list = ['i2c_cpld']
        ret_val = "cpld failed"

        if dev['i2c']['topo_info']['dev_type'] in devtype_list:
            ret_val = "cpld success"
        print ret_val


    def validate_sysstatus_device(self, dev, ops):
        dev_attribs = ['board_info', 'cpld1_version', 'power_module_status', 'system_reset5',
                        'system_reset6', 'system_reset7', 'misc1', 'cpld2_version', 'cpld3_version'
                    ]
        ret_val = "sysstatus failed"

        if dev['dev_info']['device_type'] == "SYSSTAT":
                for attr in dev['attr_list']:
                    if attr.get("attr_name") in dev_attribs:
                        ret_val = "sysstatus success"
        print ret_val

    def validate_temp_sensor_device(self, dev, ops):
        devtype_list = ['lm75']
        dev_attribs = ['temp1_max', 'temp1_max_hyst', 'temp1_input']
        ret_val = "temp sensor failed"

        if dev['dev_info']['device_type'] == "TEMP_SENSOR":
            if dev['i2c']['topo_info']['dev_type'] in devtype_list:
                for attr in dev['i2c']['attr_list']:
                    if attr.get("attr_name") in dev_attribs:
                        ret_val = "tempsensor success"
        print ret_val

    def validate_fan_device(self, dev, ops):
        devtype_list = ['fan_ctrl']
        dev_attribs = ['none']
        ret_val = "fan failed"

        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['FAN']:
            if dev['i2c']['dev_attr']['num_fan'] is not None:
                numfans = dev['i2c']['dev_attr']['num_fan']
                #for fn in range(0, numfans):
                #    cmd = "fan"+fn+"_present"
                #    if attr.get("attr_name") == cmd:
                ret_val = "fan success"

        print ret_val

    def validate_psu_device(self, dev, ops):
        devtype_list = ['psu_pmbus']
        dev_attribs = ['psu_present', 'psu_model_name', 'psu_power_good', 'psu_mfr_id', 'psu_serial_num',
                        'psu_fan_dir', 'psu_v_out', 'psu_i_out', 'psu_p_out', 'psu_fan1_speed_rpm'
                      ]
        ret_val = "psu failed"

        if dev['i2c']['topo_info']['dev_type'] in self.data['PLATFORM']['drivers']['PSU']:
            for attr in dev['i2c']['attr_list']:
                if attr.get("attr_name") in dev_attribs:
                    if attr.get("attr_devaddr") is not None:
                        if attr.get("attr_offset") is not None:
                            if attr.get("attr_mask") is not None:
                                if attr.get("attr_len") is not None:
                                        ret_val = "psu success"
                else:
                    ret_val = "psu failed"

        print ret_val

    #################################################################################################################################
    #  SPYTEST 
    #################################################################################################################################
    def verify_attr(self, key, attr, path):
            node="/sys/kernel/%s/%s"%(path, key)
            try:
                    with open(node, 'r') as f:
                            status = f.read()
            except IOError:
                    print "PDDF_VERIFY_ERR: IOError: node:%s key:%s"%(node, key)
                    return

            status=status.rstrip("\n\r")
            if attr[key]!=status:
                    print "PDDF_VERIFY_ERR: node: %s switch:%s"%(node, status)

    def verify_device(self, attr, path, ops):
            for key in attr.keys():
                    self.verify_attr(key, attr, path)


    def get_led_device(self, device_name):
        self.create_attr('device_name', self.data[device_name]['dev_info']['device_name'], "pddf/devices/led")
        self.create_attr('index', self.data[device_name]['dev_attr']['index'], "pddf/devices/led")
        cmd="echo 'verify'  > /sys/kernel/pddf/devices/led/dev_ops"
        self.runcmd(cmd)
        #print "\n"

    def validate_sysfs_creation(self, obj, validate_type):
            dir = '/sys/kernel/pddf/devices/'+validate_type
            if (os.path.exists(dir) or validate_type=='client'):
                for sysfs in obj[validate_type]:
                    if(not os.path.exists(sysfs)):
                        print "[SYSFS FILE] " + sysfs + ": does not exist"
            else:
                print "[SYSFS DIR] " + dir + ": does not exist"

    def validate_dsysfs_creation(self, obj, validate_type):
        # There is a possibility that some components dont have any device-self.data attr
        if not obj[validate_type]:
            print "[SYSFS ATTR] for " + validate_type  + ": does not exist"
        else:
            for sysfs in obj[validate_type]:
                if(not os.path.exists(sysfs)):
                    print "[SYSFS FILE] " + sysfs + ": does not exist"

    def verify_sysfs_data(self, verify_type):
            if (verify_type=='LED'):
                    for key in self.data.keys():
                            if key != 'PLATFORM':
                                    attr=self.data[key]['dev_info']
                                    if attr['device_type'] == 'LED':
                                            self.get_led_device(key)
                                            self.verify_attr('device_name', self.data[key]['dev_info'], "pddf/devices/led")
                                            self.verify_attr('index', self.data[key]['dev_attr'], "pddf/devices/led")
                                            for attr in self.data[key]['i2c']['attr_list']:
                                                    path="pddf/devices/led/" + attr['attr_name']
                                                    for entry in attr.keys():
                                                            if (entry != 'attr_name' and entry != 'swpld_addr' and entry != 'swpld_addr_offset'):
                                                                    self.verify_attr(entry, attr, path)
                                                            if ( entry == 'swpld_addr' or entry == 'swpld_addr_offset'):
                                                                    self.verify_attr(entry, attr, 'pddf/devices/led')


    def schema_validation(self, validate_type):
            for key in self.data.keys():
                    if (key != 'PLATFORM'):
                            temp_obj={}
                            schema_file=""
                            device_type=self.data[key]["dev_info"]["device_type"]
                            if (validate_type=='all' or validate_type==device_type):
                                    temp_obj[device_type]=self.data[key]
                                    schema_file="schema/"+device_type + ".schema"
                                    if (os.path.exists(schema_file)):
                                            #print "Validate " + key + " Schema: " + device_type
                                            json_data=json.dumps(temp_obj)
                                            with open(schema_file, 'r') as f:
                                                    schema=json.load(f)
                                            validate(temp_obj, schema)

    #################################################################################################################################
    #   PARSE DEFS
    #################################################################################################################################
    def psu_parse(self, dev, ops):
            str=""
            ret=""
            for ifce in dev['i2c']['interface']:
                ret=getattr(self, ops['cmd']+"_psu_device")(self.data[ifce['dev']], ops )
                if not ret is None:
                    str+=ret
            return str

    def fan_parse(self, dev, ops):
            str=""
            str=getattr(self, ops['cmd']+"_fan_device")(dev, ops )
            #print "psu_parse -- %s"%str
            return str

    def temp_sensor_parse(self, dev, ops):
            str=""
            str=getattr(self, ops['cmd']+"_temp_sensor_device")(dev, ops )
            #print "temp_sensor_parse -- %s"%str
            return str

    def cpld_parse(self, dev, ops):
        ret = ""
        ret = getattr(self, ops['cmd']+"_cpld_device")(dev, ops)
        return ret




    def sysstatus_parse(self, dev,ops):
        ret = ""
        ret = getattr(self, ops['cmd']+"_sysstatus_device")(dev, ops)
        return ret 


    def mux_parse(self, dev, ops):
            str = ""
            ret = getattr(self, ops['cmd']+"_mux_device")(dev, ops)
            if not ret is None:
                str += ret

            for ch in dev['i2c']['channel']:
                ret = self.dev_parse(self.data[ch['dev']], ops)	
                if not ret is None:
                    str += ret
            return str

    def mux_parse_reverse(self, dev, ops):
            str = ""
            for ch in reversed(dev['i2c']['channel']):
                ret = self.dev_parse(self.data[ch['dev']], ops)	
                if not ret is None:
                    str += ret

            ret = getattr(self, ops['cmd']+"_mux_device")(dev, ops)
            if not ret is None:
                str += ret

            return str


    def eeprom_parse(self, dev, ops):
        str = ""
        str = getattr(self, ops['cmd']+"_eeprom_device")(dev, ops)
        return str

    def optic_parse(self, dev, ops):
            str=""
            ret=""
            for ifce in dev['i2c']['interface']:
                ret=getattr(self, ops['cmd']+"_xcvr_device")(self.data[ifce['dev']], ops )
                if not ret is None:
                    str+=ret
            return str

    def cpu_parse(self, bus, ops):
        str = ""
        for dev in bus['i2c']['CONTROLLERS']:
            dev1 = self.data[dev['dev']]
            for d in dev1['i2c']['DEVICES']:
                ret=self.dev_parse(self.data[d['dev']], ops)
                if not ret is None:
                    str += ret
        return str

    def cpu_parse_reverse(self, bus, ops):
        str = ""
        for dev in reversed(bus['i2c']['CONTROLLERS']):
            dev1 = self.data[dev['dev']]
            for d in dev1['i2c']['DEVICES']:
                ret=self.dev_parse(self.data[d['dev']], ops)
                if not ret is None:
                    str += ret
        return str


    def dev_parse(self, dev, ops):
            attr=dev['dev_info']
            if attr['device_type'] == 'CPU':
                if ops['cmd']=='delete':
                    return self.cpu_parse_reverse(dev, ops)
                else:
                    return self.cpu_parse(dev, ops)
        
            if attr['device_type'] == 'EEPROM':
                return self.eeprom_parse(dev, ops)

            if attr['device_type'] == 'MUX':
                if ops['cmd']=='delete':
                    return self.mux_parse_reverse(dev, ops)
                else:
                    return self.mux_parse(dev, ops)

            if attr['device_type'] == 'PSU':
                    return self.psu_parse(dev, ops)

            if attr['device_type'] == 'FAN':
                    return self.fan_parse(dev, ops)

            if attr['device_type'] == 'TEMP_SENSOR':
                    return self.temp_sensor_parse(dev, ops)

            if attr['device_type'] == 'SFP' or attr['device_type'] == 'QSFP':
                    return self.optic_parse(dev, ops)

            if attr['device_type'] == 'CPLD':
                    return self.cpld_parse(dev, ops)

            if attr['device_type'] == 'SYSSTAT':
                    return self.sysstatus_parse(dev,ops)

    def create_attr(self, key, value, path):
            cmd = "echo '%s' > /sys/kernel/%s/%s"%(value,  path, key)
            self.runcmd(cmd)

    def create_led_platform_device(self, key, ops):
            if ops['attr']=='all' or ops['attr']=='PLATFORM':
                    path='pddf/devices/platform'
                    self.create_attr('num_psus', self.data['PLATFORM']['num_psus'], path)
                    self.create_attr('num_fans', self.data['PLATFORM']['num_fans'], path)

    def create_led_device(self, key, ops):
            if ops['attr']=='all' or ops['attr']==self.data[key]['dev_info']['device_name']:
                    path="pddf/devices/led"
                    ops_state=""
                    for attr in self.data[key]['i2c']['attr_list']:
                            self.create_attr('device_name', self.data[key]['dev_info']['device_name'], path)
                            self.create_device(self.data[key]['dev_attr'], path, ops)
                            for attr_key in attr.keys():
                                    if (attr_key == 'swpld_addr_offset' or attr_key == 'swpld_addr'):
                                            self.create_attr(attr_key, attr[attr_key], path)
                                    elif (attr_key != 'attr_name'):
                                            state_path=path+'/'+attr['attr_name']
                                            self.create_attr(attr_key, attr[attr_key],state_path)
                            cmd="echo '" + ops['cmd'] + '_' + attr['attr_name']+"' > /sys/kernel/pddf/devices/led/dev_ops"
                            self.runcmd(cmd)
                            #print "\n"



    def led_parse(self, ops):
            #print "led_parse cmd: " + ops['cmd']
            getattr(self, ops['cmd']+"_led_platform_device")("PLATFORM", ops)
            for key in self.data.keys():
                    if key != 'PLATFORM':
                            attr=self.data[key]['dev_info']
                            if attr['device_type'] == 'LED':
                                    getattr(self, ops['cmd']+"_led_device")(key, ops)


    def get_device_list(self, list, type):
            for key in self.data.keys():
                    if key != 'PLATFORM':
                            attr=self.data[key]['dev_info']
                            if attr['device_type'] == type:
                                    list.append(self.data[key])


    def create_pddf_devices(self):
        self.dev_parse(self.data['SYSTEM'], { "cmd": "create", "target":"all", "attr":"all" } )
        self.dev_parse(self.data['SYSSTATUS'], { "cmd": "create", "target":"all", "attr":"all" } )
        self.led_parse({ "cmd": "create", "target":"all", "attr":"all" })
        
    def delete_pddf_devices(self):
        self.dev_parse(self.data['SYSTEM'], { "cmd": "delete", "target":"all", "attr":"all" } )
        self.dev_parse(self.data['SYSSTATUS'], { "cmd": "delete", "target":"all", "attr":"all" } )

    def populate_pddf_sysfsobj(self):
        self.dev_parse(self.data['SYSTEM'], { "cmd": "show", "target":"all", "attr":"all" } )
        self.dev_parse(self.data['SYSSTATUS'], { "cmd": "show", "target":"all", "attr":"all" } )
        self.led_parse({ "cmd": "show", "target":"all", "attr":"all" })
        self.show_client_device()

    def cli_dump_dsysfs(self, component):
        self.dev_parse(self.data['SYSTEM'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
        self.dev_parse(self.data['SYSSTATUS'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
        return self.data_sysfs_obj[component]


    def validate_pddf_devices(self, *args):
        self.populate_pddf_sysfsobj() 
        alist = [item for item in args]
        devtype = alist[0]
        v_ops = { 'cmd': 'validate', 'target':'all', 'attr':'all' }
        #dev_parse(self.data, self.data[devtype], v_ops )
        self.dev_parse(self.data['SYSTEM'], v_ops )














def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action='store_true', help="create the I2C topology")
    parser.add_argument("--sysfs", action='store', nargs="+",  help="show access-attributes sysfs for the I2C topology")
    parser.add_argument("--dsysfs", action='store', nargs="+",  help="show data-attributes sysfs for the I2C topology")
    parser.add_argument("--delete", action='store_true', help="Remove all the created I2C clients from topology")
    parser.add_argument("--validate", action='store', help="Validate the device specific attribute data elements")
    parser.add_argument("--schema", action='store', nargs="+",  help="Schema Validation")
    args = parser.parse_args()
    #print args
    pddf_obj = PddfParse()

    str = ""
    if args.create:
        pddf_obj.create_pddf_devices()

    if args.sysfs:
        if args.sysfs[0] == 'all':
		pddf_obj.populate_pddf_sysfsobj()
        if args.sysfs[0] == 'print':
		pddf_obj.populate_pddf_sysfsobj()
		pddf_obj.dump_sysfs_obj(pddf_obj.sysfs_obj, args.sysfs[1])
        if args.sysfs[0] == 'validate':
		pddf_obj.populate_pddf_sysfsobj()
		pddf_obj.validate_sysfs_creation(pddf_obj.sysfs_obj, args.sysfs[1])
        if args.sysfs[0] == 'verify':
		pddf_obj.verify_sysfs_data(args.sysfs[1])


    if args.dsysfs:
	if args.dsysfs[0] == 'validate':
            pddf_obj.dev_parse(pddf_obj.data['SYSTEM'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
            pddf_obj.dev_parse(pddf_obj.data['SYSSTATUS'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
            pddf_obj.validate_dsysfs_creation(pddf_obj.data_sysfs_obj, args.dsysfs[1])

        elif args.dsysfs[0] == 'print':
            pddf_obj.dev_parse(pddf_obj.data['SYSTEM'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
            pddf_obj.dev_parse(pddf_obj.data['SYSSTATUS'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
            pddf_obj.dump_sysfs_obj(pddf_obj.data_sysfs_obj, args.dsysfs[1])

        elif args.dsysfs[0] == 'all':
            ret = pddf_obj.dev_parse(pddf_obj.data['SYSTEM'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
            ret += pddf_obj.dev_parse(pddf_obj.data['SYSSTATUS'], { "cmd": "show_attr", "target":"all", "attr":"all" } )
            pddf_obj.dump_sysfs_obj(pddf_obj.data_sysfs_obj, 'all')
            #if not ret is None:
                #ret = ret.rstrip('\n')
                #print ret
        else:
            ret = pddf_obj.dev_parse(pddf_obj.data[args.dsysfs[0]], { "cmd": "show_attr", "target":args.dsysfs[0], "attr":args.dsysfs[1] })
            #if not ret is None:
                #ret = ret.rstrip('\n')
                #print ret

    if args.delete:
        pddf_obj.delete_pddf_devices()

    if args.validate:
        if args.validate[0] == 'all':
            pddf_obj.validate_pddf_devices(args.validate[1:])
        else:
            pass

    if args.schema:
        pddf_obj.schema_validation(args.schema[0])


if __name__ == "__main__" :
        main()
