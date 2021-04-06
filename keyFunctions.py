'''
    This module contains helper functions for making calls to the backend
    rtl_power_fftw, which is much faster then rtl_power. The output data is
    output to a binary file which is encoded with C, so the importing and post
    processing are a bit more complicated.

    The output file contains a matrix in the following format:
    f1  f2  f3  ... f4  f5  f6
    db  db  db      db  db  db
    db  db  db      db  db  db
    db  db  db      db  db  db

    where f1 is hzLow and f6 is hzHigh. The step size is (hzHigh-hzLow)/numBins.
    The time step between the scans is not known until the end.
    The data can be read in with struct.unpack('f'*n, file(4*n)) where n is the
    number of bins * the number of hops. This will output a tuple with one line of data, presuming
    there is data left to read in the file. We multiply by 4 because each reading is represented by a 4 bit value.
    The number of hops is roundup((hzHigh-HzLow)/actualBandwidth).
    The number of columns is numHops*numBins
    The data is written out to the file in full scans at a time.
    The binary file will have the name 'fileName.mat'. When the scan ends, a
    metadata file named fileName.met will be written out with miscellaneous info.

    Further help: https://github.com/AD-Vega/rtl-power-fftw/blob/master/README.md
'''

def makeScanCall(fileName="default", hzLow = "89000000", hzHigh = "90000000", numBins = "500", gain = "500",  repeats= "100", exitTimer = "5m"):
    #need keys fileName, hzLow, hzHigh, numBins, gain, repeats, exitTimer
    #rtl_power_fftw -f 144100000:146100000 -b 500 -n 100 -g 350 -p 0 -e 5m -q -m myscanfilename
    call = 'rtl_power_fftw -f ' + hzLow + ':' + hzHigh  + ' -b ' + numBins  + ' -n ' + repeats  + ' -g ' + gain  + ' -e ' + exitTimer + ' -q -m ' + fileName
    return call

def detectBandwidth():
    #Detects the bandwidth of the attached hardware based on the output from a short rtl_power_fftw
    import subprocess
    actualBandwidth = None
    call = makeScanCall(exitTimer='2s')
    print('running sample scan: '+call)
    proc = subprocess.Popen(call.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    feedbackErr, feedbackOut = proc.communicate()
    lines = str(feedbackOut).split('\\n')
    for line in lines:
        if line.count('Actual sample rate:') > 0:
            actualBandwidth = int(line.split(':')[1].strip().split(' ')[0]) #this splits the line by :, then pulls the number out of the second half
            print('Found bandwidth in text.')
            break
        else:
            continue
    print('Actual bandwidth detected is '+str(actualBandwidth))
    return actualBandwidth

def calcLineLength(call):
    import math
    BW = detectBandwidth()
    #calculates the number of bits in a line of data from the matrix binary output file for a given call
    elements = call.split(' ')
    for index, element in enumerate(elements):
        if element == '-f':
            freqRange = elements[index+1].split(':')
            hzHigh = freqRange[1].strip()
            hzLow = freqRange[0].strip()
            hzHigh = hzHigh.upper().replace('G', '000000000')
            hzHigh = hzHigh.upper().replace('M', '000000')
            hzHigh = hzHigh.upper().replace('K', '000')
            hzLow = hzLow.upper().replace('G', '000000000')
            hzLow = hzLow.upper().replace('M', '000000')
            hzLow = hzLow.upper().replace('K', '000')
        if element == '-b':
            numBins = int(elements[index+1].strip())
    print('using freq range '+hzLow+ ' to '+hzHigh)
    hzLow = int(hzLow)
    hzHigh = int(hzHigh)
    #Now that we have the freqs in Hz, calculate the number of bits
    binaryLineLength = int(math.ceil((hzHigh - hzLow)/BW)*4*numBins)
    print('Number of bits in a row is '+str(binaryLineLength))
    return binaryLineLength, BW

def convertFile(inputFileName, outputFileName=None):
    import csv
    import struct
    import datetime
    import os

    if outputFileName == None:
        head, tail = os.path.split(inputFileName)
        outputFileName = os.path.join(head, 'converted_'+tail+'.csv')
        print('Saving data in '+outputFileName)
    #open the metadata file and get the key data.
    metaFileName = inputFileName+'.met'
    dataFileName = inputFileName+'.bin'
    with open(metaFileName, 'r') as f:
        line = None
        while line != '':
            line = f.readline()
            if line.count('frequency bins') > 0:
                numBins = int(line.split('#')[0])
                print(numBins)
                continue
            if line.count('startFreq') > 0:
                hzLow = int(line.split('#')[0])
                print(hzLow)
                continue
            if line.count('endFreq') > 0:
                hzHigh = int(line.split('#')[0])
                print(hzHigh)
                continue
            if line.count('stepFreq') > 0:
                hzStep = int(line.split('#')[0])
                print(hzStep)
                continue
            if line.count('avgScanDur') > 0:
                T = float(line.split('#')[0])
                stepTime = datetime.timedelta(seconds=T)
                continue
            if line.count('firstAcqTimestamp UTC') > 0:
                t = line.split('#')[0].strip()
                startTime = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S %Z')
                continue
            if line.count('lastAcqTimestamp UTC') > 0:
                t = line.split('#')[0].strip()
                startTime = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S %Z')
                continue
        #Open the file we are going to write output
        with open(outputFileName, 'w') as outFile:
            outFileWriter = csv.writer(outFile)
            header = ['Time']
            for n in range(int(numBins)):
                header.append(str(hzLow+hzStep*n))
            outFileWriter.writerow(header)
            #Now parse and write out data
            binaryLineLength = numBins*4
            with open(inputFileName+'.bin', 'rb') as dataFile:
                dataLine = dataFile.read(binaryLineLength)
                rowCounter = 0
                while dataLine != b'':
                    newTime = startTime + stepTime * rowCounter
                    rowContent = [newTime.strftime('%Y%m%d %H:%M:%S.%f')]
                    data = struct.unpack('f'*numBins, dataLine)
                    rowContent = rowContent + list(data)
                    outFileWriter.writerow(rowContent)
                    rowCounter += 1
                    dataLine = dataFile.read(binaryLineLength)
                    if len(dataLine) < binaryLineLength:
                        #If the scan was disrupted, it will write out the current hop, then end.
                        #In this case, we need to just write a partial line out
                        numBins = int(len(dataLine)/4)
        print('Completed exporting '+outputFileName)

def dataToWaterfallImage(recordFile=None, **kwargs):
    #given a record file, convert to an image showing all the data recorded.
    import struct
    import datetime
    import os
    import numpy as np
    #recordFile = 'Data//110321_110627_VHF_scan' #This is purely for testing
    if recordFile == None:
        return 'Failed. No file passed in'

    #open the metadata file and get the key data.
    #Note that if there isn't a meta data file, you really can't do anything with the data. It's just a stream of bits.
    metaFileName = recordFile+'.met'
    dataFileName = recordFile+'.bin'
    with open(metaFileName, 'r') as f:
        line = None
        while line != '':
            line = f.readline()
            if line.count('frequency bins') > 0:
                numBins = int(line.split('#')[0])
                print(numBins)
                continue
            if line.count('startFreq') > 0:
                hzLow = int(line.split('#')[0])
                print(hzLow)
                continue
            if line.count('endFreq') > 0:
                hzHigh = int(line.split('#')[0])
                print(hzHigh)
                continue
            if line.count('stepFreq') > 0:
                hzStep = int(line.split('#')[0])
                print(hzStep)
                continue
            if line.count('avgScanDur') > 0:
                T = float(line.split('#')[0])
                stepTime = datetime.timedelta(seconds=T)
                continue
            if line.count('firstAcqTimestamp UTC') > 0:
                t = line.split('#')[0].strip()
                startTime = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S %Z')
                continue
            if line.count('lastAcqTimestamp UTC') > 0:
                t = line.split('#')[0].strip()
                startTime = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S %Z')
                continue
    #Done with the meta data. Now loop through the file and grab a line at a time.
    #We are just building the array here.
    #See the comment at the top of the file for all of the clarifying info on how this works.
    binaryLineLength = numBins*4
    outputDataMatrix = np.array([])
    with open(dataFileName, 'rb') as dataFile:
        #Keep looping till all the data has been read out of the file
        dataLine = dataFile.read(binaryLineLength)
        while dataLine != b'':
            data = struct.unpack('f'*numBins, dataLine)
            if len(outputDataMatrix) == 0:
                outputDataMatrix = np.array(list(data))
            else:
                outputDataMatrix = np.vstack([outputDataMatrix, np.array(list(data))])
            dataLine = dataFile.read(binaryLineLength)
            if len(dataLine) < binaryLineLength:
                #If the scan was disrupted, it will write out the current hop, then end.
                #In this case, we need to just dump the last bit of data.
                break

    #Generate the image. For now, just generate the image and then display it to the screen.
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    imgSaveName = recordFile+'.jpg'
    ax = plt.subplot()

    im = ax.imshow(outputDataMatrix, aspect='auto')

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    plt.colorbar(im, cax=cax)
    plt.tight_layout()
    fig1 = plt.gcf()
    fig1.savefig(imgSaveName, format='jpg', dpi=1000)
    plt.show()
    '''
    savefig(fname, dpi=None, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)
    '''
