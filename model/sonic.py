#!/usr/bin/env python3
progVer = "ver 0.91"

import os
mypath=os.path.abspath(__file__)       # Find the full path of this python script
baseDir=mypath[0:mypath.rfind("/")+1]  # get the path location only (excluding script name)
baseFileName=mypath[mypath.rfind("/")+1:mypath.rfind(".")]
progName = os.path.basename(__file__)

print("%s %s using sonic-pi, web or pi-camera, python3 and OpenCV" % (progName, progVer))
print("Loading Please Wait ....")

# Check for config variable file to import and error out if not found.
configFilePath = baseDir + "config.py"
if not os.path.exists(configFilePath):
    print("ERROR - Missing config.py file - Could not find Configuration file %s" % (configFilePath))
    import urllib
    config_url = "https://raw.github.com/pageauc/sound-track/master/config.py"
    print("   Attempting to Download config.py file from %s" % ( config_url ))
    try:
        wgetfile = urllib.urlopen(config_url)
    except:
        print("ERROR - Download of config.py Failed")
        print("   Try Rerunning the sound-track-install.sh Again.")
        print("   or")
        print("   Perform GitHub curl install per Readme.md")
        print("   and Try Again")
        print("Exiting %s" % ( progName ))
        quit()
    f = open('config.py','wb')
    f.write(wgetfile.read())
    f.close()
# Read Configuration variables from config.py file
from config import *
# import the necessary packages
import io
import time
import cv2
from threading import Thread
from psonic import *


# Calculated Variables Should not need changing by user
####

# See if Web Cam is selected
if WEBCAM:
    CAMERA_WIDTH = WEBCAM_WIDTH
    CAMERA_HEIGHT = WEBCAM_HEIGHT

# Increase size of openCV display window
big_w = int(CAMERA_WIDTH * windowBigger)
big_h = int(CAMERA_HEIGHT * windowBigger)

# initialize hotspot area variables
menuTimeout = 2.0

synthHotxy = (int(CAMERA_WIDTH/synthHotSize),int(CAMERA_HEIGHT/synthHotSize))

# split screen into horz and vert zones for note changes
octaveHotxy = (int(CAMERA_WIDTH/octaveHotSize),int(CAMERA_HEIGHT/octaveHotSize))
octaveStart = octavePicks[0]

notesTotal = len(octaveList[octaveStart][1])
notesHorizZone = int(CAMERA_WIDTH / (notesTotal - 1)) # Calculate Zone Area index
notesVertZone = int(CAMERA_HEIGHT /(notesTotal - 1))

drumHotxy = (int(CAMERA_WIDTH/drumHotSize),int(CAMERA_HEIGHT/drumHotSize)) #Not implemented
drumsTotal = len(drumPicks)
drumHorizZone = int(CAMERA_WIDTH / (drumsTotal - 1)) # Calculate Zone Area index
drumVertZone = int(CAMERA_HEIGHT /(drumsTotal - 1))

noteSleepMin = float(noteSleepMin)  # make sure noteSleepMin is a float

# Color data for OpenCV lines and text
cvBlue = (255,0,0)
cvGreen = (0,255,0)
cvRed = (0,0,255)
FONT_SCALE = .3             # OpenCV window text font size scaling factor default=.5 (lower is smaller)

# These OpenCV Threshold Settings should not have to changed
THRESHOLD_SENSITIVITY = 25
BLUR_SIZE = 10

# These Three functions are optional thread loops
# that can be edited and activated/deactivated from config.py
#----------------------------------------------------------------------------------------------
def drumBass():    # Edit this optional thread loop see config.py drumBassOn variable
    c = chord(E3, MAJOR7)
    while True:
        use_synth(PROPHET)
        play(random.choice(c), release=0.6)
        sleep(0.5)

#-----------------------------------------------------------------------------------------------
def drumKick():  # Edit this optional thread loop see config.py drumKickOn Variable
    while True:
        sample(DRUM_HEAVY_KICK)
        sleep(1)

#-----------------------------------------------------------------------------------------------
def drumSnare(): # Edit this optional thread loop see config.py drumSnareOn Variable
    while True:
        sample(DRUM_SNARE_HARD)
        sleep(1)

#-----------------------------------------------------------------------------------------------


class PiVideoStream:
    def __init__(self, resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=CAMERA_FRAMERATE, rotation=0, hflip=False, vflip=False):
        # initialize the camera settings
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.camera.set(cv2.CAP_PROP_FPS, framerate)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            if self.stopped:
                self.camera.release()
                return

            # read the next frame from the camera
            ret, frame = self.camera.read()

            if ret:
                self.frame = frame

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

#-----------------------------------------------------------------------------------------------
class WebcamVideoStream:
    def __init__(self, CAM_SRC=WEBCAM_SRC, CAM_WIDTH=WEBCAM_WIDTH, CAM_HEIGHT=WEBCAM_HEIGHT):
        # initialize the video camera stream and read the first frame
        # from the stream
        self.stream = CAM_SRC
        self.stream = cv2.VideoCapture(CAM_SRC)
        self.stream.set(3,CAM_WIDTH)
        self.stream.set(4,CAM_HEIGHT)
        (self.grabbed, self.frame) = self.stream.read()

        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                    return

            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
        self.stream.release()
#-----------------------------------------------------------------------------------------------
def trackPoint(grayimage1, grayimage2):
    moveData = []   # initialize list of movementCenterPoints
    biggestArea = MIN_AREA
    # Get differences between the two greyed images
    differenceImage = cv2.absdiff( grayimage1, grayimage2 )
    # Blur difference image to enhance motion vectors
    differenceImage = cv2.blur( differenceImage,(BLUR_SIZE,BLUR_SIZE ))
    # Get threshold of blurred difference image based on THRESHOLD_SENSITIVITY variable
    retval, thresholdImage = cv2.threshold( differenceImage, THRESHOLD_SENSITIVITY, 255, cv2.THRESH_BINARY )
    try:
        thresholdImage, contours, hierarchy = cv2.findContours( thresholdImage, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )
    except:
        contours, hierarchy = cv2.findContours( thresholdImage, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )

    if contours != ():
        for c in contours:
            cArea = cv2.contourArea(c)
            if cArea > biggestArea:
                biggestArea = cArea
                ( x, y, w, h ) = cv2.boundingRect(c)
                cx = int(x + w/2)   # x center point of contour
                cy = int(y + h/2)   # y center point of contour
                moveData = [cx, cy, w, h]
    return moveData

#-----------------------------------------------------------------------------------------------
def playNotes( synthNow, octaveNow, moveData ):
    global menuLock
    global menuTime

    # Get contour data for movement position
    x, y, w, h = moveData[0], moveData[1], moveData[2], moveData[3]

    if notePlayOn:
        notexZone = int( x / notesHorizZone)
        noteyZone = int( y / notesVertZone )
        # Add entries to synthPicks array in config.py for available session synths
        if synthHotOn:   # Screen Hot Spot Area changes synthPick if movement inside area
            if ( x < synthHotxy[0] and y < synthHotxy[1] ) and not menuLock:
                menuLock = True
                menuTime = time.time()
                synthNow += 1
                if synthNow > len(synthPicks) - 1:
                    synthNow = 0
        synthCur = synthList[synthPicks[synthNow]]  # Select current synth from your synthPicks
        synthName = synthCur[1]       # Get the synthName from synthCur
        use_synth(Synth(synthName))   # Activate the selected synthName

        # Add entries to octavePicks array in config.py for available session octaves
        if octaveHotOn:   # Screen Hot Spot Area changes octavePick if movement inside area
            if ( x > CAMERA_WIDTH - octaveHotxy[0] and y < octaveHotxy[1] ) and not menuLock:
                menuLock = True
                menuTime = time.time()
                octaveNow += 1
                if octaveNow > len(octavePicks) - 1:
                    octaveNow = 0
        octaveCur = octaveList[octavePicks[octaveNow]]  # Select current synth from your synthPicks
        octaveNotes = octaveCur[1]   # Get the synthName from synthCur
        note1 = octaveNotes[notexZone]
        note2 = octaveNotes[noteyZone]

        if noteSleepVarOn:   # Vary note sleep duration based on contour height
            noteDelay =  h/float( CAMERA_HEIGHT/noteSleepMax )
            if (noteDelay < noteSleepMin):
                noteDelay = noteSleepMin
            elif (noteDelay > noteSleepMax):
                noteDelay = noteSleepMax
        else:       # Set fixed note sleep duration
            noteDelay = noteSleepMin

        if noteDoubleOn:    # Generate two notes based on contour x, y rather than one
            play(note1)     # Based on x
            sleep(noteDelay)
            play(note2)     # base on y
        else:
            play(note1)
        sleep(noteDelay)

        if verbose:
            if noteDoubleOn:
                print("Notes: zoneXY(%i,%i)  moveXY(%i,%i) cArea(%i*%i)=%i" %
                                  ( notexZone, noteyZone, x, y, w, h, w*h ))
                print("       Synth:%i %s  Octave %i  note1=%i  note2=%i  noteSleep=%.3f seconds" %
                              ( synthCur[0], synthName, octaveCur[0], note1, note2, noteDelay ))
            else:
                print("Note: zoneX(%i)  moveXY(%i,%i) cArea(%i*%i)=%i" %
                                  ( notexZone, x, y, w, h, w*h ))
                print("      Synth:%i %s  Octave %i  note1=%i  noteSleep=%.3f seconds" %
                             ( synthCur[0], synthName, octaveCur[0], note1, noteDelay ))

    if drumPlayOn:
        drumxZone = int( x / drumHorizZone)
        drumyZone = int( y / drumVertZone )

        if drumSleepVarOn:   # Vary note sleep duration based on contour height
            drumDelay =  h/float( CAMERA_HEIGHT/drumSleepMax )
            if (drumDelay < drumSleepMin):
                drumDelay = drumSleepMin
            elif (drumDelay > drumSleepMax):
                drumDelay = drumSleepMax
        else:       # Set fixed note sleep duration
            drumDelay = drumSleepMin

#        if drumHotOn:
#            if ( x < drumHotxy[0] and y > synthHotxy[1] and y < synthHotxy[1] + drumHotxy[1] ) and not menuLock:
#                menuLock = True
#                menuTime = time.time()
#                drumNow += 1
#                if drumNow > len(drumPicks) - 1:
#                    drumNow = 0

        drum1 = drumList[drumPicks[drumxZone]][1]
        drum2 = drumList[drumPicks[drumyZone]][1]
        if drumDoubleOn:
            sample(drum1)
            sleep(drumDelay)
            sample(drum2)
        else:
            sample(drum1)
        sleep(drumDelay)
        if verbose:
            if drumDoubleOn:
                print("Drums: zoneXY(%i,%i)  moveXY(%i,%i)  cArea(%i*%i)=%i" %
                                 ( drumxZone, drumyZone, x, y, w, h, w*h ))
                print("       %i %s  %i %s  drumSleep=%.3f sec" %
                             ( drumList[drumPicks[drumxZone]][0], drum1,
                               drumList[drumPicks[drumyZone]][0], drum2, drumDelay ))
            else:
                print("Drum: zoneX(%i)  moveXY(%i,%i)  cArea(%i*%i)=%i" %
                              ( drumxZone, x, y, w, h, w*h ))
                print("      %i %s  drumSleep=%.3f sec" %
                              ( drumList[drumPicks[drumxZone]][0], drum1, drumDelay ))
    if menuLock:
        if (time.time() - menuTime > menuTimeout) :
            menuLock = False  # unlock motion menu after two second
    return synthNow, octaveNow

#-----------------------------------------------------------------------------------------------
def sonicTrack():
    global menuLock
    global menuTime
    menuTime = time.time()
    menuLock = False

    if windowOn:
        print("press q to quit opencv display")
    else:
        print("press ctrl-c to quit")
    print("Start Motion Tracking ....")
    # initialize image1 using image2 (only done first time)
    vs = WebcamVideoStream()
    image2 = vs.read()
    image1 = image2
    grayimage1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    still_scanning = True
    synthNow = 0   # Initialize first synth selection from synthPicks
    octaveNow = 0  # Initialize first synth selection from

    # These Start Optional Threads for Target functions above
    if drumBassOn:
        bassThread = Thread(target=drumBass)
        bassThread.start()
    if drumSnareOn:
        snareThread = Thread(target=drumSnare)
        snareThread.start()
    if drumKickOn:
        kickThread = Thread(target=drumKick)
        kickThread.start()

    while still_scanning:
        image2 = vs.read()
        grayimage2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        moveData = trackPoint(grayimage1, grayimage2)
        grayimage1 = grayimage2

        if moveData:   # Found Movement
            synthNow, octaveNow = playNotes(synthNow, octaveNow, moveData)
            if windowOn:
                cx = moveData[0]
                cy = moveData[1]
                # show small circle at motion location
                if SHOW_CIRCLE:
                    cv2.circle(image2,(cx,cy),CIRCLE_SIZE, cvGreen, LINE_THICKNESS)
                else:
                    cw = moveData[2]
                    ch = moveData[3]
                    cv2.rectangle(image2,(int(cx - cw/2),int(cy - ch/2)),(int(cx + cw/2), int(cy+ch/2)),
                                                          cvGreen, LINE_THICKNESS)

        if windowOn:
            if notePlayOn:
                if synthHotOn:    # Box top left indicating synthHotOn Area
                    cv2.rectangle(image2,(0,0), synthHotxy, cvBlue, LINE_THICKNESS)
                    synthText = synthList[synthPicks[synthNow]][1]
                    cv2.putText( image2, synthText, (5, int(synthHotxy[1]/2)),
                                    cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE , cvGreen, 1)
                if octaveHotOn:  # Box top right indicating octave HotOn Area
                    cv2.rectangle(image2,(CAMERA_WIDTH - octaveHotxy[0], 0),
                                         (CAMERA_WIDTH - 1,octaveHotxy[1]), cvBlue, LINE_THICKNESS)
                    octaveText = ("octave %i" % octavePicks[octaveNow])
                    cv2.putText( image2, octaveText, (CAMERA_WIDTH - int(octaveHotxy[0] - 5), int(octaveHotxy[1]/2)),
                                    cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE , cvGreen, 1)
                                    
            if drumPlayOn and drumHotOn:
                for i in range ( drumHorizZone, CAMERA_WIDTH, drumHorizZone):
                    cv2.line( image2, (i, 0), (i,CAMERA_HEIGHT ), cvBlue, 1 )
                if drumDoubleOn:
                    for i in range ( drumVertZone, CAMERA_HEIGHT, drumVertZone):
                        cv2.line( image2, (0, i), (CAMERA_WIDTH, i ), cvBlue, 1 )          
            # if windowDiffOn:
            #     cv2.imshow('Difference Image', differenceImage)
            # if windowThreshOn:
            #     cv2.imshow('OpenCV Threshold', thresholdImage)
            if windowBigger > 1:  # Note setting a bigger window will slow the FPS
                image2 = cv2.resize( image2,( big_w, big_h ))
            cv2.imshow('Movement Status  (Press q in Window to Quit)', image2)

            # Close Window if q pressed while movement status window selected
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                vs.stop()
                print("End Motion Tracking")
                still_scanning = False
                quit()

#-----------------------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        while True:
            # Save Cam images frames to an in-program stream
            # Setup video stream on a processor Thread for faster speed
            if WEBCAM:   #  Start Web Cam stream (Note USB webcam must be plugged in)
                print("Initializing USB Web Camera ....")
                vs = WebcamVideoStream().start()
                vs.CAM_SRC = WEBCAM_SRC
                vs.CAM_WIDTH = WEBCAM_WIDTH
                vs.CAM_HEIGHT = WEBCAM_HEIGHT
                time.sleep(4.0)  # Allow WebCam to initialize
            else:
                print("Initializing Pi Camera ....")
                vs = PiVideoStream().start()
                #vs.camera.rotation = CAMERA_ROTATION
                #vs.camera.hflip = CAMERA_HFLIP
                #vs.camera.vflip = CAMERA_VFLIP
                time.sleep(2.0)  # Allow PiCamera to initialize

            sonicTrack()
    except KeyboardInterrupt:
        vs.stop()
        print("")
        print("+++++++++++++++++++++++++++++++++++")
        print("User Pressed Keyboard ctrl-c")
        print("%s %s - Exiting" % (progName, progVer))
        print("+++++++++++++++++++++++++++++++++++")
        print("")
        quit(0)
