'''
This module contains all the functions for generating the stream of sim data for ears. 
There are a handful of options available. The default behavior is to generate random noise across 
the spectrum requested, where power is distrubuted randomly centered on -70 dB. 
That seems to be about the typical noise floor of my hardware. 

You can select different types of activity to simulate
-a randomly selected or named 'high power' streak (fixed frequency transmission)
-frequency hopping (high power center freq jumps around randomly in a 20 MHz band)
-Wideband transmission - 4 channels of high power with a randomly or user selected set of 
frequencies and power distributions.
'''

import numpy as np
from time import sleep

class responseObject():
    def __init__(self):
        self.stdout = ''
        self.stderr = ''
        self.returncode = 0

    def clear(self):
        self.stdout = ''
        self.stderr = ''
        self.returncode = 0

def convertFreqtoInt(freqStr):
    '''commanded freqs typically use an easy to read notation with prefixes. 
    for example, cmdFreq = '30M:35M'
    This utility converts them into normal ints.
    '''
    lowFreq, highFreq = freqStr.split(':')
    rep = [('M', '_000_000'), ('G', '_000_000_000'), ('K', '_000')]
    for p, i in rep:
        lowFreq = lowFreq.replace(p, i)
        highFreq = highFreq.replace(p, i)
    return (int(lowFreq), int(highFreq))

def simFrontEnd():
    '''This function deals with taking in the user requested behavior, selecting 
    the right functions to call to get the data they want generated, then handing
    back the string for parsing just like the normal hardware routine does. '''
    pass

def genFixedFreq(selectedFreq=0, power=0):
    '''Generates fixed frequency transmission simulation with power centered on 
    selected frequency. The default behavior is to select a random center frequency
    between 30 and 88MHz'''
    pass

def genFreqHopping(hopDuration=0, power=0):
    '''Generates frequency hopping transmission simulation with power center moving
    frequency every hopDuration seconds. The default behavior is to select a random
    hop duration between .05 and .25'''
    pass

def genWidebandTransmission(channels=[0, 0, 0, 0], power=[0,0,0,0]):
    '''Generates wideband transmission simulation with 4 channels centered at 
    selected frequencies with selected center power. The default behavior is 
    to select 4 random center frequencies between 300M to 1.7G at randomly selected
    center powers.'''
    pass

def genQuickAndDirtySimForWes(queue = None, scannedFreqRange='30M:35M', txCenterFreq = 32_000_000, peakPower=0):
    '''Wes did this so he would have something to use for mobile testing. 
    It takes the range you are scanning (in hz), the peak power (in dB) and center frequency (in hz) 
    of the modeled signal, and returns the familiar string of frequency, power comma seperated pairs
    seperated by \n in the stdout of a response object. If the queue is provided, it will loop and 
    provide an object every second. Otherwise, it will just run once.'''

    s = responseObject()

    #Figure out how long the array is. It's max freq - min freq, step size of 200 hz
    lowF, highF = convertFreqtoInt(scannedFreqRange)
    freqs = np.arange(lowF, highF+200, 200) #This is our x axis, or list of frequencies
    txCenterFreqDiff = np.absolute(freqs - int(txCenterFreq)) #Absolute Difference between center tx freq and all freq values
    txCenterFreqIndex =  txCenterFreqDiff.argmin() #This is the index of frequency at which the center freq of transmission is found
    power = np.ones(len(freqs)) * -70 + np.random.uniform(-2, 2, (1, len(freqs))) #baseline power is -70, with random noise between - and 2 db
    power = power[0]
    TxDecay = np.power(np.e, (-1/350)*np.arange(0, 2200, 200))*35 #Exponential decay, peaking at 0 dB and decaying to -70 dB by 800 hz away for a total channel width of 1600 hz
    power[txCenterFreqIndex:txCenterFreqIndex+11] = power[txCenterFreqIndex:txCenterFreqIndex+11] + TxDecay
    power[txCenterFreqIndex-10:txCenterFreqIndex+1] = power[txCenterFreqIndex-10:txCenterFreqIndex+1] + np.flip(TxDecay)
    data = list(zip(freqs, power))
    s.stdout = '\\n'.join([str(x)+' '+str(y) for x,y in data])
   
    curCmd = None

    if queue:
        while curCmd is not 'QUIT':
            if not queue.empty():
                curCmd = queue.get()
            else:
                queue.put(s)
                sleep(.33) #running at around 3 hz
    else:
        return s
