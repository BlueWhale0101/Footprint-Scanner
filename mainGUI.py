"""
Footprint Scanner is designed to do VHF, UHF or total spectrum scans (VHF + UHF) in order to assist with a
full operational tactical picture in the EM spectrum
"""
"""
Dev Notes:
    2/14/2021: Initial GUI build. Script to call scan is rtl_power_script. Range of scanner 24 – 1766 MHz
"""
import sys, os.path
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPushButton, QScrollArea, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QGroupBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import datetime
import csv
import pickle
import pdb


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #Key attribute creation

        #Load config file
        self.configFile = 'config.scn'
        if os.path.exists(self.configFile):
            #If the file exists, load in the config data
            with open(self.configFile, 'rb') as inFile:
                self.configData = pickle.load(inFile)
                self.historyFileList = self.configData['historyFileList']
        else:
            self.historyFileList = []
            self.configData = dict()
            self.configData['historyFileList'] = self.historyFileList
            with open(self.configFile, 'wb') as outFile:
                pickle.dump(self.configData, outFile, protocol=pickle.HIGHEST_PROTOCOL)

        #Main Layout creation
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()

        #Add the main buttons. Lots of detail later.
        ButtonHeight = 140
        ButtonStyleSheet = "QPushButton{ border-radius:8px;\
                            border: 1px solid;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            QPushButton:pressed {background-color: #fae22d}"
        #UHF Button setup
        self.UHF_Button = QPushButton('UHF Scan')
        self.UHF_Button.clicked.connect(self.UHFScanMethod)
        self.UHF_Button.setFixedHeight(ButtonHeight)
        self.UHF_Button.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.UHF_Button)

        #VHF Button setup
        self.VHF_Button = QPushButton('VHF Scan')
        self.VHF_Button.clicked.connect(self.VHFScanMethod)
        self.VHF_Button.setFixedHeight(ButtonHeight)
        self.VHF_Button.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.VHF_Button)

        #Full Button setup
        self.Full_Button = QPushButton('Full Scan')
        self.Full_Button.clicked.connect(self.FullScanMethod)
        self.Full_Button.setFixedHeight(ButtonHeight)
        self.Full_Button.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.Full_Button)

        #Calibrate Button setup
        self.Calibrate_Button = QPushButton('Calibrate')
        self.Calibrate_Button.clicked.connect(self.calibrateMethod)
        self.Calibrate_Button.setFixedHeight(ButtonHeight)
        self.Calibrate_Button.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.Calibrate_Button)

        #Browse History Button setup
        self.browseHistory_Button = QPushButton('Browse History')
        self.browseHistory_Button.clicked.connect(self.browseHistoryMethod)
        self.browseHistory_Button.setFixedHeight(ButtonHeight)
        self.browseHistory_Button.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.browseHistory_Button)

        #Open the window and display the UI
        self.CentralWindow.setLayout(MainLayout)
        self.setCentralWidget(self.CentralWindow)
        self.setWindowTitle('Tactical Footprint Scanner')
        self.showMaximized()

    def UHFScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)
        #Open the window
        #Start the scan
        #Keep scanning until the user is done.
        #As files are written out, add the file names to the historyFile list and save them out.
        #Keep scanning until the view is closed.
        pass

    def VHFScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

    def FullScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

    def calibrateMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

    def browseHistoryMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    #Start the application
    sys.exit(app.exec_())
