from .manager import Manager

class RouteMapMgr(Manager):
    """ This class add route-map when ROUTE_MAP_TABLE in STATE_DB is updated """
    def __init__(self, common_objs, db, table):
        """
        Initialize the object
        :param common_objs: common object dictionary
        :param db: name of the db
        :param table: name of the table in the db
        """
        super(RouteMapMgr, self).__init__(
            common_objs,
            [],
            db,
            table,
        )

    VALID_RM = ['VXLAN_OV_ECMP_RM']

    def set_handler(self, key, data):
        '''Only need a name as the key, and community id as the data'''
        if not self._set_handler_validate(key, data):
            return True
        
        self._update_rm(key, data)
        return True


    def del_handler(self, key):
        if not self._del_handler_validate(key):
            return
        self._remove_rm(key)


    def _remove_rm(self, rm):
        cmds = ['no route-map %s permit 100' % rm]
        self.cfg_mgr.push_list(cmds)


    def _set_handler_validate(self, key, data):
        if key != self.VALID_RM:
            return False
        
        if data:
            community_ids = data.split(':')
            if len(community_ids) == 2:
                if community_ids[0] in range(0, 65535) \
                and community_ids[1] in (0, 65535):
                    return True

        return False


    def _del_handler_validate(self, key):
        if key in self.VALID_RM:
            return False
        return True


    def _update_rm(self, rm, community):
        cmds = [
            'route-map %s permit 100' % rm,
            ' set community %s' % community
        ]
        self.cfg_mgr.push_list(cmds)
