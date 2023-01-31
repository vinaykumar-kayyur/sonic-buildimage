#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import click
import subprocess


def io_rd(reg_addr, length =1):
    '''io read'''
    try:
        regaddr = 0
        if type(reg_addr) == int:
            regaddr = reg_addr
        else:
            regaddr = int(reg_addr, 16)
        devfile = "/dev/port"
        fd = os.open(devfile, os.O_RDWR|os.O_CREAT)
        os.lseek(fd, regaddr, os.SEEK_SET)
        str1 = os.read(fd, length)
        return "".join(["%02x"% ord(item) for item in str1])
    except ValueError:
        return None
    except Exception as e:
        print (e)
        return None
    finally:
        os.close(fd)
    return None

@click.group()
def cli():
    pass

@cli.command()
@click.argument('addr', required=True)
@click.argument('length', required=True,type = int)
def reg_read(addr,length):
    try:
        value = io_rd(addr,length)
        if value == None:
            print ("read failed")
        else:
            print (value)
    except Exception as e:
        print (e)
        return None

if __name__ == '__main__':
    cli()

