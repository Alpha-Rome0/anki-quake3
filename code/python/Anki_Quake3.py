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
g_review_count_done = 0


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
invertTF = False # If set to True, inverts and goes from right to left or top to bottom.

dockArea = Qt.TopDockWidgetArea # Shows bar at the top. Use with horizontal orientation.

__version__ = '0.1'



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

	#actual_review_count = global_review_count - 1
	#tooltip_text = "Anki Quake3: %d cards left" % actual_review_count
	#tooltip(tooltip_text, period=3000)	

	
def server_loop():
	global g_review_count_target
	global g_review_count_done

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
		number_received = struct.unpack("i", data)[0]
		if number_received > g_review_count_target:
			# update target, reset number of reviews done
			g_review_count_target = number_received
			g_review_count_done = 0
		else:
			# reviews are being done, set current count done
			g_review_count_done = g_review_count_target - number_received 
		
	
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

nm = 0
failed = 0
progressBar = None
mx = 0
limitedBarLength = 0

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


def pb():
    """Initialize and set parameters for progress bar, adding it to the dock."""
    mx = max(1, getMX())
    progressBar = QProgressBar()
    progressBar.setRange(0, mx)
    progressBar.setTextVisible(showPercent or showNumber)
    progressBar.setInvertedAppearance(invertTF)
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
    return progressBar, mx


def getMX():
    """Get deck's card counts for progress bar updates."""
    rev = nu = lrn = 0
    if includeRev:
        rev = mw.col.sched.totalRevForCurrentDeck()
    if includeLrn:
        try:
            lrn = mw.col.sched.lrnCount
        except AttributeError:
            pass
    if includeNew or (includeNewAfterRevs and rev == 0):
        nu = mw.col.sched.totalNewForCurrentDeck()
    total = rev + nu + lrn
    return total

def _getLimitedBarLength():
    """ Get a new bar length based off the number of new / lrn / rev cards you have left for the day """
    global limitedBarLength
    active_decks = mw.col.decks.active()
    if len(active_decks) > 0:
        rev = lrn = nu = 0

        # get number of cards
        for tree in [deck for deck in mw.col.sched.deckDueList() if deck[1] in active_decks]:
            if includeRev:
                rev += tree[2]
            if includeLrn:
                lrn += tree[3]
            if includeNew or (includeNewAfterRevs and rev == 0):
                nu += tree[4]
            
        if nu + rev < mx:
            limitedBarLength = nu+lrn+rev
            return
    limitedBarLength = -1

def _updatePB2():
    """Update progress bar; hiding/showing prevents flashing bug."""
    global mx
    if progressBar:
        total = getMX()
        if total > mx:
            mx = total
            progressBar.setRange(0, mx)
        curr = (mx - total)
        progressBar.hide()

        barSize = mx
        if limitToReviewSettings and limitedBarLength != -1:
            barSize = limitedBarLength

            # I this can happen if the number of "rev" cards increases during the study session
            if curr > barSize:
                barSize = curr
            progressBar.setRange(0, barSize)
            
        if showNumber:
            if showPercent:
                percent = 100 if barSize==0 else int(100*curr/barSize)
                progressBar.setFormat("%d / %d (%d%%)" % (curr, barSize, percent))
            else:
                progressBar.setFormat("%d / %d" % (curr, barSize))
        progressBar.setValue(curr)
        progressBar.show()

def _updatePB():
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
			progressBar.setFormat("Quake III %d / %d" % (g_review_count_done, g_review_count_target))
		
		
def _renderBar(state, oldState):
    global mx, progressBar
    if state == "overview":
        # Set up progress bar at deck's overview page: initialize or modify.
        if not progressBar: progressBar, mx = pb()
        else: rrenderPB()
        _getLimitedBarLength()
        if showNumber:
            _updatePB()
        progressBar.show()


def rrenderPB():
    """Modify progress bar if it was already initialized."""
    global mx
    if getMX() >= 1:
        if mx > getMX(): _updatePB()
        else:
            mx = getMX()
            progressBar.setRange(0, mx)
            progressBar.reset()
    else: progressBar.setValue(mx)




addHook("showAnswer", cardReview)	
addHook("profileLoaded", start_up)
addHook("afterStateChange", _renderBar)
addHook("showQuestion", _updatePB)		

Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, "around")
		

