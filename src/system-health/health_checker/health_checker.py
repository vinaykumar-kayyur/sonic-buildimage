class HealthChecker(object):
    checkers = set()

    def __init__(self):
        self._error_list = None

    def reset(self):
        pass

    def get_category(self):
        pass

    def get_error_list(self):
        return self._error_list

    def check(self, config):
        pass

    def __str__(self):
        return self.__class__.__name__


def checker():
    def wrapper(obj_type):
        HealthChecker.checkers.add(obj_type)
        return obj_type
    return wrapper
