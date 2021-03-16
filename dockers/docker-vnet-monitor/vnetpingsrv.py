#!/usr/bin/env python

from scapy.all import *

#
# Config
#

DEFAULT_TCP_OPTIONS = 253
DEFAULT_TCP_PORT = '1021'

#
# Setup a TCP ping server
#

def tcpserver(serverport):

    # Send SYNACK packets
    def _ack(packet, flag, seqno, ackno):
        srcip = packet[IP].src
        dstip = packet[IP].dst
        srcport = packet[TCP].sport
        dstport = packet[TCP].dport

        # send SYNACK to remote host
        ip = IP(src=dstip, dst=srcip)
        TCP_SYNACK = TCP(sport=int(serverport), dport=srcport, flags=flag, seq=seqno, ack=ackno, options=[(DEFAULT_TCP_OPTIONS, b'\0')])
        ANSWER = send(ip / TCP_SYNACK, verbose=0)

    # Process packets
    def _processpackets(packet):
        if packet.haslayer(TCP) and packet[TCP].dport == int(serverport) :
            if packet[TCP].flags & 0x02 == 0x02 : # SYNC
                seqno = random.randrange(0, (2**32)-1)
                ackno = packet[TCP].seq + 1
                _ack(packet, "SA", seqno, ackno)

            if packet[TCP].flags & 0x08 == 0x08 : # PSH
                seqno = packet[TCP].seq + 1
                ackno = packet[TCP].seq + len(packet[Raw])
                _ack(packet, "A", seqno, ackno)

    print "vnetping server starts."
    # Wait for client to connect.
    sniffstring = "tcp and dst port " + serverport
    while True:
        sniff(filter=sniffstring, prn=_processpackets)


#
# Main function
#

def main():
    tcpserver(DEFAULT_TCP_PORT)


#
# Program entry
#

if __name__ == '__main__':
    main()
