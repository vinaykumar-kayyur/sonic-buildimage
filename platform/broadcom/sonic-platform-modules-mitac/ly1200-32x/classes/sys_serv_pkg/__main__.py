#!/usr/bin/python2

import json
import time
import signal
import sys
import threading
import socket
import select
import os
import logging
import getopt

from fan_dev import  FanDevMon
from psu_dev import  PsuDevMon
from misc_dev import MiscDevMon
from commonlib import *
from config import *

MIC_FEAT_SYS_INT = 0
gpe_num  = 0x1
BMS_SYS_GPE_SYSFS     = '/sys/firmware/acpi/interrupts/gpe{:02X}'.format(gpe_num)
SYS_GPE_INTR_TAG      = 'bms_acpi PNP0C01:00 000000{:02X} 00000000'.format(gpe_num)
ACPI_SOCK_SYSFS       = '/var/run/acpid.socket'

if 0:
    BMS_SYS_GPE_SYSFS     = 'gpe{:02X}'.format(gpe_num)
    ACPI_SOCK_SYSFS       = './tt.d'

def service_shutdown(signum, frame):
    WARN('Caught signal {:2d}'.format(signum))
    raise Exception('System daemon service shutdown')

def main_thread(dm_list, wait_time=2) :
    if MIC_FEAT_SYS_INT:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect( ACPI_SOCK_SYSFS )
    try:
        while 1:
            if MIC_FEAT_SYS_INT:
                write_file(BMS_SYS_GPE_SYSFS,'enable')
                buf = sock.recv(1024)
                DEBUG( 'got acpi event data: [{}] tag[{}]'.format(buf, SYS_GPE_INTR_TAG) )
                if buf !=  SYS_GPE_INTR_TAG:
                    continue
                write_file(BMS_SYS_GPE_SYSFS,'disable')
            else:
                time.sleep(wait_time)

            for dm in dm_list:
                # intr == 0 and msk == 1 --> set intr event
                intr = dm.get_intr_src()
                msk  = dm.get_intr_msk()

                for i in range(len(intr)):
                    if intr[i] == 0 and msk[i] == 1:
                        dm.set_intr_event()
                        break
                #if 0 in intr:
                #    dm.set_intr_event()
    finally:
        if MIC_FEAT_SYS_INT:
            sock.close()

def main():
    #os.system( 'renice -20 {}'.format(os.getpid()) )
    config = None
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],"d:",["log="])
        config = args[0] if len(args) > 0 else None

        for o, a in opts:
            if o in ('--log', '-d'):
                logging.getLogger(SYSLOG_IDENT).setLevel( eval('logging.{level}'.format(level=a.upper()) ) )
    except:
        ERR('params error')

    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    if config == None:
        data = config_data_ly1200
    else :
        with open(config, 'r') as j_file:
            data = json.load(j_file)
    #DEBUG(json.dumps(data, indent=2))

    BoardType(data["board_type_path"])
    PsuType(data['psu_type'])

    root_class = (
        FanDevMon,
        PsuDevMon,
        MiscDevMon,
    )

    dm_list = [m(data[m.__dict__['_config_key']]) for m in root_class if m.__dict__['_config_key'] in data]

    try:
        [  dm.set_intr_msk(1)  for dm in dm_list ]
        [  dm.start_monitor()  for dm in dm_list ]
        main_thread(dm_list)
    except Exception as e:
        WARN(e)
    finally:
        [  dm.stop_monitor()  for dm in dm_list ]

if __name__ == '__main__':
    main()
