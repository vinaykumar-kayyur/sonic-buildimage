#!/usr/bin/env python

from paramiko import SSHClient
from scp import SCPClient
import sys
import os
import json
import re
import argparse
#import pysftp
import threading
import logging
import time
import paramiko
import subprocess
import uuid
import traceback
from datetime import datetime
from daemonize import Daemonize

import base64
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

from swsssdk import ConfigDBConnector
from swsssdk import SonicV2Connector
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler



# pip install --trusted-host=files.pythonhosted.org paramiko SSHClient SCPClient scp watchdog pycrypto
# apt-get install python python-dev libffi-dev openssl-dev


g_exp_ctx={}

g_exp_ctx['servername']='None'
g_exp_ctx['username']='None'
g_exp_ctx['password']='None'
g_exp_ctx['destdir']='supportsave'
g_exp_ctx['interval']='30'
g_exp_ctx['protocol']='scp'
g_exp_ctx['config']='disable'
g_exp_ctx['coredir']='/var/core/'
g_exp_ctx['srcdir']='/var/dump/'
g_exp_ctx['logfile']='/var/log/syslog'
g_exp_ctx['SYSLOG_IDENTIFIER']='export'
g_exp_ctx['PID']='/var/run/export.pid'

logger = None
g_last_ts = None 
keep_fds = None



#Writable wrapper structure for syslog class
class StreamToLogger(object):
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''

   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())

#Initalise the syslog infrastructure
def init_log():
    global logger

    handler = logging.handlers.SysLogHandler('/dev/log')

    formatter = logging.Formatter( '{} : %(message)s'.format(g_exp_ctx['SYSLOG_IDENTIFIER']))
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)



#AES encryption 
def encrypt(key, source, encode=True):
    key = key.ljust(16,'F')
    obj = AES.new(key, AES.MODE_CFB, 'A287AJSHJKHJS562')
    data = obj.encrypt(source)
    return base64.b64encode(data).decode("latin-1") if encode else data

#AES decryption 
def decrypt(key, source, decode=True):
    if decode:
        source = base64.b64decode(source.encode("latin-1"))

    key = key.ljust(16,'F')
    obj = AES.new(key, AES.MODE_CFB, 'A287AJSHJKHJS562')
    data = obj.decrypt(source)
    return data



#copy the support save file to remote server by SCP protocol
def copy_scp(srcfile):

    try:
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=g_exp_ctx['servername'], username=g_exp_ctx['username'], password=decrypt(str(uuid.getnode()), g_exp_ctx['password']))

        scp = SCPClient(ssh.get_transport())

        scp.put(g_exp_ctx['srcdir']+'/'+srcfile, g_exp_ctx['destdir']+'/')
        logger.debug("Tech-Support export[SCP:{}] is completed succesffully".format(srcfile))

        scp.close()
    except Exception as e:
        logger.error( "SCP copy is failed, file: {}, error:{}".format(srcfile, str(e)))
        logger.exception(str(e))



#copy the support save file to remote server by SFTP protocol
def copy_sftp(srcfile):

    try:
        transport = paramiko.Transport((g_exp_ctx['servername'],22))
        transport.connect(username=g_exp_ctx['username'], password=decrypt(str(uuid.getnode()), g_exp_ctx['password']))

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.chdir(g_exp_ctx['destdir']+'/')
        sftp.put(g_exp_ctx['srcdir']+'/'+srcfile, srcfile)
        logger.debug("Tech-Support export[SFTP:{}] is completed succesffully".format(srcfile))
        sftp.close()
    except Exception as e:
        logger.error( "SFTP copy is failed, file: {}, error:{}".format(srcfile, str(e)))
        logger.exception(str(e))


#copy the support save files
def copy_support_save(srcfile):

    if g_exp_ctx['protocol'] == 'scp':
        copy_scp(srcfile)
    else:
        copy_sftp(srcfile)


#copy the generate the support save files
g_lock = threading.Lock()
def generate_support_save():


    if g_exp_ctx['config'] != 'enable':
        logger.debug("Test-Support export is not enabled")
        return

        
    g_lock.acquire()

    now = datetime.now()
    srcdir='supportsave-'+now.strftime("%d.%m.%Y-%H.%M.%S")
    srcfile=srcdir+'.tar.gz'

    try:
        subprocess.call(['bash', '-c', 'BASE='+srcdir+' /usr/bin/generate_dump']) 
        #result = subprocess.call(['bash', '-c', 'BASE='+srcdir+' /usr/bin/generate_dump -v '], stdout=subprocess.PIPE) 
        #result.stdout
    except Exception as e:
        logger.error( "Test-Support save generation is failed!, error:"+str(e))

    try:
        if os.path.exists(g_exp_ctx['srcdir']+'/'+srcfile):
            copy_support_save(srcfile)
            os.remove(g_exp_ctx['srcdir']+'/'+srcfile)
    except Exception as e:
        logger.error( "Test-Support copy is failed!, file: {}, error:{}".format(srcfile, str(e)))


    g_lock.release()


#Register the event notification for core dump folder changes 
class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        global g_last_ts

        if event.is_directory:
            return None

        elif event.event_type == 'created' or \
             event.event_type == 'modified':
            logger.debug("Received created/modified event - %s." % event.src_path )
            generate_support_save()
            g_last_ts = time.time()


#Daemonize the export process
def export_daemon():

    config_db = ConfigDBConnector()
    config_db.connect()

    if not os.path.exists('/var/lib/systemd/coredump'):
        os.mkdir('/var/lib/systemd/coredump')

    observer = Observer()
    event_handler = Handler()
    observer.schedule(event_handler, g_exp_ctx['coredir'], recursive=True)
    observer.start()
    try:

        g_last_ts = curr_ts = time.time()

        while True:
            g_cfg= config_db.get_entry('EXPORT', 'export')
            for entry in g_cfg:
                g_exp_ctx[entry]=g_cfg[entry]

            cfg_entry = g_exp_ctx.copy()
            del cfg_entry['password']

            if int(g_exp_ctx['interval']) == 0:
                #logger.debug("Sleeping...{}".format(time.time()))
                time.sleep(60)
                continue
                

            curr_ts = time.time()
            diff = curr_ts - g_last_ts
            if diff > (int(g_exp_ctx['interval'])*60)/2:
                   logger.debug("Tech-Support export - curr:{}, last:{}, diff:{}\n".format(curr_ts, g_last_ts, diff))
                   generate_support_save()
            else:
                logger.debug("Skipping the current slot, curr:{}, last:{}, diff:{}\n".format(curr_ts, g_last_ts, diff))
                pass

            g_last_ts = curr_ts
            time.sleep(int(g_exp_ctx['interval'])*60)

    except Exception as e:
        logger.error( "Tech-Support export is failed, Error"+str(e) )
        logger.exception(str(e))
        #traceback.print_exc(file=STDERR)

    observer.stop()
    observer.join()


if __name__ == "__main__":

    init_log()

    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action='store_true', help="Start with daemon mode")
    args = parser.parse_args()

    if args.daemon:
        try:
            pid = os.fork()
        except OSError:
            sys.stderr.write("Could not create a child process\n")
        #parent
        if pid != 0:
            exit()

        #daemon = Daemonize(app="export", pid=g_exp_ctx['PID'], action=export_daemon, keep_fds=keep_fds)
        #daemon.start()
    
    export_daemon()


# Todo
# hide password
# watch for core event
# support save export 
# pip tools integration
# service startup
# config show
# check options <scp/sftp>
# logginh
# exception handling
