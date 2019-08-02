#coding=utf-8
import time
import os
import re
import logging
import commands
import subprocess
import portutil
import click

from sonic_platform import get_machine_info
from sonic_platform import get_platform_info

MACHINE_FILE = "/host/machine.conf"
MACHINE_PLATFORM_PREDIX = "onie_platform="


global_mgmt_kr_ports = {
    "x86_64-ruijie_b6510-48vs8cq-r0":{"eth1":66, "eth2":130},
    "x86_64-alibaba_as13-32h-rj-r0":{"eth1":66, "eth2":130},
    "x86_64-alibaba_as13-48f8h-rj-r0":{"eth1":66, "eth2":130},
    "x86_64-alibaba_as23-128h-rj-r0":{"eth1":38, "eth2":118}
}


def prepare_kr_test():
    cmd = "ifconfig eth1 up"
    ret, output = commands.getstatusoutput(cmd)
    cmd = "ifconfig eth2 up"
    ret, output = commands.getstatusoutput(cmd)
    cmd = "bcmcmd \"port all en=1\""
    ret, output = commands.getstatusoutput(cmd)


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


class PortKrTest(object):


    def __init__(self):
        self.__install_pktgen_mode()


    def __get_onie_platform(self):
        with open(MACHINE_FILE, "r") as machine_f:
            for line in machine_f:
                if(re.search('%s(.*?)$' % MACHINE_PLATFORM_PREDIX, line)):
                    onie_platform = re.findall(r"%s(.*?)$" % MACHINE_PLATFORM_PREDIX, line)[0]
                    return onie_platform
        return None


    def __install_pktgen_mode(self):
        cmd = "lsmod | grep pktgen"
        ret, output = commands.getstatusoutput(cmd)
        if(not output):
            cmd = "modprobe pktgen"
            ret, output = commands.getstatusoutput(cmd)
            cmd = "echo \"add_device eth1\" > /proc/net/pktgen/kpktgend_0"
            ret, output = commands.getstatusoutput(cmd)
            cmd = "echo \"add_device eth2\" > /proc/net/pktgen/kpktgend_0"
            ret, output = commands.getstatusoutput(cmd)
            time.sleep(3)


    def get_mgmt_bcmport(self, port):
        cmd = "bcmcmd ps"
        ret, output = commands.getstatusoutput(cmd)
        lines = output.split("\n")
        logic_port = global_mgmt_kr_ports[self.__get_onie_platform()][port]
        for line in lines:
            line.strip()
            if re.search(r"^.*?\(.*?\)", line) and int(re.findall(r"^.*?\((.*?)\)", 
                line)[0].strip()) == logic_port:
                return re.findall("^(.*?)\(.*?\)", line)[0].strip()
        return None
 

    def start_send_port_packets(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff", vlan=4080):
        cmd = "echo \"pkt_size %d\" > /proc/net/pktgen/%s" % (size, port)
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"count %d\" > /proc/net/pktgen/%s" % (count, port)
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"dst_mac %s\" > /proc/net/pktgen/%s" % (dst_mac, port)
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"vlan_id %s\" > /proc/net/pktgen/%s" % (vlan, port)
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"start\" > /proc/net/pktgen/pgctrl"
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        time.sleep(2)
        cmd = "echo \"stop\" > /proc/net/pktgen/pgctrl"
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "cat /proc/net/pktgen/%s" % port
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def clear_port_packets(self):
        for port in global_mgmt_kr_ports[self.__get_onie_platform()]:
            cmd = "bcmcmd \"clear c %s\"" % self.get_mgmt_bcmport(port)
            ret, output = commands.getstatusoutput(cmd)
            if(ret != 0):
                return False, output
        return True, output


    def check_port_packets(self, port, count):
        cmd = "bcmcmd \"show c XLMIB_RPOK.%s\"" % self.get_mgmt_bcmport(port)
        ret, output = commands.getstatusoutput(cmd)
        lines = output.split("\n")
        if(lines[1].strip()):
            if (count == int(re.sub('[,]', '', lines[1].split()[2].strip("+-")))):
                return True, lines[1].split()[2]
            else:
                return False, lines[1].split()[2]
        return False, "fail"


class PortTest(object):
    __mode = 0
    
    interfaces = []
    porttabfile = " "
    bcm_ports = []

    def __init__(self, mode = "sdk"):
        self.__install_pktgen_mode()
        self.__get_global_interfaces()
        self.__get_global_bcmports()
        if(mode == "sonic"):
            self.__mode = 1
        else:
            self.__mode = 0


    def __install_pktgen_mode(self):
        cmd = "lsmod | grep pktgen"
        strs = os.popen(cmd)
        lines = strs.readlines()
        if(not lines):
            cmd = "modprobe pktgen"
            ret, output = commands.getstatusoutput(cmd)


    def __get_global_interfaces(self):
        if(len(self.interfaces)):
            #print("inited interfaces")
            pass
        else:
            cmd = "show interfaces status"
            strs = os.popen(cmd)
            for line in strs:
                line.strip()
                if(len(line.split()) and re.search("Ethernet[0-9]+", line.split()[0])): 
                    self.interfaces.append(line.split()[0])


    def __get_global_bcmports(self):
        if(len(self.bcm_ports)):
            pass
        else: 
            pu = portutil.PortUtil()
            cmd = "bcmcmd ps"
            strs = os.popen(cmd)
            lines = strs.readlines()
            for port in pu.device_port_list:
                for line in lines:
                    line.strip()
                    if re.search(r"^.*?\(.*?\)", line) and int(re.findall(r"^.*?\((.*?)\)", line)[0].strip()) == port.logic_port:
                        self.bcm_ports.append(re.findall("^(.*?)\(.*?\)", line)[0].strip())
                        break


    def __get_port_status_by_sonic(self, port):
        cmd = "show int status %s" % self.interfaces[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        return lines[-2].split()[5]


    def __get_port_status_by_sdk(self, port):
        cmd = "bcmcmd \"ps %s\"" % self.bcm_ports[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        if(re.search("up", lines[3])):
            return "up"
        elif(re.search("!ena", lines[3])):
            return "!ena"
        else:
            return "down"


    def __get_unit_port_by_bcm(self, port):
        cmd = "bcmcmd \"ps %s\"" % self.bcm_ports[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        unit_port = int(re.findall("%s\((.*?)\)" % self.bcm_ports[port - 1], lines[3])[0].strip())
        return unit_port


    def __start_send_port_packets_by_sonic(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff"):
        cmd = "echo \"add_device %s\" > /proc/net/pktgen/kpktgend_0" % self.interfaces[port - 1]
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"pkt_size %d\" > /proc/net/pktgen/%s" % (size,  self.interfaces[port - 1])
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"count %d\" > /proc/net/pktgen/%s" % (count, self.interfaces[port - 1])
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"dst_mac %s\" > /proc/net/pktgen/%s" % (dst_mac, self.interfaces[port - 1])
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "echo \"start\" > /proc/net/pktgen/pgctrl"
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = "cat /proc/net/pktgen/%s" % self.interfaces[port - 1]
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def __start_send_port_packets_by_sdk(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff"):
        cmd = "bcmcmd \"pbmp %s\"" % self.bcm_ports[port - 1]
        strs = os.popen(cmd)
        lines = strs.readlines()
        pbmp = re.findall("0x[0-9]+",lines[1].strip())[0]
        cmd = "bcmcmd \"tx %d VLantag=1 TXUnit=0 PortBitMap=%s Length=%d DestMac=%s\"" % (count, pbmp, size, dst_mac)
        ret, output = commands.getstatusoutput(cmd)
        #print output
        if(ret != 0 ):
            return False, output
        return True, output


    def __clear_port_packets_by_sonic(self):
        cmd = "show interfaces counters -c"
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def __clear_port_packets_by_sdk(self):
        cmd = "bcmcmd \"clear c\""
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def __check_port_packets_by_sonic(self, port, count, direc = "tx"):
        cmd = "show interfaces counters"
        strs = os.popen(cmd)
        lines = strs.readlines()
        for line in lines:
            line.strip()
            if(len(line.split()) and re.search("Ethernet[0-9]+", line.split()[0])): 
                if(self.interfaces[port - 1] == line.split()[0]):
                    if(direc == "tx"):
                        if(count == int(re.sub('[,]', '', line.split()[9]))):
                            return True, line.split()[9]
                        else:
                            #print("packets num = %s" % int(re.sub('[,]', '', line.split()[9]))) 
                            return False, line.split()[9]
                    elif(direc == "rx"):
                        if(count == int(re.sub('[,]', '', line.split()[2]))):
                            return True, line.split()[9]
                        else:
                            #print("packets num = %s" % int(re.sub('[,]', '', line.split()[2]))) 
                            return False, line.split()[9]
        return False, "fail"


    def __check_port_packets_by_sdk(self, port, count, direc = "tx"):
        if(direc == "tx"):
            cmd = "bcmcmd \"show c CLMIB_TPOK\""
            strs = os.popen(cmd)
            line = strs.read()
            if re.search(r"failed", line):
                showc = "CDMIB_TPKT"
            else :
                showc = "CLMIB_TPKT"
            cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
            strs = os.popen(cmd)
            lines = strs.readlines()
            if(lines[1].strip()):
                if(count == int(re.sub('[,]', '', lines[1].split()[2].strip("+-")))):
                    return True, lines[1].split()[2]
                else:
                    return False, lines[1].split()[2]
        elif(direc == "rx"):
            cmd = "bcmcmd \"show c CLMIB_RPOK\""
            strs = os.popen(cmd)
            line = strs.read()
            if re.search(r"failed", line):
                showc = "CDMIB_RPKT"
            else :
                showc = "CLMIB_RPKT"
            logging.debug(self.bcm_ports[port - 1])
            cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
            strs = os.popen(cmd)
            lines = strs.readlines()
            #logging.debug(lines)
            if(lines[1].strip()):
                if (count == int(re.sub('[,]', '', lines[1].split()[2].strip("+-")))):
                    return True, lines[1].split()[2]
                else:
                    return False, lines[1].split()[2]
        return False, "fail"


    ################################################################################################


    def get_port_status(self, port):
        if(self.__mode == 0):
            return self.__get_port_status_by_sdk(port)
        elif(self.__mode == 1):
            return self.__get_port_status_by_sonic(port)


    def get_port_fcs_status(self, port):
        tfcs = 0
        rfcs = 0
        cmd = "bcmcmd \"show c CLMIB_TPOK\""
        strs = os.popen(cmd)
        line = strs.read()
        if re.search(r"failed", line):
            showc = "CDMIB_TFCS"
        else :
            showc = "CLMIB_TFCS"
        cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
        strs = os.popen(cmd)
        lines = strs.readlines()
        if lines[1].strip():
            tfcs = int(re.sub('[,]', '', lines[1].split()[2]))
        cmd = "bcmcmd \"show c CLMIB_RPOK\""
        strs = os.popen(cmd)
        line = strs.read()
        if re.search(r"failed", line):
            showc = "CDMIB_RFCS"
        else :
            showc = "CLMIB_RFCS"
        cmd = "bcmcmd \"show c %s.%s\"" % (showc, self.bcm_ports[port - 1])
        strs = os.popen(cmd)
        lines = strs.readlines()
        if lines[1].strip():
            rfcs = int(re.sub('[,]', '', lines[1].split()[2]))
        if(tfcs == 0 and rfcs == 0):
            return True, (tfcs, rfcs)
        return False, (tfcs, rfcs)


    def start_send_port_packets(self, port, count, size=64, dst_mac="ff:ff:ff:ff:ff:ff"):
        if(self.__mode == 0):
            return self.__start_send_port_packets_by_sdk(port, count, size, dst_mac)
        elif(self.__mode == 1):
            return self.__start_send_port_packets_by_sonic(port, count, size, dst_mac)
        return False, "fail"


    def stop_send_port_packets(self):
        cmd = "bcmcmd \"port xe,ce en=0\""
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        time.sleep(2)
        cmd = "bcmcmd \"port xe,ce en=1\""
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def clear_port_packets(self):
        if(self.__mode == 0):
            return self.__clear_port_packets_by_sdk()
        elif(self.__mode == 1):
            return self.__clear_port_packets_by_sonic()
        return False, "fail"


    def check_port_packets(self, port, count, direc = "tx"):
        if(self.__mode == 0):
            return self.__check_port_packets_by_sdk(port, count, direc)
        elif(self.__mode == 1):
            return self.__check_port_packets_by_sonic(port, count, direc)
        return False, "fail"


    def init_port_cpu(self):
        cmd = "bcmcmd \"cint /usr/share/sonic/platform/cpu.cint\""
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def reset_port_cpu(self):
        cmd = "bcmcmd \"cint;\r\n bcm_field_entry_destroy(0, 2048);\r\n bcm_field_group_destroy(0, 5);\r\n exit;\""
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def init_port_prbs(self):
        cmd = "bcmcmd \"cint /usr/share/sonic/platform/prbs.cint\""
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def reset_port_prbs(self):
        time.sleep(1)


    def set_port_prbs(self, port, enable):
        unit_port = self.__get_unit_port_by_bcm(port)
        cmd = "bcmcmd \"cint;\r\n set_port_prbs(%d, %d);\r\n exit;\"" % (unit_port, enable)
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def get_port_prbs_result(self, port):
        unit_port = self.__get_unit_port_by_bcm(port)
        cmd = "bcmcmd \"cint;\r\n print get_port_prbs_result(%d);\r\n exit;\"" % unit_port
        strs = os.popen(cmd)
        time.sleep(1)
        cmd = "bcmcmd \"cint;\r\n print get_port_prbs_result(%d);\r\n exit;\"" % unit_port
        strs = os.popen(cmd)
        lines = strs.readlines()
        status = int(re.findall(" = (.*?) ",lines[-5])[0])
        return status


    def test(self):
        circle = 0
        while True:
            print("circle %d:" % (circle + 1))
            self.init_port_cpu()
            self.clear_port_packets()
            for i in range(len(self.bcm_ports)):
                self.start_send_port_packets(i + 1, 10000, 1000)
            time.sleep(5)
            for i in range(len(self.bcm_ports)):
                if(self.check_port_packets(i + 1, 10000, "rx")):
                    print("port %d is ok" % (i + 1))
                else:
                    print ("error:%d" % (i + 1))
            self.reset_port_cpu()
            circle += 1


class PortPrbsTest(object):
    mac_output = []
    sys_output = []
    line_output = []
    bcm_ports = []
    standard = 0
    
    def __init__(self, standard = 1.0e-10):
        self.standard = standard
        self.__get_global_bcmports()


    def __get_global_bcmports(self):
        if(len(self.bcm_ports)):
            pass
        else: 
            pu = portutil.PortUtil()
            cmd = "bcmcmd ps"
            strs = os.popen(cmd)
            lines = strs.readlines()
            for port in pu.device_port_list:
                for line in lines:
                    line.strip()
                    if re.search(r"^.*?\(.*?\)", line) and int(re.findall(r"^.*?\((.*?)\)", line)[0].strip()) == port.logic_port:
                        self.bcm_ports.append(re.findall("^(.*?)\(.*?\)", line)[0].strip())
                        break


    def _get_mac_side_prbsstat_ber(self, port):
        results = []
        i = 0
        for line in self.mac_output:
            if ((self.bcm_ports[port - 1] + "[0]") in line) or ((self.bcm_ports[port - 1] + "[1]") in line):
                results.append(line)
                i = i + 1
        for result in results:
            i = i - 1
            ex = "[0-9]{0,}[.][0-9]{0,}[e][+][0-9]{0,}|[0-9]{0,}[.][0-9]{0,}[e][-][0-9]{0,}"
            ber = (re.search(ex,result))
            if (ber != None):
                if (float(ber.group()) > float(self.standard)):
                    return False, results
                elif(i == 0):
                    return True, results
        return False, results


    def _get_sys_side_prbsstat_ber(self, port):
        results = []
        icount = 2
        ex = "[0-9]+$"
        num = (re.search(ex, self.bcm_ports[port - 1])).group()
        num = int(num) * 2 + 1
        results.append(self.sys_output[num])
        results.append(self.sys_output[num+1])
        for result in results:
            icount = icount - 1
            ex = "[0-9]{0,}[.][0-9]{0,}[e][+][0-9]{0,}|[0-9]{0,}[.][0-9]{0,}[e][-][0-9]{0,}"
            ber = re.search(ex, result)
            if(ber != None):
                if(float(ber.group()) > float(self.standard)):
                    return False, results
                elif(icount == 0):
                    return True, results
        return False, results


    def _get_line_side_prbsstat_ber(self, port):
        results = []
        icount = 4
        ex = "[0-9]+$"
        num = (re.search(ex, self.bcm_ports[port - 1])).group()
        num = int(num) * 4 + 1
        results.append(self.line_output[num])
        results.append(self.line_output[num + 1])
        results.append(self.line_output[num + 2])
        results.append(self.line_output[num + 3])
        for result in results:
            icount = icount - 1
            ex = "[0-9]{0,}[.][0-9]{0,}[e][+][0-9]{0,}|[0-9]{0,}[.][0-9]{0,}[e][-][0-9]{0,}"
            ber = re.search(ex, result)
            if(ber != None):
                if(float(ber.group()) > float(self.standard)):
                    return False, results
                elif(icount == 0):
                    return True, results
        return False, results


    def init_port_prbs(self):
        cmd = 'bcmcmd "phy diag ce prbs set p=3"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=1 p=5"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0 p=5"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy diag ce prbs get"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy diag ce prbs get"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy diag ce prbsstat start i=120"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=1"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
             return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
             return False, output
        time.sleep(120)
        cmd = 'bcmcmd "phy control ce prbs lnside=1 time=120 cal=1"'
        ret, output = commands.getstatusoutput(cmd)
        self.sys_output = output.split("\r\n")
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0 time=120 cal=1"'
        ret, output = commands.getstatusoutput(cmd)
        self.line_output = output.split("\r\n")
        if(ret != 0):
            return False, output
        time.sleep(30)
        cmd = 'bcmcmd "phy diag ce prbsstat ber"'
        ret, output = commands.getstatusoutput(cmd)
        self.mac_output = output.split("\r\n")
        if(ret != 0):
            return False, output
        return True, output


    def clear_port_prbs(self):
        cmd = 'bcmcmd "phy diag ce prbs clear"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=1 clear=1"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        cmd = 'bcmcmd "phy control ce prbs lnside=0 clear=1"'
        ret, output = commands.getstatusoutput(cmd)
        if(ret != 0):
            return False, output
        return True, output


    def get_port_prbs_result(self, flag, port):
        if (flag == "mac"):
            ret, output = self._get_mac_side_prbsstat_ber(port)
            return ret,output
        elif (flag == "sys"):
            ret, output = self._get_sys_side_prbsstat_ber(port)
            return ret, output
        elif (flag == "line"):
            ret, output = self._get_line_side_prbsstat_ber(port)
            return ret, output
        else:
            return False, "fail"


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''device operator'''
    pass


@main.command()
def test():
    pr = PortPrbsTest()
    pr.clear_port_prbs()
    pr.init_port_prbs()
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("mac", i + 1)
        print ret
        print result
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("sys", i + 1)
        print ret
        print result
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("line", i + 1)
        print ret
        print result
    pr.clear_port_prbs()


if __name__ == '__main__':
    main()


'''
portts = PortTest()


portts.init_port_prbs()
for i in range(64):
    portts.set_port_prbs((i+1),1)
    #portts.set_port_prbs(2,1)

time.sleep(5)

for i in range(64):
    print portts.get_port_prbs_result((i+1))
    #print portts.get_port_prbs_result(2)
    
for i in range(64):
    portts.set_port_prbs((i+1),0)


#status = get_port_status(i + 1)
'''

