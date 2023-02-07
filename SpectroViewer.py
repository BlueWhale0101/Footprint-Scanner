import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pdb

#Baseline data - 220221_090207_VHF_scan.csv
#Last measurement - 220221_090645_VHF_scan.csv
#Peak measurement is 220221_090645_VHF_scan.csv & 220221_091804_VHF_scan.csv

'''
Unfortunately, this is old data, so the format is in these csv files and not the binary files we use now. 
The format of the data is:

date, time, Hz low, Hz high, Hz step, samples, dbm, dbm,....
where n * Hz step + Hz Low = current freq; the power measurements are for each bin. 
so bin 0 is Hz low + Hz step * 0, bin 1 is Hz Low + Hz step * 1, bin n i s Hz Low + Hz step * n

Hz low and high change throughout the file to give the entire bandwidth we are using. so to get the 
hz MIN and hz MAX we have to look at multiple lines.

To work with this data easily, we will want to rectangularize it - that is, we would really like this:

date, time, hz min, hz 1, hz 2 .... hz max 
'''

plt.ion()
plt.style.use('dark_background')

def getFreqVsPower(data):
    #Make our baseline plot
    minFreqList = data['HzLow'].unique()
    maxData = data.groupby('HzLow').max() #This is a dataframe with the max of every column against each sweep
    deltaFreq = data['HzStep'][0]
    snap = []
    for minFreq in minFreqList:
        freqData = maxData.query('index == @minFreq')
        freqList = [n*deltaFreq + minFreq for n in range(129)]
        i = 0
        for f in freqList:
            #Use format (freq, power)
            pow = float(freqData['power'+str(i)])
            #Data format is frequency in MHz and power in dBm
            snap.append((f/1000000, pow))
            i += 1

    SnapDF = pd.DataFrame(snap, columns=['frequency', 'power'])
    return SnapDF

powCols = ['power'+str(i) for i in range(129)]
baselineData = pd.read_csv('Data//220221_090207_VHF_scan.csv', index_col=False\
    , names=['date', 'time', 'HzLow', 'HzHigh', 'HzStep', 'samples']+powCols)
currentData = pd.read_csv('Data//220221_090645_VHF_scan.csv', index_col=False\
    , names=['date', 'time', 'HzLow', 'HzHigh', 'HzStep', 'samples']+powCols)
prevData = pd.read_csv('Data//220221_091804_VHF_scan.csv', index_col=False\
    , names=['date', 'time', 'HzLow', 'HzHigh', 'HzStep', 'samples']+powCols)

fig, ax = plt.subplots()

baseSnapDF = getFreqVsPower(baselineData)
baseSnapDF.plot(ax=ax, x='frequency', y='power', style='r--', label='base')
currentDataSnap = getFreqVsPower(currentData)
currentDataSnap.plot(ax=ax, x='frequency', y='power', style='y', label='max hold', grid='On', title = 'ScanView')
prevDataSnap = getFreqVsPower(prevData)
prevDataSnap.plot(ax=ax, x='frequency', y='power', grid='On', title = 'ScanView', label='current', alpha = .1)
ax.fill_between(prevDataSnap['frequency'], prevDataSnap['power'], baseSnapDF['power'].min(), alpha = .5)

#Show the data
plt.show()
plt.pause(0.1)
input('Press enter to continue...')

