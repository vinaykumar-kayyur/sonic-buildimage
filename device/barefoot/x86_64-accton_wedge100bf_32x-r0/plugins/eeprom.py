#!/usr/bin/env python

try:
    import exceptions
    import binascii
    import time
    import optparse
    import warnings
    import os
    import sys
    from sonic_eeprom import eeprom_base
    from sonic_eeprom import eeprom_tlvinfo
    import subprocess
    import re
    import pexpect
    import cPickle as pickle

except ImportError, e:
    raise ImportError (str(e) + "- required module not found")

class board(eeprom_tlvinfo.TlvInfoDecoder):
    _TLV_INFO_MAX_LEN = 256
    bf_commands = ["ucli", "..", "..", "bf_pltfm", "cp2112"]
    BFCMD="do_bfshell.py -c ucli \
                -c .. -c .. -c bf_pltfm -c cp2112 -c"
    cache = "" 
    DATA = {'last_poll':0, 'raw': ""}
    CHECK_INTV = 5 #in seconds

    def __init__(self, name, path, cpld_root, ro):
        self.cache = "/tmp/.%s.cache" % os.path.basename(sys.argv[0])
        super(board, self).__init__("", 0, '', True)

    def eeprom_up2date(self):
        if os.path.exists(self.cache):
            self.DATA = pickle.load(open(self.cache, "rb"))
        last_poll = self.DATA['last_poll']

        #check interval
        now = time.time()
        if now < (last_poll + self.CHECK_INTV):
            return True
        else:
            return False

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


    def read_eeprom_bytes(self, byteCount, offset=0):
        if self.eeprom_up2date() == True:
            str = self.DATA['raw']
        else:
            subcmd =  "write 1 0xe8 1 0x40; write 1 0xa0 2 0 0; read 1 0xa0 ff"
            cmd = self.BFCMD + "\'" + subcmd + "\'"
            cmds = self.bf_commands
            cmds.append(subcmd)
            #lines = os.popen(cmd).readlines() 
            lines = self.interact_with_bfshell(cmds)

            last = lines[-1].strip()
            raw = last.split()
            hex = []
            for byte in raw: 
                hex.append(chr(int(byte,16))) 
            str = ''.join(hex)
            if len(str) < offset+byteCount:
                raise RuntimeError("expected to read %d bytes from %s, " \
                               %(byteCount, "bfshell") +
                               "but only read %d" %(len(str)))
            self.DATA['raw'] = str
            self.DATA['last_poll'] = time.time()
            pickle.dump(self.DATA, open(self.cache, "wb"))

        return str[offset:offset+byteCount]

