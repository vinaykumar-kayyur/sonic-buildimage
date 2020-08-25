import os


class FileUtils(object):
    last_error = ''

    @classmethod
    def read(cls, file_path, default=None, no_raise=True):
        cls.last_error = ''
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except IOError as e:
            cls.last_error = 'Failed to read from {} - {}'.format(file_path, repr(e))
            return default

    @classmethod
    def read_int(cls, file_path, default=0):
        try:
            return int(cls.read(file_path, default))
        except ValueError as e:
            cls.last_error = 'Failed to read from {} - {}'.format(file_path, repr(e))
            return default

    @classmethod
    def read_float(cls, file_path, default=0):
        try:
            return float(cls.read(file_path, default))
        except ValueError as e:
            cls.last_error = 'Failed to read from {} - {}'.format(file_path, repr(e))
            return default

    classmethod
    def write(cls, file_path, value):
        cls.last_error = ''
        try:
            with open(file_path, 'w') as f:
                f.write(str(value))
            return True
        except IOError as e:
            cls.last_error = 'Failed to write to {} - {}'.format(file_path, repr(e))
            return False
