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
    __GPIO_PIN_START = 48
    __GPIO_PIN_END = 271
    __SFP_EEPROM_ADDR = 50

    __TYPE_PRESENT = 'present'
    __TYPE_LPMODE = 'lpmode'
    __TYPE_LOS = 'los'
    __TYPE_TX_DISABLE = 'tx_disable'
    __TYPE_TX_FAULT = 'tx_fault'
    __TYPE_INTERRUPT = 'interrupt'

    __GPIO_D_IN = 'in'
    __GPIO_D_OUT = 'out'
    __GPIO_D_HI = 'high'
    __GPIO_D_LOW = 'low'

    __port_to_gpio_addr = {
         ( 0,__TYPE_PRESENT) : 201,
         ( 1,__TYPE_PRESENT) : 200,
         ( 2,__TYPE_PRESENT) : 203,
         ( 3,__TYPE_PRESENT) : 202,
         ( 4,__TYPE_PRESENT) : 205,
         ( 5,__TYPE_PRESENT) : 204,
         ( 6,__TYPE_PRESENT) : 207,
         ( 7,__TYPE_PRESENT) : 206,
         ( 8,__TYPE_PRESENT) : 193,
         ( 9,__TYPE_PRESENT) : 192,
         (10,__TYPE_PRESENT) : 195,
         (11,__TYPE_PRESENT) : 194,
         (12,__TYPE_PRESENT) : 197,
         (13,__TYPE_PRESENT) : 196,
         (14,__TYPE_PRESENT) : 199,
         (15,__TYPE_PRESENT) : 198,
         (16,__TYPE_PRESENT) : 217,
         (17,__TYPE_PRESENT) : 216,
         (18,__TYPE_PRESENT) : 219,
         (19,__TYPE_PRESENT) : 218,
         (20,__TYPE_PRESENT) : 221,
         (21,__TYPE_PRESENT) : 220,
         (22,__TYPE_PRESENT) : 223,
         (23,__TYPE_PRESENT) : 222,
         (24,__TYPE_PRESENT) : 209,
         (25,__TYPE_PRESENT) : 208,
         (26,__TYPE_PRESENT) : 211,
         (27,__TYPE_PRESENT) : 210,
         (28,__TYPE_PRESENT) : 213,
         (29,__TYPE_PRESENT) : 212,
         (30,__TYPE_PRESENT) : 215,
         (31,__TYPE_PRESENT) : 214,
         (32,__TYPE_PRESENT) : 233,
         (33,__TYPE_PRESENT) : 232,
         (34,__TYPE_PRESENT) : 235,
         (35,__TYPE_PRESENT) : 234,
         (36,__TYPE_PRESENT) : 237,
         (37,__TYPE_PRESENT) : 236,
         (38,__TYPE_PRESENT) : 239,
         (39,__TYPE_PRESENT) : 238,
         (40,__TYPE_PRESENT) : 225,
         (41,__TYPE_PRESENT) : 224,
         (42,__TYPE_PRESENT) : 227,
         (43,__TYPE_PRESENT) : 226,
         (44,__TYPE_PRESENT) : 229,
         (45,__TYPE_PRESENT) : 228,
         (46,__TYPE_PRESENT) : 231,
         (47,__TYPE_PRESENT) : 230,
         (48,__TYPE_PRESENT) : 265,
         (49,__TYPE_PRESENT) : 264,
         (50,__TYPE_PRESENT) : 267,
         (51,__TYPE_PRESENT) : 266,
         (52,__TYPE_PRESENT) : 269,
         (53,__TYPE_PRESENT) : 268,
         (54,__TYPE_PRESENT) : 271,
         (55,__TYPE_PRESENT) : 270,
         ( 0,__TYPE_TX_FAULT) : 57,
         ( 1,__TYPE_TX_FAULT) : 56,
         ( 2,__TYPE_TX_FAULT) : 59,
         ( 3,__TYPE_TX_FAULT) : 58,
         ( 4,__TYPE_TX_FAULT) : 61,
         ( 5,__TYPE_TX_FAULT) : 60,
         ( 6,__TYPE_TX_FAULT) : 63,
         ( 7,__TYPE_TX_FAULT) : 62,
         ( 8,__TYPE_TX_FAULT) : 49,
         ( 9,__TYPE_TX_FAULT) : 48,
         (10,__TYPE_TX_FAULT) : 51,
         (11,__TYPE_TX_FAULT) : 50,
         (12,__TYPE_TX_FAULT) : 53,
         (13,__TYPE_TX_FAULT) : 52,
         (14,__TYPE_TX_FAULT) : 55,
         (15,__TYPE_TX_FAULT) : 54,
         (16,__TYPE_TX_FAULT) : 73,
         (17,__TYPE_TX_FAULT) : 72,
         (18,__TYPE_TX_FAULT) : 75,
         (19,__TYPE_TX_FAULT) : 74,
         (20,__TYPE_TX_FAULT) : 77,
         (21,__TYPE_TX_FAULT) : 76,
         (22,__TYPE_TX_FAULT) : 79,
         (23,__TYPE_TX_FAULT) : 78,
         (24,__TYPE_TX_FAULT) : 65,
         (25,__TYPE_TX_FAULT) : 64,
         (26,__TYPE_TX_FAULT) : 67,
         (27,__TYPE_TX_FAULT) : 66,
         (28,__TYPE_TX_FAULT) : 69,
         (29,__TYPE_TX_FAULT) : 68,
         (30,__TYPE_TX_FAULT) : 71,
         (31,__TYPE_TX_FAULT) : 70,
         (32,__TYPE_TX_FAULT) : 89,
         (33,__TYPE_TX_FAULT) : 88,
         (34,__TYPE_TX_FAULT) : 91,
         (35,__TYPE_TX_FAULT) : 90,
         (36,__TYPE_TX_FAULT) : 93,
         (37,__TYPE_TX_FAULT) : 92,
         (38,__TYPE_TX_FAULT) : 95,
         (39,__TYPE_TX_FAULT) : 94,
         (40,__TYPE_TX_FAULT) : 81,
         (41,__TYPE_TX_FAULT) : 80,
         (42,__TYPE_TX_FAULT) : 83,
         (43,__TYPE_TX_FAULT) : 82,
         (44,__TYPE_TX_FAULT) : 85,
         (45,__TYPE_TX_FAULT) : 84,
         (46,__TYPE_TX_FAULT) : 87,
         (47,__TYPE_TX_FAULT) : 86,
         (48,__TYPE_LPMODE)   : 241,
         (49,__TYPE_LPMODE)   : 240,
         (50,__TYPE_LPMODE)   : 243,
         (51,__TYPE_LPMODE)   : 242,
         (52,__TYPE_LPMODE)   : 245,
         (53,__TYPE_LPMODE)   : 244,
         (54,__TYPE_LPMODE)   : 247,
         (55,__TYPE_LPMODE)   : 246,
         ( 0,__TYPE_LOS) : 105,
         ( 1,__TYPE_LOS) : 104,
         ( 2,__TYPE_LOS) : 107,
         ( 3,__TYPE_LOS) : 106,
         ( 4,__TYPE_LOS) : 109,
         ( 5,__TYPE_LOS) : 108,
         ( 6,__TYPE_LOS) : 111,
         ( 7,__TYPE_LOS) : 110,
         ( 8,__TYPE_LOS) : 97,
         ( 9,__TYPE_LOS) : 96,
         (10,__TYPE_LOS) : 99,
         (11,__TYPE_LOS) : 98,
         (12,__TYPE_LOS) : 101,
         (13,__TYPE_LOS) : 100,
         (14,__TYPE_LOS) : 103,
         (15,__TYPE_LOS) : 102,
         (16,__TYPE_LOS) : 121,
         (17,__TYPE_LOS) : 120,
         (18,__TYPE_LOS) : 123,
         (19,__TYPE_LOS) : 122,
         (20,__TYPE_LOS) : 125,
         (21,__TYPE_LOS) : 124,
         (22,__TYPE_LOS) : 127,
         (23,__TYPE_LOS) : 126,
         (24,__TYPE_LOS) : 113,
         (25,__TYPE_LOS) : 112,
         (26,__TYPE_LOS) : 115,
         (27,__TYPE_LOS) : 114,
         (28,__TYPE_LOS) : 117,
         (29,__TYPE_LOS) : 116,
         (30,__TYPE_LOS) : 119,
         (31,__TYPE_LOS) : 118,
         (32,__TYPE_LOS) : 137,
         (33,__TYPE_LOS) : 136,
         (34,__TYPE_LOS) : 139,
         (35,__TYPE_LOS) : 138,
         (36,__TYPE_LOS) : 141,
         (37,__TYPE_LOS) : 140,
         (38,__TYPE_LOS) : 143,
         (39,__TYPE_LOS) : 142,
         (40,__TYPE_LOS) : 129,
         (41,__TYPE_LOS) : 128,
         (42,__TYPE_LOS) : 131,
         (43,__TYPE_LOS) : 130,
         (44,__TYPE_LOS) : 133,
         (45,__TYPE_LOS) : 132,
         (46,__TYPE_LOS) : 135,
         (47,__TYPE_LOS) : 134,
         (48,__TYPE_INTERRUPT)   : 257,
         (49,__TYPE_INTERRUPT)   : 256,
         (50,__TYPE_INTERRUPT)   : 259,
         (51,__TYPE_INTERRUPT)   : 258,
         (52,__TYPE_INTERRUPT)   : 261,
         (53,__TYPE_INTERRUPT)   : 260,
         (54,__TYPE_INTERRUPT)   : 263,
         (55,__TYPE_INTERRUPT)   : 262,
         ( 0,__TYPE_TX_DISABLE) : 153,
         ( 1,__TYPE_TX_DISABLE) : 152,
         ( 2,__TYPE_TX_DISABLE) : 155,
         ( 3,__TYPE_TX_DISABLE) : 154,
         ( 4,__TYPE_TX_DISABLE) : 157,
         ( 5,__TYPE_TX_DISABLE) : 156,
         ( 6,__TYPE_TX_DISABLE) : 159,
         ( 7,__TYPE_TX_DISABLE) : 158,
         ( 8,__TYPE_TX_DISABLE) : 145,
         ( 9,__TYPE_TX_DISABLE) : 144,
         (10,__TYPE_TX_DISABLE) : 147,
         (11,__TYPE_TX_DISABLE) : 146,
         (12,__TYPE_TX_DISABLE) : 149,
         (13,__TYPE_TX_DISABLE) : 148,
         (14,__TYPE_TX_DISABLE) : 151,
         (15,__TYPE_TX_DISABLE) : 150,
         (16,__TYPE_TX_DISABLE) : 169,
         (17,__TYPE_TX_DISABLE) : 168,
         (18,__TYPE_TX_DISABLE) : 171,
         (19,__TYPE_TX_DISABLE) : 170,
         (20,__TYPE_TX_DISABLE) : 173,
         (21,__TYPE_TX_DISABLE) : 172,
         (22,__TYPE_TX_DISABLE) : 175,
         (23,__TYPE_TX_DISABLE) : 174,
         (24,__TYPE_TX_DISABLE) : 161,
         (25,__TYPE_TX_DISABLE) : 160,
         (26,__TYPE_TX_DISABLE) : 163,
         (27,__TYPE_TX_DISABLE) : 162,
         (28,__TYPE_TX_DISABLE) : 165,
         (29,__TYPE_TX_DISABLE) : 164,
         (30,__TYPE_TX_DISABLE) : 167,
         (31,__TYPE_TX_DISABLE) : 166,
         (32,__TYPE_TX_DISABLE) : 185,
         (33,__TYPE_TX_DISABLE) : 184,
         (34,__TYPE_TX_DISABLE) : 187,
         (35,__TYPE_TX_DISABLE) : 186,
         (36,__TYPE_TX_DISABLE) : 189,
         (37,__TYPE_TX_DISABLE) : 188,
         (38,__TYPE_TX_DISABLE) : 191,
         (39,__TYPE_TX_DISABLE) : 190,
         (40,__TYPE_TX_DISABLE) : 177,
         (41,__TYPE_TX_DISABLE) : 176,
         (42,__TYPE_TX_DISABLE) : 179,
         (43,__TYPE_TX_DISABLE) : 178,
         (44,__TYPE_TX_DISABLE) : 181,
         (45,__TYPE_TX_DISABLE) : 180,
         (46,__TYPE_TX_DISABLE) : 183,
         (47,__TYPE_TX_DISABLE) : 182
    }
    __port_to_eeprom_addr = {
         0 : '33-0050',
         1 : '32-0050',
         2 : '35-0050',
         3 : '34-0050',
         4 : '37-0050',
         5 : '36-0050',
         6 : '39-0050',
         7 : '38-0050',
         8 : '41-0050',
         9 : '40-0050',
        10 : '43-0050',
        11 : '42-0050',
        12 : '45-0050',
        13 : '44-0050',
        14 : '47-0050',
        15 : '46-0050',
        16 : '49-0050',
        17 : '48-0050',
        18 : '51-0050',
        19 : '50-0050',
        20 : '53-0050',
        21 : '52-0050',
        22 : '55-0050',
        23 : '54-0050',
        24 : '57-0050',
        25 : '56-0050',
        26 : '59-0050',
        27 : '58-0050',
        28 : '61-0050',
        29 : '60-0050',
        30 : '63-0050',
        31 : '62-0050',
        32 : '65-0050',
        33 : '64-0050',
        34 : '67-0050',
        35 : '66-0050',
        36 : '69-0050',
        37 : '68-0050',
        38 : '71-0050',
        39 : '70-0050',
        40 : '73-0050',
        41 : '72-0050',
        42 : '75-0050',
        43 : '74-0050',
        44 : '77-0050',
        45 : '76-0050',
        46 : '79-0050',
        47 : '78-0050',
        48 : '81-0050',#QSFP49
        49 : '80-0050',#QSFP50
        50 : '83-0050',#QSFP51
        51 : '82-0050',#QSFP52
        52 : '85-0050',#QSFP53
        53 : '84-0050',#QSFP54
        54 : '87-0050',#QSFP55
        55 : '86-0050',#QSFP56
    }
    __previous_port_presence = {}

    __gpio_path = '/sys/class/gpio/gpio{0}/value'
    __gpio_path_direction = '/sys/class/gpio/gpio{0}/direction'
    __gpio_path_export = 'echo {0} > /sys/class/gpio/export'
    __gpio_path_unexport = 'echo {0} > /sys/class/gpio/unexport'
    __sfp_eeprom_path = '/sys/bus/i2c/devices/{0}/{1}'
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

    def _gpio_direction_set(self, gpio_pin_num, direction):
        """
        :param gpio_pin_num :
        :param direction : valid value - "in" , "out", "high", "low"
        Note : gpio_pin_num should be exported before set direction
        """
        # Check for invalid gpio_pin_num
        if gpio_pin_num < self.__GPIO_PIN_START or gpio_pin_num > self.__GPIO_PIN_END:
            print("Error: gpio_pin_num %d not in %d to %d" % (gpio_pin_num,
                   self.__GPIO_PIN_START, self.__GPIO_PIN_END))
            return

        port_ps = self.__gpio_path_direction.format(gpio_pin_num)

        try:
            reg_file = open(port_ps, 'r+')
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return
        # read direction if the direction is the same with configured direction, skip it
        reg_value = reg_file.readline().rstrip()
        # low active pin
        if str(reg_value) == str(direction):
            return

        #toggle reset, set direction
        reg_file.seek(0)
        reg_file.write(str(direction))
        reg_file.close()

    def _gpio_export(self, gpio_pin_num):
        """
        :param gpio_pin_num : the gpio_pin is going to be exported
        :
        """
        # check gpio pin range
        if gpio_pin_num < self.__GPIO_PIN_START or gpio_pin_num > self.__GPIO_PIN_END:
            print("Error: gpio pin %d not in" % (gpio_pin_num, self.__GPIO_PIN_START, self.__GPIO_PIN_END))
            return

        port_ps = self.__gpio_path_export.format(gpio_pin_num)

        process = Popen(port_ps, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_export exec fail, reason = %s" % stderr)

    def _gpio_unexport(self, gpio_pin_num):
        """
        :param gpio_pin_num : the gpio_pin is going to be unexported
        :
        """
        # check gpio pin range
        if gpio_pin_num < self.__GPIO_PIN_START or gpio_pin_num > self.__GPIO_PIN_END:
            print("Error: gpio pin %d not in" % (gpio_pin_num, self.__GPIO_PIN_START, self.__GPIO_PIN_END))
            return

        port_ps = self.__gpio_path_unexport.format(gpio_pin_num)
        process = Popen(port_ps, stdout=PIPE, stderr=PIPE, shell= True)
        stdout, stderr = process.communicate()
        if stderr:
            print("_gpio_unexport exec fail, reason = %s" % stderr)

    def port_init(self):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if tranceiver is present, False if not
        """
        try:
            # init SFP pin
            for port_num in range(self.__SFP_PORT_START, self.__SFP_PORT_END + 1):
                gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_TX_DISABLE)]
                try:
                    # export GPIO pin
                    self._gpio_export(gpio_pin_num)

                    # init tx_disable pin to enable port
                    self._gpio_direction_set(gpio_pin_num, self.__GPIO_D_LOW)
                finally:
                    self._gpio_unexport(gpio_pin_num)

            # init QSFP pin
            for port_num in range(self.__QSFP_PORT_START, self.__QSFP_PORT_END + 1):
                gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_LPMODE)]
                try:
                    # export GPIO pin
                    self._gpio_export(gpio_pin_num)

                    # init lp_mode pin to enable port
                    self._gpio_direction_set(gpio_pin_num, self.__GPIO_D_LOW)
                finally:
                    self._gpio_unexport(gpio_pin_num)
            #release QSFP reset
	    for port_num in range(self.__QSFP_PORT_START, self.__QSFP_PORT_END + 1):
		index = (port_num % 8)
	        path = self.port_reset_path
		port_path = path.format(index)
                try:
		    reg_file = open(port_path, 'w')
		except IOError as e:
		    print "Error: unable to open file: %s" % str(e)
		    return False
                reg_file.write('1')
                reg_file.close()


        except Exception as e:
            print("GPIO init FAIL, exception = %s" % str(e))
            return False


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

        # get gpio pin num
        gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_PRESENT)]

        try:
            # export GPIO pin
            self._gpio_export(gpio_pin_num)

            # set direction
            self._gpio_direction_set(gpio_pin_num, self.__GPIO_D_IN)

            # read value
            port_ps = self.__gpio_path.format(gpio_pin_num)

            try:
                reg_file = open(port_ps)
            except IOError as e:
                print("Error: unable to open file: %s" % str(e))
                return False

            reg_value = reg_file.readline().rstrip()
            # low active pin
            if int(reg_value) == 0:
                return True

            return False
        finally:
            self._gpio_unexport(gpio_pin_num)

    def get_low_power_mode(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if low-power mode enabled, False if disabled
        """

        # Check for invalid port_num
        if port_num >= self.__SFP_PORT_START and port_num <= self.__SFP_PORT_END:
            return False

        # get gpio pin num
        gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_LPMODE)]

        try:
            # export GPIO pin
            self._gpio_export(gpio_pin_num)

            # read value
            port_ps = self.__gpio_path.format(gpio_pin_num)
            try:
                reg_file = open(port_ps)
            except IOError as e:
                print("Error: unable to open file: %s" % str(e))
                return False

            reg_value = reg_file.readline().rstrip()
            if int(reg_value) == 0:
                return True

            return False
        finally:
            self._gpio_unexport(gpio_pin_num)

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

        # get gpio pin num
        if port_num >= self.__SFP_PORT_START and port_num <= self.__SFP_PORT_END:
            gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_TX_DISABLE)]
        else:
            gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_LPMODE)]

        try:
            # export GPIO pin
            self._gpio_export(gpio_pin_num)

            # set direction and output value
            if lpmode == True:
                self._gpio_direction_set(gpio_pin_num, self.__GPIO_D_HI)
            else:
                self._gpio_direction_set(gpio_pin_num, self.__GPIO_D_LOW)
            return True
        finally:
            self._gpio_unexport(gpio_pin_num)

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

        # get gpio pin num
        gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_TX_DISABLE)]

        try:
            # export GPIO pin
            self._gpio_export(gpio_pin_num)

            # set direction and output value
            if tx_disable == True:
                self._gpio_direction_set(gpio_pin_num, self.__GPIO_D_HI)
            else:
                self._gpio_direction_set(gpio_pin_num, self.__GPIO_D_LOW)
            return True
        finally:
            self._gpio_unexport(gpio_pin_num)

    def sfputil_tx_disable_get(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if tx-disable mode enabled, False if disabled
        """

        # Check for invalid port_num
        if port_num < self.__SFP_PORT_START or port_num > self.__SFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__SFP_PORT_START, self.__SFP_PORT_END))
            return False

        # get gpio pin num
        gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_TX_DISABLE)]

        try:
            # export GPIO pin
            self._gpio_export(gpio_pin_num)

            # read value
            port_ps = self.__gpio_path.format(gpio_pin_num)
            try:
                reg_file = open(port_ps)
            except IOError as e:
                print("Error: unable to open file: %s" % str(e))
                return False

            reg_value = reg_file.readline().rstrip()
            if int(reg_value) == 1:
                return True

            return False
        finally:
            self._gpio_unexport(gpio_pin_num)

    def sfputil_los_get(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if rx-loss detected, False if not
        """

        # Check for invalid port_num
        if port_num < self.__SFP_PORT_START or port_num > self.__SFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__SFP_PORT_START, self.__SFP_PORT_END))
            return False

        # get gpio pin num
        gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_LOS)]

        try:
            # export GPIO pin
            self._gpio_export(gpio_pin_num)

            # read value
            port_ps = self.__gpio_path.format(gpio_pin_num)
            try:
                reg_file = open(port_ps)
            except IOError as e:
                print("Error: unable to open file: %s" % str(e))
                return False

            reg_value = reg_file.readline().rstrip()
            if int(reg_value) == 1:
                return True

            return False
        finally:
            self._gpio_unexport(gpio_pin_num)

    def sfputil_interrupt_get(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if interrupt is detected, False if not
        """

        # Check for invalid port_num
        if port_num < self.__QSFP_PORT_START or port_num > self.__QSFP_PORT_END:
            print("Error: port %d not in range %d to %d" % (port_num, self.__QSFP_PORT_START, self.__QSFP_PORT_END))
            return False

        # get gpio pin num
        gpio_pin_num = self.__port_to_gpio_addr[(port_num, self.__TYPE_INTERRUPT)]

        try:
            # export GPIO pin
            self._gpio_export(gpio_pin_num)

            # read value
            port_ps = self.__gpio_path.format(gpio_pin_num)
            try:
                reg_file = open(port_ps)
            except IOError as e:
                print("Error: unable to open file: %s" % str(e))
                return False

            reg_value = reg_file.readline().rstrip()
            if int(reg_value) == 1:
                return True

            return False
        finally:
            self._gpio_unexport(gpio_pin_num)

