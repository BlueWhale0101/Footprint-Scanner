'''
WaterfallView generates a window with a matplotlib imshow view showing a waterfall graph of the slice of the spectrum
requested. It takes a dictionary argument with the request for the spectrum to be analyzed. It depends on various
functions in keyFunctions.py and for the C++ drivers to all be setup correctly. It calls the drivers which collect
data from the sensors, then reads data in from the binary file as it is written. The waterfall view is updated at a
rate determined by the type of scan called for.

Update notes 9/25/2022
SimWaterfallView is a clone of this module.
'''
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QPushButton, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
import pandas as pd
import datetime
from BinarySpectroViewer import *
from multiprocessing import Process, Queue

#Imports for spectrogram
import matplotlib
matplotlib.use('Qt5Agg')
#import seaborn as sns


class MplCanvas(FigureCanvasQTAgg):
    #This is a class for setting up the embedded matplotlib figure
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class EARSscanWindow(QMainWindow):

    def __init__(self, cmdFreqs='30M:35M', simFlag=False, simConfig=None):
        super().__init__()
        self.initUI(cmdFreqs, simFlag, simConfig)

    def initUI(self, cmdFreqs, simFlag, simConfig):
        print('Initializing scan...')
        # Add status bar
        self.statusBar()
        # Main Layout creation
        self.CentralWindow = QWidget()
        MainLayout = QVBoxLayout()
        matplotlib.pyplot.style.use('dark_background')

        # Start the first scan so there is data in the pipe
        self.initScanMethod()

        # Show the scan Data
        self.powerGraph = MplCanvas(self)
        self.axesRef = self.powerGraph.figure.axes[0]
        self.powerGraph.figure.tight_layout()
        self.updateCount = 0
        
        # call the update event This drives both the scanning calls and the graph updating
        # Set up the update function
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateMethod)
        #Update interval is set in milliseconds
        self.updateTimer.setInterval(1000)
        self.updateTimer.start()
        #Start software bus queue
        self.SWBQueue = Queue(25)
        # Add the graph widget which shows the moving average of the power, in decibels, of the band.
        MainLayout.addWidget(self.powerGraph)
        #Add a loading message to the power graph
        self.axesRef.text(0.05, .95, 'Loading data...')
        #Start the hardware scanning process
        self.hwScanProcess = Process(target=streamScan, args = (cmdFreqs, self.SWBQueue, simFlag, simConfig))
        self.hwScanProcess.start()

        # Close Button setup
        self.Close_Button = QPushButton('End Scan')
        self.Close_Button.setStyleSheet("QPushButton{ border-radius:8px;\
                            height: 30px;\
                            border: 1px solid;\
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, \
                            stop: 0 #ccd9ff, stop: 1 #2b50bd); }\
                            QPushButton:pressed {background-color: #fae22d}")
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
        #Return True if the method completed without issues. Return False if there were errors.
        # configDict has keys title, minFreq, maxFreq, binSize, interval, exitTimer
        pass

    def updateMethod(self):

        #check for an update in the queue
        if not self.SWBQueue.empty():
            self.updateCount += 1
            #Got data in the queue
            df, maxDF, baseline = self.SWBQueue.get()
            #Clear axes
            self.axesRef.cla()
            #Add time and number of updates annotation
            curTime = datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
            curTimeUpdateText = 'Last update: ' + curTime
            curUpdateText = 'Number of scans: ' + str(self.updateCount)
            print(curUpdateText)
            print(curTimeUpdateText)
            self.axesRef.text(0.05, .95, curTimeUpdateText)
            self.axesRef.text(0.05, .90, curUpdateText)
            #Plot our data
            maxDF.plot(ax=self.axesRef, x='freqCompare', y='power', style='y', linewidth = .5, label='max hold', grid='On', title = 'ScanView')
            df.plot(ax=self.axesRef, x='frequency', y='power', grid='On', title = 'ScanView', label='current', alpha = .7, linewidth = .5)
            self.axesRef.fill_between(df['frequency'], df['power'], df['power'].min(), alpha = .5)
            baseline.plot(ax=self.axesRef, x='frequency', y='power', style='r-.', linewidth=.3, alpha = .7)
            
            #Draw and allow matplotlib to do plot update
            self.powerGraph.draw()
            matplotlib.pyplot.pause(.05)



    def updatePlot(self):
        #Read in all the new data
        pass

    def closeEvent(self, event):
        # Make sure we are gracefully ending the scan and not just leaving the process running in the background.
        # This would probably cause problems if the user then immediately tried to start another scan.
        print('gracefully closing...')
        while not self.SWBQueue.empty():
            print('Flushing queue...')
            #Ensure the queue is empty before sending the command. 
            #This ensures that this is the next item in the queue when the hw process looks.
            flushVar = self.SWBQueue.get()
        self.SWBQueue.put('QUIT')
        print('Closed the SWB Queue and hardware process.')
        #self.hwScanProcess.join()
        self.SWBQueue.get(block=True, timeout=300)
        self.SWBQueue.close()
        self.hwScanProcess.terminate()
        print('Closed scan and queue')
        self.updateTimer.stop()
        event.accept()


'''
    #Set a tracepoint in the Python debugger that works with Qt
    from PyQt5.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()
'''
def startScanWindow(cmdFreq = '30M:35M', simFlag = False, simConfig = None):
    import sys
    app = QApplication(sys.argv)
    mainWindow = EARSscanWindow(cmdFreq, simFlag, simConfig)
    #Start the application
    sys.exit(app.exec_())


if __name__ == '__main__':
    startScanWindow()