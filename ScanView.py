import sys, os.path
import subprocess
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from create_baselines import *
import pyqtgraph as pg
import numpy as np
import datetime
import pickle
from random import randint


class ScanWindow(QMainWindow):

    def __init__(self, configDict):
        super().__init__()
        self.initUI(configDict)


    def initUI(self, configDict):
        #Key attribute creation
        #The passed in configDict must have the keys title, minFreq, maxFreq, binSize, interval, exitTimer
        self.configDict = configDict
        self.statusBar()
        self.currentScanTime = 0
        #Main Layout creation
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()

        #Start the first scan so there is data in the pipe
        self.initScanMethod()
        #Show the scan Data
        self.sampleNum = []
        self.avgPower  = []
        pen = pg.mkPen(color=(255, 255, 255))
        self.data_line =  self.powerGraph.plot(self.sampleNum, self.avgPower, pen=pen)

        #call the update event This drives both the scanning calls and the graph updating
        #Set up the update function
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateMethod)
        self.updateTimer.setInterval(1*1000) #interval is set in milliseconds. Run the update every second while debugging, update to a minute later
        self.updateTimer.start()

        #Add the graph widget which shows the moving average of the power, in decibels, of the band.
        self.powerGraph = pg.PlotWidget()
        MainLayout.addWidget(self.powerGraph)

        #Close Button setup
        self.Close_Button = QPushButton('End Scan')
        self.Close_Button.clicked.connect(self.close)
        MainLayout.addWidget(self.Close_Button)

        #Open the window and display the UI
        self.CentralWindow.setLayout(MainLayout)
        self.setCentralWidget(self.CentralWindow)
        self.setWindowTitle('Tactical Footprint Scanner')
        self.setWindowModality(Qt.ApplicationModal)
        self.showMaximized()

    def initScanMethod(self):
        #we have not started the first scan. Build the Command
        #configDict has keys title, minFreq, maxFreq, binSize, interval, exitTimer
        self.dataFileName = "Data/" + datetime.datetime.now().strftime('%y%m%d%H%M%S') + '_scan.csv'
        self.currentCommand = makeCommand(fileName=self.dataFileName, hzLow = self.configDict['minFreq'], hzHigh = self.configDict['maxFreq'], binSize = self.configDict['binSize'], interval = self.configDict['interval'], exitTimer = self.configDict['exitTimer'])
        #This opens the command asynchronously. poll whether the scan is running with p.poll().
        #This returns 0 if the scan is done or None if it is still going.
        self.currentScanCommandCall = subprocess.Popen(self.currentCommand, shell=True)
        self.currentScanTime = datetime.datetime.now()

    def updateMethod(self):
        #Check that the scan is still running. If it has stopped, start a new one
        if self.currentScanCommandCall.poll() == 0:
            #The scan ended. Start a new one.
            self.initScanMethod()
        #Now that we are sure a scan is going, update the data we are plotting
        self.sampleNum.append()
        self.avgPower.append()
        self.powerGraph.update()


        print('Update the graph!')

    def closeEvent(self, event):
        #Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        #This would probably cause problems if the user then immediately tried to start another scan.
        print("User has closed the window")
        self.updateTimer.stop()
        self.currentScanCommandCall.terminate()
        self.currentScanCommandCall.wait()
        event.accept()
