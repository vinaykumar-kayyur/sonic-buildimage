import os
import copy

from commonlib import *

PSU_POWER_GOOD = 0
PSU_PRESENT    = 0
PSU_POWER_FAULT= 1

EVT_UNPLUG = 'evt_ps'
EVT_PLUG   = 'evt_ps_n'
EVT_PG     = 'evt_pg'
EVT_PG_N   = 'evt_pg_n'
EVT_PF     = 'evt_pf'
EVT_PF_N   = 'evt_pf_n'

PSU_MODEL_TYPE_INIT      = 0xFF
PSU_MODEL_TYPE_NOT_FOUND = 0xFE

class AbsentState(State):
    def __init__(self):
        self.msg = 'Absent'
    def on_event(self, event):
        evtmap = {
            EVT_PLUG : PresentState(),
        }
        return evtmap[event]  if event in evtmap else self

class PresentState(State):
    def __init__(self):
        self.msg = 'Present but no power'
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG : AbsentState(),
            EVT_PG     : NormalState(),
        }
        return evtmap[event]  if event in evtmap else self

class NormalState(State):
    def __init__(self):
        self.msg = 'Present and work normal'
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG : AbsentState(),
            EVT_PG_N   : PresentState(),
            EVT_PF     : FaultState(),
        }
        return evtmap[event]  if event in evtmap else self

class FaultState(State):
    def on_event(self, event):
        evtmap = {
            EVT_UNPLUG : AbsentState(),
            EVT_PG_N :   PresentState(),
            EVT_PF_N :   NormalState(),
        }
        return evtmap[event]  if event in evtmap else self

class PsuDev(StateDev):

    def __init__(self, param):
        super(PsuDev, self).__init__(param)

        self.sysfs_cmd    =    param["sysfs_cmd"]
        self.present_node =    param['present']
        self.power_good_node = param['power_good']
        self.model_type_node = param['model_reg']

        self.power_good = int(not PSU_POWER_GOOD)
        self.power_fault = dict([( x, int(not PSU_POWER_FAULT) ) for x in param['psu_intr_src'] ])
        self.state = AbsentState()
        self.model_type = None
        self.model_type_index = PSU_MODEL_TYPE_INIT

        self.sysfs_init_flag = 0

        self.present_changed = 1
        self.power_good_changed = 1
        self.power_fault_changed = 1

        self.update_state()

        self._crate_hwmon_sysfs()

    def _crate_hwmon_sysfs(self):
        #if self.sysfs_init_flag == 0 and self.power_good  and self.present:
        if self.sysfs_init_flag == 0  and self.present:
            if not os.path.exists(self.hwmon_path) :
                INFO('{0.name} : run command --> {0.sysfs_cmd}'.format(self))
                os.system(self.sysfs_cmd)

            self.sysfs_init_flag = 1
            if self.hwmon_path :
                try:
                    listofdir = [f for f in os.listdir(self.hwmon_path) if os.path.isdir( os.path.join(self.hwmon_path,str(f)))]
                    if len(listofdir) :
                        self.hwmon_ext_path = listofdir[0]
                except :
                    self.sysfs_init_flag = 0

    def refresh_present(self):
        v = cat_file( os.path.join(self.cpld_path, self.present_node), 16)
        self.present = 1 if v == PSU_PRESENT else 0

    def refresh_power_good(self):
        v = cat_file( os.path.join(self.cpld_path, self.power_good_node), 16)
        self.power_good = 1 if v == PSU_POWER_GOOD else 0

    def refresh_power_fault(self):
        if self.sysfs_init_flag == 0 : return
        if not self.present: return

        for f in self.power_fault:
            self.power_fault[f] = cat_file(os.path.join(self.hwmon_path, self.hwmon_ext_path ,f), 16)

    def refresh(self):
        self.refresh_present()
        self.refresh_power_good()
        self.refresh_power_fault()

    def update_model_type(self):
        if self.model_type_index == PSU_MODEL_TYPE_INIT :
            if not self.present : return

            if self.sysfs_init_flag == 0 : 
                self.model_type = None
            else:
                self.model_type = cat_file_str(os.path.join(self.hwmon_path, self.hwmon_ext_path, self.model_type_node)).strip()
                if self.model_type == None:
                    return
                INFO( '{0.name} type : {0.model_type}'.format(self) )
                try:
                    self.model_type_index = PsuType().psu_type.index(self.model_type)
                    if self.model_type_index != BoardType().board_type :
                        pass
                except ValueError:
                    self.model_type_index = PSU_MODEL_TYPE_NOT_FOUND

    def get_power_good(self):
        return self.power_good

    def get_power_fault(self):
        return copy.copy(self.power_fault)

    def dump_dev(self):
        pass

    def on_event(self, event):
        state = self.state
        new_state = self.state.on_event(event)
        self.state = new_state

        if state != new_state :
            DEBUG("{0.name} state ({old} --> {new}) {evt} ".format( self, old=state, new=new_state, evt=event ))
            INFO("{0.name} : {msg}".format( self, msg=new_state.msg))
            self.dump_dev()
            if new_state == NormalState():
                self._crate_hwmon_sysfs()
        
        if event == EVT_UNPLUG:
            self.model_type_index = PSU_MODEL_TYPE_INIT
            for f in self.power_fault: self.power_fault[f] = 0
        elif event == EVT_PLUG:
            self.power_good_changed = 1
            self.power_fault_changed = 1
        elif event == EVT_PG:
            self.power_fault_changed = 1

    def update_state(self):
        old_present    = self.get_present
        old_power_good = self.get_power_good()
        old_power_fault = self.get_power_fault()
        
        self.refresh()

        if old_present != self.get_present :         self.present_changed = 1
        elif old_power_good != self.get_power_good():    self.power_good_changed = 1
        elif old_power_fault != self.get_power_fault():  self.power_fault_changed = 1

        if self.present_changed:
            self.present_changed = 0
            self.on_event(EVT_PLUG if self.get_present else EVT_UNPLUG )
        if self.power_good_changed:
            self.power_good_changed = 0
            self.on_event(EVT_PG if self.get_power_good() else EVT_PG_N )
        if self.power_fault_changed:
            self.power_fault_changed = 0

            pf = self.get_power_fault().values()
            self.on_event( EVT_PF if list(pf).count(1) else EVT_PF_N )

            if old_power_fault != self.get_power_fault():
                diff = set(self.power_fault.items()) - set(old_power_fault.items()) 
                [INFO ('{0.name} {key:15}: {val}'.format(self, key=e[0], val=e[1]) )  for e in diff]

class PsuDevMon(StateMon):
    _config_key = 'mon_psu'
    def __init__(self, data):
        super(PsuDevMon, self).__init__(data, PsuDev)

        ledmap = {
            'OFF'  : 0,
            'AMBER': 1,
            'GREEN': 2,
            'BLINK': 3,
        }
        self.led = Led(os.path.join(self.dev_list[0].cpld_path, data['devs'][0]['psu_panel_led']) , 'PsuPanel', ledmap )
        self.led.set_led('GREEN')

    def state_change(self):
        fault = bool( [ (isinstance(i, FaultState) ) for i in self.get_state() ].count(True) )

        brd_type_error = False
        for d in self.dev_list :
            if d.model_type_index != PSU_MODEL_TYPE_INIT and d.model_type_index != BoardType().board_type :
                ERR( '{0.name} type error {0.model_type_index} : {type}'.format(d, type=BoardType().board_type) )
                brd_type_error = True
                break

        self.led.set_led( 'AMBER' if fault or brd_type_error else 'GREEN' )

    def force_state_change(self) :
        for d in self.dev_list :
            index = d.model_type_index

            d.update_model_type()
            if index != d.model_type_index :
                return True
        return False
