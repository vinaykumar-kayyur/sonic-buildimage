class HealthChecker(object):
    def __init__(self):
        self._error_info = None

    def reset(self):
        pass

    def get_category(self):
        pass

    def get_error_info(self):
        return self._error_info

    def check(self, config):
        pass

    def __str__(self):
        return self.__class__.__name__
