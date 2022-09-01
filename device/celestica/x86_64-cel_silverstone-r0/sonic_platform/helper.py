import os
import struct
import subprocess
from mmap import *

HOST_CHK_CMD = "docker"
EMPTY_STRING = ""


class APIHelper():

    def __init__(self):
        pass

    def is_host(self):
        return subprocess.run(HOST_CHK_CMD, stdout=None, stderr=None).returncode == 0

    def pci_get_value(self, resource, offset):
        status = True
        result = ""
        try:
            fd = os.open(resource, os.O_RDWR)
            mm = mmap(fd, 0)
            mm.seek(int(offset))
            read_data_stream = mm.read(4)
            result = struct.unpack('I', read_data_stream)
        except:
            status = False
        return status, result

    def run_command(self, cmd1_args, cmd2_args):
        status = True
        result = ""
        try:
            with subprocess.Popen(cmd1_args, universal_newlines=True, stdout=subprocess.PIPE) as p1:
                with subprocess.Popen(cmd2_args, universal_newlines=True, stdin=p1.stdout, stdout=subprocess.PIPE) as p2:
                    raw_data = p2.communicate()[0]
                    if p2.returncode == 1:
                        raise subprocess.CalledProcessError(returncode=p2.returncode, cmd=cmd, output=output)
        except subprocess.CalledProcessError:
            status = False
        return status, raw_data.strip()

    def run_interactive_command(self, cmd):
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            return False
        return True

    def read_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

    def ipmi_raw(self, netfn, cmd):
        status = True
        result = ""
        try:
            cmd = ["ipmitool", "raw", str(netfn), str(cmd)]
            p = subprocess.Popen(
                cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except:
            status = False
        return status, result

    def ipmi_fru_id(self, id, key=None):
        status = True
        result = ""
        cmd1_args = ["ipmitool", "fru", "print", str(id)]
        try:
            if not key:
                p = subprocess.Popen(
                    cmd1_args, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                raw_data, err = p.communicate()
            else:
                cmd2_args = ["grep", str(key)]
                with subprocess.Popen(cmd1_args, universal_newlines=True, stdout=subprocess.PIPE) as p1:
                    with subprocess.Popen(cmd2_args, universal_newlines=True, stdin=p1.stdout, stdout=subprocess.PIPE) as p2:
                        raw_data = p2.communicate()[0]
                        if p2.returncode == 1:
                            raise subprocess.CalledProcessError(returncode=p2.returncode, cmd=cmd, output=raw_data)
        except subprocess.CalledProcessError:
            status = False
        return status, raw_data.strip()

    def ipmi_set_ss_thres(self, id, threshold_key, value):
        status = True
        result = ""
        try:
            cmd = ["ipmitool", "sensor", "thresh", str(id), str(threshold_key), str(value)]
            p = subprocess.Popen(
                cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except:
            status = False
        return status, result
