# -*- coding: utf-8 -*-
"""
Anki Add-on: Anki Quake 3
Gamify your Anki session using Quake3. Review cards to get ammunition, health and armor

uses some code from the Handy Answer Keys Shortcuts, by Vitalie Spinu
and Progress Bar, by Unknown author, SebastienGllmt, Glutanimate 

License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

### imports
### =======

from __future__ import unicode_literals

from anki.hooks import addHook, wrap, runHook
from anki import version as anki_version

from aqt.qt import *
from aqt import mw
from aqt.utils import tooltip
from aqt.reviewer import Reviewer

import PyQt4.QtCore

import socket
from threading import Thread
import struct

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

### quake command line

# ioquake3.x86_64.exe +set sv_pure 0 +set vm_cgame 0 +set vm_game 0 +set vm_ui 0
# building
# make ARCH=x86_64

### configuration section for AnkiQuake3
### ====================================

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


g_review_count_target = -1
g_review_count_done = -1

g_pb_notifier = None

### constants related to progress bar
### ---------------------------------

# Which queues to include in the progress calculation (all True by default)
includeNew = True
includeRev = True
includeLrn = True

# Only include new cards once reviews are exhausted.
includeNewAfterRevs = True

# Limit count to your review settings as opposed to deck overall
limitToReviewSettings = True

# PROGRESS BAR APPEARANCE

showPercent = False # Show the progress text percentage or not.
showNumber = True # Show the progress text as a fraction

qtxt = "#f1ced1" # Percentage color, if text visible.
qbg = "#7d2029" # Background color of progress bar.
qfg = "#91131f" # Foreground color of progress bar.
qbr = 0 # Border radius (> 0 for rounded corners).

# optionally restricts progress bar width
maxWidth = ""  # (e.g. "5px". default: "")

orientationHV = Qt.Horizontal # Show bar horizontally (side to side). Use with top/bottom dockArea.
# orientationHV = Qt.Vertical # Show bar vertically (up and down). Use with right/left dockArea.

pbStyle = ""

dockArea = Qt.TopDockWidgetArea # Shows bar at the top. Use with horizontal orientation.

__version__ = '0.1'

class ProgressBarNotifier(PyQt4.QtCore.QObject):
    
    def __init__(self, update_function):
       PyQt4.QtCore.QObject.__init__(self) # initialisation required for object inheritance
       PyQt4.QtCore.QObject.connect(self, PyQt4.QtCore.SIGNAL('review_count_update'), update_function)

    def signal_update(self):
       self.emit(PyQt4.QtCore.SIGNAL('review_count_update'))


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

	
def server_loop():
	global g_review_count_target
	global g_review_count_done
	global g_pb_notifier

	try:
		# Create a TCP/IP socket
		global_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Bind the socket to the port
		server_address = (ANKI_IP, ANKI_PORT)
		global_socket.bind(server_address)	
	except socket.error as e:
		print >> sys.stderr, 'failed to bind to socket:', e
        
	
	while True:
		data, address = global_socket.recvfrom(1024)
		unpacked = struct.unpack(b"ii", data)
		g_review_count_target = unpacked[0]
		g_review_count_done = unpacked[1]
		g_pb_notifier.signal_update()
		
	
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
		
## Set up variables for progress bar

failed = 0
progressBar = None
mx = 0

pbdStyle = QStyleFactory.create("%s" % (pbStyle)) # Don't touch.

#Defining palette in case needed for custom colors with themes.
palette = QPalette()
palette.setColor(QPalette.Base, QColor(qbg))
palette.setColor(QPalette.Highlight, QColor(qfg))
palette.setColor(QPalette.Button, QColor(qbg))
palette.setColor(QPalette.WindowText, QColor(qtxt))
palette.setColor(QPalette.Window, QColor(qbg))

if maxWidth:
    if orientationHV == Qt.Horizontal:
        restrictSize = "max-height: %s;" % maxWidth
    else:
        restrictSize = "max-width: %s;" % maxWidth
else:
    restrictSize = ""

def _dock(pb):
    """Dock for the progress bar. Giving it a blank title bar,
        making sure to set focus back to the reviewer."""
    dock = QDockWidget()
    tWidget = QWidget()
    dock.setObjectName("pbDock")
    dock.setWidget(pb)
    dock.setTitleBarWidget( tWidget )
    
    ## Note: if there is another widget already in this dock position, we have to add ourself to the list

    # first check existing widgets
    existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]

    # then add ourselves
    mw.addDockWidget(dockArea, dock)

    # stack with any existing widgets
    if len(existing_widgets) > 0:
        mw.setDockNestingEnabled(True)

        if dockArea == Qt.TopDockWidgetArea or dockArea == Qt.BottomDockWidgetArea:
            stack_method = Qt.Vertical
        if dockArea == Qt.LeftDockWidgetArea or dockArea == Qt.RightDockWidgetArea:
            stack_method = Qt.Horizontal
        mw.splitDockWidget(existing_widgets[0], dock, stack_method)

    if qbr > 0 or pbdStyle != None:
        # Matches background for round corners.
        # Also handles background for themes' percentage text.
        mw.setPalette(palette)
    mw.web.setFocus()
    return dock

	
def create_progressbar():	
    """Initialize and set parameters for progress bar, adding it to the dock."""

    global g_pb_notifier

    g_pb_notifier = ProgressBarNotifier(update_progressbar)

    progressBar = QProgressBar()
    progressBar.setTextVisible(True)
    progressBar.setValue(0)
    progressBar.setFormat("Quake III Anki - Waiting for connection")	
    progressBar.setOrientation(orientationHV)
    if pbdStyle == None:
        progressBar.setStyleSheet(
        '''
                    QProgressBar
                {
                    text-align:center;
                    color:%s;
                    background-color: %s;
                    border-radius: %dpx;
                    %s
                }
                    QProgressBar::chunk
                {
                    background-color: %s;
                    margin: 0px;
                    border-radius: %dpx;
                }
                ''' % (qtxt, qbg, qbr, restrictSize, qfg, qbr))
    else:
        progressBar.setStyle(pbdStyle)
        progressBar.setPalette(palette)
    _dock(progressBar)
    return progressBar
	
def setup_progressbar():
	global progressBar
	progressBar = create_progressbar()

def update_progressbar():
    """Update progress bar; hiding/showing prevents flashing bug."""
    global mx
    if progressBar:
	
		if g_review_count_target == -1:
			# didn't get target review count from quake3
			progressBar.setValue(0)
			progressBar.setFormat("Quake III not connected")
		else:
			progressBar.setRange(0, g_review_count_target)
			progressBar.setValue(g_review_count_done)
			if g_review_count_done < g_review_count_target:
				progressBar.setFormat("Quake III %d / %d" % (g_review_count_done, g_review_count_target))
			else:
				progressBar.setFormat("Quake III all reviews done")
		


addHook("showAnswer", cardReview)	
addHook("profileLoaded", start_up)
addHook("profileLoaded", setup_progressbar)
addHook("showQuestion", update_progressbar)

Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, "around")
		

