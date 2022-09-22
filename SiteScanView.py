import subprocess
import os
import signal
import pickle
import io
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt
from create_baselines import *

import numpy as np
import datetime
from time import sleep


class SiteScanWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Key attribute creation
        self.configFile = 'config.scn'
        with open(self.configFile, 'rb') as inFile:
            self.configData = pickle.load(inFile)
        # The passed in configDict must have the keys title, minFreq, maxFreq, binSize, interval, exitTimer
        self.statusBar()

        #Setup main app window
        self.CentralWindow = QWidget()
        MainLayout = QGridLayout()
        ButtonHeight = 100
        ButtonWidth = 100
        ButtonStyleSheet = "QPushButton{ border-radius:50px;\
                            border: 1px solid;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            QPushButton:pressed {background-color: #fae22d}"

        #QGridLayout addWidget(Widget, row, column, rowspan, columnspan)
        #Location Survey Buttons grid setup
        #North
        self.NorthSensorButton = QPushButton('Scan \nNorth')
        self.NorthSensorButton.clicked.connect(self.SiteScanMethod)
        self.NorthSensorButton.setFixedHeight(ButtonHeight)
        self.NorthSensorButton.setFixedWidth(ButtonWidth)
        self.NorthSensorButton.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.NorthSensorButton, 1, 2, 1, 1)
        #North West
        self.NorthWestSensorButton = QPushButton('Scan\nNorthWest')
        self.NorthWestSensorButton.clicked.connect(self.SiteScanMethod)
        self.NorthWestSensorButton.setFixedHeight(ButtonHeight)
        self.NorthWestSensorButton.setFixedWidth(ButtonWidth)
        self.NorthWestSensorButton.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.NorthWestSensorButton, 2, 1, 1, 1)
        #North East
        self.NorthEastSensorButton = QPushButton('Scan\nNorthEast')
        self.NorthEastSensorButton.clicked.connect(self.SiteScanMethod)
        self.NorthEastSensorButton.setFixedHeight(ButtonHeight)
        self.NorthEastSensorButton.setFixedWidth(ButtonWidth)
        self.NorthEastSensorButton.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.NorthEastSensorButton, 2, 3, 1, 1)
        #South West
        self.SouthWestSensorButton = QPushButton('Scan\nSouthWest')
        self.SouthWestSensorButton.clicked.connect(self.SiteScanMethod)
        self.SouthWestSensorButton.setFixedHeight(ButtonHeight)
        self.SouthWestSensorButton.setFixedWidth(ButtonWidth)
        self.SouthWestSensorButton.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.SouthWestSensorButton, 3, 1, 1, 1)
        #South East
        self.SouthEastSensorButton = QPushButton('Scan\nSouthEast')
        self.SouthEastSensorButton.clicked.connect(self.SiteScanMethod)
        self.SouthEastSensorButton.setFixedHeight(ButtonHeight)
        self.SouthEastSensorButton.setFixedWidth(ButtonWidth)
        self.SouthEastSensorButton.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.SouthEastSensorButton, 3, 3, 1, 1)
        #South
        self.SouthSensorButton = QPushButton('Scan\nSouth')
        self.SouthSensorButton.clicked.connect(self.SiteScanMethod)
        self.SouthSensorButton.setFixedHeight(ButtonHeight)
        self.SouthSensorButton.setFixedWidth(ButtonWidth)
        self.SouthSensorButton.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.SouthSensorButton, 4, 2, 1, 1)

        # Close Button setup
        self.Close_Button = QPushButton('Results')
        self.Close_Button.clicked.connect(self.genSummaryMethod)
        MainLayout.addWidget(self.Close_Button, 5, 1, 1, 3)

        # Close Button setup
        self.Close_Button = QPushButton('Close')
        self.Close_Button.clicked.connect(self.close)
        MainLayout.addWidget(self.Close_Button, 6, 1, 1, 3)

        # Open the window and display the UI
        self.CentralWindow.setLayout(MainLayout)
        self.setCentralWidget(self.CentralWindow)
        self.setWindowTitle('Site Spectrum Survey')
        self.setWindowModality(Qt.ApplicationModal)
        self.showMaximized()

    def SiteScanMethod(self):
        #VHF Scan

        #VHF Results

        #UHF Scan`

        #UHF Results

        #Gen a new style sheet for the button based off of Results
        resultPoorColor = '#ff0000'
        resultFairColor = "#ffff00"
        resultGoodColor = "#60ff55"

        result1 = resultGoodColor
        result2 = resultFairColor

        ButtonStyleSheet = "QPushButton{ border-radius:50px;\
                            border: 1px solid;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 %result1, stop: 1 %result2); }\
                            QPushButton:pressed {background-color: #fae22d}"

        #This is obviously a poor way to do this, but I can't remember the better way off hand.
        ButtonStyleSheet = ButtonStyleSheet.replace('%result1', result1)
        ButtonStyleSheet = ButtonStyleSheet.replace('%result2', result2)
        self.sender().setStyleSheet(ButtonStyleSheet)

    def genSummaryMethod(self):
        pass

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print("User has closed the window")
        event.accept()


# from pdb import set_trace
# from PyQt5.QtCore import pyqtRemoveInputHook
# pyqtRemoveInputHook()
# set_trace()
