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
    number of bins. This will output a tuple with one line of data, presuming
    there is data left to read in the file.
    The data is written out to the file in full scans at a time.
    The binary file will have the name 'fileName.mat'. When the scan ends, a
    metadata file named fileName.met will be written out with miscellaneous info.
'''

def makeScanCall(fileName="default", hzLow = "89000000", hzHigh = "90000000", numBins = "500", gain = "500",  repeats= "100", exitTimer = "5m"):
    #rtl_power_fftw -f 144100000:146100000 -b 500 -n 100 -g 350 -p 0 -e 5m -q -m myscanfilename
    call = 'rtl_power_fftw -f ' + hzLow + ':' + hzHigh  + ' -b ' + numBins  + ' -n ' + repeats  + ' -g ' + gain  + ' -e ' + exitTimer + ' -q -m ' + fileName
    binaryLineLength = int(numBins)*4 #this is the length of a 'scan', or a sequence of dBm readings covering the indicated frequency band.
    return call, binaryLineLength

def convertFile(inputFileName, outputFileName=None):
    import csv
    import struct
    import datetime

    if outputFileName == None:
        outputFileName = 'converted_'+inputFileName+'.csv'
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
        print('Completed exporting '+outputFileName)
