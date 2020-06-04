import subprocess


def run_command(command):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        return process.communicate()[0].decode('utf-8')
    except:
        return None
