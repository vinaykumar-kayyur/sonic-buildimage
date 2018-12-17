import time
import copy
import os

from commonlib import *

FAN_PRESENT    = 0

PWM_MIN = 38
PWM_MAX = 255
INLET_MIN_SPEED_MIN = 2510
INLET_MIN_SPEED_MAX = 3910
INLET_MAX_SPEED_MIN = 19260
INLET_MAX_SPEED_MAX = 23540
INLET_MAX_SLOPE = ((INLET_MAX_SPEED_MAX - INLET_MIN_SPEED_MAX)/(PWM_MAX - PWM_MIN))
INLET_MIN_SLOPE = ((INLET_MAX_SPEED_MIN - INLET_MIN_SPEED_MIN)/(PWM_MAX - PWM_MIN))
INLET_MAX_SPEED = lambda _pwm : ((INLET_MAX_SLOPE * (_pwm - PWM_MIN)) + INLET_MIN_SPEED_MAX)
INLET_MIN_SPEED = lambda _pwm : ((INLET_MIN_SLOPE * (_pwm - PWM_MIN)) + INLET_MIN_SPEED_MIN)

#/* if only one fan in a fan module, do not care below values */
OUTLET_MIN_SPEED_MIN = 2615
OUTLET_MIN_SPEED_MAX = 4015
OUTLET_MAX_SPEED_MIN = 19890
OUTLET_MAX_SPEED_MAX = 24310
OUTLET_MAX_SLOPE = ((OUTLET_MAX_SPEED_MAX - OUTLET_MIN_SPEED_MAX)/(PWM_MAX - PWM_MIN))
OUTLET_MIN_SLOPE = ((OUTLET_MAX_SPEED_MIN - OUTLET_MIN_SPEED_MIN)/(PWM_MAX - PWM_MIN))
OUTLET_MAX_SPEED = lambda _pwm: ((OUTLET_MAX_SLOPE * (_pwm - PWM_MIN)) + OUTLET_MIN_SPEED_MAX)
OUTLET_MIN_SPEED = lambda _pwm: ((OUTLET_MIN_SLOPE * (_pwm - PWM_MIN)) + OUTLET_MIN_SPEED_MIN)

EVT_UNPLUG = 'evt_unplug'
EVT_PLUG   = 'evt_plug'
EVT_PWM    = 'evt_pwm'
EVT_NORMAL = 'evt_normal'
EVT_FAIL   = 'evt_fail'
EVT_RETRY  = 'evt_retry'
EVT_POLL   = 'evt_poll'

FAN_INIT_RETRY = 5
FAN_PWM_RETRY  = 6
FAN_FAILED_RETRY = 3

class UnplugState(State):
    def __init__(self):
        self.msg = 'Unplugged'
    def on_event(self, event):
        evtmap = {
            EVT_PLUG: InitState(),
        }
        return evtmap[event]  if event in evtmap else self

class InitState(State):
    def __init__(self):
        self.msg = 'Plugged'
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG: UnplugState(),
            EVT_NORMAL: NormalState(),
            EVT_FAIL  : FailState(),
        }
        return evtmap[event]  if event in evtmap else self

class NormalState(State):
    def __init__(self):
        self.msg = 'Plugged and normal'
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG: UnplugState(),
            EVT_PWM   : PwmState(),
            EVT_RETRY : FailRetryState(),
        }
        return evtmap[event]  if event in evtmap else self

class PwmState(State):
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG: UnplugState(),
            EVT_NORMAL: NormalState(),
            EVT_FAIL  : FailState(),
        }
        return evtmap[event]  if event in evtmap else self

class FailState(State):
    def __init__(self):
        self.msg = 'Fail'
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG : UnplugState(),
            EVT_NORMAL : NormalState(),
        }
        return evtmap[event]  if event in evtmap else self

class FailRetryState(State):
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG: UnplugState(),
            EVT_NORMAL: NormalState(),
            EVT_PWM   : PwmState(),
            EVT_FAIL  : FailState(),
        }
        return evtmap[event]  if event in evtmap else self

_NUM_ROTOR = 2
class FanDev(StateDev):
    def __init__(self, param):
        super(FanDev, self).__init__(param)

        self.fan_input = [param['fan_input'][i] for i in range(_NUM_ROTOR)]
        self.pwms      = [param['pwm'][i] for i in range(_NUM_ROTOR)]
        self.pwm_enable= [param['pwm_enable'][i] for i in range(_NUM_ROTOR)]
        self.present_node = param['present']
        self.type_node = param['type']

        ledmap = {
            'OFF': 0,
            'GREEN': 1,
            'AMBER': 2
        }
        self.led = Led( os.path.join(self.cpld_path, param['tray_led']), self.name, ledmap)
        self.led.set_led('OFF')

        self.rpm = [0]*_NUM_ROTOR
        self.pwm = [0]*_NUM_ROTOR
        self.state = UnplugState()
        self.type = None
        self.retry_count = 0

        [ write_file(os.path.join(self.hwmon_path, self.hwmon_ext_path, p), 1)  for p in self.pwm_enable ]

    def refresh_rpm(self):
        self.rpm = [  cat_file(os.path.join(self.hwmon_path, self.hwmon_ext_path, r))  for r in self.fan_input ]

    def refresh_pwm(self):
        self.pwm = [  cat_file(os.path.join(self.hwmon_path, self.hwmon_ext_path, p))  for p in self.pwms ]

    def refresh_present(self):
        v = cat_file( os.path.join(self.cpld_path, self.present_node), 16)
        self.present = 1 if v == FAN_PRESENT else 0

    def refresh(self):
        self.refresh_present()
        self.refresh_pwm()
        self.refresh_rpm()

    def update_type(self):
        self.type = cat_file( os.path.join(self.cpld_path, self.type_node), 16) if self.get_present else None
        DEBUG('{0.name} type {0.type}:{0.check_fan_type}'.format(self))

    def get_rpm(self, *args):
        return copy.copy(self.rpm)

    def get_pwm(self, *args):
        return copy.copy(self.pwm)

    def set_pwm(self, index, v):
        write_file( os.path.join(self.hwmon_path, self.hwmon_ext_path, self.pwms[index]), v)

    def dump_dev(self):
        DEBUG ('{0.name} present:{0.get_present:2} inlet({0.pwm[0]:3},{0.rpm[0]:5})  outlet({0.pwm[1]:3},{0.rpm[1]:5})'.format(self))

    def check_fan(self):
        ret = 0
        for id in range(_NUM_ROTOR):
            max = INLET_MAX_SPEED(self.pwm[id]) if id==0 else OUTLET_MAX_SPEED(self.pwm[id])
            min = INLET_MIN_SPEED(self.pwm[id]) if id==0 else OUTLET_MIN_SPEED(self.pwm[id])
            #DEBUG('{}-{} pwm:{:3} rpm:{:5} ({:5} ~ {:5})'.format(self.name, id, self.pwm[id], self.rpm[id],min, max))
            if(self.rpm[id] > max or self.rpm[id] < min):
                ret |= 1<<id
        return ret

    @property
    def check_fan_type(self) :
        b = BoardType().board_type
        f = self.type
        return bool(  (f == 1 and (b == 0 or b == 2) )  or  (f == 0 and (b == 1 or b == 3) )  )

    def on_event(self, event):
        state = self.state
        new_state = self.state.on_event(event)
        self.state = new_state

        if(state != new_state):
            DEBUG('{0.name} state ({old} --> {new}) {evt} retry:{0.retry_count}'.format( self, old=state, new=new_state, evt=event))
            show_msg = False
            if self.state in [FailState(), UnplugState(), InitState()]:
                show_msg = True
            elif self.state == NormalState() and state not in [PwmState(), FailRetryState()]:
                show_msg = True
            if show_msg:
                INFO('{0.name} : {msg}'.format( self, msg=new_state.msg))
            self.dump_dev()

            if self.state == NormalState() :
                self.led.set_led('GREEN')
            elif self.state == FailState() :
                self.led.set_led('AMBER' if self.check_fan_type else 'OFF')
            elif self.state == UnplugState() :
                self.led.set_led('OFF')

    def update_state(self):
        old_pwm = self.get_pwm()
        old_present = self.get_present
        
        self.refresh()

        if old_present != self.get_present:
            self.update_type()
            if self.get_present:
                self.retry_count = FAN_INIT_RETRY
                self.on_event(EVT_PLUG)
            else:
                self.on_event(EVT_UNPLUG)
        elif self.get_present:
            if not self.check_fan_type:
                self.on_event(EVT_FAIL)
            elif self.check_fan() == 0 :
                self.on_event(EVT_NORMAL)
            elif old_pwm != self.get_pwm():
                self.retry_count = FAN_PWM_RETRY
                self.on_event(EVT_PWM)
            elif self.state == NormalState() :
                self.retry_count = FAN_FAILED_RETRY
                self.on_event(EVT_RETRY)    
            elif self.retry_count > 0 :
                self.retry_count -= 1
                self.on_event(EVT_POLL)
            else:
                self.on_event(EVT_FAIL)

class FanDevMon(StateMon):
    _config_key = 'mon_fan'
    def __init__(self, data):
        super(FanDevMon, self).__init__( data, FanDev)

        self._fan_fail = None
        ledmap = {
            'OFF'  : 0,
            'AMBER': 1,
            'GREEN': 2,
            'BLINK': 3,
        }
        self.led = Led(os.path.join(self.dev_list[0].cpld_path, data['devs'][0]['fan_panel_led']) , 'FanPanel', ledmap )
        self.led.set_led('OFF')
        self.start_smart_fan = data['start_smart_fan']
        self.stop_smart_fan  = data['stop_smart_fan']

        self.shutdown_func()

    def shutdown_func(self):
        os.system(self.stop_smart_fan)
        [d.set_pwm( j , PWM_MAX) for j in range(_NUM_ROTOR) for d in self.dev_list]
    def state_change(self):
        state = self.get_state()
        fan_fail = bool( [ (isinstance(i, FailState) or isinstance(i, UnplugState) or isinstance(i, InitState)) for i in state].count(True) )

        if fan_fail != self._fan_fail:
            self._fan_fail = fan_fail

            self.led.set_led( 'BLINK' if fan_fail else 'GREEN' )
            smart_fan_cmd =  self.stop_smart_fan if fan_fail else self.start_smart_fan
            DEBUG( smart_fan_cmd )
            os.system(smart_fan_cmd)
            if fan_fail:
                DEBUG('set fan pwm to max')
                [d.set_pwm( j , PWM_MAX) for j in range(_NUM_ROTOR) for d in self.dev_list]
