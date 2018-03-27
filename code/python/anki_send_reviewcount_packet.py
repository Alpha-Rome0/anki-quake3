import socket
import struct

# addressing information of target
IPADDR = '127.0.0.1'
PORTNUM = 27975
# enter the data content of the UDP packet as hex
packet = struct.pack(b"ii", 20, 5)
# initialize a socket, think of it as a cable
# SOCK_DGRAM specifies that this is UDP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
# connect the socket, think of it as connecting the cable to the address location
s.connect((IPADDR, PORTNUM))
# send the command
s.send(packet)
# close the socket
s.close()