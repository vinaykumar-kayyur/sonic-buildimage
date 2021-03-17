#!/usr/bin/env python

#############################################################################
# PDDF
# Module contains an implementation of SONiC Chassis API
#
#############################################################################

try:
    import time
    from sonic_platform_pddf_base.pddf_chassis import PddfChassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Chassis(PddfChassis):
    """
    PDDF Platform-specific Chassis class
    """

    def __init__(self, pddf_data=None, pddf_plugin_data=None):
        PddfChassis.__init__(self, pddf_data, pddf_plugin_data)

    # Provide the functions/variables below for which implementation is to be overwritten
    def get_change_event(self, timeout=0):
        start_time = time.time()
        port_dict = {}
        change_dict = {}
        change_dict['sfp'] = port_dict
        forever = False

        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000)  # Convert to secs
        else:
            print("get_change_event:Invalid timeout value", timeout)
            return False, change_dict

        end_time = start_time + timeout
        if start_time > end_time:
            print('get_change_event: time wrap / invalid timeout value', timeout)
            return False, change_dict  # Time wrap or possibly incorrect timeout

        while timeout >= 0:
            change_status = 0
            for index in range(32):
                intr_status = self.get_sfp(index).get_intr_status()
                if intr_status:
                    port_dict[index] = 1
                else:
                    port_dict[index] = 0

            for key, value in port_dict.items():
                if value == 1:
                    present = self.get_sfp(key).get_presence()
                    change_status = 1
                    if present:
                        port_dict[key] = '1'
                    else:
                        port_dict[key] = '0'

            if change_status:
                return True, change_dict
            if forever:
                time.sleep(1)
            else:
                timeout = end_time - time.time()
                if timeout >= 1:
                    time.sleep(1)  # We poll at 1 second granularity
                else:
                    if timeout > 0:
                        time.sleep(timeout)
                    return True, change_dict

        print("get_change_event: Control should not reach here")
        return False, change_dict
