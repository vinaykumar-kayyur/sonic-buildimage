import subprocess
import imp
import json
import requests
from sonic_py_common.device_info import get_platform_and_hwsku


PLATFORM_ROOT_PATH = "/usr/share/sonic/device"
PLATFORM_ROOT_PATH_DOCKER = "/usr/share/sonic/platform"


def load_platform_util_module(module_name):
    platform_util_module = None

    (platform, hwsku) = get_platform_and_hwsku()
    platform_path = ''
    if len(platform) != 0:
        platform_path = "/".join([PLATFORM_ROOT_PATH, platform])
    else:
        platform_path = PLATFORM_ROOT_PATH_DOCKER

    try:
        module_file = "/".join([platform_path, "plugins", module_name + ".py"])
        platform_util_module = imp.load_source(module_name, module_file)
    except IOError as e:
        return None

    return platform_util_module


def convert_unicode(input):
    if isinstance(input, dict):
        return {convert_unicode(key): convert_unicode(val) for key, val in input.iteritems()}
    elif isinstance(input, unicode):
        return input.encode("utf-8")
    else:
        return input


def run_command(cmd):
    proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if err and proc.returncode != 0:
        return proc.returncode, err
    return 0, out.decode().rstrip('\n')


def restful_command(cmd):
    url = "https://240.1.1.1:8080/api/hw/rawcmd"
    data = json.dumps({
        "Command" : cmd
    })

    for i in range(3):
        try:
            r = requests.post(url, data)
            r.url
            response_json = r.json()

            if "status" in response_json and response_json["status"] == "OK":
                ret = response_json["data"]["Outputs"]
                return True, ret
            else:
                return False, ""
        except Exception as e:
            print(e)
            continue
    return False, ""
