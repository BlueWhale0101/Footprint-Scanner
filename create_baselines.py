import os
import datetime
import subprocess
import time
import numpy as np
from keyFunctions import *
'''
create_baselines has the functions used to perform a short scan in each spectra performing the following steps:
1. Scan and store ~5 lines of data
2. Take the last line as the 'sample data' row
3. Ensure this line is well correlated to the other lines. Correlate each line to each other line and make sure
	the value spread is reasonable tight. This means something different for each spectrum because the data
	sizes are different.
4. Save this row as the calibration data into a binary file with extension .cal.
'''

def calibrate_L1():
	'''
	For a clean scan, no activity, using this equation:
	np.correlate(dataRow, np.random.random(250)*2-X)
	This sets the comparison to data which is approximately X randomly varying by about 2, which is normal behavior
	#Correlation Table#
	 X		score
	self	935000
	-60		897000
	-50		745000
	-40		593000
	-30		441000
	-20		290000
	-10		137000
	0		-15169
	'''
	print('Calibrate L1')
	scanComplete = False
	#Make the scan call
	scanDict = {'title':'GPS Scan', 'hzLow':'1575400000', 'hzHigh':'1575440000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'10s'}
	while not scanComplete:
		dataFileName = performScanMethod(scanDict, 'L1')
		data = fileToMatrix(dataFileName)
		#The last row is sometimes partial, so take the second to last as our sample row
		calRow = data[-2,:]
		#Ensure this row is well correlated with the first 10 rows of data. This is an indication that the
		#row contains data 'typical'
		for index in range(9):
			score = np.correlate(calRow, data[index, :])
			if score < 900000:
				#This is a poorly correlated row. try try again....
				scanComplete = False
				break
			else:
				scanComplete = True

	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_L1_cal'#The file will be saved as Date_band_cal.npy
	np.save(fileName, calRow)
	return fileName + '.npy'

def calibrate_L2():
		'''
		For a clean scan, no activity, using this equation:
		np.correlate(dataRow, np.random.random(250)*2-X)
		This sets the comparison to data which is approximately X randomly varying by about 2, which is normal behavior
		#Correlation Table#
		 X		score
		self	935000
		-60		897000
		-50		745000
		-40		593000
		-30		441000
		-20		290000
		-10		137000
		0		-15169
		'''
	scanComplete = False
	#Make the scan call
	scanDict = {'title':'GPS Scan', 'hzLow':'1227580000', 'hzHigh':'1227620000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'10s'}
	while not scanComplete:
		dataFileName = performScanMethod(scanDict, 'L2')
		data = fileToMatrix(dataFileName)
		#The last row is sometimes partial, so take the second to last as our sample row
		calRow = data[-2,:]
		#Ensure this row is well correlated with the first 10 rows of data. This is an indication that the
		#row contains data 'typical'
		for index in range(9):
			score = np.correlate(calRow, data[index, :])
			if score < 900000:
				#This is a poorly correlated row. try try again....
				scanComplete = False
				break
			else:
				scanComplete = True

	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_L2_cal'#The file will be saved as Date_band_cal.npy
	np.save(fileName, calRow)
	return fileName + '.npy'

def calibrate_VHF():
		'''
		For a clean scan, no activity, using this equation:
		np.correlate(dataRow, np.random.random(250)*2-X)
		This sets the comparison to data which is approximately X randomly varying by about 2, which is normal behavior
		#Correlation Table#
		 X		score
		self	935000
		-60		897000
		-50		745000
		-40		593000
		-30		441000
		-20		290000
		-10		137000
		0		-15169
		'''
	print('Calibrate VHF')
	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_VHF_cal'
	return fileName

def calibrate_UHF():
		'''
		For a clean scan, no activity, using this equation:
		np.correlate(dataRow, np.random.random(250)*2-X)
		This sets the comparison to data which is approximately X randomly varying by about 2, which is normal behavior
		#Correlation Table#
		 X		score
		self	935000
		-60		897000
		-50		745000
		-40		593000
		-30		441000
		-20		290000
		-10		137000
		0		-15169
		'''
	print('Calibrate UHF')
	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_UHF_cal'
	return fileName

def calibrate_FullSpectrum():
		'''
		For a clean scan, no activity, using this equation:
		np.correlate(dataRow, np.random.random(250)*2-X)
		This sets the comparison to data which is approximately X randomly varying by about 2, which is normal behavior
		#Correlation Table#
		 X		score
		self	935000
		-60		897000
		-50		745000
		-40		593000
		-30		441000
		-20		290000
		-10		137000
		0		-15169
		'''
	print('Calibrate Full Spectrum')
	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_Full_Spectrum_cal'
	return fileName

def performScanMethod(configDict, scanType ):
	#Perform the scan from the configDict, then return the filename
	# Build the Command
	# configDict has keys title, minFreq, maxFreq, binSize, interval, exitTimer
	dataFileName = "Data/" +\
		datetime.datetime.now().strftime('%d%m%y_%H%M%S_') + scanType + '_scan'
	print('Scan saving to '+dataFileName)
	currentCommand = makeScanCall(fileName=dataFileName, hzLow = configDict['hzLow'], hzHigh = configDict['hzHigh'], \
		numBins = configDict['numBins'], gain = configDict['gain'],  repeats= configDict['repeats'], exitTimer = configDict['exitTimer'])
	binaryLineLength, actualBandwidth = calcLineLength(currentCommand) #calculates the number of bits in one row of the output file and detects the bandwidth of this device.

	# This opens the command asynchronously. poll whether the scan is running with p.poll().
	# This returns 0 if the scan is done or None if it is still going.
	currentScanCommandProcess = subprocess.Popen(currentCommand, shell=True, preexec_fn=os.setsid)
	print('Running command '+currentCommand)

	while currentScanCommandProcess.poll() != 0:
		#wait for the scan to finish
		time.sleep(1)
	return dataFileName

'''
##############################################
from PyQt5.QtCore import pyqtRemoveInputHook
from pdb import set_trace
pyqtRemoveInputHook()
set_trace()
##############################################
'''
