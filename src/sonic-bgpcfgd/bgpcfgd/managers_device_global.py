from .manager import Manager
from .log import log_err, log_debug
from swsscommon import swsscommon
import subprocess
import re

class DeviceGlobalCfgMgr(Manager):
    """This class responds to change in device-specific state"""

    def __init__(self, common_objs, db, table):
        """
        Initialize the object
        :param common_objs: common object dictionary
        :param db: name of the db
        :param table: name of the table in the db
        """
        self.directory = common_objs['directory']
        self.cfg_mgr = common_objs['cfg_mgr']
        self.constants = common_objs['constants']
        self.tsa_template = common_objs['tf'].from_file("bgpd/tsa/bgpd.tsa.isolate.conf.j2")
        self.tsb_template = common_objs['tf'].from_file("bgpd/tsa/bgpd.tsa.unisolate.conf.j2")
        super(DeviceGlobalCfgMgr, self).__init__(
            common_objs,
            [],
            db,
            table,
        )

    def set_handler(self, key, data):
        log_debug("DeviceGlobalCfgMgr:: set handler")
        """ Handle device tsa_enabled state change """
        if not data:
            log_err("DeviceGlobalCfgMgr:: data is None")
            return False

        if "tsa_enabled" in data:
            self.cfg_mgr.commit()
            self.isolate_unisolate_device(data["tsa_enabled"])
            self.directory.put(self.db_name, self.table_name, "tsa_enabled", data["tsa_enabled"])
            return True        
        return False

    def del_handler(self, key):
        log_debug("DeviceGlobalCfgMgr:: del handler")
        return True

    def check_state_and_get_tsa_routemaps(self, cmds):
        """ API to get TSA route-maps if device is isolated"""
        cmd = ""
        if self.directory.path_exist("CONFIG_DB", "BGP_DEVICE_GLOBAL", "tsa_enabled"):
            tsa_status = self.directory.get_slot("CONFIG_DB", "BGP_DEVICE_GLOBAL")["tsa_enabled"]
            if tsa_status == "True":
                log_debug("DeviceGlobalCfgMgr:: Device is isolated. Applying TSA route-maps")
                cmd = self.get_tsa_routemaps(cmds)            
        return cmd

    def isolate_unisolate_device(self, tsa_status):
        """ API to get TSA/TSB route-maps and apply configuration"""
        cmd = "\n"
        if tsa_status == "True":
            log_debug("DeviceGlobalCfgMgr:: Device isolated. Executing TSA")
            cmd += self.get_tsa_routemaps(self.cfg_mgr.get_text())
        else:
            log_debug("DeviceGlobalCfgMgr:: Device un-isolated. Executing TSB")
            cmd += self.get_tsb_routemaps(self.cfg_mgr.get_text())

        self.cfg_mgr.push(cmd)
        log_debug("DeviceGlobalCfgMgr::Done")

    def get_tsa_routemaps(self, cfg):
        route_map_names = self.__extract_out_route_map_names(cfg)
        return self.__generate_routemaps_from_template(route_map_names, self.tsa_template)

    def get_tsb_routemaps(self, cfg):
        route_map_names = self.__extract_out_route_map_names(cfg)
        return self.__generate_routemaps_from_template(route_map_names, self.tsb_template)

    def __generate_routemaps_from_template(self, route_map_names, template):
        cmd = "\n"
        for rm in route_map_names:
            if "_INTERNAL_" in rm:
                continue            
            if "V4" in rm:
                ipv="V4" ; ipp="ip"
            elif "V6" in rm:
                ipv="V6" ; ipp="ipv6"                
            else:
                continue                        
            cmd += template.render(route_map_name=rm,ip_version=ipv,ip_protocol=ipp, constants=self.constants)
        log_debug("DeviceGlobalCfgMgr::get_tsa_routemaps:: Done")
        return cmd

    def __extract_out_route_map_names(self, cfg):
        route_map_names = []
        out_route_map = re.compile(r'^\s*neighbor \S+ route-map (\S+) out$')        
        for line in cfg.replace("#012", "\n").split("\n"):
            result = out_route_map.match(line)            
            if result:
                route_map_names.append(result.group(1))                
        return route_map_names

    def __update_traffic_shift_using_cmd(self, tsa_status):
        if tsa_status == "True":
            log_debug("DeviceGlobalCfgMgr:: Device isolated. Executing TSA")
            subprocess.run(['TSA'])
        else:
            log_debug("DeviceGlobalCfgMgr:: Device un-isolated. Executing TSB")
            subprocess.run(['TSB'])        
        log_debug("DeviceGlobalCfgMgr::Done")


