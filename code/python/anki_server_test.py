# -*- coding: utf-8 -*-
"""
Anki Add-on: Progress Bar

Shows progress in the Reviewer in terms of passed cards per session.

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) Glutanimate 2017 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

import socket
from threading import Thread
import struct

import signal 
import time

# import atexit

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

global_review_count = 0
global_socket = None
global_server_active = True

__version__ = '0.1'


def shutdown_server():
	global global_socket
	global global_server_active
	
	print "shutdown"
	
	global_server_active = False
	
	if global_socket != None:
		global_socket.shutdown()
		global_socket.close()
	
	
def server_loop():
	global global_review_count
	global global_socket
	global global_server_active

	try:
		# Create a TCP/IP socket
		global_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#global_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# global_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

		# Bind the socket to the port
		server_address = ('localhost', 27976)
		#print >>sys.stderr, 'starting up on %s port %s' % server_address
		global_socket.bind(server_address)	
		
		print "bound to socket" 
		
	except socket.error as e:
		print >> sys.stderr, 'failed to bind to socket:', e
        
	
	while global_server_active:
		print "receive loop"
		data, address = global_socket.recvfrom(1024)
		
		print "received data %s" % data
		
		#global_review_count = struct.unpack("i", data)[0]
		
		#print >> sys.stderr, "review_count: %d" % global_review_count
	
	print "shutting down"
	global_socket.shutdown()
	global_socket.close()

		
# atexit.register(shutdown_server)

#signal.signal(signal.SIGINT, signal_handler)

thread = Thread(target = server_loop)
thread.daemon = True
thread.start()

if __name__ == '__main__':
	while True:
		print "waiting"
		time.sleep(1)