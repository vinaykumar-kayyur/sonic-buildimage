
from commonlib import *

class MiscDev(CommonDev):
    def __init__(self, param):
        super(MiscDev, self).__init__(param)
        self.present = 1
    def event_handler(self):
        WARN( '{0.name} event_handler'.format(self)  )

class MiscDevMon(DevMon):
    _config_key = 'mon_misc'
    def __init__(self, data):
        super(MiscDevMon, self).__init__(data, MiscDev)
