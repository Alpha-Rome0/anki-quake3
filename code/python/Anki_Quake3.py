# -*- coding: utf-8 -*-
"""
Anki Add-on: Anki Quake 3
"""

from __future__ import unicode_literals

from anki.hooks import addHook, wrap
from anki import version as anki_version

from aqt.qt import *
from aqt import mw
from aqt.utils import tooltip
from aqt.reviewer import Reviewer

import socket
from threading import Thread
import struct

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

global_review_count = 0
global_socket = None
global_server_active = True

__version__ = '0.1'

### configuration section
### =====================

# IP/port where Quake3 is running. the port is the default,
# you should see it appear in the Quake3 console at startup
QUAKE3_IP = '127.0.0.1'
QUAKE3_PORT = 27960

# IP/port where Anki should listen to messages from Quake3
# if you change those, make sure to change the corresponding host/port 
# in q3config.cfg:
# seta cl_ankiHostPort "127.0.0.1:27975"
ANKI_IP = 'localhost'
ANKI_PORT = 27975



### ======================

def getPacketData():
	return 'FFFFFFFF'.decode('hex') + b'anki_review'

def cardReview():
	global global_review_count

	# enter the data content of the UDP packet as hex
	PACKETDATA = getPacketData()
	# initialize a socket, think of it as a cable
	# SOCK_DGRAM specifies that this is UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
	# connect the socket, think of it as connecting the cable to the address location
	s.connect((QUAKE3_IP, QUAKE3_PORT))
	# send the command
	s.send(PACKETDATA)
	# close the socket
	s.close()

	actual_review_count = global_review_count - 1
	tooltip_text = "Anki Quake3: %d cards left" % actual_review_count
	tooltip(tooltip_text, period=3000)	

	
def server_loop():
	global global_review_count
	global global_socket
	global global_server_active
	
	# print >> sys.stderr, "server_loop"

	try:
		# Create a TCP/IP socket
		global_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Bind the socket to the port
		server_address = (ANKI_IP, ANKI_PORT)
		global_socket.bind(server_address)	
	except socket.error as e:
		print >> sys.stderr, 'failed to bind to socket:', e
        
	
	while global_server_active:
		data, address = global_socket.recvfrom(1024)
		global_review_count = struct.unpack("i", data)[0]
		
	
def start_up():
	thread = Thread(target = server_loop)
	thread.daemon = True
	thread.start()		
	
def keyHandler(self, evt, _old):
    key = unicode(evt.text())
    if key == "z":
        try:# throws an error on undo -> do -> undo pattern,  otherwise works fine
            mw.onUndo()
        except:
            pass
    elif key in ["q", "e",]: # allow answering with a and d keys, to keep fingers on WASD
        cnt = mw.col.sched.answerButtons(mw.reviewer.card) # Get button count
        isq = self.state == "question"
        if isq:
            self._showAnswerHack()
        if key == "q":
            self._answerCard(1)
        elif key == "e":
            self._answerCard(cnt)
        else:
            return _old(self, evt)
    else:
        return _old(self, evt)	

addHook("showAnswer", cardReview)	
addHook("profileLoaded", start_up)

Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, "around")
		

