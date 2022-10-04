'''
WaterfallView generates a window with a matplotlib imshow view showing a waterfall graph of the slice of the spectrum
requested. It takes a dictionary argument with the request for the spectrum to be analyzed. It depends on various
functions in keyFunctions.py and for the C++ drivers to all be setup correctly. It calls the drivers which collect
data from the sensors, then reads data in from the binary file as it is written. The waterfall view is updated at a
rate determined by the type of scan called for.

Update notes 9/25/2022
SimWaterfallView was originally a clone of WaterfallView
'''
#import matplotlib.pylab as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from keyFunctions import *
from SDRSimulator import *
import numpy as np
import datetime
from time import sleep
import subprocess
import os
import signal
import pickle
import io
import struct

#Imports for spectrogram
import matplotlib
matplotlib.use('Qt5Agg')
#import seaborn as sns


class MplCanvas(FigureCanvasQTAgg):
    #This is a class for setting up the embedded matplotlib figure
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class SimWaterfallWindow(QMainWindow):

    def __init__(self, configDict):
        super().__init__()
        self.initUI(configDict)

    def initUI(self, configDict):
        # Key attribute creation
        self.configFile = 'config.scn'
        with open(self.configFile, 'rb') as inFile:
            self.configData = pickle.load(inFile)
        # The passed in configDict must have the keys title, minFreq, maxFreq, binSize, interval, exitTimer
        self.configDict = configDict
        self.actualBandwidth = None  # this is set in the initScanMethod
        self.statusBar()
        self.currentScanTime = 0
        if self.configDict['title'] == 'UHF Scan':
            self.scanTypeBaseline = 'UHFBaseline'
            self.scanType = 'UHF'
            self.vmin = -60
            self.vmax = 0
            intTime = 500  # the interval time is adjusted depending on the type of scan
        elif self.configDict['title'] == 'VHF Scan':
            self.scanTypeBaseline = 'VHFBaseline'
            self.scanType = 'VHF'
            self.vmin = -60
            self.vmax = 0
            intTime = 100  # the interval time is adjusted depending on the type of scan
        elif self.configDict['title'] == 'Full Scan':
            # For full scans, use the UHF baseline since it's more relevant.
            self.scanTypeBaseline = 'UHFBaseline'
            self.scanType = 'Full'
            self.vmin = -60
            self.vmax = 0
            intTime = 500  # the interval time is adjusted depending on the type of scan
        elif self.configDict['title'] == 'GPS Scan':
            # For full scans, use the UHF baseline since it's more relevant.
            self.scanTypeBaseline = 'UHFBaseline'
            self.scanType = 'GPS'
            self.vmin = -75
            self.vmax = -55
            intTime = 100  # the interval time is adjusted depending on the type of scan
        else:
            # Something is wrong, no baseline is passed in.
            from warnings import warn
            warn(
                'something went wrong. No baseline is set, WaterfallView is going to close')
            return
        # Main Layout creation
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()

        # Start the first scan so there is data in the pipe
        #SIM - use the
        self.initScanMethod()

        #Init the main graph
        self.dataMatrix = np.array([])

        # Show the scan Data
        self.powerGraph = MplCanvas(self)
        self.axesRef = self.powerGraph.figure.axes[0]
        heatMap = self.axesRef.imshow(np.array(
            [[0, 0]]), cmap='inferno', aspect='auto', norm=None, vmin=self.vmin, vmax=self.vmax)
        self.powerGraph.figure.colorbar(heatMap)
        self.powerGraph.figure.tight_layout()
        # call the update event This drives both the scanning calls and the graph updating
        # Set up the update function
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateMethod)
        # interval is set in milliseconds. Run the update every second while debugging, update to a minute later
        self.updateTimer.setInterval(intTime)
        self.updateTimer.start()

        # Add the graph widget which shows the moving average of the power, in decibels, of the band.
        MainLayout.addWidget(self.powerGraph)

        # Close Button setup
        self.Close_Button = QPushButton('End Scan')
        self.Close_Button.setStyleSheet("QPushButton{ border-radius:8px;\
                            height: 30px;\
                            border: 1px solid;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            QPushButton:pressed {background-color: #fae22d}")
        self.Close_Button.clicked.connect(self.close)
        MainLayout.addWidget(self.Close_Button)

        # Open the window and display the UI
        self.CentralWindow.setLayout(MainLayout)
        self.setCentralWidget(self.CentralWindow)
        self.setWindowTitle('Tactical Footprint Scanner')
        self.setWindowModality(Qt.ApplicationModal)
        self.showMaximized()

    def initScanMethod(self):
        # we have not started the first scan. Build the Command
        #Return True if the method completed without issues. Return False if there were errors.
        # configDict has keys title, minFreq, maxFreq, binSize, interval, exitTimer
        self.dataFileName = 'Data/' + \
            datetime.datetime.now().strftime('%d%m%y_%H%M%S_') + self.scanType + '_scan'
        print('Scan saving to '+self.dataFileName)
        self.currentCommand = SIM_makeScanCall(fileName=self.dataFileName, hzLow=self.configDict['hzLow'], hzHigh=self.configDict['hzHigh'], numBins=self.configDict[
                                           'numBins'], gain=self.configDict['gain'],  repeats=self.configDict['repeats'], exitTimer=self.configDict['exitTimer'])
        print('###################')
        print(self.currentCommand)
        print('###################')
        # calculates the number of bits in one row of the output file and detects the bandwidth of this device.
        self.binaryLineLength, self.actualBandwidth = SIM_calcLineLength(
            self.currentCommand)

        #Before starting the scan, write out a meta data file so that even if we terminate the scan early
        #the data can still be understood.
        # This opens the command asynchronously. poll whether the scan is running with p.poll().
        # This returns 0 if the scan is done or None if it is still going.
        # The call below is the original, and sets all the standard IO to PIPEs. For some reason,
        #this breaks the FullScan method. It just stops outputting after a few seconds. I left -q in the call
        #and let it otherwise print to the screen, and it works with no errors. This actually gives more insight
        #into whats going on anyway.
        #self.currentScanCommandProcess = subprocess.Popen(self.currentCommand, shell=True, stdout = subprocess.PIPE,\
        #stderr = subprocess.PIPE, preexec_fn=os.setsid)
        self.currentScanCommandProcess = subprocess.Popen(
            self.currentCommand, shell=True, preexec_fn=os.setsid, env=os.environ)
        print('Running command '+self.currentCommand)
        self.currentScanTime = datetime.datetime.now()
        while not os.path.exists(self.dataFileName+'.bin'):
            sleep(.5)
        self.dataFileStream = open(self.dataFileName+'.bin', 'rb')
        return True

    def updateMethod(self):
        #check if there is a process
        if hasattr(self, 'currentScanCommandProcess'):
            #There is a process
            if self.currentScanCommandProcess.poll() == 0:
                #there is a process, but it has stopped
                result = self.initScanMethod()
                if not result:
                    self.parent.close()
                    return

        else:  # There is no process
            result = self.initScanMethod()
            if not result:
                self.close()
                return
        #Get the updated data
        self.updateFromBin()
        if self.dataMatrix.size == 0:
            self.axesRef.imshow(np.array([[0, 0]]), aspect='auto')
        else:
            self.axesRef.imshow(self.dataMatrix, aspect='auto',
                                cmap='inferno', norm=None, vmin=self.vmin, vmax=self.vmax)
        self.powerGraph.draw()

    def updateFromBin(self):
        #Read in all the new data
        lastPos = self.dataFileStream.tell()
        allNewData = self.dataFileStream.read()

        if len(allNewData) == 0:
            print('nothing written yet...')
            return
        elif np.mod(len(allNewData), self.binaryLineLength) > 0:
            #There is a partial row here, ane there may be less than a full row.
            #keep the complete rows,
            #and reset the pointer to the start of the next row for next update
            numLines = np.floor(len(allNewData)/self.binaryLineLength)
            self.dataFileStream.seek(lastPos)
            if numLines == 0:
                #We got less then a row. just end the update and wait for the next cycle
                return
            allNewData = self.dataFileStream.read(
                int(numLines*self.binaryLineLength))
            print('number of bits read in: '+str(len(allNewData)))
            print('number of expected lines: '+str(numLines))

        elif len(allNewData) < self.binaryLineLength:
            #There is not enough data for a full line. reset the pointer
            print('Not enough data yet...')
            print('Current Pointer: '+str(self.dataFileStream.tell()))
            self.dataFileStream.seek(lastPos)
            #wait for the next update cycle
            return

        print('Found '+str(len(allNewData))+' of data')
        allNewDataStream = io.BytesIO(allNewData)
        newLineBinary = allNewDataStream.read(self.binaryLineLength)
        #from this block of data, unpack one row at a time and add them to the matrix
        while newLineBinary != b'':
            # Any injects to simulate attack need to happen here
            newLine = struct.unpack(
                'f'*int(self.binaryLineLength/4), newLineBinary)
            #Update the data matrix
            if self.dataMatrix.size == 0:
                self.dataMatrix = np.array([list(newLine)])
            else:
                self.dataMatrix = np.append(
                    self.dataMatrix, [list(newLine)], axis=0)
            #read the data for the next line
            newLineBinary = allNewDataStream.read(self.binaryLineLength)
        if self.dataMatrix.shape[0] > 150:
            # just the last 150 rows
            self.dataMatrix = self.dataMatrix[self.dataMatrix.shape[0]-150:, :]

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        try:
            print("User has closed the window")
            self.updateTimer.stop()
            self.dataFileStream.close()
            self.currentScanCommandProcess.terminate()
            os.killpg(self.currentScanCommandProcess.pid, signal.SIGINT)
            self.currentScanCommandProcess.wait(10)
            event.accept()
        except:
            from warnings import warn
            warn('Unhandled exception')
            print('either too many clicks or a hw problem.')


'''
    #Set a tracepoint in the Python debugger that works with Qt
    from PyQt5.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()
'''
