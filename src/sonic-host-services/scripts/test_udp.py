#! /usr/bin/python

import socket
import argparse

SERVER_IP = "127.0.0.1"
SERVER_PORT = 20001
BUFFER_SIZE = 1024

def run_server():
    # Create a datagram socket
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
     
    # Bind to address and ip
    UDPServerSocket.bind((SERVER_IP, SERVER_PORT))
     
    print("UDP server up and listening @ {}:{}".format(SERVER_IP, SERVER_PORT))
     
    # Listen for incoming datagrams
    while(True):
        bytesAddressPair = UDPServerSocket.recvfrom(BUFFER_SIZE)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        clientMsg = "Message from Client:{}".format(message)
        clientIP  = "Client IP Address:{}".format(address)
        
        print(clientMsg)
        print(clientIP)
   

def run_client(msg):
    bytesToSend         = str.encode(msg)
    serverAddressPort   = (SERVER_IP, SERVER_PORT)
    bufferSize          = 1024
     
    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
     
    # Send to server using created UDP socket
    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
     
    print("{} sent".format(msg))


def main():
    parser=argparse.ArgumentParser(description="run client or server")
    parser.add_argument("-m", "--msg", help="msg to send", default="test message")
    parser.add_argument("-c", "--client", action='store_true',
            help="Running as client", default=False)
    parser.add_argument("-s", "--server", action='store_true',
            help="Running as server", default=False)
  
    args = parser.parse_args()

    if args.client:
        run_client(args.msg)
    elif args.server:
        run_server()
    else:
        print("Choose to run as client or server\n")

    return


if __name__ == "__main__":
    main()


