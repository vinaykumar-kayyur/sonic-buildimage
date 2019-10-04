#!/usr/bin/env python
""" JSON based configlet update

A tool to update CONFIG-DB with JSON diffs that can update/delete redis-DB.

All elements in the list are processed in the same order as it is present.
The list entry, contains objects for delete & update
Within an list entry that has delete & update, delete gets done first, followed by update.
Within an op (delete/update), the tables are handled in any order.
Within a table, the keys are handled in any order.
[
    {
        "delete": {
            "TABLE1": {
                "Key1": {
                    "Key2": {
                        "Field1": "Val1"
                    }
                }
            }
        },
        "update": {
            "TABLE1": {
                "Key1": {
                    "Key2": {
                        "Field1": "Val1",
                        "Field2": "Val2",
                        "Field3": "Val3"
                    },
                    "Key2_1": {
                        "Field2_1": "Val1",
                        "Field2_2": "Val2",
                        "Field2_3": "Val3"
                    }
                }
            },
            "TABLE2": {
                "Key1": {
                    "Key2": {
                        "Field2": "Val2"
                    }
                }
            }
        }
    },
    {
        "delete": {
            "TABLE2": {
            }
        }
    },
    {
        "update": {
            "TABLE2": {
                "Key22_1": {
                    "Key22_2": {
                        "Field22_2": "Val22_2"
                    }
                }
            }
        }
    }
]


"""

from __future__ import print_function
import sys
import os.path
import argparse
import json
from collections import OrderedDict
from natsort import natsorted
from db_updater import *

test_only = False

def do_update(t, k, lst):
    if test_only == False:
        db_update(t, k, lst)
    else:
        print ("TEST update")
        print ("table: " + t)
        print ("key: " + str(k))
        print (lst)
        print ("---------------------")

def do_delete(t, k, lst):
    if test_only == False:
        db_delete(t, k, lst)
    else:
        print ("TEST delete")
        print ("table: " + t)
        print ("key: " + str(k))
        print (lst)
        print ("---------------------")


def do_operate(op, t, k, lst):
    if lst:
        if type(lst[lst.keys()[0]]) == dict:
            for i in lst:
                do_operate(op, t, k+(i,), lst[i])
            return

    if op == "delete":
        do_delete(t, k, lst)

    elif op == "update":
        do_update(t, k, lst)

    else:
        assert False, "Internal error: Unknown operation (" + op + ")"


def process_entry(data):
    for op in ["delete", "update"]:
        if op in data.keys():
            for t in data[op].keys():
                do_operate(op, t, (), data[op][t])

def main():
    global test_only

    parser=argparse.ArgumentParser(description="Manage configlets for CUD (Update & Delete")
    parser.add_argument("-j", "--json", help="json file that contains configlet with action", action='append')
    parser.add_argument("-t", "--test", help="Test only", action='store_true', default=False)
    parser.add_argument("-p", "--parse", help="Parse JSON only", action='store_true', default=False)

    args = parser.parse_args()

    test_only = args.test
    parse_only = args.parse

    for json_file in args.json:
        with open(json_file, 'r') as stream:
            data = json.load(stream)
            if parse_only == False:
                for i in data:
                    process_entry (i)
            else:
                print("Parsed:")
                print(data)


if __name__ == "__main__":
    main()

