#
# psuutil.py
# Platform-specific PSU status interface for SONiC
#

import os
import logging


try:
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    def __init__(self):
        PsuBase.__init__(self)
        # DX010 PSU pin mapping
        self.psu = [
            {'base': self.get_gpio_base()},
            {'abs':27, 'power':22},
            {'abs':28, 'power':25}
        ]

    def get_gpio_base(self):
        sys_gpio_dir = "/sys/class/gpio"
        try:
            for r in os.listdir(sys_gpio_dir):
                if "gpiochip" in r:
                    return int(r[8:],10)
        except Exception as error:
            logging.error("Unable to get gpio base")


    def init_psu_gpio(self, pinnum):
        # export pin, input as default
        gpio_base = self.psu[0]['base']
        export_file = "/sys/class/gpio/export"
        try:
            with open(export_file, 'w') as fd:
                fd.write(str(gpio_base+pinnum))
        except Exception as error:
            logging.error("Unable to export gpio " + str(gpio_base+pinnum))


    # Get a psu status and presence
    def read_psu_statuses(self, pinnum):
        sys_gpio_dir = "/sys/class/gpio"
        gpio_base = self.psu[0]['base']
        retval = 'ERR'

        gpio_dir = sys_gpio_dir + '/gpio' + str(gpio_base+pinnum)
        gpio_file = gpio_dir + "/value"

        # init gpio 
        if (not os.path.isdir(gpio_dir)):
            self.init_psu_gpio(pinnum)

        try:
            with open(gpio_file, 'r') as fd:
                retval = fd.read()
        except Exception as error:
            logging.error("Unable to open " + gpio_file + "file !")

        retval = retval.rstrip('\r\n')
        return retval

    def get_num_psus(self):
        """
        Retrieves the number of PSUs available on the device
        :return: An integer, the number of PSUs available on the device
         """
        DX010_MAX_PSUS = 2
        return DX010_MAX_PSUS

    def get_psu_status(self, index):
        """
        Retrieves the oprational status of power supply unit (PSU) defined
                by index <index>
        :param index: An integer, index of the PSU of which to query status
        :return: Boolean, True if PSU is operating properly, False if PSU is\
        faulty
        """
        status = 0
        psu_status = self.read_psu_statuses(self.psu[index]['power'])
        if (psu_status != 'ERR'):
            psu_status = int(psu_status, 10)
            # Check for PSU status
            if (psu_status == 1):
                    status = 1

        return status

    def get_psu_presence(self, index):
        """
        Retrieves the presence status of power supply unit (PSU) defined
                by index <index>
        :param index: An integer, index of the PSU of which to query status
        :return: Boolean, True if PSU is plugged, False if not
        """
        status = 0
        psu_absence = self.read_psu_statuses(self.psu[index]['abs'])
        if (psu_absence != 'ERR'):
            psu_absence = (int(psu_absence, 10))
            # Check for PSU presence
            if (psu_absence == 0):
                    status = 1

        return status
