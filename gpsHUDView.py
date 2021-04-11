'''
GPS Heads Up Display is a HUD for tactical enemy GPS effects. It will notify the user via the status
circle, and connects the user to various helpful information and actions, such as a waterfall scan of the L2 GPS
band and the average power reading for L1 and L2 up to that point.
'''
from PyQt5.QtWidgets import QMainWindow, QScrollArea, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from keyFunctions import *
import numpy as np
import datetime
from time import sleep
import subprocess
import os
import signal
import pickle
import io
import struct

class gpsHUDView(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #set constants
        self.actualBandwidth = None
        self.currentSpectra = 'L1'
        #Initial layout setup
        self.CentralWindow = QWidget()
        self.MainLayout = QGridLayout()
        #self.MainLayout.addWidget(widget, row, col, rowspan, colspan)

        #System messages
        self.sysMsgScrollArea = QScrollArea()
        self.sysMsgScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.sysMsgScrollArea.setWidgetResizable(True)
        self.sysMsgWidget = QWidget()
        self.sysMsgLayout = QVBoxLayout()
        self.sysMsgLayout.addWidget(QLabel(datetime.datetime.now().strftime('%H:%M')+'   Initializing...'))
        self.sysMsgWidget.setLayout(self.sysMsgLayout)
        self.sysMsgScrollArea.setWidget(self.sysMsgWidget)
        self.MainLayout.addWidget(self.sysMsgScrollArea, 1, 1, 7, 10)
        #L1 Avg Power display
        self.MainLayout.addWidget(QLabel('L1 Avg Pwr: '), 8, 1, 1, 3)
        self.L1AvgPwrField = QLabel('-65')
        self.MainLayout.addWidget(self.L1AvgPwrField, 8, 4, 1, 6)
        #L2 Avg Power display
        self.MainLayout.addWidget(QLabel('L2 Avg Pwr: '), 9, 1, 1, 3)
        self.L2AvgPwrField = QLabel('-65')
        self.MainLayout.addWidget(self.L2AvgPwrField, 9, 4, 1, 6)
        #Status Button
        self.statusButton = QPushButton('Status')
        self.statusButton.setStyleSheet("QPushButton{ border-radius:400px;\
                            height: 800px;\
                            border: 1px solid;}")
        self.MainLayout.addWidget(self.statusButton, 1, 12, 7, 6)
        #Scanner Button

        #Close button
        self.closeButton = QPushButton('Close')
        self.closeButton.clicked.connect(self.close)
        self.MainLayout.addWidget(self.closeButton, 12, 1, 1, 18)
        #Final setup and display
        self.CentralWindow.setLayout(self.MainLayout)
        self.setCentralWidget(self.CentralWindow)
        self.setWindowTitle('GPS Heads Up Display')
        self.setWindowModality(Qt.ApplicationModal)
        self.showMaximized()

        # Set up the update function
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateMethod)
        # interval is set in milliseconds.
        self.updateTimer.setInterval(1000)
        self.updateTimer.start()

    def updateMethod(self):
        #Master loop function.
        self.gpsSpectra = {'L1':{'title':'GPS Scan','hzLow':'1575400000', 'hzHigh':'1575440000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'30s','avgPwr':'-65'},\
         'L2':{'title':'GPS Scan', 'hzLow':'1227590000', 'hzHigh':'1227610000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'30s','avgPwr':'-65'}}
        self.dataMatrix = {'L1':np.array([]), 'L2':np.array([])}
        #If the last scan ended, choose the next source and start another scan
        #check if there is a process
        if hasattr(self, 'currentScanCommandProcess'):
            #There is a process
            if self.currentScanCommandProcess.poll() == 0:
                #there is a process, but it has stopped
                #Determine what we are scanning now
                if self.currentSpectra == 'L1':
                    self.currentSpectra = 'L2'
                    self.sysMsgLayout.addWidget(QLabel(datetime.datetime.now().strftime('%H:%M')+'   Scanning L2...'))
                elif self.currentSpectra == 'L2':
                    self.currentSpectra = 'L1'
                    self.sysMsgLayout.addWidget(QLabel(datetime.datetime.now().strftime('%H:%M')+'   Scanning L1...'))
                self.initScanMethod()
        else:#There is no process
            self.sysMsgLayout.addWidget(QLabel(datetime.datetime.now().strftime('%H:%M')+'   Scanning L1...'))
            self.initScanMethod()
        #Get the updated data
        self.updateFromBin()
        #self.update()


    def initScanMethod(self):
        # we have not started the scan. Build the Command
        # configDict has keys title, minFreq, maxFreq, binSize, interval, exitTimer
        self.dataFileName = "Data/" +\
            datetime.datetime.now().strftime('%d%m%y_%H%M%S_') + self.currentSpectra + '_scan'
        self.currentCommand = makeScanCall(fileName=self.dataFileName, hzLow = self.gpsSpectra[self.currentSpectra]['hzLow'], hzHigh = self.gpsSpectra[self.currentSpectra]['hzHigh'], \
            numBins = self.gpsSpectra[self.currentSpectra]['numBins'], gain = self.gpsSpectra[self.currentSpectra]['gain'],  repeats= self.gpsSpectra[self.currentSpectra]['repeats'], \
            exitTimer = self.gpsSpectra[self.currentSpectra]['exitTimer'])
        if self.actualBandwidth == None:
            self.binaryLineLength, self.actualBandwidth = calcLineLength(self.currentCommand) #calculates the number of bits in one row of the output file and detects the bandwidth of this device.
        #Before starting the scan, write out a meta data file so that even if we terminate the scan early
        #the data can still be understood.
        generateMetaDataFile(self.currentCommand, self.actualBandwidth)
        # This opens the command asynchronously. poll whether the scan is running with p.poll().
        # This returns 0 if the scan is done or None if it is still going.

        self.currentScanCommandProcess = subprocess.Popen(self.currentCommand, shell=True, preexec_fn=os.setsid)
        print('Running command '+self.currentCommand)
        self.currentScanTime = datetime.datetime.now()
        while not os.path.exists(self.dataFileName+'.bin'):
            sleep(.5)
        self.dataFileStream = open(self.dataFileName+'.bin', 'rb')

        print('Scanning '+self.currentSpectra+'...')

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
            allNewData = self.dataFileStream.read(int(numLines*self.binaryLineLength))
            print('number of bits read in: '+str(len(allNewData)))
            print('number of expected lines: '+str(numLines))

        elif len(allNewData) < self.binaryLineLength:
            #There is not enough data for a full line. reset the pointer
            print('Not enough data yet...')
            print('Current Pointer: '+str(self.dataFileStream.tell()))
            self.dataFileStream.seek(lastPos)
            #wait for the next update cycle
            return

        allNewDataStream = io.BytesIO(allNewData)
        newLineBinary = allNewDataStream.read(self.binaryLineLength)
        #from this block of data, unpack one row at a time and add them to the matrix
        while newLineBinary != b'':
            newLine = struct.unpack('f'*int(self.binaryLineLength/4), newLineBinary) # Any injects to simulate attack need to happen here
            #Update the appropriate data matrix

            if self.dataMatrix[self.currentSpectra].size == 0:
                self.dataMatrix[self.currentSpectra] = np.array([list(newLine)])
            else:
                self.dataMatrix[self.currentSpectra] = np.vstack([self.dataMatrix[self.currentSpectra], list(newLine)])
            #read the data for the next line
            newLineBinary = allNewDataStream.read(self.binaryLineLength)
            if self.dataMatrix[self.currentSpectra].shape[0] > 200:
                self.dataMatrix[self.currentSpectra] = self.dataMatrix[self.currentSpectra][self.dataMatrix[self.currentSpectra].shape[0]-1000:, :] #just the last 1000 rows
                from PyQt5.QtCore import pyqtRemoveInputHook
                from pdb import set_trace
                pyqtRemoveInputHook()
                set_trace()

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print("User has closed the window")
        self.dataFileStream.close()
        self.updateTimer.stop()
        os.killpg(os.getpgid(self.currentScanCommandProcess.pid), signal.SIGTERM)
        self.currentScanCommandProcess.wait(10)
        event.accept()
'''
##############################################
from PyQt5.QtCore import pyqtRemoveInputHook
from pdb import set_trace
pyqtRemoveInputHook()
set_trace()
##############################################
'''
