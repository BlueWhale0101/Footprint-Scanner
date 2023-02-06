'''
This module contains functions to handle a command with the same arguments as the sdr drivers, and return a similar file handle with a bystream connected to it. It will further take arguments on whether to simulate any known profile.

VHF Simple - narrow frequency band of high energy in VHF.
VHF Tactical - frequency hopping sim. high energy is randomly applied to freqs across tactical spectrum.
UHF Simple - narrow frequency band of high energy in UHF.
UHF Tactical - frequency hopping sim. high energy is randomly applied to freqs across tactical spectrum.
UHF Wideband Satcom - Low signature, four stable 'bands' of higher energy each spanning 10 MHz at random intervals.
####################################################################################################
Typical values are used for hardware.
Bandwidth: 2000000


####################################################################################################
From keyFunctions.py:
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
    there is data left to read in the file. We multiply by 4 because each reading is represented by a 4 byte value.
    The number of hops is roundup((hzHigh-HzLow)/actualBandwidth).
    The number of columns is numHops*numBins
    The data is written out to the file in full scans at a time.
    The binary file will have the name 'fileName.bin'. When the scan ends, a
    metadata file named fileName.met will be written out with miscellaneous info.

    Further help: https://github.com/AD-Vega/rtl-power-fftw/blob/master/README.md
    https://github.com/AD-Vega/rtl-power-fftw/blob/master/doc/rtl_power_fftw.1.md
####################################################################################################
'''
import sys
import datetime
import io
import statistics
import struct
import time
import random


def SIM_makeScanCall(fileName="default", hzLow="89000000", hzHigh="90000000", numBins="500", gain="500",  repeats="100", exitTimer="5m"):
    #need keys fileName, hzLow, hzHigh, numBins, gain, repeats, exitTimer
    #rtl_power_fftw -f 144100000:146100000 -b 500 -n 100 -g 350 -p 0 -e 5m -q -m myscanfilename
    call = 'python3 SDRSimulator.py -f ' + hzLow + ':' + hzHigh + ' -b ' + numBins + \
        ' -n ' + repeats + ' -g ' + gain + ' -e ' + exitTimer + ' -q -m ' + fileName
    return call


def SIM_calcLineLength(call):
    import math
    #Bandwidth is a representative number from hardware testing.
    BW = 2000000
    #calculates the number of bytes in a line of data from the matrix binary output file for a given call
    elements = call.split(' ')
    for index, element in enumerate(elements):
        if element == '-f':
            freqRange = elements[index+1].split(':')
            hzHigh = freqRange[1].strip().upper()
            hzLow = freqRange[0].strip().upper()
            if 'G' in hzHigh:
                hzHigh = str(int(float(hzHigh[0:-1])*1000000000))
            elif 'M' in hzHigh:
                hzHigh = str(int(float(hzHigh[0:-1])*1000000))
            elif 'K' in hzHigh:
                hzHigh = str(int(float(hzHigh[0:-1])*1000))
            if 'G' in hzLow:
                hzLow = str(int(float(hzLow[0:-1])*1000000000))
            elif 'M' in hzLow:
                hzLow = str(int(float(hzLow[0:-1])*1000000))
            elif 'K' in hzLow:
                hzLow = str(int(float(hzLow[0:-1])*1000))
        if element == '-b':
            numBins = int(elements[index+1].strip())
    print('using freq range '+hzLow + ' to '+hzHigh)
    hzLow = int(hzLow)
    hzHigh = int(hzHigh)
    #Now that we have the freqs in Hz, calculate the number of bytes
    binaryLineLength = int(math.ceil((hzHigh - hzLow)/BW)*4*numBins)
    print('Number of bytes in a row is '+str(binaryLineLength))
    return binaryLineLength, BW


def SIM_startDataPipe(call):
    #This will start a process that hands off data to a bytestream
    #Similar to the c drivers that are typically used to communicate with the hardware, this will generate a meta data file then a data file will be periodically written to.
    print('Entered Sim data pipe startup')
    print(call)
    BW = 2000000
    #process arguments
    for index, element in enumerate(call):
        if element == '-f':
            freqRange = call[index+1].split(':')
            hzHigh = freqRange[1].strip().upper()
            hzLow = freqRange[0].strip().upper()
            if 'G' in hzHigh:
                hzHigh = str(int(float(hzHigh[0:-1])*1000000000))
            elif 'M' in hzHigh:
                hzHigh = str(int(float(hzHigh[0:-1])*1000000))
            elif 'K' in hzHigh:
                hzHigh = str(int(float(hzHigh[0:-1])*1000))
            if 'G' in hzLow:
                hzLow = str(int(float(hzLow[0:-1])*1000000000))
            elif 'M' in hzLow:
                hzLow = str(int(float(hzLow[0:-1])*1000000))
            elif 'K' in hzLow:
                hzLow = str(int(float(hzLow[0:-1])*1000))
        if element == '-b':
            numBins = int(call[index+1].strip())
    print('using freq range '+hzLow + ' to '+hzHigh)
    hzLow = int(hzLow)
    hzHigh = int(hzHigh)
    filenameBase = call[-1]
    #Generate the meta data file
    '''
    SAMPLE:
    136080 # frequency bins (columns)
    0 # scans (rows)
    30000000 # startFreq (Hz)
    49985714 # endFreq (Hz)
    14285 # stepFreq (Hz)
    0.0007 # effective integration time secs
    4 # avgScanDur (sec)
    2022-09-22 06:06:35 UTC # firstAcqTimestamp UTC
    2022-09-22 06:07:35 UTC # lastAcqTimestamp UTC
    '''
    with open(filenameBase+'.met', 'w') as f:
        f.write('#########################\n')
        f.write('SIMULATED DATA\n')
        f.write(str(numBins) + ' # frequency bins (columns)\n')
        f.write('0 # scans (rows)\n')
        f.write(str(hzLow) + ' # startFreq (Hz)\n')
        f.write(str(hzHigh) + ' # endFreq (Hz)\n')
        stepSize = (hzHigh - hzLow)/numBins
        f.write(str(stepSize) + ' # stepFreq (Hz)\n')
        f.write('0.0007 # effective integration time secs\n')
        f.write('.5 # avgScanDur (sec)\n')
        f.write(datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S') + ' local # firstAcqTimestamp local')

    #for this case, we are just going to generate noise (a random number for power)
    #We will write 1000 rows of data for this case.
    with io.FileIO(filenameBase+'.bin', 'w') as f:
        #Use a normally distributed, low power distrubution. You shouldn't really see any pattern in this data
        dist = statistics.NormalDist(-50, 3)
        for i in range(0, 10000):
            #Generate a noisy measurement for each freq bin in our range.
            data = dist.samples(numBins)
            #Set 1 target freq to have way higher power then others.
            #tgtHz = 40000000
            #deltaHz = tgtHz - hzLow
            #tgtBin = deltaHz/BW
            #data[int(round(tgtBin, 0))] += 30
            binData = struct.pack('f'*numBins, *data)
            f.write(binData)
            #wait to sim hardware retuning time.
            time.sleep(random.random()/1000)

    print('Closed the data file, updating meta file')
    with open(filenameBase+'.met', 'a') as f:
        f.write(datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S') + ' local # lastAcqTimestamp local')
        f.write('#########################\n')


if __name__ == "__main__":
    print('started script')
    SIM_startDataPipe(sys.argv)
