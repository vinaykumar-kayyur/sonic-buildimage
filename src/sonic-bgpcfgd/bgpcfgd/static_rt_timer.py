from .log import log_err, log_debug
from swsssdk import SonicV2Connector
import time

class StaticRouteTimer(object):
    """ This class checks the static routes and deletes those entries that have not been refreshed """
    def __init__(self):
        self.db = SonicV2Connector()
        self.db.connect(self.db.APPL_DB)
        self.timer = None
        self.start = None

    DEFAULT_TIMER = 180
    MAX_TIMER     = 1800

    def set_timer(self):
        """ Check for custom route expiry time in STATIC_ROUTE:EXPIRY_TIME """
        timer = self.db.get(self.db.APPL_DB, "STATIC_ROUTE:EXPIRY_TIME", "time")
        if timer is not None:
            timer = int(timer)     
            if timer > 0 and timer <= self.MAX_TIMER:
                self.timer = timer
                return
            log_err("Custom static route expiry time of {}s is invalid!".format(timer))
        return

    def alarm(self):
        """ Clear unrefreshed static routes """
        static_routes = self.db.keys(self.db.APPL_DB, "STATIC_ROUTE:*:*")
        if static_routes is not None:
            for sr in static_routes:
                refresh = self.db.get(self.db.APPL_DB, sr, "refresh")
                val = sr.split(":")
                if refresh == "true":
                    self.db.set(self.db.APPL_DB, sr, "refresh", "false")
                    log_debug("Refresh status of static route {}:{} is set to false".format(val[0], val[1]))
                else:
                    self.db.delete(self.db.APPL_DB, sr)
                    log_debug("Static route {}:{} deleted".format(val[0], val[1]))
        self.start = time.time()
        return

    def run(self):
        while True:
            self.set_timer()
            log_debug("Static route expiry set to {}s".format(self.timer))
            if self.timer:
                time.sleep(self.timer)
                self.alarm()
            else:
                time.sleep(1)
                if time.time() - self.start == self.DEFAULT_TIMER:
                    self.alarm()
