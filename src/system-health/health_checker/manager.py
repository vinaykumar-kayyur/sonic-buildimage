import time


class HealthCheckerManager(object):
    STATE_BOOTING = 'booting'
    STATE_RUNNING = 'running'

    def __init__(self):
        self._checkers = []
        self._state = self.STATE_BOOTING

        from .config import Config
        self.config = Config()
        self.initialize()

    def initialize(self):
        from .service_checker import ServiceChecker
        from .hardware_checker import HardwareChecker
        self._checkers.append(ServiceChecker())
        self._checkers.append(HardwareChecker())

    def check(self):
        stats = {}
        self.config.load_config()
        # check state first to avoid user change boot timeout in configuration file
        # after finishing system boot
        if self._state == self.STATE_BOOTING and self._is_system_booting():
            return self._state, stats

        for checker in self._checkers:
            self._do_check(checker, stats)

        if self.config.external_checkers:
            from .external_checker import ExternalChecker
            for external_checker in self.config.external_checkers:
                checker = ExternalChecker(external_checker)
                self._do_check(checker, stats)
        return self._state, stats

    def _do_check(self, checker, stats):
        try:
            checker.check(self.config)
            category = checker.get_category()
            error_info = checker.get_error_info()
            if category not in stats:
                stats[category] = {} if error_info is None else error_info
            else:
                if error_info:
                    stats[category].update(error_info)
        except Exception as e:
            error_msg = 'Failed to perform health check for {} due to exception - {}'.format(checker, repr(e))
            if 'Internal' not in stats:
                stats['Internal'] = {str(checker): error_msg}
            else:
                stats['Internal'].update({str(checker): error_msg})

    def _is_system_booting(self):
        from .utils import get_uptime
        uptime = get_uptime()
        timeout = self.config.get_bootup_timeout()
        booting = uptime < timeout
        if not booting:
            self._state = self.STATE_RUNNING
        return booting

