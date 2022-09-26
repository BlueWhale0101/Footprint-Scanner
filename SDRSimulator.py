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
    print('using freq range '+hzLow+ ' to '+hzHigh)
    hzLow = int(hzLow)
    hzHigh = int(hzHigh)
    #Now that we have the freqs in Hz, calculate the number of bytes
    binaryLineLength = int(math.ceil((hzHigh - hzLow)/BW)*4*numBins)
    print('Number of bytes in a row is '+str(binaryLineLength))
    return binaryLineLength, BW
