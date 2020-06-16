class HealthChecker(object):
    INFO_FIELD_OBJECT_TYPE = 'type'
    INFO_FIELD_OBJECT_STATUS = 'status'
    INFO_FIELD_OBJECT_MSG = 'message'

    STATUS_OK = 'OK'
    STATUS_NOT_OK = 'Not OK'

    def __init__(self):
        self._info = {}

    def reset(self):
        pass

    def get_category(self):
        pass

    def get_info(self):
        return self._info

    def check(self, config):
        pass

    def __str__(self):
        return self.__class__.__name__

    def add_info(self, object_name, key, value):
        if object_name not in self._info:
            self._info[object_name] = {}

        self._info[object_name][key] = value

    def set_object_not_ok(self, object_type, object_name, message):
        self.add_info(object_name, self.INFO_FIELD_OBJECT_TYPE, object_type)
        self.add_info(object_name, self.INFO_FIELD_OBJECT_MSG, message)
        self.add_info(object_name, self.INFO_FIELD_OBJECT_STATUS, self.STATUS_NOT_OK)

    def set_object_ok(self, object_type, object_name):,
        self.add_info(object_name, self.INFO_FIELD_OBJECT_TYPE, object_type)
        self.add_info(object_name, self.INFO_FIELD_OBJECT_MSG, '')
        self.add_info(object_name, self.INFO_FIELD_OBJECT_STATUS, self.STATUS_OK)
