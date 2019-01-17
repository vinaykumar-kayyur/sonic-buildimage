#!/usr/bin/env python
#
# led_control.py
#
# Platform-specific LED control functionality for SONiC
#

try:
    from sonic_led.led_control_base import LedControlBase
    import os.path
    import time
    import socket
    import swsssdk
except ImportError, e:
    raise ImportError (str(e) + " - required module not found")


class LedControl(LedControlBase):
    """Platform specific LED control class"""

    # SYSTEM(STAT) LED
    SYSTEM_LED_PATH  = "/sys/bus/i2c/devices/1-0070/system_led"

    SYSTEM_LED_OFF   = 0
    SYSTEM_LED_AMBER = 1
    SYSTEM_LED_GREEN = 2

    # PORT LED
    SYNCD_SOCK_PATH = "/var/run/sswsyncd/sswsyncd.socket"

    PORT_TABLE_PREFIX = "PORT_TABLE:"
    PORT_NAME_PREFIX = "Ethernet"

    LED_COLOR_OFF    = 0x00
    LED_COLOR_GREEN  = 0x10
    LED_COLOR_YELLOW = 0x01

    _port_start = 0
    _port_end = 71
    _qsfp_port_start = 48
    _qsfp_port_end = 71

    #    n:  [c,    o, s]
    #
    # n - Internal port number (0,71)
    # c - LED controller (0,1)
    # o - Data Ram offset in CMIC_LEDUPc_DATA_RAM(o)
    # s - Port state (0 - off, 1 - on)
    #
    _port_to_led_mapping = {
        # CMIC_LEDUP0_DATA_RAM
         0:  [0,  160, 0],
         1:  [0,  161, 0],
         2:  [0,  162, 0],
         3:  [0,  163, 0],
         4:  [0,  164, 0],
         5:  [0,  165, 0],
         6:  [0,  166, 0],
         7:  [0,  167, 0],
         8:  [0,  168, 0],
         9:  [0,  169, 0],
        10:  [0,  170, 0],
        11:  [0,  171, 0],
        12:  [0,  172, 0],
        13:  [0,  173, 0],
        14:  [0,  174, 0],
        15:  [0,  175, 0],
        16:  [0,  176, 0],
        17:  [0,  177, 0],
        18:  [0,  178, 0],
        19:  [0,  179, 0],
        20:  [0,  180, 0],
        21:  [0,  181, 0],
        22:  [0,  182, 0],
        23:  [0,  183, 0],
        24:  [0,  184, 0],
        25:  [0,  185, 0],
        26:  [0,  186, 0],
        27:  [0,  187, 0],
        28:  [0,  188, 0],
        29:  [0,  189, 0],
        30:  [0,  190, 0],
        31:  [0,  191, 0],
        32:  [0,  192, 0],
        33:  [0,  193, 0],
        34:  [0,  194, 0],
        35:  [0,  195, 0],
        # CMIC_LEDUP1_DATA_RAM
        36:  [1,  160, 0],
        37:  [1,  161, 0],
        38:  [1,  162, 0],
        39:  [1,  163, 0],
        40:  [1,  164, 0],
        41:  [1,  165, 0],
        42:  [1,  166, 0],
        43:  [1,  167, 0],
        44:  [1,  168, 0],
        45:  [1,  169, 0],
        46:  [1,  170, 0],
        47:  [1,  171, 0],
        48:  [1,  172, 0],#QSFP49
        49:  [1,  172, 0],
        50:  [1,  172, 0],
        51:  [1,  172, 0],
        52:  [1,  176, 0],#QSFP50
        53:  [1,  176, 0],
        54:  [1,  176, 0],
        55:  [1,  176, 0],
        56:  [1,  180, 0],#QSFP51
        57:  [1,  180, 0],
        58:  [1,  180, 0],
        59:  [1,  180, 0],
        60:  [1,  184, 0],#QSFP52
        61:  [1,  184, 0],
        62:  [1,  184, 0],
        63:  [1,  184, 0],
        64:  [1,  188, 0],#QSFP53
        65:  [1,  188, 0],
        66:  [1,  188, 0],
        67:  [1,  188, 0],
        68:  [1,  192, 0],#QSFP54
        69:  [1,  192, 0],
        70:  [1,  192, 0],
        71:  [1,  192, 0],
    }

    _qsfp_nr_sfp_up = {
        172: 0,#QSFP49
        176: 0,#QSFP50
        180: 0,#QSFP51
        184: 0,#QSFP52
        188: 0,#QSFP53
        192: 0,#QSFP54
    }

    swss = None

    @property
    def port_start(self):
        return self._port_start

    @property
    def port_end(self):
        return self._port_end

    @property
    def qsfp_port_start(self):
        return self._qsfp_port_start

    @property
    def qsfp_port_end(self):
        return self._qsfp_port_end

    @property
    def qsfp_ports(self):
        return range(self._qsfp_port_start, self._qsfp_port_end + 1)

    # Concrete implementation of port_link_state_change() method
    def port_link_state_change(self, port, state):
        # Strip "Ethernet" off port name
        if not port.startswith(self.PORT_NAME_PREFIX):
            return

        port_num = int(port[len(self.PORT_NAME_PREFIX):])

        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return

        # Check for port state change
        ostate = self._port_to_led_mapping[port_num][2]
        nstate = int(state == "up")
        if nstate == ostate:
            return
        self._port_to_led_mapping[port_num][2] = nstate

        if port_num < self.qsfp_port_start:
            if nstate:
                speed = self.get_port_speed(port)
                if speed is None or speed < 10000:
                    color = self.LED_COLOR_YELLOW
                else:
                    color = self.LED_COLOR_GREEN
            else:
                color = self.LED_COLOR_OFF
        else:
            x = self._port_to_led_mapping[port_num][1]

            old_nr_sfp_up = self._qsfp_nr_sfp_up[x]
            old_color = self.qsfp_port_led_color(old_nr_sfp_up)

            nr_sfp_up = old_nr_sfp_up - (ostate - nstate)
            color = self.qsfp_port_led_color(nr_sfp_up)

            self._qsfp_nr_sfp_up[x] = nr_sfp_up

            if color == old_color:
                return

        # Create one time socket to prevent blocking
        # access to drivshell for other users (e.g. bcmcmd)
        sock = None
        try:
            # Setup non-blocking socket
            sock = socket.socket(socket.AF_UNIX)
            sock.settimeout(1)
            sock.connect(self.SYNCD_SOCK_PATH)

            # Send setreg command
            setreg = self.get_port_setreg(port_num, color)
            sock.sendall(setreg)

            # Read back reply (e.g. command echo and drivshell>)
            sock.recv(1024)
        except:
            pass
        finally:
            del sock

    # Get QSFP port color
    def qsfp_port_led_color(self, nr_sfp_up):
        if nr_sfp_up >= 4:
            return self.LED_COLOR_GREEN
        elif nr_sfp_up > 0:
            return self.LED_COLOR_YELLOW
        else:
            return self.LED_COLOR_OFF

    # Get drivshell "setreg CMIC_LEDUPc_DATA_RAM(o) v" command
    def get_port_setreg(self, port_num, color):
        return "\nsetreg CMIC_LEDUP{:d}_DATA_RAM({:d}) {:#x}\n".format(
                     self._port_to_led_mapping[port_num][0],
                     self._port_to_led_mapping[port_num][1],
                     color
               )

    # Routines to get physical port speed from APPL_DB
    def get_port_speed(self, port_name):
        port_name = self.PORT_TABLE_PREFIX + port_name
        for i in range(0, 2):
            try:
                speed = self.swss.get(self.swss.APPL_DB, port_name, 'speed')
            except:
                self.fini_swsssdk()
                if i > 0:
                    return None
                self.init_swsssdk()
                if self.swss is None:
                    return None
            else:
                return int(speed)

    def init_swsssdk(self):
        try:
            self.swss = swsssdk.SonicV2Connector()
            self.swss.connect(self.swss.APPL_DB)
        except:
            self.swss = None

    def fini_swsssdk(self):
        try:
            self.swss.close(self.swss.APPL_DB)
            del self.swss
        except:
            return
        finally:
            self.swss = None

    # Initialize with color or turn off all port LEDs
    # optionally waiting indefinitely for socket
    def config_port_leds(self, color = LED_COLOR_OFF, wait_for_sock = False):
        sock = None
        while True:
            try:
                sock = socket.socket(socket.AF_UNIX)
                sock.settimeout(1)
                sock.connect(self.SYNCD_SOCK_PATH)
            except:
                if not wait_for_sock:
                    return False
                while not os.path.exists(self.SYNCD_SOCK_PATH):
                    time.sleep(1)
            else:
                try:
                    for port_num in self._port_to_led_mapping:
                        setreg = self.get_port_setreg(port_num, self.LED_COLOR_OFF)
                        sock.sendall(setreg)
                        sock.recv(1024)
                except:
                    pass
                else:
                    return True
            finally:
                # Do this explicitly to ensure we close soket before retry
                del sock

    # Initialize with color or turn off status LED
    # optionally waiting indefinitely for hardware monitor (hwmon) sysfs path
    def config_system_led(self, color = SYSTEM_LED_OFF, wait_for_hwmon = False):
        while True:
            try:
                with open(self.SYSTEM_LED_PATH, 'w') as f:
                    f.write(str(color))
            except:
                if not wait_for_hwmon:
                    return False
                while not os.path.exists(self.SYSTEM_LED_PATH):
                    time.sleep(1)
            else:
                return True

    # Constructor
    def __init__(self):
        # Initialize front-panel status LED to amber
        self.config_system_led(color = self.SYSTEM_LED_AMBER, wait_for_hwmon = True)

        # Initialize swss APPL_DB communication
        self.init_swsssdk()

        # Turn off port LEDs
        self.config_port_leds(wait_for_sock = True)

        # Initialize front-panel status LED to green
        self.config_system_led(color = self.SYSTEM_LED_GREEN, wait_for_hwmon = True)

    # Destructor
    def __del__(self):
        # Turn off front-panel status LED
        self.config_system_led()

        # Turn off port LEDs
        self.config_port_leds()

        # Finalize swss APPL_DB communication
        self.fini_swsssdk()
