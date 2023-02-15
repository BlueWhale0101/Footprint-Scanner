"""
Footprint Scanner is designed to do VHF, UHF or total spectrum scans (VHF + UHF) in order to assist with a
full operational tactical picture in the EM spectrum
"""
"""
Dev Notes:
    2/14/2021: Initial GUI build. Script to call scan is rtl_power_script. Range of scanner 24 – 1766 MHz
    2/12/2023: Gutted and reworked along with ASU Dev team. It is VASTLY simplified in terms
    of both readability and actual method.
    """




import pickle
from PyQt5.QtWidgets import QMainWindow, QDialog, QDialogButtonBox, QCheckBox, QMessageBox, QPushButton, QScrollArea, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QGroupBox, QFileDialog
import sys
import os.path
from BinarySpectroViewer import *
from EARSscan import *

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
            #streamScan('225M:400M')
            '''
            Sigh..... this starts a brand new process for the scan window, then this window's
            process blocks until we close the new window. HOWEVER - this doesn't stop the user 
            from opening multiple windows. That's also fine, but it will make both windows 
            appear to perform quite poorly as the two compete for use of the SDR.
            '''
            scanWindowProcess = Process(target=startScanWindow, args=('225M:400M', ))
            scanWindowProcess.start()
            scanWindowProcess.join()
        else:
            #Sim is not implemented yet
            return

    def VHFScanMethod(self):
        if not self.configData['Sim']:
            #streamScan('30M:50M')
            scanWindowProcess = Process(target=startScanWindow, args=('30M:50M', ))
            scanWindowProcess.start()
            scanWindowProcess.join()
        else:
            #Sim is not implemented yet
            return    

    def FullScanMethod(self):
        if not self.configData['Sim']:
            #streamScan('30M:1.7G')
            scanWindowProcess = Process(target=startScanWindow, args=('30M:1.7G', ))
            scanWindowProcess.start()
            scanWindowProcess.join()
        else:
            #Sim is not implemented yet
            return

    def GPSScanMethod(self):
        if not self.configData['Sim']:
            #streamScan('1227590000:1227610000')
            scanWindowProcess = Process(target=startScanWindow, args=('1227590000:1227610000', ))
            scanWindowProcess.start()
            scanWindowProcess.join()
        else:
            #Sim is not implemented yet
            return

    def calibrateMethod(self):
        '''
        The calibration method scans the environment across the entire UHF and VHF
        frequency ranges. It returns the median power received across the frequency bands
        for each band, in dB. The difference between this value and the filtered value
        will later be used to determine whether anything unexpected is happening
        in the spectrum.

        'rtl_power_fftw -f 30M:1.7G -b 500 -n 500 -g 100 -q'
        frequency range is from 30 MHz to 1.7 GHz. 
        Each fft bin is sampled 500 times.
        '''
        if takeBaselineMeasurement() == 'Error':
            self.msgBox = QMessageBox()
            self.msgBox.setWindowTitle('Error!')
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setText("Failed to Calibrate System\nCheck hardware connections")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.statusBar().showMessage('Error Calibrating')
            self.msgBox.exec()
        else:
            #Popup a message that the cal was successful.
            print("succesfully performed Calibration")
            self.msgBox = QMessageBox()
            self.msgBox.setWindowTitle('Sucess!')
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setText("Successfully Calibrated System")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.statusBar().showMessage('Done Calibrating')
            self.msgBox.exec()

    def setSimMode(self, checkBox):
        '''
        If the simulation state is changed, set the global variable for sim mode to True or False
        '''
        if checkBox.isChecked():
            self.configData['Sim'] = True
            print('Setting SIM mode to TRUE')
        else:
            self.configData['Sim'] = False
            print('Setting SIM mode to FALSE')

    def browseHistoryMethod(self):
        '''
        TODO
        Should allow browsing previous data via database retrievals.
        '''
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    #Start the application
    sys.exit(app.exec_())

'''
#####################PyQt Debug trace point#########################
from PyQt5.QtCore import pyqtRemoveInputHook
from pdb import set_trace
pyqtRemoveInputHook()
set_trace()
####################################################################
'''
