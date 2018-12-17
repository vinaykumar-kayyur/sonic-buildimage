import threading
import logging
import os
from logging.handlers import SysLogHandler

SYSLOG_IDENT = 'sys-servd'

class MitacLog(object) :
    log = logging.getLogger(SYSLOG_IDENT)
    log.setLevel(logging.DEBUG)

    #https://docs.python.org/2/library/logging.html
    # DEBUG INFO WARNING ERROR CRITICAL
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)-8s %(module)-9s %(funcName)-10s: %(message)s', '%y-%m-%d %H:%M:%S'))
    handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)-8s %(message)s', '%y-%m-%d %H:%M:%S'))
    log.addHandler(handler)

    handler = SysLogHandler(address = '/dev/log')
    #handler.setLevel(logging.INFO)
    handler.setFormatter( logging.Formatter('%(name)s: %(levelname)-8s %(message)s') )
    handler.setFormatter( logging.Formatter('%(name)s: %(message)s') )
    log.addHandler(handler)

def DEBUG(arg): MitacLog.log.debug(arg)
def INFO(arg):  MitacLog.log.info(arg)
def WARN(arg):  MitacLog.log.warn(arg)
def ERR(arg):   MitacLog.log.error(arg)
def CRITICAL(arg): MitacLog.log.critical(arg)

class Led(object):
    def __init__(self, *args):
        self._node  = args[0]
        self._name  = args[1]
        self.ledmap = dict([ (k.upper(), v ) for k, v in args[2].items() ])
        self.val = None
    def set_led(self, val):
        val = val.upper()
        if val == self.val : return
        self.val = val
        try :
            v = self.ledmap[val]
        except KeyError:
            v = None
        INFO( '{0.__class__.__name__}-{0._name}: {1}({2})'.format(self, val, v) )
        if v != None: write_file( self._node,  v )

class State(object):
    """
    We define a state object which provides some utility functions for the
    individual states within the state machine.
    """
    def __init__(self):
        #print 'Processing current state:', str(self)
        self.msg = self.__class__.__name__
        pass
    def on_event(self, event):
        pass
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return self.__class__.__name__
    def __eq__(self, other): 
        return self.__class__.__name__ == other.__class__.__name__

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance

class BoardType(Singleton):
    board_type = 0
    def __init__(self, node = None):
        if(node == None): return
        try:
            self.board_type = cat_file(node, 16)
        except:
            self.board_type = 0

class PsuType(Singleton):
    psu_type = None
    def __init__(self, type = None):
        if type == None: return

        try:
            self.psu_type = type
        except:
            self.psu_type = None

class CommonDev(object):
    def __init__(self, param):
        super(CommonDev, self).__init__()

        self.name  = (param['name'] if 'name' in param else 'unknown_dev').upper()
        self.present = 0

        self.cpld_path  = param['cpld_path']  if 'cpld_path' in param else None

        self.intr_src = param['intr_src']
        self.intr_msk = param['intr_msk']

    def get_intr_src(self):
        return  cat_file( os.path.join(self.cpld_path, self.intr_src), 16)

    def get_intr_msk(self):
        return  cat_file( os.path.join(self.cpld_path, self.intr_msk), 16)

    def set_intr_msk(self, v):
        write_file( os.path.join(self.cpld_path, self.intr_msk), v)

    @property
    def get_present(self):
        return self.present

    def event_handler(self):
        pass

class StateDev(CommonDev):
    def __init__(self, param):
        super(StateDev, self).__init__(param)

        self.state = State()
        self.hwmon_path = param['hwmon_path'] if 'hwmon_path' in param else None
        self.hwmon_ext_path = ''
        if self.hwmon_path :
            try:
                listofdir = [f for f in os.listdir(self.hwmon_path) if os.path.isdir( os.path.join(self.hwmon_path,str(f)))]
                if len(listofdir) :
                    self.hwmon_ext_path = listofdir[0]
            except :
                pass
    def get_intr_src(self):     return  1
    def get_intr_msk(self):     return  0
    def set_intr_msk(self, v):  pass
    def refresh(self):
        pass
    def on_event(self, event):
        pass
    def update_state(self):
        pass
    def get_state(self):
        return self.state
    def dump_dev(self):
        pass

def _threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.setDaemon(True)
        thread.start()
        return thread
    return wrapper

class DevMon(object):
    def __init__(self, *args):
        super(DevMon, self).__init__()
        data = args[0]
        dev_class = args[1]
        self.dev_list = [  dev_class(d) for d in data['devs'] ]

        self.delay_time = float(data['timeout'])/1000 if 'timeout' in data else None
        self.tMonitor = None
        self.shutdown_event = threading.Event()
        self.intr_event     = threading.Event()
        self.handler_list = [self.intr_handler]

    def set_intr_event(self):
        self.intr_event.set()

    def get_intr_src(self):
        return [d.get_intr_src() for d in self.dev_list ]

    def set_intr_msk(self, v):
        [d.set_intr_msk(v) for d in self.dev_list ]

    def get_intr_msk(self):
        return [d.get_intr_msk() for d in self.dev_list ]

    def start_monitor(self):
        if type(self.tMonitor) == type(None):
            self.shutdown_event.clear()
            self.tMonitor = self._dev_monitor_thread()

    def stop_monitor(self):
        if type(self.tMonitor) != type(None):
            self.shutdown_event.set()
            self.intr_event.set()
            self.tMonitor.join()
            self.tMonitor = None

    def intr_handler(self, intr):
        if intr:
            for d in self.dev_list:
                if d.get_intr_src() == 0:
                    d.event_handler()
                    d.set_intr_msk(0)
    def shutdown_func(self):
        pass
    @_threaded
    def _dev_monitor_thread(self):
        while not self.shutdown_event.is_set():
            intr = self.intr_event.wait(self.delay_time)

            if self.shutdown_event.is_set(): break

            self.intr_event.clear()
            [handler(intr) for handler in self.handler_list]

        self.shutdown_func()
        DEBUG('{}: Exit monitoring thread'.format(self.__class__.__name__))

class StateMon(DevMon):
    def __init__(self, *args):
        super(StateMon, self).__init__(*args)

        self.handler_list.append(self.update_all_state)
    def state_change(self):
        pass

    def force_state_change(self) :
        return False

    def get_state(self):
        return [d.get_state() for d in self.dev_list ]

    def dump_devs(self):
        [ d.dump_dev() for d in self.dev_list ]

    def update_all_state(self, intr):
        old_state = self.get_state()
        [d.update_state() for d in self.dev_list ]

        if old_state != self.get_state() or self.force_state_change() :
            self.state_change()

## common function
def cat_file(fstr, base=10):
    try:
        with open(fstr, 'r') as f:
            return int(f.read(), base)
    except IOError:
        pass

def cat_file_str(fstr):
    try:
        with open(fstr, 'r') as f:
            return f.read()
    except IOError:
        pass

def write_file(fstr, v):
    try:
        with open(fstr, 'r+') as f:
            f.write(str(v)+'\n')
    except IOError:
        ERR('write {} to {} fail'.format(v, fstr))
