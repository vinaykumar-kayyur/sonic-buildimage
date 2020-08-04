import subprocess


def run_command(command):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        return process.communicate()[0].encode('utf-8')
    except Exception:
        return None


def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])

    return uptime_seconds
