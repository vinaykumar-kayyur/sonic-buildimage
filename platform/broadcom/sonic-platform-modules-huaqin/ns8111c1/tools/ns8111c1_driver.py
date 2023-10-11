#! /usr/bin/python

import os, sys, subprocess, string

def new_device(driver, addr, bus, devdir):
    if not os.path.exists(os.path.join(bus, devdir)):
        try:
            with open("%s/new_device" % bus, "w") as f:
                f.write("%s 0x%x\n" % (driver, addr))
        except Exception as e:
            print("Unexpected error initialize device %s:0x%x:%s: %s" % (driver, addr, bus, e))
    else:
        print("Device %s:%x:%s already exists." % (driver, addr, bus))

def new_i2c_device(driver, addr, bus_number):
    bus = '/sys/bus/i2c/devices/i2c-%d' % bus_number
    devdir = "%d-%4.4x" % (bus_number, addr)
    return new_device(driver, addr, bus, devdir)

def baseconfig():
    print("Initialize EEPROM driver")
    # tlv eeprom device
    new_i2c_device('24lc64t', 0x56, 0)
    # Baseboard eeprom device
    new_i2c_device('24lc64t', 0x50, 15)
    # BMC eeprom device
    new_i2c_device('24lc64t', 0x51, 15)
    # switchboard eeprom device
    new_i2c_device('24lc64t', 0x52, 15)
    # SFP+/QSFPDD eeprom
    for y in range(24):
        new_i2c_device('optoe1',0x50,37+y)
    for x in range(8):
        new_i2c_device('optoe3',0x50,61+x)

def main():
    baseconfig()


if __name__ == "__main__":
    sys.exit(main())
