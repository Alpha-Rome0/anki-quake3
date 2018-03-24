import socket
# addressing information of target
IPADDR = '127.0.0.1'
PORTNUM = 27960
# enter the data content of the UDP packet as hex
PACKETDATA = 'FFFFFFFF'.decode('hex') + "anki_review"
# initialize a socket, think of it as a cable
# SOCK_DGRAM specifies that this is UDP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
# connect the socket, think of it as connecting the cable to the address location
s.connect((IPADDR, PORTNUM))
# send the command
s.send(PACKETDATA)
# close the socket
s.close()