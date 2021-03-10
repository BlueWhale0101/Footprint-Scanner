import subprocess
import os
import signal
import pickle
import io
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from makeCall import *

import numpy as np
import datetime
from time import sleep
#Imports for spectrogram
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import seaborn as sns
import matplotlib.pylab as plt

class MplCanvas(FigureCanvasQTAgg):
    #This is a class for setting up the embedded matplotlib figure
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class WaterfallWindow(QMainWindow):

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
            self.scanType = 'UHF'
        elif self.configDict['title'] == 'VHF Scan':
            self.scanTypeBaseline = 'VHFBaseline'
            self.scanType = 'VHF'
        elif self.configDict['title'] == 'Full Scan':
            # For full scans, use the UHF baseline since it's more relevant.
            self.scanTypeBaseline = 'UHFBaseline'
            self.scanType = 'Full'
        else:
            # Something is wrong, no baseline is passed in.
            from warnings import warn
            warn('something went wrong. No baseline is set, WaterfallView is going to crash')
        # Main Layout creation
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()

        # Start the first scan so there is data in the pipe
        self.initScanMethod()
        #Init the main graph
        self.avgPower = []
        self.timeData = []

        # Show the scan Data
        self.powerGraph = MplCanvas(self, width=8, height=5, dpi=150)
        self.plotRef = None
        self.axesRef = self.powerGraph.figure.axes[0]
        #self.axesRef.set_xlim(0, 1000)

        #Debug data, sample plot
        uniform_data = np.random.random((1600, 1600))
        self.axesRef.imshow(uniform_data)
        # from PyQt5.QtCore import pyqtRemoveInputHook
        # from pdb import set_trace
        # pyqtRemoveInputHook()
        # set_trace()
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
        self.dataFileName = "Data/" +\
            datetime.datetime.now().strftime('%d%m%y_%H%M%S_') + self.scanType + '_scan'
        self.currentCommand = makeScanCall(fileName=self.dataFileName, hzLow = self.configDict['hzLow'], hzHigh = self.configDict['hzHigh'], \
            numBins = self.configDict['numBins'], gain = self.configDict['gain'],  repeats= self.configDict['repeats'], exitTimer = self.configDict['exitTimer'])
        self.binaryLineLength, self.actualBandwidth = calcLineLength(self.currentCommand) #calculates the number of bits in one row of the output file and detects the bandwidth of this device.
        # This opens the command asynchronously. poll whether the scan is running with p.poll().
        # This returns 0 if the scan is done or None if it is still going.
        self.currentScanCommandProcess = subprocess.Popen(self.currentCommand, shell=True, stdout = subprocess.PIPE,\
                                        stdin = subprocess.PIPE, stderr = subprocess.PIPE, preexec_fn=os.setsid)
        self.currentScanTime = datetime.datetime.now()
        while not os.path.exists(self.dataFileName+'.bin'):
            sleep(.5)
        self.dataFileStream = open(self.dataFileName+'.bin', 'rb')

    def updateMethod(self):
        pass

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print("User has closed the window")
        self.dataFileStream.close()
        self.updateTimer.stop()
        os.killpg(os.getpgid(self.currentScanCommandProcess.pid), signal.SIGTERM)
        self.currentScanCommandProcess.wait(10)
        event.accept()


  #from PyQt5.QtCore import pyqtRemoveInputHook
  #from pdb import set_trace
  #pyqtRemoveInputHook()
  #set_trace()
