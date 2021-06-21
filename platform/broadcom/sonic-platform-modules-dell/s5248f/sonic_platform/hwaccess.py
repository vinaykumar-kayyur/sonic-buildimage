""" Helper functions to access hardware """

import struct
import mmap
import subprocess

def pci_mem_read(memmap, offset):
    """ Read PCI device """
    memmap.seek(offset)
    read_data_stream = memmap.read(4)
    return struct.unpack('I', read_data_stream)[0]

def pci_get_value(resource, offset):
    """ Get a value from  PCI device """
    val = None
    with open(resource, 'r+b') as filed:
        memmap = None
        try:
            memmap = mmap.mmap(filed.fileno(), 0)
            val = pci_mem_read(memmap, offset)
        except EnvironmentError:
            pass
        if memmap is not None:
            memmap.close()
    return val

def pci_mem_write(memmap, offset, data):
    """ Write PCI device """
    memmap.seek(offset)
    memmap.write(struct.pack('I', data))

def pci_set_value(resource, val, offset):
    """ Set a value to PCI device """
    with open(resource, 'w+b') as filed:
        memmap = None
        try:
            memmap = mmap.mmap(filed.fileno(), 0)
            pci_mem_write(memmap, offset, val)
        except EnvironmentError:
            pass
        if memmap is not None:
            memmap.close()

def i2c_get(bus, i2caddr, ofs):
    """ Read I2C device """
    try:
        result = int(subprocess.check_output\
            (['/usr/sbin/i2cget', '-y', str(bus), str(i2caddr), str(ofs)]), 16)
    except EnvironmentError:
        result = None
    return result
