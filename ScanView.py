import subprocess
import os
import signal
import pickle
import io
import time

from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from create_baselines import *
import pyqtgraph as pg
import numpy as np
import datetime
from time import sleep


class ScanWindow(QMainWindow):

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
        self.statusBar()
        self.currentScanTime = 0
        if self.configDict['title'] == 'UHF Scan':
            self.scanTypeBaseline = 'UHFBaseline'
        elif self.configDict['title'] == 'VHF Scan':
            self.scanTypeBaseline = 'VHFBaseline'
        elif self.configDict['title'] == 'Full Scan':
            # For full scans, use the UHF baseline since it's more relevant.
            self.scanTypeBaseline = 'UHFBaseline'
        else:
            # Something is wrong, no baseline is passed in.
            from warnings import warn
            warn('something went wrong. No baseline is set, ScanView is going to crash')
        # Main Layout creation
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()

        # Start the first scan so there is data in the pipe
        self.initScanMethod()
        # Show the scan Data
        self.powerGraph = pg.PlotWidget()
        self.powerGraph.setBackground((59, 79, 65))
        self.powerGraph.showGrid(x=True, y=True)
        self.avgPower = []
        self.timeData = []

        self.binData = np.array()

        # Show the scan Data
        self.powerGraph = MplCanvas(self, width=5, height=4, dpi=100)
        self.plotRef = None
        self.axesRef = self.powerGraph.figure.axes[0]
        self.axesRef.set_xlim(0, 1000)
        # call the update event This drives both the scanning calls and the graph updating
        # Set up the update function
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateMethod)
        # interval is set in milliseconds. Run the update every second while debugging, update to a minute later
        self.updateTimer.setInterval(1000)
        self.updateTimer.start()

        # Add the graph widget which shows the moving average of the power, in decibels, of the band.
        MainLayout.addWidget(self.powerGraph)

        # Close Button setup
        self.Close_Button = QPushButton('End Scan')
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
        # configDict has keys title, minFreq, maxFreq, binSize, interval, exitTimer
        self.dataFileName = "Data/" + \
            datetime.datetime.now().strftime('%d%m%y_%H%M%S') + '_scan.csv'
        self.currentCommand = makeCommand(fileName=self.dataFileName, hzLow=self.configDict['minFreq'], hzHigh=self.configDict[
                                          'maxFreq'], binSize=self.configDict['binSize'], interval=self.configDict['interval'], exitTimer=self.configDict['exitTimer'])
        # This opens the command asynchronously. poll whether the scan is running with p.poll().
        # This returns 0 if the scan is done or None if it is still going.
        self.currentScanCommandCall = subprocess.Popen(
            self.currentCommand, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        self.currentScanTime = datetime.datetime.now()
        while not os.path.exists(self.dataFileName):
            sleep(.5)
        self.inStream = io.FileIO(self.dataFileName)

    def updateMethod(self):
        #time test
        #TODO remove this after timing is optimized
        if 'lastUpdateTime' not in self.keys():
            self.lastUpdateTime = time.perf_counter()
        else:
            newUpdateTime = time.perf_counter()
            delta = newUpdateTime - self.lastUpdateTime
            self.lastUpdatetime = newUpdateTime
            print('delta: {}'.format(delta))
        # Check that the scan is still running. If it has stopped, start a new one
        if self.currentScanCommandCall.poll() == 0:
            # The scan ended. Start a new one.
            print('New file: ' + self.dataFileName)
            self.inStream.close()
            self.initScanMethod()
        # Now that we are sure a scan is going, update the data we are plotting
        # Get all the data which has been written since the last time.
        rawData = self.inStream.read()
        counter = 0
        if rawData == b'':
            # some issues with reading too fast
            print('No data, skip')
            return
        # Get the numeric data
        dataArray = np.genfromtxt(io.StringIO(
            rawData.decode('utf-8')), delimiter=',', encoding='utf-8')


        #### determine how to slice the data (can be passed 1+ data "bursts" in dataArray) ######
        bucketReadings = dataArray[:,6:-1] ### slice off headings
        identifier = str(dataArray[0][1]) ### grab timestamp
        numRows = 0
        for i in range(len(dataArracleary)):
            if str(dataArray[i][1]) == identifier: ### compare current timestamp to reference
                numRows+=1
            else:
                break
        print(numRows)
        numBins = numRows * len(bucketReadings[0])
        print(numBins)

        formattedData = np.reshape(bucketReadings, (-1,numBins))
        #### each row in formattedData is a burst without headings ##############################

        for reading in dataArray:
            counter += 1
            print(counter)
            if self.configDict['title'] == 'Full Scan':
                dbPower = reading[-1] #In full scan, the bins are so large that only one value is returned.
            else:
                dbPower = np.median(reading[6:-2])
            # db have to be converted to a dec to be added and subtracted
            #newPower = np.log10(
                #np.abs(10**dbPower - 10**np.median(self.configData[self.scanTypeBaseline][0])))
            newPower = dbPower
            if len(self.avgPower) > 3:
                self.avgPower.append(newPower)
                self.timeData.append(len(self.avgPower))
                # TODO This may be the right place to do some filtering to remove noise without removing signals of interest.
            else:
                self.avgPower.append(newPower)
        # Don't let the plotter build up more then 300 points.
        print('end fx length')
        print(len(self.avgPower))
        if len(self.avgPower) > 1000:
            self.avgPower = self.avgPower[-1000:]
            print('new Length: '+str(len(self.avgPower)))
        #Update the graph
        self.data_line.setData(self.avgPower)
        # from pdb import set_trace
        # from PyQt5.QtCore import pyqtRemoveInputHook
        # pyqtRemoveInputHook()
        # set_trace()

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print("User has closed the window")
        self.inStream.close()
        self.updateTimer.stop()
        os.killpg(os.getpgid(self.currentScanCommandCall.pid), signal.SIGTERM)
        self.currentScanCommandCall.wait(10)
        event.accept()
