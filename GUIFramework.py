import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QStackedLayout, QTextEdit
from PyQt5.QtCore import Qt
import pickle
import os.path
from BinarySpectroViewer import *
from multiprocessing import set_start_method
from EARSscan import *

''' Let's set globals up here for any formatting that will be used across all pages'''
ButtonStyleSheet = "QPushButton{ border-radius:8px;\
                            border: 1px solid;\
                            font-size: 14pt; font-weight: bold; \
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            QPushButton:pressed {background-color: #fae22d}"
BackgroundStyle = "background-color: black;"

class MainWidget(QMainWindow):
    def __init__(self, stackLayout):
        super().__init__()

    # Set up main window properties

        # set title for main window
        self.setWindowTitle("E.A.R.")

        ''' TODO: make everything scale correctly based on screen size while maintaining relative sixes between layouts.
        Ex. The buttons of the left layout should be the same width as the recent scans area on the right no matter screen size'''
        # self.setWindowState(Qt.WindowMaximized)

        # changing the background color to black
        self.setStyleSheet(BackgroundStyle)

        # Set up central widget and layout
        self.central_widget = QWidget()
        self.central_layout = QHBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        # Set up left widget and layout
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)

        # create buttons
        self.quick_scan_button = QPushButton('Quick Scan')
        self.toggle_scan_button = QPushButton('Toggle Scan')
        self.simulated_scan_button = QPushButton('Simulated Scan')
        self.calibration_button = QPushButton('Calibration')
        self.MainButtons = [self.quick_scan_button, self.toggle_scan_button, self.simulated_scan_button, self.calibration_button]

        for button in self.MainButtons:
            button.setFixedSize(500, 100)
            button.setFlat(True)
            button.setStyleSheet(ButtonStyleSheet)
            #button.setStyleSheet("font-size: 14pt; font-weight: bold; border: 2px solid gray;border-radius: 10px; background-color: white;")

        # Add buttons to left layout
        for button in self.MainButtons:
            self.left_layout.addWidget(button)

        # Set up right widget and layout
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)

        # Set up alerts/recent scans text area
        '''TODO: this is currently setup very generically as a textbox to be a placeholder,
        but this will need to be fully redone to actually display a list of recent scans that can be
        opened and viewed. Maybe someday have a sort of comparison feature for comparing scans'''
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setFixedSize(500, 400)
        self.alerts_text.setStyleSheet("border: 2px solid; border-radius: 10px; background-color: white;")
        self.alerts_header = QLabel("Recent Scans")
        self.alerts_header.setAlignment(Qt.AlignCenter)
        self.alerts_header.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;")

        # Add alerts header and text to right layout
        self.right_layout.addWidget(self.alerts_header)
        self.right_layout.addWidget(self.alerts_text)

        # Add left and right widgets to central layout
        self.central_layout.addWidget(self.left_widget)
        self.central_layout.addWidget(self.right_widget)

        # Set central widget
        self.setCentralWidget(self.central_widget)

        # set connections for buttons
        self.quick_scan_button.clicked.connect(self.openQuickScanWidget)
        self.toggle_scan_button.clicked.connect(self.openToggleScanWidget)
        self.simulated_scan_button.clicked.connect(self.openSimulatedScanWidget)
        self.calibration_button.clicked.connect(self.calibrateMethod)

        # set stack layout
        self.stackLayout = stackLayout

    def openQuickScanWidget(self):
        self.quickScanWidget = QWidget()
        self.quickScanWidget.setStyleSheet(BackgroundStyle)
        self.quickScanLayout = QVBoxLayout()
        self.quickScanBackButton = QPushButton('Back')
        self.VHFButton = QPushButton('VHF')
        self.UHFButton = QPushButton('UHF')
        self.FullScanButton = QPushButton('Full Scan')
        self.GPSScanButton = QPushButton('GPS Scan')
        self.quickScanButtons = [self.VHFButton, self.UHFButton, self.FullScanButton, self.GPSScanButton]
        for button in self.quickScanButtons:
            button.setFixedSize(500, 100)
            button.setFlat(True)
            button.setStyleSheet(ButtonStyleSheet)
            #button.setStyleSheet("font-size: 14pt; font-weight: bold; border: 2px solid gray;border-radius: 10px; background-color: white;")
            self.quickScanLayout.addWidget(button, alignment=Qt.AlignCenter)
        self.quickScanBackButton.setStyleSheet("font-size: 14pt; font-weight: bold; border: 2px solid gray;border-radius: 10px; background-color: white;")
        self.quickScanLayout.addWidget(self.quickScanBackButton)
        self.quickScanWidget.setLayout(self.quickScanLayout)
        self.stackLayout.addWidget(self.quickScanWidget)
        self.stackLayout.setCurrentWidget(self.quickScanWidget)

        # set connections for buttons
        self.quickScanBackButton.clicked.connect(self.openMainWidget)
        self.VHFButton.clicked.connect(self.VHFScanMethod)
        self.UHFButton.clicked.connect(self.UHFScanMethod)
        self.FullScanButton.clicked.connect(self.FullScanMethod)
        self.GPSScanButton.clicked.connect(self.GPSScanMethod)

    def openToggleScanWidget(self):
        self.toggleScanWidget = QWidget()
        self.toggleScanWidget.setStyleSheet(BackgroundStyle)
        self.toggleScanLayout = QVBoxLayout()
        self.toggleScanBackButton = QPushButton('Back')
        '''TODO: Need to setup input fields for taking specifics of requested scan, frequency range for example,
        need to setup process for calling this scan as well, if it's just frequency as an input then should be easy '''
        self.toggleScanBackButton.setStyleSheet("font-size: 14pt; font-weight: bold; border: 2px solid gray;border-radius: 10px; background-color: white;")
        self.toggleScanLayout.addWidget(self.toggleScanBackButton)
        self.toggleScanWidget.setLayout(self.toggleScanLayout)
        self.stackLayout.addWidget(self.toggleScanWidget)
        self.stackLayout.setCurrentWidget(self.toggleScanWidget)

        # set connections for buttons
        self.toggleScanBackButton.clicked.connect(self.openMainWidget)

    def openSimulatedScanWidget(self):
        self.simulatedScanWidget = QWidget()
        self.simulatedScanWidget.setStyleSheet(BackgroundStyle)
        self.simScanLayout = QVBoxLayout()
        self.simScanBackButton = QPushButton('Back')
        self.fixedFrequencyScanButton = QPushButton('Fixed Frequency Scan')
        self.frequencyHoppingScanButton = QPushButton('Frequency Hopping Scan')
        self.widebandTransmissionScanButton = QPushButton('Wideband Transmission Scan')
        self.simScanButtons = [self.fixedFrequencyScanButton, self.frequencyHoppingScanButton, self.widebandTransmissionScanButton]
        for button in self.simScanButtons:
            button.setFixedSize(500, 100)
            button.setFlat(True)
            button.setStyleSheet(ButtonStyleSheet)
            #button.setStyleSheet("font-size: 14pt; font-weight: bold; border: 2px solid gray;border-radius: 10px; background-color: white;")
            self.simScanLayout.addWidget(button, alignment=Qt.AlignCenter)
        self.simScanBackButton.setStyleSheet("font-size: 14pt; font-weight: bold; border: 2px solid gray;border-radius: 10px; background-color: white;")
        self.simScanLayout.addWidget(self.simScanBackButton)
        self.simulatedScanWidget.setLayout(self.simScanLayout)
        self.stackLayout.addWidget(self.simulatedScanWidget)
        self.stackLayout.setCurrentWidget(self.simulatedScanWidget)

        # set connections for buttons
        self.simScanBackButton.clicked.connect(self.openMainWidget)
        self.fixedFrequencyScanButton.clicked.connect(self.openFixedFreqWidget)
        self.frequencyHoppingScanButton.clicked.connect(self.openFreqHoppingWidget)
        self.widebandTransmissionScanButton.clicked.connect(self.openWidebandTransmissionWidget)

    '''TODO: All 3 sim scan widgets need to be built out. Needs to be structured to accept inputs, to initiate scan, 
        and needs to give useful description of scans'''

    def openFixedFreqWidget(self):
        self.widget1_1 = QWidget()
        self.layout1_1 = QVBoxLayout()
        self.backButton1_1 = QPushButton('Back')
        self.label1_1 = QLabel('This is the 1.1 widget')
        self.scanbutton = QPushButton('Scan')
        self.layout1_1.addWidget(self.scanbutton)
        self.layout1_1.addWidget(self.backButton1_1)
        self.layout1_1.addWidget(self.label1_1)
        self.widget1_1.setLayout(self.layout1_1)
        self.stackLayout.addWidget(self.widget1_1)
        self.stackLayout.setCurrentWidget(self.widget1_1)

        # set connections for buttons
        self.backButton1_1.clicked.connect(self.openSimulatedScanWidget)
        self.scanbutton.clicked.connect(self.fixedFrequencyScanMethod)

    def openFreqHoppingWidget(self):
        self.widget2_1 = QWidget()
        self.layout2_1 = QVBoxLayout()
        self.backButton2_1 = QPushButton('Back')
        self.label2_1 = QLabel('This is the 2.1 widget')
        self.scanbutton = QPushButton('Scan')
        self.layout2_1.addWidget(self.scanbutton)
        self.layout2_1.addWidget(self.backButton2_1)
        self.layout2_1.addWidget(self.label2_1)
        self.widget2_1.setLayout(self.layout2_1)
        self.stackLayout.addWidget(self.widget2_1)
        self.stackLayout.setCurrentWidget(self.widget2_1)

        # set connections for buttons
        self.backButton2_1.clicked.connect(self.openSimulatedScanWidget)
        self.scanbutton.clicked.connect(self.frequencyHoppingScanMethod)

    def openWidebandTransmissionWidget(self):
        self.widget3_1 = QWidget()
        self.layout3_1 = QVBoxLayout()
        self.backButton3_1 = QPushButton('Back')
        self.label3_1 = QLabel('This is the 3.1 widget')
        self.scanbutton = QPushButton('Scan')
        self.layout3_1.addWidget(self.scanbutton)
        self.layout3_1.addWidget(self.backButton3_1)
        self.layout3_1.addWidget(self.label3_1)
        self.widget3_1.setLayout(self.layout3_1)
        self.stackLayout.addWidget(self.widget3_1)
        self.stackLayout.setCurrentWidget(self.widget3_1)

        # set connections for buttons
        self.backButton3_1.clicked.connect(self.openSimulatedScanWidget)
        self.scanbutton.clicked.connect(self.widebandTransmissionScanMethod)

    def openMainWidget(self):
        self.stackLayout.setCurrentWidget(self)

    ''' TODO: Decide if we should migrate from using seperate pop up pages for graphing to instead using
    dedicated widgets that don't allow overlap'''

    def VHFScanMethod(self):
        scanWindowProcess = Process(target=startScanWindow, args=('30M:50M', ))
        scanWindowProcess.start()

    def UHFScanMethod(self):
        '''
        Sigh..... this starts a brand new process for the scan window, then this window's
        process blocks until we close the new window. HOWEVER - this doesn't stop the user 
        from opening multiple windows. That's also fine, but it will make both windows 
        appear to perform quite poorly as the two compete for use of the SDR.
        '''
        scanWindowProcess = Process(target=startScanWindow, args=('225M:400M', ))
        scanWindowProcess.start()

    def FullScanMethod(self):
        scanWindowProcess = Process(target=startScanWindow, args=('30M:1.7G', ))
        scanWindowProcess.start()

    def GPSScanMethod(self):
        scanWindowProcess = Process(target=startScanWindow, args=('1227590000:1227610000', ))
        scanWindowProcess.start()

    def toggleScanMethod(self):
        '''TODO'''
        return
    
    def fixedFrequencyScanMethod(self):
        '''TODO'''
        scanWindowProcess = Process(target=startScanWindow, args=('30M:1.7G', ))
        scanWindowProcess.start()
        
    
    def frequencyHoppingScanMethod(self):
        '''TODO'''
        scanWindowProcess = Process(target=startScanWindow, args=('30M:1.7G', ))
        scanWindowProcess.start()
        
    
    def widebandTransmissionScanMethod(self):
        '''TODO'''
        scanWindowProcess = Process(target=startScanWindow, args=('300M:1.7G', ))
        scanWindowProcess.start()

    def calibrateMethod(self):
        '''TODO: This should be revisited in the case we want to handle the calibration method 
        differently with respect to the GUI layout. Particularly if we change how we build the pages
        for data visualization'''

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
        #This takes forever, so Popup a message that the cal is starting.
        print("starting Calibration")
        self.msgBox = QMessageBox()
        self.msgBox.setWindowTitle('Calibrating')
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText("Calibrating system...\nThis typically takes several minutes")
        self.msgBox.setStandardButtons(QMessageBox.Ok)
        self.statusBar().showMessage('Calibrating')
        self.msgBox.exec()

        if takeBaselineMeasurement() == 'Error':
            self.msgBox.close()
            self.msgBox = QMessageBox()
            self.msgBox.setWindowTitle('Error!')
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setText("Failed to Calibrate System\nCheck hardware connections")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.statusBar().showMessage('Error Calibrating')
            self.msgBox.exec()
        else:
            self.msgBox.close()
            #Popup a message that the cal was successful.
            print("succesfully performed Calibration")
            self.msgBox = QMessageBox()
            self.msgBox.setWindowTitle('Sucess!')
            self.msgBox.setIcon(QMessageBox.Information)
            self.msgBox.setText("Successfully Calibrated System")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.statusBar().showMessage('Done Calibrating')
            self.msgBox.exec()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # create stacked layout
        self.stackLayout = QStackedLayout()

        # create main widget
        self.mainWidget = MainWidget(self.stackLayout)

        # add widgets to stacked layout
        self.stackLayout.addWidget(self.mainWidget)

        # set layout
        self.setLayout(self.stackLayout)


if __name__ == '__main__':
    #Global multiprocessing setup, needs to be set at the start of the context definition
    #This line is required for multiprocessing on linux specifically due to a nuance in 
    #how the new processes are generated. Without it, calling bound C code (which we use
    # in pytables) will get deadlocked.
    set_start_method("spawn")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())





