try:
    import time
    from .helper import APIHelper
    from sonic_py_common.logger import Logger
    from minipack.fpgautil import FpgaUtil
except ImportError as e:
    raise ImportError(repr(e) + " - required module not found")

POLL_INTERVAL_IN_SEC = 1

class SfpEvent:
    ''' Listen to insert/remove sfp events '''

    def __init__(self, sfp_list):
        self._api_helper = APIHelper()
        self._sfp_list = sfp_list
        self._logger = Logger()
        self._sfp_change_event_data = {'present': 0}

    def get_presence_bitmap(self):
        bitmap = 0
        for sfp in self._sfp_list:
            modpres = sfp.get_presence()
            i=sfp.port_num-1
            if modpres:
                bitmap = bitmap | (1 << i)
        return bitmap

    def get_sfp_event(self, timeout=2000):
        pim = FpgaUtil()
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
            print("get_transceiver_change_event:Invalid timeout value", timeout)
            return False, {}

        end_time = start_time + timeout
        if start_time > end_time:
            print('get_transceiver_change_event:'
                  'time wrap / invalid timeout value', timeout)

            return False, {}  # Time wrap or possibly incorrect timeout

        while timeout >= 0:
            change_status = 0
            check_dict = pim.get_qsfp_interrupt()
            present = 0
            for key, value in check_dict.items():
                if value == 1:
                    present = pim.get_qsfp_presence(key)
                    change_status = 1
                    if present:
                        port_dict[key+1] = '1'
                    else:
                        port_dict[key+1] = '0'

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
        print("get_evt_change_event: Should not reach here.")
        return False, {}