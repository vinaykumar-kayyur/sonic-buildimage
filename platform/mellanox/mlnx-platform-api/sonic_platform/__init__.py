__all__ = ["platform", "chassis"]
try:
    from sonic_platform import *
except ImportError as e:
    pass
