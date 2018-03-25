# -*- coding: utf-8 -*-
"""
Anki Add-on: Progress Bar

Shows progress in the Reviewer in terms of passed cards per session.

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) Glutanimate 2017 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

# Do not modify the following lines
from __future__ import unicode_literals

from anki.hooks import addHook, wrap
from anki import version as anki_version

from aqt.qt import *
from aqt import mw
from aqt.utils import tooltip

import socket
from threading import Thread
import struct


import atexit

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

global_review_count = 0
global_socket = None
global_server_active = True

__version__ = '0.1'

def getPacketData():
	return 'FFFFFFFF'.decode('hex') + b'anki_review'

def cardReview():
	global global_review_count
	
	# addressing information of target
	IPADDR = '127.0.0.1'
	PORTNUM = 27960
	# enter the data content of the UDP packet as hex
	PACKETDATA = getPacketData()
	# initialize a socket, think of it as a cable
	# SOCK_DGRAM specifies that this is UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
	# connect the socket, think of it as connecting the cable to the address location
	s.connect((IPADDR, PORTNUM))
	# send the command
	s.send(PACKETDATA)
	# close the socket
	s.close()

	actual_review_count = global_review_count - 1
	tooltip_text = "Anki Quake3: %d cards left" % actual_review_count
	tooltip(tooltip_text, period=3000)	

def shutdown_server():
	global global_socket
	global global_server_active
	
	global_server_active = False
	
	global_socket.shutdown()
	global_socket.close()
	
	
def server_loop():
	global global_review_count
	global global_socket
	global global_server_active
	
	# print >> sys.stderr, "server_loop"

	try:
		# Create a TCP/IP socket
		global_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#global_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# global_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

		# Bind the socket to the port
		server_address = ('localhost', 27975)
		#print >>sys.stderr, 'starting up on %s port %s' % server_address
		global_socket.bind(server_address)	
	except socket.error as e:
		print >> sys.stderr, 'failed to bind to socket:', e
        
	
	while global_server_active:
		data, address = global_socket.recvfrom(1024)
		

		global_review_count = struct.unpack("i", data)[0]
		
		#print >> sys.stderr, "review_count: %d" % global_review_count
		
def start_up():
	thread = Thread(target = server_loop)
	thread.daemon = True
	thread.start()		

addHook("showAnswer", cardReview)	
addHook("profileLoaded", start_up)
		
# atexit.register(shutdown_server)


