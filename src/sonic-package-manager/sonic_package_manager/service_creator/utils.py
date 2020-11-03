#!/usr/bin/env python

import os


def in_chroot() -> bool:
    root_stat = os.stat('/')
    init_root_stat = os.stat('/proc/1/root')

    return (root_stat.st_dev, root_stat.st_ino) != \
           (init_root_stat.st_dev, init_root_stat.st_ino)
