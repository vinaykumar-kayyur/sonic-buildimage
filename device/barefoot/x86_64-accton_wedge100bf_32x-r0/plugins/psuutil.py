#!/usr/bin/env python

#############################################################################
# Accton
#
# Module contains an implementation of SONiC PSU Base API and
# provides the PSUs status which are available in the platform
#
#############################################################################
import sys
import commands
import time
import os.path
import re
import pexpect
import cPickle as pickle

try:
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    BF_INTV = 10 # in seconds
    cache = ""
    DATA = {1: {'last_poll':0,
                'status':False,
                'presence':False},
            2: {'status':False,
                'presence':False}
           }
    bf_commands = ["ucli", "..", "..", "bf_pltfm", "chss_mgmt"]

    def __init__(self):
        PsuBase.__init__(self)
        self.cache = "/tmp/.%s.cache" % os.path.basename(sys.argv[0])

    def get_num_psus(self):
        return len(self.DATA)

    def interact_with_bfshell(self, cmds, timeout=20):
        bfshell_path = 'docker exec -it syncd /opt/bfn/install/bin/bfshell'
        bfshell_cmd = [ bfshell_path ]

        prompt_list = ['bfshell> $', 'bf-sde\.*.*> $', 'pd-switch:\d+> $', pexpect.EOF]
        child = pexpect.spawn(' '.join(bfshell_cmd))
        child.expect(prompt_list)
        lines = []
        for cmd in cmds:
            child.sendline(cmd)
            child.expect(prompt_list)
            for line in child.before.splitlines():
                if line.strip() and line != cmd:
                    lines.append(line)

        return lines 

    def bf_poll_psu(self):
        if os.path.exists(self.cache):
            self.DATA = pickle.load(open(self.cache, "rb"))
        last_poll = self.DATA[1]['last_poll']
        now = time.time()
        if now < (last_poll + self.BF_INTV):
            return True    

        for d in self.DATA:
            index = d
            subcmd = "ps_show %d" % index
            cmds = list(self.bf_commands)
            cmds.append(subcmd)
            lines = self.interact_with_bfshell(cmds)
            log = "".join(lines)
            mt = re.search("error:", log, re.I) 
            if mt != None:
                self.DATA[d]['presence'] = False
                return False


            buf = log.replace("\r", "")    
            buf = buf.replace("\n", "")    
            mt = re.search("Presence\s+true", buf)
            if mt == None:
                self.DATA[d]['presence'] = False
            else:    
                self.DATA[d]['presence'] = True
            pw = re.sub(r"(.*Power output\s+)(\d+)(.*)", r"\2", buf)
            pw = int(pw)
            if pw <=  100:  #for output power < 100mW, it'd off
                self.DATA[d]['status'] = False
            else:    
                self.DATA[d]['status'] = True


        self.DATA[1]['last_poll'] = time.time()
        pickle.dump(self.DATA, open(self.cache, "wb"))
        return True

    def get_psu_status(self, index):
        if index is None:
            return False

        self.bf_poll_psu()
        d = self.DATA[index]
        return d['status']

    def get_psu_presence(self, index):
        if index is None:
            return False

        self.bf_poll_psu()
        d = self.DATA[index]
        return d['presence']

