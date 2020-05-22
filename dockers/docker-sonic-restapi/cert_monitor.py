#!/usr/bin/env python

'''
This script monitors the certificate needed by rest-api container and safely restarts
the process when it detects a certificate roll-over
'''
import os, subprocess, time
from swsscommon import swsscommon
from sonic_daemon_base.daemon_base import Logger
import json

RESTAPI_SERVER_PROCESS = "go-server-server"
PATH_TO_CERT_TRACKER = "/restapi/cert_tracker"
POLLING_FREQUENCY = 3600
REDIS_TIMEOUT_MS = 0
logger = Logger()

def get_pid(process_name):
    '''
    return Process ID of the given process
    '''
    cmd = "ps aux"
    response = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = response.communicate()
    if (response.returncode != 0):
        logger.log_error(stderr, True)
        return None
    else:
        pid = None
        processes = stdout.splitlines()
        for process in processes:
            if process_name in process:
                pid = process.split()[1]
                break
        return pid           

def monitor_certificates(certificates, path_to_cert_tracker):
    '''
    Continuously monitor for change in 'last modified' time of the certs and restart restapi if
    change is detected
    '''
    while True:
        if os.path.isfile(path_to_cert_tracker):
            # load last read 'last modified' times
            cert_tracker = json.load(open(path_to_cert_tracker))
        else:
            cert_tracker = {}
        restart = False
        for certificate in certificates:
            if os.path.isfile(certificate):
                # Get 'last modified' time of the symbolic link of the cert
                m_time = os.lstat(certificate).st_mtime
                if certificate in cert_tracker:
                    if cert_tracker[certificate] != m_time:
                        logger.log_info("monitor_certificates: Certificate has rolled. Restart required")
                        restart = True
                cert_tracker[certificate] = m_time
            else:
                logger.log_error("monitor_certificates: "+certificate+" not found!")
        # Save 'last modifed' times
        json.dump(cert_tracker, open(path_to_cert_tracker, "w"))

        if restart:
            pid = get_pid(RESTAPI_SERVER_PROCESS)
            if pid:
                # Send SIGQUIT to go-server-server
                cmd = "kill -3 "+pid
                response = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = response.communicate()
                if (response.returncode != 0):
                    logger.log_error(stderr, True)
                else:
                    logger.log_info("monitor_certificates: SIGQUIT sent to go-server-server")
                    while get_pid(RESTAPI_SERVER_PROCESS) != None:
                        time.sleep(0.1)
                    logger.log_info("monitor_certificates: go-server-server has shutdown")
            else:
                logger.log_warn("monitor_certificates: RESTAPI Server (go-server-server) is not running!")
            
            # Safe to restart restapi server now
            cmd = "supervisorctl restart restapi"
            response = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = response.communicate()
            if (response.returncode != 0):
                logger.log_error(stderr, True)
                logger.log_info("monitor_certificates: RESTAPI Server restart failed")
            else:
                logger.log_info("monitor_certificates: RESTAPI Server has been restarted")

        time.sleep(POLLING_FREQUENCY)


if __name__ == '__main__':
    config_db = swsscommon.DBConnector("CONFIG_DB", REDIS_TIMEOUT_MS, True)
    restapi_table = swsscommon.Table(config_db, "RESTAPI")
    (status, tuples) = restapi_table.get("certs")
    restapi_certs = dict(tuples)

    certificates = []
    certificates.append(restapi_certs['client_ca_crt'])
    certificates.append(restapi_certs['server_crt'])
    certificates.append(restapi_certs['server_key'])

    # wait for go-server-server to start
    while True:
        if get_pid(RESTAPI_SERVER_PROCESS):
            break
        else:
            time.sleep(5)

    monitor_certificates(certificates, PATH_TO_CERT_TRACKER)
