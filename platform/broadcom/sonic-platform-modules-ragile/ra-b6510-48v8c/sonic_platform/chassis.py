#############################################################################
# PDDF
# Module contains an implementation of SONiC Chassis API
#
#############################################################################

try:
    import time
    import traceback
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.sfp import *
    from sonic_platform.psu import Psu
    from sonic_platform.fan import Fan
    from sonic_platform.fan_drawer import FanDrawer
    from sonic_platform.thermal import Thermal
    from sonic_platform.watchdog import Watchdog
    from sonic_platform.component import Component
    from sonic_platform.eeprom import Eeprom
    from sonic_platform.logger import logger
    from sonic_platform.dcdc import Dcdc
    from .sfp_config import *
    from sonic_py_common.general import getstatusoutput_noshell

except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Chassis(ChassisBase):
    """
    Platform-specific Chassis class
    """
    STATUS_INSERTED = "1"
    STATUS_REMOVED = "0"
    sfp_present_dict = {}
    
    def __init__(self):
        ChassisBase.__init__(self)
        self._dcdc_list = []

        try:
            sfp_config = get_sfp_config()
            self.port_start_index = sfp_config.get("port_index_start", 0)
            self.port_num = sfp_config.get("port_num", 0)
            # fix problem with first index is 1, we add a fake sfp node
            if self.port_start_index == 1:
                self._sfp_list.append(Sfp(1))

            # sfp id always start at 1
            for index in range(1, self.port_num + 1):
                self._sfp_list.append(Sfp(index))

            for i in range(self.port_start_index, self.port_start_index + self.port_num):
                self.sfp_present_dict[i] = self.STATUS_REMOVED

        except Exception as err:
            print("SFP init error: %s" % str(err))

    def get_revision(self):
        val  = ord(self._eeprom.revision_str())
        test = "{}".format(val)
        return test

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot
        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
#        try:
#            is_power_loss = False
#            # enable read
#            getstatusoutput_noshell(self.disable_write)
#            getstatusoutput_noshell(self.enable_read)
#            ret, log = getstatusoutput_noshell(self.read_value)
#            if ret == 0 and "0x0a" in log:
#                is_power_loss = True
#
#            # erase i2c and e2
#            getstatusoutput_noshell(self.enable_erase)
#            time.sleep(1)
#            getstatusoutput_noshell(self.disable_erase)
#            # clear data
#            getstatusoutput_noshell(self.enable_write)
#            getstatusoutput_noshell(self.disable_read)
#            getstatusoutput_noshell(self.disable_write)
#            getstatusoutput_noshell(self.enable_read)
#            # enable write and set data
#            getstatusoutput_noshell(self.enable_write)
#            getstatusoutput_noshell(self.disable_read)
#            getstatusoutput_noshell(self.write_value)
#            if is_power_loss:
#                return(self.REBOOT_CAUSE_POWER_LOSS, None)
#        except Exception as e:
#            logger.error(str(e))

        return (self.REBOOT_CAUSE_NON_HARDWARE, None)

    def get_change_event(self, timeout=0):
        change_event_dict = {"fan": {}, "sfp": {}, "voltage": {}}

        start_time = time.time()
        forever = False

        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000)  # Convert to secs
        else:
            print("get_change_event:Invalid timeout value", timeout)
            return False, change_event_dict

        end_time = start_time + timeout
        if start_time > end_time:
            print(
                "get_change_event:" "time wrap / invalid timeout value",
                timeout,
            )
            return False, change_event_dict  # Time wrap or possibly incorrect timeout
        try:
            while timeout >= 0:
                # check for sfp
                sfp_change_dict = self.get_transceiver_change_event()
                if sfp_change_dict :
                    change_event_dict["sfp"] = sfp_change_dict
                    return True, change_event_dict
                if forever:
                    time.sleep(1)
                else:
                    timeout = end_time - time.time()
                    if timeout >= 1:
                        time.sleep(1)  # We poll at 1 second granularity
                    else:
                        if timeout > 0:
                            time.sleep(timeout)
                        return True, change_event_dict
        except Exception as e:
            logger.error(str(e))
            print(e)
        print("get_change_event: Should not reach here.")
        return False, change_event_dict

    def get_transceiver_change_event(self):
        cur_sfp_present_dict = {}
        ret_dict = {}

        # Check for OIR events and return ret_dict
        for i in range(self.port_start_index, self.port_start_index + self.port_num):
            sfp = self._sfp_list[i]
            if sfp.get_presence():
                cur_sfp_present_dict[i] = self.STATUS_INSERTED

            else:
                cur_sfp_present_dict[i] = self.STATUS_REMOVED

        # Update reg value
        if cur_sfp_present_dict == self.sfp_present_dict:
            return ret_dict

        for index, status in cur_sfp_present_dict.items():
            if self.sfp_present_dict[index] != status:
                ret_dict[index] = status

        self.sfp_present_dict = cur_sfp_present_dict

        return ret_dict
