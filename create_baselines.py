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
	scanComplete = False
	#Make the scan call
	scanDict = {'title':'GPS Scan', 'hzLow':'1575400000', 'hzHigh':'1575440000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'10s'}
	while not scanComplete:
		print('scanning L1')
		dataFileName = performScanMethod(scanDict, 'L1')
		data = fileToMatrix(dataFileName)
		#The last row is sometimes partial, so take the second to last as our sample row
		calRow = data[-2,:]
		#Ensure this row is well correlated with the first 10 rows of data. This is an indication that the
		#row contains data 'typical'
		for index in range(9):
			score = np.corrcoef(calRow, data[index, :])
			if score[0,1] < .85:
				#This is a poorly correlated row. try try again....
				scanComplete = False
				print('Bad scan, retrying....')
				from PyQt5.QtCore import pyqtRemoveInputHook
				from pdb import set_trace
				pyqtRemoveInputHook()
				set_trace()
				break
			else:
				scanComplete = True

	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_L1_cal'#The file will be saved as Date_band_cal.npy
	np.save(fileName, calRow)
	return fileName + '.npy'

def calibrate_L2():
	scanComplete = False
	#Make the scan call
	scanDict = {'title':'GPS Scan', 'hzLow':'1227580000', 'hzHigh':'1227620000', 'numBins':'250', 'gain': '500', 'repeats':'10', 'exitTimer':'10s'}
	while not scanComplete:
		print('Scannning L2')
		dataFileName = performScanMethod(scanDict, 'L2')
		data = fileToMatrix(dataFileName)
		#The last row is sometimes partial, so take the second to last as our sample row
		calRow = data[-2,:]
		#Ensure this row is well correlated with the first 10 rows of data. This is an indication that the
		#row contains data 'typical'
		for index in range(9):
			score = np.corrcoef(calRow, data[index, :])
			if score[0,1] < .85:
				#This is a poorly correlated row. try try again....
				scanComplete = False
				print('Bad scan, retrying....')
				break
			else:
				scanComplete = True

	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_L2_cal'#The file will be saved as Date_band_cal.npy
	np.save(fileName, calRow)
	return fileName + '.npy'

def calibrate_VHF():
	scanComplete = False
	#Make the scan call
	scanDict = {'title':'VHF Scan', 'hzLow':'30000000', 'hzHigh':'50000000', 'numBins':'140', 'gain': '500', 'repeats':'10', 'exitTimer':'30s'}
	while not scanComplete:
		print('Scanning VHF')
		dataFileName = performScanMethod(scanDict, 'VHF')
		data = fileToMatrix(dataFileName)
		#The last row is sometimes partial, so take the second to last as our sample row
		calRow = data[-2,:]
		#Ensure this row is well correlated with the first 10 rows of data. This is an indication that the
		#row contains data 'typical'
		for index in range(9):
			score = np.corrcoef(calRow, data[index, :])
			if score[0,1] < .85:
				print('Bad scan, retrying....')
				#This is a poorly correlated row. try try again....
				scanComplete = False
				break
			else:
				scanComplete = True

	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_VHF_cal'#The file will be saved as Date_band_cal.npy
	np.save(fileName, calRow)
	return fileName + '.npy'

def calibrate_UHF():
	scanComplete = False
	#Make the scan call
	scanDict = {'title':'UHF Scan', 'hzLow':'225000000', 'hzHigh':'400000000', 'gain': '500', 'numBins':'140', 'repeats':'10', 'exitTimer':'30s'}
	while not scanComplete:
		print('Scannng UHF')
		dataFileName = performScanMethod(scanDict, 'UHF')
		data = fileToMatrix(dataFileName)
		#The last row is sometimes partial, so take the second to last as our sample row
		calRow = data[-2,:]
		#Ensure this row is well correlated with the first 10 rows of data. This is an indication that the
		#row contains data 'typical'
		for index in range(3):
			score = np.corrcoef(calRow, data[index, :])
			if score[0,1] < .85:
				print('Bad scan, retrying....')
				#This is a poorly correlated row. try try again....
				scanComplete = False
				break
			else:
				scanComplete = True

	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_UHF_cal'#The file will be saved as Date_band_cal.npy
	np.save(fileName, calRow)
	return fileName + '.npy'

def calibrate_FullSpectrum():
	scanComplete = False
	#Make the scan call
	scanDict = {'title':'Full Scan', 'hzLow':'30000000', 'hzHigh':'1700000000', 'numBins':'10', 'gain': '500', 'repeats':'1', 'exitTimer':'3m'}
	while not scanComplete:
		print('Scanning Full Spectrum')
		dataFileName = performScanMethod(scanDict, 'FullScan')
		data = fileToMatrix(dataFileName)
		#The last row is sometimes partial, so take the second to last as our sample row
		calRow = data[-2,:]
		#Ensure this row is well correlated with the first 10 rows of data. This is an indication that the
		#row contains data 'typical'
		for index in range(3):
			score = np.corrcoef(calRow, data[index, :])
			if score[0,1] < .85:
				#This is a poorly correlated row. try try again....
				print('Bad scan, retrying....')
				scanComplete = False
				break
			else:
				scanComplete = True

	fileName = datetime.datetime.now().strftime('%Y%m%d')+'_Full_Spectrum_cal'#The file will be saved as Date_band_cal.npy
	np.save(fileName, calRow)
	return fileName + '.npy'

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
