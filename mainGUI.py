"""
Footprint Scanner is designed to do VHF, UHF or total spectrum scans (VHF + UHF) in order to assist with a
full operational tactical picture in the EM spectrum
"""
"""
Dev Notes:
    2/14/2021: Initial GUI build. Script to call scan is rtl_power_script. Range of scanner 24 – 1766 MHz
"""




from PyQt5.QtCore import pyqtRemoveInputHook
import pdb
import pickle
import datetime
from SimWaterfallView import SimWaterfallWindow
from WaterfallView import WaterfallWindow
from create_baselines import *
from keyFunctions import *
from gpsHUDView import gpsHUDView
from ScanView import ScanWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QDialog, QDialogButtonBox, QCheckBox, QMessageBox, QPushButton, QScrollArea, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QGroupBox, QFileDialog
import sys
import os.path
class confirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Confirm")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.prompt = QLabel(" ")
        self.layout.addWidget(self.prompt)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


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
                # Use protocol 3 because the PI is on python 3.7
                pickle.dump(self.configData, outFile, protocol=3)

        #General storage space for variables
        self.configData = {'Sim': False}
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

        #Declare  horizontal box for History and sim
        self.HLayout = QHBoxLayout()

        #Browse History Button setup
        self.browseHistory_Button = QPushButton('Browse History')
        self.browseHistory_Button.clicked.connect(self.browseHistoryMethod)
        self.browseHistory_Button.setFixedHeight(ButtonHeight)
        self.browseHistory_Button.setStyleSheet(ButtonStyleSheet)
        self.HLayout.addWidget(self.browseHistory_Button)

        #Set Simulator state checkbox
        self.setSimMode_Checkbox = QCheckBox('Simulation Mode')
        self.setSimMode_Checkbox.setChecked(False)
        self.setSimMode_Checkbox.stateChanged.connect(
            lambda: self.setSimMode(self.setSimMode_Checkbox))
        self.browseHistory_Button.setFixedHeight(ButtonHeight)
        self.HLayout.addWidget(self.setSimMode_Checkbox)

        #Add horizontal layout to main layout
        MainLayout.addLayout(self.HLayout)

        #Open the window and display the UI
        self.CentralWindow.setLayout(MainLayout)
        self.setCentralWidget(self.CentralWindow)
        self.setWindowTitle('Tactical Footprint Scanner')
        self.showMaximized()

    def UHFScanMethod(self):
        if not self.configData['Sim']:
            #Not simulated, use real hardware
            print('Scanning on HW. IF no SDR is connected this will fail')
            #Perform a scan across the tactical UHF spectrum
            #need keys fileName, hzLow, hzHigh, numBins, gain, repeats, exitTimer
            scanDict = {'title': 'UHF Scan', 'hzLow': '225000000', 'hzHigh': '400000000', 'gain': '500',
                        'numBins': '140', 'repeats': '10', 'exitTimer': '3m', 'simMode': self.configData['Sim']}
            self.ScanWindow = WaterfallWindow(scanDict)
            #The scanView is modal, so it will block the mainGUI window until we are done with it.
            self.ScanWindow.show()
        else:
            #Simulated input data. Select a past file to be used for this process
            '''
            #This works fine, but I want to hard set the sim file for now.
            selectedFileDetails, opts = QFileDialog.getOpenFileName(self)
            selFilePath, selFileName = os.path.split(selectedFileDetails)
            selFileBase, selFileExt = os.path.splitext(selFileName)
            '''
            #TODO model file selection for playback data
            simDataInputFilePath = os.path.abspath(
                "SimData\\210922_230951_UHF_scan.bin")
            print('Setting up sim...')
            #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
            scanDict = {'title': 'UHF Scan', 'hzLow': '225000000', 'hzHigh': '400000000', 'gain': '500',
                        'numBins': '140', 'repeats': '10', 'exitTimer': '3m', 'simMode': self.configData['Sim']}
            self.ScanWindow = SimWaterfallWindow(scanDict)
            #The scanView is modal, so it will block the mainGUI window until we are done with it.
            self.ScanWindow.show()

    def VHFScanMethod(self):
        if not self.configData['Sim']:
            #Not simulated, use real hardware
            # Perform a scan across the tactical VHF spectrum
            print('Scanning on HW. IF no SDR is connected this will fail')
            #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
            scanDict = {'title': 'VHF Scan', 'hzLow': '30000000', 'hzHigh': '50000000', 'numBins': '140',
                        'gain': '500', 'repeats': '10', 'exitTimer': '1m', 'simMode': self.configData['Sim']}
            self.ScanWindow = WaterfallWindow(scanDict)
            #The scanView is modal, so it will block the mainGUI window until we are done with it.
            self.ScanWindow.show()
        else:
            #Simulated input data. Select a past file to be used for this process
            #TODO model file selection for playback data
            '''
            #This works fine, but I want to hard set the sim file for now.
            selectedFileDetails, opts = QFileDialog.getOpenFileName(self)
            selFilePath, selFileName = os.path.split(selectedFileDetails)
            selFileBase, selFileExt = os.path.splitext(selFileName)
            '''
            simDataInputFilePath = os.path.abspath(
                "SimData\\210922_223435_VHF_scan.bin")
            print('Setting up sim...')
            #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
            scanDict = {'title': 'VHF Scan', 'hzLow': '30000000', 'hzHigh': '50000000', 'numBins': '140',
                        'gain': '500', 'repeats': '10', 'exitTimer': '1m', 'simMode': self.configData['Sim']}
            self.ScanWindow = SimWaterfallWindow(scanDict)
            #The scanView is modal, so it will block the mainGUI window until we are done with it.
            self.ScanWindow.show()

    def FullScanMethod(self):
        if not self.configData['Sim']:
            #Not simulated, use real hardware#Perform a scan across the spectrum available to the dongle
            #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
            scanDict = {'title': 'Full Scan', 'hzLow': '30000000', 'hzHigh': '1700000000', 'numBins': '10',
                        'gain': '500', 'repeats': '1', 'exitTimer': '10m', 'simMode': self.configData['Sim']}
            self.ScanWindow = WaterfallWindow(scanDict)
            #The scanView is modal, so it will block the mainGUI window until we are done with it.
            self.ScanWindow.show()
        else:
            #Simulated input data. Select a past file to be used for this process
            #TODO model file selection for playback data
            '''
            #This works fine, but I want to hard set the sim file for now.
            selectedFileDetails, opts = QFileDialog.getOpenFileName(self)
            selFilePath, selFileName = os.path.split(selectedFileDetails)
            selFileBase, selFileExt = os.path.splitext(selFileName)
            '''
            simDataInputFilePath = os.path.abspath(
                "SimData\\250922_152601_Full_scan.bin")
            print('Setting up sim...')
            #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
            scanDict = {'title': 'Full Scan', 'hzLow': '30000000', 'hzHigh': '1700000000', 'numBins': '10',
                        'gain': '500', 'repeats': '1', 'exitTimer': '10m', 'simMode': self.configData['Sim']}
            self.ScanWindow = SimWaterfallWindow(scanDict)
            #The scanView is modal, so it will block the mainGUI window until we are done with it.
            self.ScanWindow.show()

    def GPSScanMethod(self):
        #Determine if the user wants the tactical GPS heads up display or the waterfall scan
        dialogBox = QDialog()
        dialogLayout = QVBoxLayout()
        dialogLayout.addWidget(QLabel('Open GPS Scanner or Heads Up display?'))
        scannerButton = QPushButton('GPS Scanner')
        # sets dialogBox.result() to 0. This is also triggered by clicking cancel
        scannerButton.clicked.connect(dialogBox.reject)
        dialogLayout.addWidget(scannerButton)
        hudButton = QPushButton('HUD Display')
        # sets dialogBox.result() to 1
        hudButton.clicked.connect(dialogBox.accept)
        dialogLayout.addWidget(hudButton)
        dialogBox.setLayout(dialogLayout)
        dialogBox.exec_()
        if dialogBox.result():
            #HUD Display was selected
            print('Selected for HUD Display!')
            self.gpsHUDView = gpsHUDView()
            self.gpsHUDView.show()
        else:
            if not self.configData['Sim']:
                #Not simulated, use real hardware#Perform a scan across the spectrum available to the dongle
                #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
                scanDict = {'title': 'GPS Scan', 'hzLow': '1227590000', 'hzHigh': '1227610000', 'numBins': '250',
                            'gain': '500', 'repeats': '10', 'exitTimer': '1m', 'simMode': self.configData['Sim']}
                self.ScanWindow = WaterfallWindow(scanDict)
                #The scanView is modal, so it will block the mainGUI window until we are done with it.
                self.ScanWindow.show()
            else:
                #Simulated input data. Select a past file to be used for this process
                #TODO model file selection for playback data
                '''
                #This works fine, but I want to hard set the sim file for now.
                selectedFileDetails, opts = QFileDialog.getOpenFileName(self)
                selFilePath, selFileName = os.path.split(selectedFileDetails)
                selFileBase, selFileExt = os.path.splitext(selFileName)
                '''
                simDataInputFilePath = os.path.abspath(
                    "SimData\\250922_152601_Full_scan.bin")
                print('Setting up sim...')
                #must have keys title, minFreq, maxFreq, binSize, interval, exitTimer
                scanDict = {'title': 'GPS Scan', 'hzLow': '1227590000', 'hzHigh': '1227610000', 'numBins': '250',
                            'gain': '500', 'repeats': '10', 'exitTimer': '1m', 'simMode': self.configData['Sim']}
                self.ScanWindow = SimWaterfallWindow(scanDict)
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
        #Check if there is already a cal config file. If not, we need to make one with all the bands.
        if not os.path.exists('calibration_config.txt'):
            allBands = True
            self.infoBox = QMessageBox()
            self.infoBox.setWindowTitle('Sucess!')
            self.infoBox.setIcon(QMessageBox.Information)
            self.infoBox.setText(
                "No Calibrations Configuration found. Calibrating all Bands.")
            self.infoBox.setStandardButtons(QMessageBox.Ok)
            self.infoBox.exec()
        else:
            allBands = False
            #Read in the current values.
            with open('calibration_config.txt', 'r') as calFile:
                for line in calFile:
                    if '#' in line:
                        continue
                    lineInfo = line.split(':')
                    if 'L1' in lineInfo[0]:
                        L1_cal_filename = lineInfo[1].strip()
                    elif 'L2' in lineInfo[0]:
                        L2_cal_filename = lineInfo[1].strip()
                    elif 'VHF' in lineInfo[0]:
                        VHF_cal_filename = lineInfo[1].strip()
                    elif 'UHF' in lineInfo[0]:
                        UHF_cal_filename = lineInfo[1].strip()
                    elif 'Full_Spectrum' in lineInfo[0]:
                        Full_Spectrum_cal_filename = lineInfo[1].strip()

        #Popup message box to inform of process. Check if user wants to do all bands
        confirmStart = confirmDialog(self)
        confirmStart.prompt.setText('Perform System Calibration?')
        if confirmStart.exec_():
            if not allBands:
                confirmAllBands = confirmDialog(self)
                confirmAllBands.prompt.setText(
                    'Calibrate all RF bands? Click Cancel to choose bands, or Ok to calibrate all.')
                if confirmAllBands.exec_():
                    allBands = True
        else:
            return
        #Perform requested calibrations, update cal files
        if not allBands:
            confirmStart = confirmDialog(self)
            confirmStart.prompt.setText('Perform GPS Calibration?')
            if confirmStart.exec_():
                L1_cal_filename = calibrate_L1()
                L2_cal_filename = calibrate_L2()
            confirmStart.prompt.setText('Perform VHF Calibration?')
            if confirmStart.exec_():
                VHF_cal_filename = calibrate_VHF()
            confirmStart.prompt.setText('Perform UHF Calibration?')
            if confirmStart.exec_():
                UHF_cal_filename = calibrate_UHF()
            confirmStart.prompt.setText('Perform Full Spectrum Calibration?')
            if confirmStart.exec_():
                FullSpectrum_cal_filename = calibrate_FullSpectrum()
        else:
            L1_cal_filename = calibrate_L1()
            L2_cal_filename = calibrate_L2()
            VHF_cal_filename = calibrate_VHF()
            UHF_cal_filename = calibrate_UHF()
            FullSpectrum_cal_filename = calibrate_FullSpectrum()
        #Set the values in the config file.
        with open('calibration_config.txt', 'w') as calFile:
            calFile.write(
                '#Date '+datetime.datetime.now().strftime('%Y-%m-%d')+'\n')
            calFile.write('L1: '+L1_cal_filename+'\n')
            calFile.write('L2: '+L2_cal_filename+'\n')
            calFile.write('VHF: '+VHF_cal_filename+'\n')
            calFile.write('UHF: '+UHF_cal_filename+'\n')
            calFile.write('Full_Spectrum: '+FullSpectrum_cal_filename+'\n')

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
                warningBox.setText(
                    'The selected file could not be loaded. No meta data file was found.')
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
                warningBox.setText(
                    'The selected file could not be loaded. No meta data file was found.')
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
