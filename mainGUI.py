"""
Footprint Scanner is designed to do VHF, UHF or total spectrum scans (VHF + UHF) in order to assist with a
full operational tactical picture in the EM spectrum
"""
"""
Dev Notes:
    2/14/2021: Initial GUI build. Script to call scan is rtl_power_script. Range of scanner 24 – 1766 MHz
"""
import sys, os.path
from PyQt5.QtWidgets import QMainWindow, QDialog, QMessageBox, QPushButton, QScrollArea, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QGroupBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from create_baselines import *
from ScanView import ScanWindow
from gpsHUDView import gpsHUDView
from keyFunctions import *
from WaterfallView import WaterfallWindow
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

        #GPS Button setup
        self.GPS_Button = QPushButton('GPS Scan')
        self.GPS_Button.clicked.connect(self.GPSScanMethod)
        self.GPS_Button.setFixedHeight(ButtonHeight)
        self.GPS_Button.setStyleSheet(ButtonStyleSheet)
        MainLayout.addWidget(self.GPS_Button)

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
        #Perform a scan across the tactical UHF spectrum
        #need keys fileName, hzLow, hzHigh, numBins, gain, repeats, exitTimer
        scanDict = {'title':'UHF Scan', 'hzLow':'225000000', 'hzHigh':'400000000', 'gain': '500', 'numBins':'140', 'repeats':'10', 'exitTimer':'3m'}
        self.ScanWindow = WaterfallWindow(scanDict)
        #The scanView is modal, so it will block the mainGUI window until we are done with it.
        self.ScanWindow.show()

    def VHFScanMethod(self):
        #Perform a scan across the tactical VHF spectrum
        #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
        scanDict = {'title':'VHF Scan', 'hzLow':'30000000', 'hzHigh':'50000000', 'numBins':'140', 'gain': '500', 'repeats':'10', 'exitTimer':'1m'}
        self.ScanWindow = WaterfallWindow(scanDict)
        #The scanView is modal, so it will block the mainGUI window until we are done with it.
        self.ScanWindow.show()


    def FullScanMethod(self):
        #Perform a scan across the spectrum available to the dongle
        #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
        scanDict = {'title':'Full Scan', 'hzLow':'30000000', 'hzHigh':'1700000000', 'numBins':'10', 'gain': '500', 'repeats':'1', 'exitTimer':'10m'}
        self.ScanWindow = WaterfallWindow(scanDict)
        #The scanView is modal, so it will block the mainGUI window until we are done with it.
        self.ScanWindow.show()

    def GPSScanMethod(self):
        #Determine if the user wants the tactical GPS heads up display or the waterfall scan
        dialogBox = QDialog()
        dialogLayout = QVBoxLayout()
        dialogLayout.addWidget(QLabel('Open GPS Scanner or Heads Up display?'))
        scannerButton = QPushButton('GPS Scanner')
        scannerButton.clicked.connect(dialogBox.reject) #sets dialogBox.result() to 0. This is also triggered by clicking cancel
        dialogLayout.addWidget(scannerButton)
        hudButton = QPushButton('HUD Display')
        hudButton.clicked.connect(dialogBox.accept) #sets dialogBox.result() to 1
        dialogLayout.addWidget(hudButton)
        dialogBox.setLayout(dialogLayout)
        dialogBox.exec_()
        if dialogBox.result():
            #HUD Display was selected
            print('Selected for HUD Display!')
            self.gpsHUDView = gpsHUDView()
            self.gpsHUDView.show()
        else:
            #Open a new window with immediate tactical info (Relative power level)
            #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
            scanDict = {'title':'GPS Scan', 'hzLow':'1227590000', 'hzHigh':'1227610000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'1m'}
            self.ScanWindow = WaterfallWindow(scanDict)
            #The scanView is modal, so it will block the mainGUI window until we are done with it.
            self.ScanWindow.show()

    def calibrateMethod(self):
        '''
        The calibration method scans the environment across the entire UHF and VHF
        frequency ranges. It returns the median power received across the frequency bands
        for each band, in dB. The difference between this value and the filtered value
        will later be used to determine whether anything unexpected is happening
        in the spectrum.
        '''
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
        '''
        Open a file browser in the Data folder.
        If the user selects an image, just open the image.
        If the user selects a data file, convert it to an image with keyFunctions.dataToWaterfallImage(recordFile=None, **kwargs)
        '''
        selectedFileDetails, opts = QFileDialog.getOpenFileName(self)
        selFilePath, selFileName = os.path.split(selectedFileDetails)
        selFileBase, selFileExt = os.path.splitext(selFileName)
        if selFileExt == '.jpg':
            #This is an image, and hopefully one of the ones that we generated previously.
            #Try and open it with internal tools.
            os.system('xdg-open '+selectedFileDetails)
        elif selFileExt == '.bin':
            #This is a binary file. We need to ensure that the associated meta data file is available.
            if not os.path.exists(os.path.join(selFilePath, selFileBase+'.met')):
                #It doesn't exist. show a popup and break out.
                warningBox = QMessageBox()
                warningBox.setText('The selected file could not be loaded. No meta data file was found.')
                warningBox.setWindowTitle('Load Failed')
                warningBox.setModal(True)
                warningBox.exec_()
                return
            #The meta file is present. Do the conversion.
            dataToWaterfallImage(os.path.join(selFilePath, selFileBase))
        elif selFileExt == '.met':
            #This is a metadata file. We need to ensure that the associated binary data file is available.
            if not os.path.exists(os.path.join(selFilePath, selFileBase+'.bin')):
                #It doesn't exist. show a popup and break out.
                warningBox = QMessageBox()
                warningBox.setText('The selected file could not be loaded. No meta data file was found.')
                warningBox.setWindowTitle('Load Failed')
                warningBox.setModal(True)
                warningBox.exec_()
                return
            #The meta file is present. Do the conversion.
            dataToWaterfallImage(os.path.join(selFilePath, selFileBase))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    #Start the application
    sys.exit(app.exec_())

'''
##############################################
from PyQt5.QtCore import pyqtRemoveInputHook
from pdb import set_trace
pyqtRemoveInputHook()
set_trace()
##############################################
'''
