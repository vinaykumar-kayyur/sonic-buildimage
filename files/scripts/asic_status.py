#!/usr/bin/env python3

"""
    bootstrap-asic
"""
try:
    import re
    import syslog
    import sys
    from sonic_py_common import daemon_base
    from swsscommon import swsscommon
    from sonic_py_common import device_info
except ImportError as e:
    raise ImportError(str(e) + " - required module not found")

#
# Constants ====================================================================
#
CHASSIS_ASIC_INFO_TABLE = 'CHASSIS_ASIC_TABLE'
SELECT_TIMEOUT_MSECS = 5000

def main():
    if len(sys.argv) != 2:
        raise Exception('Pass valid asic-id as argument')

    args_asic_id = sys.argv[1]

    # Get num asics
    num_asics = 0
    num_asics = device_info.get_num_npus()
    if num_asics == 0:
        syslog.syslog(syslog.LOG_ERR,
                'Detected no asics on this platform')
        sys.exit(1)

    # Connect to STATE_DB and subscribe to chassis-module table notifications
    state_db = daemon_base.db_connect("STATE_DB")

    sel = swsscommon.Select()
    sst = swsscommon.SubscriberStateTable(state_db, CHASSIS_ASIC_INFO_TABLE)
    sel.addSelectable(sst)

    while True:
        (state, c) = sel.select(SELECT_TIMEOUT_MSECS)
        if state == swsscommon.Select.TIMEOUT:
            continue
        if state != swsscommon.Select.OBJECT:
            continue

        (asic_key, asic_op, asic_fvp) = sst.pop()
        asic_id=re.search(r'\d+$', asic_key)
        global_asic_id = asic_id.group(0)

        if asic_op == 'SET':
            asic_fvs = dict(asic_fvp)
            if asic_fvs['module_name'].startswith('FABRIC-CARD') is False:
                continue

            if (global_asic_id == args_asic_id):
                syslog.syslog(syslog.LOG_INFO,
                        'Detected asic{} is online'.format(global_asic_id))
                sys.exit(0)
        elif asic_op == 'DEL':
            syslog.syslog(syslog.LOG_INFO,
                    'Detected asic{} is offline'.format(global_asic_id))
            sys.exit(1)
        else:
            continue

if __name__ == "__main__":
    main()
