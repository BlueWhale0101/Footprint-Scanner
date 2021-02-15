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
from create_baselines import *
from ScanView import ScanWindow
import datetime
import pickle
import pdb
from PyQt5.QtCore import pyqtRemoveInputHook


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #Key attribute creation
        self.statusBar()

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
                pickle.dump(self.configData, outFile, protocol=3) #Use protocol 3 because the PI is on python 3.7

        #Main Layout creation
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()

        #self.setFixedWidth(600)
        #self.setFixedHeight(300)

        #Add the main buttons. Lots of detail later.
        ButtonHeight = 75
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
        #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
        scanDict = {'title':'UHF Scan', 'minFreq':'225M', 'maxFreq':'400M', 'binSize':'25k', 'interval':'1', 'exitTimer':'10m'}
        self.UHFScanWindow = ScanWindow(scanDict)
        #The scanView is modal, so it will block the mainGUI window until we are done with it.
        self.UHFScanWindow.show()

    def VHFScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)
        #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
        scanDict = {'title':'VHF Scan', 'minFreq':'30M', 'maxFreq':'50M', 'binSize':'25k', 'interval':'1', 'exitTimer':'10m'}
        self.VHFScanWindow = ScanWindow(scanDict)
        #The scanView is modal, so it will block the mainGUI window until we are done with it.
        self.VHFScanWindow.show()


    def FullScanMethod(self):
        #Open a new window with immediate tactical info (Relative power level)
        #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
        scanDict = {'title':'UHF Scan', 'minFreq':'30M', 'maxFreq':'1700M', 'binSize':'1M', 'interval':'30', 'exitTimer':'20m'}
        self.UHFScanWindow = ScanWindow(scanDict)
        #The scanView is modal, so it will block the mainGUI window until we are done with it.
        self.UHFScanWindow.show()

    def calibrateMethod(self):
        #Popup message box to inform of processself.msgBox = QMessageBox()
        self.statusBar().showMessage('Calibrating....')

        #Perform a calibration, which updates the baseline values.
        self.UHFBaseline = makeUhfBaseline()
        self.VHFBaseline = makeVhfBaseline()

        #Set the values in the config file.
        self.configData['UHFBaseline'] = self.UHFBaseline
        self.configData['VHFBaseline'] = self.VHFBaseline
        with open(self.configFile, 'wb') as outFile:
            pickle.dump(self.configData, outFile, protocol=3)

        #Popup a message that the cal was successful.
        print("succesfully performed Calibration")
        self.msgBox = QMessageBox()
        self.msgBox.setWindowTitle('Sucess!')
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText("Successfully Calibrated System")
        self.msgBox.setStandardButtons(QMessageBox.Ok)
        self.statusBar().showMessage('Done Calibrating')
        self.msgBox.exec()

    def browseHistoryMethod(self):
        #Open a new window with immediate tactical info (Relative power level)

        #Keep scanning until the view is closed.
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    #Start the application
    sys.exit(app.exec_())
