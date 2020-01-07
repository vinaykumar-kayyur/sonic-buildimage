#!/usr/bin/env python
#
# sfputil.py
#
# Platform-specific SFP utility for SONiC
#

# ----------------------------------------------------------------------------
# import modules
# ----------------------------------------------------------------------------
import os.path
import syslog
try:
    import time
    import sys
    from subprocess import Popen, PIPE
    from sonic_sfp.sfputilbase import SfpUtilBase


except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

# ----------------------------------------------------------------------------
# Global variables
# ----------------------------------------------------------------------------
DEBUG_EN = False
#DEBUG_EN = True

# ----------------------------------------------------------------------------
# Debug messages
# ----------------------------------------------------------------------------
def DEG_MSG(msg):
    """
    Output debug message on the console
    """

    if DEBUG_EN == True:
        print "[DEBMSG]: %s" % msg

# ----------------------------------------------------------------------------
# Check if file path existing or not
# ----------------------------------------------------------------------------
def file_path_exist(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False

# ----------------------------------------------------------------------------
# Class declaration
# ----------------------------------------------------------------------------
class SfpUtil(SfpUtilBase):
    """
        Platform specific SfpUtill class
    """

    __PORT_START = 0
    __PORT_COUNT = 56
    __SFP_PORT_START = 0
    __SFP_PORT_END = 47
    __QSFP_PORT_START = 48
    __QSFP_PORT_END = 55
    __PORT_END   = __PORT_START + __PORT_COUNT - 1
    __SFP_EEPROM_ADDR = 50

    __TYPE_PRESENT = 'present'
    __TYPE_LPMODE = 'lpmode'
    __TYPE_LOS = 'los'
    __TYPE_TX_DISABLE = 'tx_disable'
    __TYPE_TX_FAULT = 'tx_fault'
    __TYPE_INTERRUPT = 'interrupt'
    
    __port_to_io_addr = {
         ( 0,__TYPE_PRESENT) : 'sfp28_present1',       
         ( 1,__TYPE_PRESENT) : 'sfp28_present0',      
         ( 2,__TYPE_PRESENT) : 'sfp28_present3',        
         ( 3,__TYPE_PRESENT) : 'sfp28_present2',        
         ( 4,__TYPE_PRESENT) : 'sfp28_present5',        
         ( 5,__TYPE_PRESENT) : 'sfp28_present4',        
         ( 6,__TYPE_PRESENT) : 'sfp28_present7',        
         ( 7,__TYPE_PRESENT) : 'sfp28_present6',        
         ( 8,__TYPE_PRESENT) : 'sfp28_present9',        
         ( 9,__TYPE_PRESENT) : 'sfp28_present8',        
         (10,__TYPE_PRESENT) : 'sfp28_present11',        
         (11,__TYPE_PRESENT) : 'sfp28_present10',        
         (12,__TYPE_PRESENT) : 'sfp28_present13',        
         (13,__TYPE_PRESENT) : 'sfp28_present12',        
         (14,__TYPE_PRESENT) : 'sfp28_present15',        
         (15,__TYPE_PRESENT) : 'sfp28_present14',        
         (16,__TYPE_PRESENT) : 'sfp28_present17',        
         (17,__TYPE_PRESENT) : 'sfp28_present16',        
         (18,__TYPE_PRESENT) : 'sfp28_present19',        
         (19,__TYPE_PRESENT) : 'sfp28_present18',        
         (20,__TYPE_PRESENT) : 'sfp28_present21',        
         (21,__TYPE_PRESENT) : 'sfp28_present20',        
         (22,__TYPE_PRESENT) : 'sfp28_present23',        
         (23,__TYPE_PRESENT) : 'sfp28_present22',        
         (24,__TYPE_PRESENT) : 'sfp28_present25',        
         (25,__TYPE_PRESENT) : 'sfp28_present24',        
         (26,__TYPE_PRESENT) : 'sfp28_present27',        
         (27,__TYPE_PRESENT) : 'sfp28_present26',        
         (28,__TYPE_PRESENT) : 'sfp28_present29',        
         (29,__TYPE_PRESENT) : 'sfp28_present28',        
         (30,__TYPE_PRESENT) : 'sfp28_present31',        
         (31,__TYPE_PRESENT) : 'sfp28_present30',        
         (32,__TYPE_PRESENT) : 'sfp28_present33',        
         (33,__TYPE_PRESENT) : 'sfp28_present32',        
         (34,__TYPE_PRESENT) : 'sfp28_present35',        
         (35,__TYPE_PRESENT) : 'sfp28_present34',        
         (36,__TYPE_PRESENT) : 'sfp28_present37',        
         (37,__TYPE_PRESENT) : 'sfp28_present36',        
         (38,__TYPE_PRESENT) : 'sfp28_present39',        
         (39,__TYPE_PRESENT) : 'sfp28_present38',        
         (40,__TYPE_PRESENT) : 'sfp28_present41',        
         (41,__TYPE_PRESENT) : 'sfp28_present40',        
         (42,__TYPE_PRESENT) : 'sfp28_present43',        
         (43,__TYPE_PRESENT) : 'sfp28_present42',        
         (44,__TYPE_PRESENT) : 'sfp28_present45',        
         (45,__TYPE_PRESENT) : 'sfp28_present44',        
         (46,__TYPE_PRESENT) : 'sfp28_present47',        
         (47,__TYPE_PRESENT) : 'sfp28_present46',        
         (48,__TYPE_PRESENT) : 'qsfp28_present49',
         (49,__TYPE_PRESENT) : 'qsfp28_present48',
         (50,__TYPE_PRESENT) : 'qsfp28_present51',
         (51,__TYPE_PRESENT) : 'qsfp28_present50',
         (52,__TYPE_PRESENT) : 'qsfp28_present53',
         (53,__TYPE_PRESENT) : 'qsfp28_present52',
         (54,__TYPE_PRESENT) : 'qsfp28_present55',
         (55,__TYPE_PRESENT) : 'qsfp28_present54',
         ( 0,__TYPE_TX_FAULT) : 'sfp28_fault1',       
         ( 1,__TYPE_TX_FAULT) : 'sfp28_fault0',      
         ( 2,__TYPE_TX_FAULT) : 'sfp28_fault3',        
         ( 3,__TYPE_TX_FAULT) : 'sfp28_fault2',        
         ( 4,__TYPE_TX_FAULT) : 'sfp28_fault5',        
         ( 5,__TYPE_TX_FAULT) : 'sfp28_fault4',        
         ( 6,__TYPE_TX_FAULT) : 'sfp28_fault7',        
         ( 7,__TYPE_TX_FAULT) : 'sfp28_fault6',        
         ( 8,__TYPE_TX_FAULT) : 'sfp28_fault9',        
         ( 9,__TYPE_TX_FAULT) : 'sfp28_fault8',        
         (10,__TYPE_TX_FAULT) : 'sfp28_fault11',        
         (11,__TYPE_TX_FAULT) : 'sfp28_fault10',        
         (12,__TYPE_TX_FAULT) : 'sfp28_fault13',        
         (13,__TYPE_TX_FAULT) : 'sfp28_fault12',        
         (14,__TYPE_TX_FAULT) : 'sfp28_fault15',        
         (15,__TYPE_TX_FAULT) : 'sfp28_fault14',        
         (16,__TYPE_TX_FAULT) : 'sfp28_fault17',        
         (17,__TYPE_TX_FAULT) : 'sfp28_fault16',        
         (18,__TYPE_TX_FAULT) : 'sfp28_fault19',        
         (19,__TYPE_TX_FAULT) : 'sfp28_fault18',        
         (20,__TYPE_TX_FAULT) : 'sfp28_fault21',        
         (21,__TYPE_TX_FAULT) : 'sfp28_fault20',        
         (22,__TYPE_TX_FAULT) : 'sfp28_fault23',        
         (23,__TYPE_TX_FAULT) : 'sfp28_fault22',        
         (24,__TYPE_TX_FAULT) : 'sfp28_fault25',        
         (25,__TYPE_TX_FAULT) : 'sfp28_fault24',        
         (26,__TYPE_TX_FAULT) : 'sfp28_fault27',        
         (27,__TYPE_TX_FAULT) : 'sfp28_fault26',        
         (28,__TYPE_TX_FAULT) : 'sfp28_fault29',        
         (29,__TYPE_TX_FAULT) : 'sfp28_fault28',        
         (30,__TYPE_TX_FAULT) : 'sfp28_fault31',        
         (31,__TYPE_TX_FAULT) : 'sfp28_fault30',        
         (32,__TYPE_TX_FAULT) : 'sfp28_fault33',        
         (33,__TYPE_TX_FAULT) : 'sfp28_fault32',        
         (34,__TYPE_TX_FAULT) : 'sfp28_fault35',        
         (35,__TYPE_TX_FAULT) : 'sfp28_fault34',        
         (36,__TYPE_TX_FAULT) : 'sfp28_fault37',        
         (37,__TYPE_TX_FAULT) : 'sfp28_fault36',        
         (38,__TYPE_TX_FAULT) : 'sfp28_fault39',        
         (39,__TYPE_TX_FAULT) : 'sfp28_fault38',        
         (40,__TYPE_TX_FAULT) : 'sfp28_fault41',        
         (41,__TYPE_TX_FAULT) : 'sfp28_fault40',        
         (42,__TYPE_TX_FAULT) : 'sfp28_fault43',        
         (43,__TYPE_TX_FAULT) : 'sfp28_fault42',        
         (44,__TYPE_TX_FAULT) : 'sfp28_fault45',        
         (45,__TYPE_TX_FAULT) : 'sfp28_fault44',        
         (46,__TYPE_TX_FAULT) : 'sfp28_fault47',        
         (47,__TYPE_TX_FAULT) : 'sfp28_fault46',        
         (48,__TYPE_LPMODE)   : 'qsfp28_lpmode49',
         (49,__TYPE_LPMODE)   : 'qsfp28_lpmode48',
         (50,__TYPE_LPMODE)   : 'qsfp28_lpmode51',
         (51,__TYPE_LPMODE)   : 'qsfp28_lpmode50',
         (52,__TYPE_LPMODE)   : 'qsfp28_lpmode53',
         (53,__TYPE_LPMODE)   : 'qsfp28_lpmode52',
         (54,__TYPE_LPMODE)   : 'qsfp28_lpmode55',
         (55,__TYPE_LPMODE)   : 'qsfp28_lpmode54',
         ( 0,__TYPE_LOS) : 'sfp28_los1',       
         ( 1,__TYPE_LOS) : 'sfp28_los0',      
         ( 2,__TYPE_LOS) : 'sfp28_los3',        
         ( 3,__TYPE_LOS) : 'sfp28_los2',        
         ( 4,__TYPE_LOS) : 'sfp28_los5',        
         ( 5,__TYPE_LOS) : 'sfp28_los4',        
         ( 6,__TYPE_LOS) : 'sfp28_los7',        
         ( 7,__TYPE_LOS) : 'sfp28_los6',        
         ( 8,__TYPE_LOS) : 'sfp28_los9',        
         ( 9,__TYPE_LOS) : 'sfp28_los8',        
         (10,__TYPE_LOS) : 'sfp28_los11',        
         (11,__TYPE_LOS) : 'sfp28_los10',        
         (12,__TYPE_LOS) : 'sfp28_los13',        
         (13,__TYPE_LOS) : 'sfp28_los12',        
         (14,__TYPE_LOS) : 'sfp28_los15',        
         (15,__TYPE_LOS) : 'sfp28_los14',        
         (16,__TYPE_LOS) : 'sfp28_los17',        
         (17,__TYPE_LOS) : 'sfp28_los16',        
         (18,__TYPE_LOS) : 'sfp28_los19',        
         (19,__TYPE_LOS) : 'sfp28_los18',        
         (20,__TYPE_LOS) : 'sfp28_los21',        
         (21,__TYPE_LOS) : 'sfp28_los20',        
         (22,__TYPE_LOS) : 'sfp28_los23',        
         (23,__TYPE_LOS) : 'sfp28_los22',        
         (24,__TYPE_LOS) : 'sfp28_los25',        
         (25,__TYPE_LOS) : 'sfp28_los24',        
         (26,__TYPE_LOS) : 'sfp28_los27',        
         (27,__TYPE_LOS) : 'sfp28_los26',        
         (28,__TYPE_LOS) : 'sfp28_los29',        
         (29,__TYPE_LOS) : 'sfp28_los28',        
         (30,__TYPE_LOS) : 'sfp28_los31',        
         (31,__TYPE_LOS) : 'sfp28_los30',        
         (32,__TYPE_LOS) : 'sfp28_los33',        
         (33,__TYPE_LOS) : 'sfp28_los32',        
         (34,__TYPE_LOS) : 'sfp28_los35',        
         (35,__TYPE_LOS) : 'sfp28_los34',        
         (36,__TYPE_LOS) : 'sfp28_los37',        
         (37,__TYPE_LOS) : 'sfp28_los36',        
         (38,__TYPE_LOS) : 'sfp28_los39',        
         (39,__TYPE_LOS) : 'sfp28_los38',        
         (40,__TYPE_LOS) : 'sfp28_los41',        
         (41,__TYPE_LOS) : 'sfp28_los40',        
         (42,__TYPE_LOS) : 'sfp28_los43',        
         (43,__TYPE_LOS) : 'sfp28_los42',        
         (44,__TYPE_LOS) : 'sfp28_los45',        
         (45,__TYPE_LOS) : 'sfp28_los44',        
         (46,__TYPE_LOS) : 'sfp28_los47',        
         (47,__TYPE_LOS) : 'sfp28_los46',  
         (48,__TYPE_INTERRUPT)   : 'qsfp28_interrupt49',
         (49,__TYPE_INTERRUPT)   : 'qsfp28_interrupt48',
         (50,__TYPE_INTERRUPT)   : 'qsfp28_interrupt51',
         (51,__TYPE_INTERRUPT)   : 'qsfp28_interrupt50',
         (52,__TYPE_INTERRUPT)   : 'qsfp28_interrupt53',
         (53,__TYPE_INTERRUPT)   : 'qsfp28_interrupt52',
         (54,__TYPE_INTERRUPT)   : 'qsfp28_interrupt55',
         (55,__TYPE_INTERRUPT)   : 'qsfp28_interrupt54',     
         ( 0,__TYPE_TX_DISABLE) : 'sfp28_disable1',       
         ( 1,__TYPE_TX_DISABLE) : 'sfp28_disable0',      
         ( 2,__TYPE_TX_DISABLE) : 'sfp28_disable3',        
         ( 3,__TYPE_TX_DISABLE) : 'sfp28_disable2',        
         ( 4,__TYPE_TX_DISABLE) : 'sfp28_disable5',        
         ( 5,__TYPE_TX_DISABLE) : 'sfp28_disable4',        
         ( 6,__TYPE_TX_DISABLE) : 'sfp28_disable7',        
         ( 7,__TYPE_TX_DISABLE) : 'sfp28_disable6',        
         ( 8,__TYPE_TX_DISABLE) : 'sfp28_disable9',        
         ( 9,__TYPE_TX_DISABLE) : 'sfp28_disable8',        
         (10,__TYPE_TX_DISABLE) : 'sfp28_disable11',        
         (11,__TYPE_TX_DISABLE) : 'sfp28_disable10',        
         (12,__TYPE_TX_DISABLE) : 'sfp28_disable13',        
         (13,__TYPE_TX_DISABLE) : 'sfp28_disable12',        
         (14,__TYPE_TX_DISABLE) : 'sfp28_disable15',        
         (15,__TYPE_TX_DISABLE) : 'sfp28_disable14',        
         (16,__TYPE_TX_DISABLE) : 'sfp28_disable17',        
         (17,__TYPE_TX_DISABLE) : 'sfp28_disable16',        
         (18,__TYPE_TX_DISABLE) : 'sfp28_disable19',        
         (19,__TYPE_TX_DISABLE) : 'sfp28_disable18',        
         (20,__TYPE_TX_DISABLE) : 'sfp28_disable21',        
         (21,__TYPE_TX_DISABLE) : 'sfp28_disable20',        
         (22,__TYPE_TX_DISABLE) : 'sfp28_disable23',        
         (23,__TYPE_TX_DISABLE) : 'sfp28_disable22',        
         (24,__TYPE_TX_DISABLE) : 'sfp28_disable25',        
         (25,__TYPE_TX_DISABLE) : 'sfp28_disable24',        
         (26,__TYPE_TX_DISABLE) : 'sfp28_disable27',        
         (27,__TYPE_TX_DISABLE) : 'sfp28_disable26',        
         (28,__TYPE_TX_DISABLE) : 'sfp28_disable29',        
         (29,__TYPE_TX_DISABLE) : 'sfp28_disable28',        
         (30,__TYPE_TX_DISABLE) : 'sfp28_disable31',        
         (31,__TYPE_TX_DISABLE) : 'sfp28_disable30',        
         (32,__TYPE_TX_DISABLE) : 'sfp28_disable33',        
         (33,__TYPE_TX_DISABLE) : 'sfp28_disable32',        
         (34,__TYPE_TX_DISABLE) : 'sfp28_disable35',        
         (35,__TYPE_TX_DISABLE) : 'sfp28_disable34',        
         (36,__TYPE_TX_DISABLE) : 'sfp28_disable37',        
         (37,__TYPE_TX_DISABLE) : 'sfp28_disable36',        
         (38,__TYPE_TX_DISABLE) : 'sfp28_disable39',        
         (39,__TYPE_TX_DISABLE) : 'sfp28_disable38',        
         (40,__TYPE_TX_DISABLE) : 'sfp28_disable41',        
         (41,__TYPE_TX_DISABLE) : 'sfp28_disable40',        
         (42,__TYPE_TX_DISABLE) : 'sfp28_disable43',        
         (43,__TYPE_TX_DISABLE) : 'sfp28_disable42',        
         (44,__TYPE_TX_DISABLE) : 'sfp28_disable45',        
         (45,__TYPE_TX_DISABLE) : 'sfp28_disable44',        
         (46,__TYPE_TX_DISABLE) : 'sfp28_disable47',        
         (47,__TYPE_TX_DISABLE) : 'sfp28_disable46'
    }
    __port_to_eeprom_addr = {
         0 : 'optoe1',
         1 : 'optoe0',
         2 : 'optoe3',
         3 : 'optoe2',
         4 : 'optoe5',
         5 : 'optoe4',
         6 : 'optoe7',
         7 : 'optoe6',
         8 : 'optoe9',
         9 : 'optoe8',
        10 : 'optoe11',
        11 : 'optoe10',
        12 : 'optoe13',
        13 : 'optoe12',
        14 : 'optoe15',
        15 : 'optoe14',
        16 : 'optoe17',
        17 : 'optoe16',
        18 : 'optoe19',
        19 : 'optoe18',
        20 : 'optoe21',
        21 : 'optoe20',
        22 : 'optoe23',
        23 : 'optoe22',
        24 : 'optoe25',
        25 : 'optoe24',
        26 : 'optoe27',
        27 : 'optoe26',
        28 : 'optoe29',
        29 : 'optoe28',
        30 : 'optoe31',
        31 : 'optoe30',
        32 : 'optoe33',
        33 : 'optoe32',
        34 : 'optoe35',
        35 : 'optoe34',
        36 : 'optoe37',
        37 : 'optoe36',
        38 : 'optoe39',
        39 : 'optoe38',
        40 : 'optoe41',
        41 : 'optoe40',
        42 : 'optoe43',
        43 : 'optoe42',
        44 : 'optoe45',
        45 : 'optoe44',
        46 : 'optoe47',
        47 : 'optoe46',
        48 : 'optoe49',#QSFP49
        49 : 'optoe48',#QSFP50
        50 : 'optoe51',#QSFP51
        51 : 'optoe50',#QSFP52
        52 : 'optoe53',#QSFP53
        53 : 'optoe52',#QSFP54
        54 : 'optoe55',#QSFP55
        55 : 'optoe54',#QSFP56
    }
    __previous_port_presence = {}

    __sfp_io_path = '/sys/bus/i2c/devices/i2c-16/16-0020/{0}/port_value'
    __sfp_eeprom_path = '/sys/bus/i2c/devices/i2c-23/23-0050/{0}/{1}'
    port_reset_path = "/sys/bus/i2c/devices/101-0068/p{0}_reset"
    __port_to_eeprom_mapping = {}
    
    @property
    def port_start(self):
        return self.__PORT_START

    @property
    def port_end(self):
        return self.__PORT_END

    @property
    def qsfp_port_start(self):
        return self.__QSFP_PORT_START

    @property
    def qsfp_ports(self):
        return range(self.__QSFP_PORT_START, self.__PORT_COUNT)
    
    @property
    def port_to_eeprom_mapping(self):
         return self.__port_to_eeprom_mapping

    def __init__(self):
        """
            Class initialization
        """
        for x in self.__port_to_eeprom_addr:
            # configure eeprom path
            port_eeprom_path = self.__sfp_eeprom_path.format(self.__port_to_eeprom_addr[x], 'eeprom')
            self.__port_to_eeprom_mapping[x] = port_eeprom_path

    def port_init(self):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if tranceiver is present, False if not
        """
        # init SFP pin
        for port_num in range(self.__SFP_PORT_START, self.__SFP_PORT_END + 1):
            self.sfputil_tx_disable_set(port_num, False)

        # init QSFP pin
        for port_num in range(self.__QSFP_PORT_START, self.__QSFP_PORT_END + 1):
            self.set_low_power_mode(port_num, False)

        #release QSFP reset
        for port_num in range(self.__QSFP_PORT_START, self.__QSFP_PORT_END + 1):
            index = (port_num % 8)
            port_path = self.port_reset_path.format(index)
            try:
                reg_file = open(port_path, 'w')
            except IOError as e:
                print "Error: unable to open file: %s" % str(e)
                return False
            
            reg_file.write('1')
            reg_file.close()

        return True

    def get_count(self, port_num, pin_type, direction):
        """
        :returns: count of SFP and QSFP
        """
        return self.__PORT_COUNT

    def get_presence(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if tranceiver is present, False if not
        """
        # Check for invalid port_num
        if port_num < self.__PORT_START or port_num > self.__PORT_END:
            print("Error: port %d not in %d to %d" % (port_num, self.__PORT_START, self.__PORT_END))
            return False
            
        # get sfp io addr
        sfp_io_addr = self.__port_to_io_addr[(port_num, self.__TYPE_PRESENT)]

        port_ps = self.__sfp_io_path.format(sfp_io_addr)
        
        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()
        
        reg_file.close()
        
        # low active pin
        if int(reg_value) == 0: 
            return True

        return False

    def get_low_power_mode(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if low-power mode enabled, False if disabled
        """
        # Check for invalid port_num
        if port_num < self.__QSFP_PORT_START or port_num > self.__QSFP_PORT_END:
            print("Error: port %d not in %d to %d" % (port_num, self.__QSFP_PORT_START, self.__QSFP_PORT_END))
            return False
        
        # get sfp io addr
        sfp_io_addr = self.__port_to_io_addr[(port_num, self.__TYPE_LPMODE)]

        port_ps = self.__sfp_io_path.format(sfp_io_addr)

        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()

        reg_file.close()

        if int(reg_value) == 1:
            return True
        
        return False

    def set_low_power_mode(self, port_num, lpmode):
        """
        :param port_num: Integer, index of physical port
        :param lpmode: Boolean, True to enable low-power mode, False to disable it
        :returns: Boolean, True if low-power mode set successfully, False if not
        """
        # Check for invalid port_num
        if port_num < self.__QSFP_PORT_START or port_num > self.__QSFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__QSFP_PORT_START, self.__QSFP_PORT_END))
            return False
         
        # get sfp io addr
        sfp_io_addr = self.__port_to_io_addr[(port_num, self.__TYPE_LPMODE)]

        port_ps = self.__sfp_io_path.format(sfp_io_addr)
   
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        if lpmode == True:
            reg_file.write('1')
        else:
            reg_file.write('0')
        
        reg_file.close()
        return True

    def get_transceiver_change_event(self, timeout = 0):
        """
        :param timeout in milliseconds. The method is a blocking call. When timeout is
         zero, it only returns when there is change event, i.e., transceiver plug-in/out
         event. When timeout is non-zero, the function can also return when the timer expires.
         When timer expires, the return status is True and events is empty.
        :returns: (status, events)
        :status: Boolean, True if call successful, False if not;
        :events: dictionary for pysical port index and the SFP status,
        status='1' represent plug in, '0' represent plug out like {'0': '1', '31':'0'}
        """

        raise NotImplementedError

    def reset(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if reset successful, False if not
        """
        # need CPLD support
        return True
        
    def sfputil_tx_disable_set(self, port_num, tx_disable):
        """
        :param port_num: Integer, index of physical port
        :param tx_disable: Boolean, True to disable tx, False to enable it
        :returns: Boolean, True if tx_disable set successfully, False if not
        """
        # Check for invalid port_num
        if port_num < self.__SFP_PORT_START or port_num > self.__SFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__SFP_PORT_START, self.__SFP_PORT_END))
            return False
        
        # get sfp io addr
        sfp_io_addr = self.__port_to_io_addr[(port_num, self.__TYPE_TX_DISABLE)]

        port_ps = self.__sfp_io_path.format(sfp_io_addr)

        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        if tx_disable == True:
            reg_file.write('1')
        else:
            reg_file.write('0')
        
        reg_file.close()
        return True
        
    def sfputil_tx_disable_get(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if tx-disable mode enabled, False if disabled
        """

        # Check for invalid port_num
        if port_num < self.__SFP_PORT_START or port_num > self.__SFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__SFP_PORT_START, self.__SFP_PORT_END))
            return False
        
        # get sfp io addr
        sfp_io_addr = self.__port_to_io_addr[(port_num, self.__TYPE_TX_DISABLE)]

        port_ps = self.__sfp_io_path.format(sfp_io_addr)

        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()

        reg_file.close()

        if int(reg_value) == 1:
            return True
        
        return False
    
    def sfputil_los_get(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if rx-loss detected, False if not
        """
        # Check for invalid port_num
        if port_num < self.__SFP_PORT_START or port_num > self.__SFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__SFP_PORT_START, self.__SFP_PORT_END))
            return False
        
        # get sfp io addr
        sfp_io_addr = self.__port_to_io_addr[(port_num, self.__TYPE_LOS)]

        port_ps = self.__sfp_io_path.format(sfp_io_addr)

        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()

        reg_file.close()

        if int(reg_value) == 1:
            return True
        
        return False

    def sfputil_interrupt_get(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if interrupt is detected, False if not
        """
        # Check for invalid port_num
        if port_num < self.__QSFP_PORT_START or port_num > self.__QSFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__QSFP_PORT_START, self.__QSFP_PORT_END))
            return False
        
        # get sfp io addr
        sfp_io_addr = self.__port_to_io_addr[(port_num, self.__TYPE_INTERRUPT)]

        port_ps = self.__sfp_io_path.format(sfp_io_addr)

        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()

        reg_file.close()

        if int(reg_value) == 1:
            return True
        
        return False

