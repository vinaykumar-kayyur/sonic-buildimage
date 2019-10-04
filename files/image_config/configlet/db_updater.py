#!/usr/bin/env python

from __future__ import print_function
import sys
import os.path
import argparse
import json
from collections import OrderedDict
from natsort import natsorted
from swsssdk import ConfigDBConnector

connected = False
db = ConfigDBConnector()

def db_update(t, k, lst):
    init()
    db.mod_entry(t, k, lst)

def db_filtered_upd(t, k, lst):
    init()
    data = db.get_entry(t, k)
    for i in lst.keys():
        data.pop(i)
    db.set_entry(t, k, data)


def db_delete_deep(t, k):
    if not k:
        db.delete_table(t)
    else:
        db.mod_entry(t, k, None)

def db_delete(t, k, lst):
    init()
    if lst:
        db_filtered_upd(t, k, lst)
    else:
        db_delete_deep(t, k)


def init():
    global connected

    if connected == False:
        db.connect(False)
        connected = True
