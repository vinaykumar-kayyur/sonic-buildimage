#!/usr/bin/env python

import click
import re
import json
import collections

from sfputil.main import *
from rjutil.baseutil import get_machine_info
from rjutil.baseutil import get_platform_info

SAI_PROFILE = "sai.profile"
SAI_PROFILE_PREDIX = "SAI_INIT_CONFIG_FILE=/usr/share/sonic/hwsku/"
CONFIG_DB_JSON_PATH = "/etc/sonic/config_db.json"
LANE_MAX = 4

global_speed_preemphasis = {
"x86_64-ragile_b6520-64cq-r0":{
    "10G_40G":["0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", "0x135001", 
        "0x135001"], \
    "25g_100G":["0x154609", "0x154609", "0x154609", "0x154609", "0x12480a", "0x12480a", "0x154609", 
        "0x12480a", "0x0f4b0a", "0x0f4b0a", "0x12480a", "0x12480a", "0x0f4b0a", "0x0f4b0a", 
        "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", 
        "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", 
        "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", 
        "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", 
        "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", 
        "0x0f4b0a", "0x0f4b0a", "0x0f4b0a", "0x12480a", "0x12480a", "0x12480a", "0x12480a", 
        "0x12480a", "0x12480a", "0x12480a", "0x12480a", "0x154609", "0x154609", "0x154609", 
        "0x154609"]
    },
"x86_64-ragile_b6510-48vs8cq-r0":{
    "10G_40G":["0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", 
        "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", 
        "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", 
        "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", 
        "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", 
        "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", 
        "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", 
        "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02", "0x154d02"], \
    "25G_100G":["0x0f480d", "0x0f480d", "0x0f480d", "0x0f480d", "0x0f480d", "0x0f480d", "0x0d4b0c", 
        "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", 
        "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", 
        "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", 
        "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", 
        "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", 
        "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", 
        "0x0d4b0c", "0x0d4b0c", "0x0d4b0c", "0x0f480d", "0x0f480d", "0x0f480d", "0x0f480d"]
    }
}

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


class PortClass(object):


    def __init__(self, lport = 0, interface = "", logic_port = 0, phy_port = 0, cmd_speed = 0, 
        phy_speed = 0):
        self._lport = lport
        self._interface = interface
        self._logic_port = logic_port
        self._phy_port = phy_port
        self._cmd_speed = cmd_speed
        self._phy_speed = phy_speed

    @property
    def lport(self):
        return self._lport

    @property
    def interface(self):
        return self._interface

    @property
    def logic_port(self):
        return self._logic_port

    @property
    def phy_port(self):
        return self._phy_port

    @property
    def cmd_speed(self):
        return self._cmd_speed

    @property
    def phy_speed(self):
        return self._phy_speed

    def set_lport(self, lport):
        self._lport = lport

    def set_interface(self, interface):
        self._interface = interface

    def set_logic_port(self, logic_port):
        self._logic_port = logic_port

    def set_phy_port(self, phy_port):
        self._phy_port = phy_port

    def set_cmd_speed(self, cmd_speed):
        self._cmd_speed = cmd_speed

    def set_phy_speed(self, phy_speed):
        self._phy_speed = phy_speed


class ReUtil(object):


    @staticmethod
    def is_portmap_line(line):
        if re.search('portmap_(.*?)=(.*?):(.*?)$', line):
            return True
        return False

    @staticmethod
    def is_preemphasis_line(line):
        if re.search('serdes_preemphasis_lane([0-9])_([0-9]+)=(.*?)$', line):
            return True
        return False

    @staticmethod
    def getre_portmap_phy_port(line):
        return int(re.findall(r"portmap_.*?=(.*?):.*?$", line)[0])

    @staticmethod
    def getre_portmap_logic_port(line):
        return int(re.findall(r"portmap_(.*?)=.*?:.*?$", line)[0])

    @staticmethod
    def getre_portmap_phy_speed(line):
        return int(re.findall(r"portmap_.*?=.*?:([0-9]+).*?$", line)[0])

    @staticmethod
    def getre_preemphasis_logic_port(line):
        return int(re.findall(r"serdes_preemphasis_lane.*?_([0-9]+)=.*?$", line)[0])

    @staticmethod
    def getre_preemphasis_pree_value(line):
        return re.findall(r"serdes_preemphasis_lane.*?_[0-9]+=(.*?)$", line)[0]

    @staticmethod
    def setre_portmap_speed(line, speed):
        return re.sub(r'portmap_(.*?)=(.*?):[0-9]+(.*?)$', r'portmap_\1=\2:%d\3' % speed, line)

    @staticmethod
    def setre_preemphasis_pree_value(line, value):
        return re.sub(r'serdes_preemphasis_lane([0-9])_([0-9]+)=(.*?)$', 
            r'serdes_preemphasis_lane\1_\2=%s' % value, line)



class PortUtil(object):


    _config_json_path = CONFIG_DB_JSON_PATH
    _config_bcm_path = ""
    _port_config_path = ""
    _device_port_list = []

    def __init__(self):
        self._config_json_file = open(self.config_json_path, 'r+')
        self._config_bcm_file = open(self.config_bcm_path, 'r+')
        self._port_config_file = open(self.port_config_path, 'r+')
        self._parse_port_config()
        self._parse_config_json()
        self._parse_config_bcm()
    
    def __del__(self):
        self._config_json_file.flush()
        self._config_bcm_file.flush()
        self._port_config_file.flush()
        self._config_json_file.close()
        self._config_bcm_file.close()
        self._port_config_file.close()

    @property
    def device_port_list(self):
        return self._device_port_list

    @property
    def config_json_path(self):
        return self._config_json_path

    @property
    def config_bcm_path(self):
        if self._config_bcm_path == "":
            (platform, hwsku) = get_platform_and_hwsku()
            platform_path = "/".join([PLATFORM_ROOT_PATH, platform])
            hwsku_path = "/".join([platform_path, hwsku])
            saiprofile_path = "/".join([hwsku_path, SAI_PROFILE])
            with open(saiprofile_path, "r") as saiprofile_f:
                for line in saiprofile_f:
                    if(re.search('%s(.*?)$' % SAI_PROFILE_PREDIX, line)):
                        config_bcm = re.findall(r"%s(.*?)$" % SAI_PROFILE_PREDIX, line)[0]
                        self._config_bcm_path = "/".join([hwsku_path, config_bcm])
        return self._config_bcm_path

    @property
    def port_config_path(self):
        if self._port_config_path == "":
            self._port_config_path = get_path_to_port_config_file()
        return self._port_config_path

    def sync_cmd_speed(self):
        self._config_bcm_file.seek(0)
        lines = self._config_bcm_file.readlines()
        self._config_bcm_file.seek(0)
        for line in lines:
            result = ""
            if ReUtil.is_portmap_line(line):
                phy_port = ReUtil.getre_portmap_phy_port(line)
                logic_port = ReUtil.getre_portmap_logic_port(line)
                phy_speed = ReUtil.getre_portmap_phy_speed(line)
                for port in self._device_port_list:
                    port_index = self._device_port_list.index(port)
                    if port.phy_port == phy_port:
                        if self._get_speed_mask()[port_index] == 0 or port.cmd_speed == phy_speed:
                            break
                        port.set_phy_speed(phy_speed)
                        result = ReUtil.setre_portmap_speed(line, port.cmd_speed)
                        break
            if result == "":
                result = line
            self._config_bcm_file.write(result)
        return True

    def set_port_preem(self):
        try:
            speed_preemphasis = global_speed_preemphasis[get_platform_info(get_machine_info())]
        except Exception, err:
            return False
        self._config_bcm_file.seek(0)
        lines = self._config_bcm_file.readlines()
        self._config_bcm_file.seek(0)
        for line in lines:
            result = ""
            if ReUtil.is_preemphasis_line(line):
                logic_port = ReUtil.getre_preemphasis_logic_port(line)
                value = ReUtil.getre_preemphasis_pree_value(line)
                for port in self._device_port_list:
                    port_index = self._device_port_list.index(port)
                    if port.logic_port == logic_port:
                        if port.phy_speed == 10 or port.phy_speed == 40:
                            preem_value = speed_preemphasis["10G_40G"]
                        elif port.phy_speed == 25 or port.phy_speed == 100:
                            preem_value = speed_preemphasis["25G_100G"]
                        else :
                            break
                        if preem_value[port_index] == value:
                            break
                        result = ReUtil.setre_preemphasis_pree_value(line, preem_value[port_index])
                        break
            if result == "":
                result = line
            self._config_bcm_file.write(result)
        return True

    def _parse_port_config(self):
        lport_num = 0
        for line in self._port_config_file:
            line.strip()
            if(len(line.split()) and re.search("Ethernet[0-9]+", line.split()[0])):
                lport_num = lport_num + 1
                self._device_port_list.append(PortClass(lport = lport_num, 
                    interface = line.split()[0], phy_port = int(line.split()[1].split(',')[0])))

    def _parse_config_json(self):
        config_json_dict = json.load(self._config_json_file, 
            object_pairs_hook = collections.OrderedDict)
        for key in config_json_dict["PORT"].keys():
            if config_json_dict["PORT"][key].__contains__("speed"):
                for port in self._device_port_list:
                    if port.interface == key:
                        port.set_cmd_speed(int(config_json_dict["PORT"][key]["speed"]) / 1000)
                        break

    def _parse_config_bcm(self):
        for line in self._config_bcm_file:
            if ReUtil.is_portmap_line(line):
                phy_port = ReUtil.getre_portmap_phy_port(line)
                logic_port = ReUtil.getre_portmap_logic_port(line)
                phy_speed = ReUtil.getre_portmap_phy_speed(line)
                for port in self._device_port_list:
                    if port.phy_port == phy_port:
                        port.set_logic_port(logic_port)
                        port.set_phy_speed(phy_speed)
                        break

    def _get_speed_mask(self):
        interfaces_num = [int(port.interface[len("Ethernet"):]) for port in self._device_port_list]
        interfaces_mask = [1 for port in self._device_port_list]
        for port in self._device_port_list :
            port_index = self._device_port_list.index(port)
            port_num = interfaces_num[port_index]
            if(port_num % LANE_MAX == 0 and (port_num + LANE_MAX - 1) in interfaces_num):
                lane_ports = self._device_port_list[port_index:port_index + LANE_MAX]
                interfaces_speed = [lane.cmd_speed for lane in lane_ports]
                for interface_speed in interfaces_speed:
                    if interfaces_speed[0] != interface_speed:
                        for i in range(LANE_MAX):
                            interfaces_mask[port_index + i] = 0
                        break
        return interfaces_mask


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''device operator'''
    pass

@main.command()
def sync():
    pt = PortUtil()
    pt.sync_cmd_speed()
    click.echo("port sync success")

@main.command()
def setpreem():
    pt = PortUtil()
    pt.set_port_preem()
    click.echo("port setpreem success")

@main.command()
def start():
    '''start port control'''
    pt = PortUtil()
    pt.sync_cmd_speed()
    pt.set_port_preem()
    click.echo("port start success")

@main.command()
def stop():
    '''stop port control '''
    pass

if __name__ == '__main__':
    main()
