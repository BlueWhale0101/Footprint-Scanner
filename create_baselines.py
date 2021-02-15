import os
#import schedule
import time
from datetime import datetime, timedelta, date
import numpy as np
import subprocess

#rtl_power -f 674.230M:674.233M:1 -g 50 -i 1 -e 1h radar.csv
'''
Usage example:
python3 create_baselines.py will print out the create_baselines
UHFBaseline = create_baselines.makeUhfBaseline() will return the vector representing UHF power baseline
VHFBaseline = create_baselines.makeVhfBaseline() will return the vector representing VHF power baseline
'''

def makeCommand(fileName="", hzLow = "89M", hzHigh = "90M", binSize = "5k", gain = "50", interval = "10", exitTimer = "1M"):
	answer = "rtl_power -f "
	fileName = fileName
	hzLow = hzLow
	hzHigh = hzHigh
	binSize = binSize
	gain = gain
	interval = interval
	exitTimer = exitTimer
	answer += hzLow + ":" + hzHigh + ":" + binSize + " -g " + gain + " -i " + interval + " -e " + exitTimer + " " + fileName
	return answer

def makeNumBins(hzLow, hzHigh, binSize):
	hzHigh = float(hzHigh[:-1])
	hzLow = float(hzLow[:-1])
	binSizeStr = binSize
	if binSizeStr[-1] =='K':
		binSize = float(binSizeStr[:-1])/1000
	else:
		binSize = float(binSize[:-1])
	numBins = (hzHigh - hzLow)/binSize
	if numBins % 1 > 0:
		numBins = int(numBins) + 1
	numBins = int(numBins)
	return numBins

def makeUhfBaseline():
	fileName = "outputFiles/uhfBaselineInput.csv"
	hzLow = "300M"
	hzHigh = "1766M"
	binSize = "1M"
	numBins = makeNumBins(hzLow, hzHigh, binSize)
	exitTimer = "1M"
	command = makeCommand(fileName=fileName, hzLow=hzLow, hzHigh=hzHigh, binSize=binSize, exitTimer=exitTimer)
	commandCall = subprocess.Popen(command, shell=True)
	commandCall.wait()
	text = np.genfromtxt(fileName, delimiter=",", dtype=None)
	csv = np.genfromtxt(fileName, delimiter=",")
	csv = np.array(csv)
	bucketReadings = csv[:,6:-1]

	identifier = text[0][1]
	numRows = 0
	for i in range(len(text)):
		if text[i][1] == identifier:
			numRows+=1
		else:
			break
	print(numRows)
	numBins = numRows * len(bucketReadings[0])
	print(numBins)

	baselineData = np.reshape(bucketReadings, (-1,numBins))
	medianData = np.median(baselineData, axis = 0)

	return medianData


def makeVhfBaseline():
	fileName = "outputFiles/vhfBaselineInput.csv"
	hzLow = "30M"
	hzHigh = "300M"
	binSize = "200K"
	exitTimer = "1M"
	command = makeCommand(fileName=fileName, hzLow=hzLow, hzHigh=hzHigh, binSize=binSize, exitTimer=exitTimer)
	commandCall = subprocess.Popen(command, shell=True)
	commandCall.wait()
	text = np.genfromtxt(fileName, delimiter=",", dtype=None)
	csv = np.genfromtxt(fileName, delimiter=",")
	csv = np.array(csv)
	bucketReadings = csv[:,6:-1]

	identifier = text[0][1]
	numRows = 0
	for i in range(len(text)):
		if text[i][1] == identifier:
			numRows+=1
		else:
			break
	print(numRows)
	numBins = numRows * len(bucketReadings[0])
	print(numBins)

	baselineData = np.reshape(bucketReadings, (-1,numBins))
	medianData = np.median(baselineData, axis = 0)

	return medianData

if __name__ == '__main__':
	UHFbaseline = makeUhfBaseline()
	print('UHF Baseline Power Readings:')
	print(UHFbaseline)

	print('VHF Baseline Power Readings:')
	VHFbaseline = makeVhfBaseline()
	print(VHFbaseline)
