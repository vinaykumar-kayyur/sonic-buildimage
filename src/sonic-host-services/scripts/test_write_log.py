#! /usr/bin/python3

import argparse
import syslog
import time

def do_log(fname, identity):
    with open(fname, "r") as s:
        lines = s.readlines()

    tstart = time.time()
    syslog.openlog(identity)
    for line in lines:
        line = line.strip()
        if line:
            syslog.syslog(syslog.LOG_INFO, line)
    tend = time.time()

    print("tstart: {}".format(tstart))
    print("tend: {}".format(tend))
    print("time_taken: {}".format(tend - tstart))
        

def main():
    parser=argparse.ArgumentParser(description="log from file")
    parser.add_argument("-f", "--file", help="i/p file with log messages",
            required=True)
    parser.add_argument("-i", "--identity", help="Identity to use. e.g. bgp#bgpcfgd",
            required=True)

    args = parser.parse_args()

    do_log(args.file, args.identity)


if __name__ == "__main__":
    main()


