'''
GPS Heads Up Display is a HUD for tactical enemy GPS effects. It will notify the user via the status
circle, and connects the user to various helpful information and actions, such as a waterfall scan of the L2 GPS
band and the average power reading for L1 and L2 up to that point.
'''
from PyQt5.QtWidgets import QMainWindow, QAction, QScrollArea, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from keyFunctions import *
from WaterfallView import WaterfallWindow
import numpy as np
from time import sleep
import subprocess
import datetime
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
        #set constants and key data bins
        self.actualBandwidth = None
        self.currentSpectra = 'L1'
        self.gpsSpectra = {'L1':{'title':'GPS Scan','hzLow':'1575400000', 'hzHigh':'1575440000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'30s','avgPwr':'-65'},\
         'L2':{'title':'GPS Scan', 'hzLow':'1227580000', 'hzHigh':'1227620000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'30s','avgPwr':'-65'}}
        self.dataMatrix = {'L1':np.array([]), 'L2':np.array([])}
        #Initial layout setup
        self.CentralWindow = QWidget()
        self.CentralWindow.setStyleSheet("QWidget{ background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #627876, stop: 1 #c6f5f0); }\
                            border: 1px solid;}")
        self.MainLayout = QGridLayout()
        #self.MainLayout.addWidget(widget, row, col, rowspan, colspan)

        #System messages
        self.sysMsgScrollArea = QScrollArea()
        self.sysMsgScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.sysMsgScrollArea.setWidgetResizable(True)
        self.sysMsgWidget = QWidget()
        self.sysMsgLayout = QVBoxLayout()
        self.sysMsgLayout.addWidget(msgLabel('Initializing...'))
        self.sysMsgWidget.setLayout(self.sysMsgLayout)
        self.sysMsgScrollArea.setWidget(self.sysMsgWidget)
        self.sysMsgWidget.setStyleSheet("QWidget{\
                            background-color: #363636\
                            }")
        self.MainLayout.addWidget(self.sysMsgScrollArea, 1, 1, 7, 10)
        #Power Labels Style sheet
        pwrLabelStyleSheet = "QLabel{ background-color: #325e47;\
                            color:#ffffff;\
                            border-radius:8px;\
                            border: 1px solid;}"
        #L1 Avg Power display
        self.L1Label = QLabel('L1 Avg Pwr: ')
        self.L1Label.setStyleSheet(pwrLabelStyleSheet)
        self.MainLayout.addWidget(self.L1Label, 8, 1, 1, 3)
        self.L1AvgPwrField = QLabel('-65')
        self.L1AvgPwrField.setStyleSheet(pwrLabelStyleSheet)
        self.MainLayout.addWidget(self.L1AvgPwrField, 8, 4, 1, 6)
        #L2 Avg Power display
        self.L2Label = QLabel('L2 Avg Pwr: ')
        self.L2Label.setStyleSheet(pwrLabelStyleSheet)
        self.MainLayout.addWidget(self.L2Label, 9, 1, 1, 3)
        self.L2AvgPwrField = QLabel('-65')
        self.L2AvgPwrField.setStyleSheet(pwrLabelStyleSheet)
        self.MainLayout.addWidget(self.L2AvgPwrField, 9, 4, 1, 6)
        #Status Button
        self.statusButton = QPushButton('Status')
        self.statusButton.setStyleSheet("QPushButton{ border-radius:30px;\
                            height: 35em;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            border: 1px solid;}")
        self.MainLayout.addWidget(self.statusButton, 1, 12, 7, 6)
        #Scanner Button
        self.scannerButton = QPushButton('Scan GPS L1')
        self.scannerButton.clicked.connect(self.GPSScanMethod)
        self.scannerButton.setStyleSheet("QPushButton{ border-radius:30px;\
                            height: 2em;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #33cfff, stop: 1 #2b50bd); }\
                            border: 1px solid;\
                            QPushButton:pressed {background-color: #fae22d};")
        self.MainLayout.addWidget(self.scannerButton, 8, 12, 2, 6)
        #Close button
        self.closeButton = QPushButton('Close')
        self.closeButton.setStyleSheet("QPushButton{ border-radius:8px;\
                            border: 1px solid;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            QPushButton:pressed {background-color: #fae22d}")
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

        #If the last scan ended, choose the next source and start another scan
        #check if there is a process
        if hasattr(self, 'currentScanCommandProcess'):
            #There is a process
            if self.currentScanCommandProcess.poll() == 0:
                #there is a process, but it has stopped
                #Determine what we are scanning now
                if self.currentSpectra == 'L1':
                    self.currentSpectra = 'L2'
                    self.sysMsgLayout.addWidget(msgLabel('Scanning L2...'))
                elif self.currentSpectra == 'L2':
                    self.currentSpectra = 'L1'
                    self.sysMsgLayout.addWidget(msgLabel('Scanning L1...'))
                self.initScanMethod()
        else:#There is no process
            self.sysMsgLayout.addWidget(msgLabel('Scanning L1...'))
            self.initScanMethod()
        #Get the updated data
        self.updateFromBin()


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
        print('updatin from bin')
        lastPos = self.dataFileStream.tell()
        allNewData = self.dataFileStream.read()
        if len(allNewData) == 0:
            print('nothing written yet...')
            return
        elif np.mod(len(allNewData), self.binaryLineLength) > 0:
            print('got some data')
            #There is a partial row here, ane there may be less than a full row.
            #keep the complete rows,
            #and reset the pointer to the start of the next row for next update
            numLines = np.floor(len(allNewData)/self.binaryLineLength)
            self.dataFileStream.seek(lastPos)
            if numLines == 0:
                print('not enough, still waiting...')
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
        print('got enough for at least a line')
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
            print(self.currentSpectra+ ' has rows: '+str(self.dataMatrix[self.currentSpectra].shape[0]))
            if self.dataMatrix[self.currentSpectra].shape[0] > 50:
                self.dataMatrix[self.currentSpectra] = self.dataMatrix[self.currentSpectra][self.dataMatrix[self.currentSpectra].shape[0]-1000:, :] #just the last 1000 rows
                print('only taking last 50 lines...')
        #From the last line we used, update the average GPS power
        newAvg = str(round(np.average(np.array([list(newLine)])), 1))
        self.L2AvgPwrField
        if self.currentSpectra == 'L1':
            self.L1AvgPwrField.setText(newAvg)
        else:
            self.L2AvgPwrField.setText(newAvg)


    def GPSScanMethod(self):
        #End the current scan
        self.dataFileStream.close()
        self.updateTimer.stop()
        os.killpg(os.getpgid(self.currentScanCommandProcess.pid), signal.SIGTERM)
        self.currentScanCommandProcess.wait(10)
        #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
        scanDict = {'title':'GPS Scan', 'hzLow':'1227590000', 'hzHigh':'1227610000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'1m'}
        self.ScanWindow = WaterfallWindow(scanDict)
        #Once the window is closed, start this back up
        self.close()
        #The scanView is modal, so it will block the mainGUI window until we are done with it.
        self.ScanWindow.show()


    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print("User has closed the window")
        self.dataFileStream.close()
        self.updateTimer.stop()
        os.killpg(os.getpgid(self.currentScanCommandProcess.pid), signal.SIGTERM)
        self.currentScanCommandProcess.wait(10)
        event.accept()


class msgLabel(QLabel):
    def __init__(self, msgText):
        super().__init__()
        self.init(msgText)

    def init(self, msgText):
        timeText = datetime.datetime.now().strftime('%H:%M:%S')
        self.setText(timeText+' '+msgText)
        self.setStyleSheet("QLabel{\
        color:#11c900;\
        }")
'''
##############################################
from PyQt5.QtCore import pyqtRemoveInputHook
from pdb import set_trace
pyqtRemoveInputHook()
set_trace()
##############################################
'''
