import subprocess
import os
import signal
import pickle
import io
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
        pen = pg.mkPen(color=(242, 245, 66))
        self.data_line = self.powerGraph.plot(self.avgPower, pen=pen)

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

    def updateMethod(self):
        # Check that the scan is still running. If it has stopped, start a new one
        if self.currentScanCommandCall.poll() == 0:
            # The scan ended. Start a new one.
            print('New file: ' + self.dataFileName)
            self.initScanMethod()
            sleep(1)
        # Now that we are sure a scan is going, update the data we are plotting
        with io.FileIO(self.dataFileName) as inStream:
            # Get all the data which has been written since the last time.
            rawData = inStream.read()
            timeout = 0
            if rawData == b'':
                # some issues with reading too fast
                print('No data, skip')
                return
            # Get the numeric data
            dataArray = np.genfromtxt(io.StringIO(
                rawData.decode('utf-8')), delimiter=',', encoding='utf-8')
            print("#######################")
            for reading in dataArray:
                dbPower = np.median(reading[6:-2])
                # db have to be converted to a dec to be added and subtracted
                newPower = np.log10(
                    np.abs(10**dbPower - 10**np.median(self.configData[self.scanTypeBaseline][0])))
                if len(self.avgPower) > 3:
                    # If there is enough data in the list,
                    movingAvg = np.average(
                        [self.avgPower[-2], self.avgPower[-1], newPower])
                    self.avgPower.append(movingAvg)
                    self.data_line.setData(self.avgPower)
                else:
                    self.avgPower.append(newPower)
                    self.data_line.setData(self.avgPower)
            print(self.avgPower)
        # Don't let the plotter build up more then 60 points. after 60 seconds, this just becomes a rolling plot
        if len(self.avgPower) > 60:
            self.avgPower = self.avgPower[-60:]

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print("User has closed the window")
        self.updateTimer.stop()
        os.killpg(os.getpgid(self.currentScanCommandCall.pid), signal.SIGTERM)
        self.currentScanCommandCall.wait(10)
        event.accept()


# from pdb import set_trace
# from PyQt5.QtCore import pyqtRemoveInputHook
# pyqtRemoveInputHook()
# set_trace()
