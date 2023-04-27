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
import random
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

def genFixedFreq(queue = None, scannedFreqRange='30M:35M', selectedFreq = 32_000_000, peakPower=0, snr=10):
    '''Generates fixed frequency transmission simulation with power centered on 
    selected frequency. The default behavior is to select a random center frequency
    between 30 and 88MHz
    :param selectedFreq: the center frequency of the transmission (in MHz)
    :param power: the power of the transmission (in dBm)
    :param snr: the signal-to-noise ratio of the added noise (in dB)
    '''

    #This is using a hard coded peak power of 0 dB at the Rx, and a channel width of nearly 12.5kHz. 
    s = responseObject()

    
    freqLow, freqHigh = convertFreqtoInt(scannedFreqRange)

    # If Frequency not selected give random
    if selectedFreq == 0:
        selectedFreq = np.random.uniform(freqLow + 50_000 , freqHigh - 50_001)

    

    # If peak power not selected give random
    if peakPower == 0:
        peakPower = np.random.uniform(-50, -1)

    # Create frequency array
    freqs = np.arange(freqLow, freqHigh, 100)

    width = 50000
   
    # Calculate power at each frequency using a piecewise function
    power = np.piecewise(freqs, [freqs < selectedFreq-width, 
                                 (freqs >= selectedFreq-width) & (freqs <= selectedFreq+width), 
                                 freqs > selectedFreq+width], 
                         [-70, peakPower, -70])
    
    # Decay peak power to baseline
    decay_const = 100  # Adjust as needed to control decay rate
    txCenterFreqDiff = np.absolute(freqs - int(selectedFreq))
    txCenterFreqIndex = txCenterFreqDiff.argmin()
    decay_range = np.arange(-500, 501)
    decay_func = lambda x: (peakPower - (-70)) * np.exp(-abs(x) / decay_const) + (-70)
    decay_range_left = txCenterFreqIndex + decay_range[decay_range < 0]
    decay_range_right = txCenterFreqIndex + decay_range[decay_range >= 0]
    power[decay_range_left] = [decay_func(x) for x in decay_range[decay_range < 0]]
    power[decay_range_right] = [decay_func(x) for x in decay_range[decay_range >= 0]]

     # Check if selected frequency plus width is greater than the maximum frequency
    if selectedFreq + width > freqs[-1] or selectedFreq - width < freqs[0]:
        power[freqs > selectedFreq + width] = -70
        power[freqs < selectedFreq - width] = -70

    # Add noise to power using the specified SNR
    noise = np.random.normal(0, 1, len(power))
    noise_power = np.var(power) / (10**(snr/10))
    scaled_noise = np.sqrt(noise_power) * noise
    power = power + scaled_noise
    data = list(zip(freqs, power))
    s.stdout = '\\n'.join([str(x)+' '+str(y) for x,y in data])
   
    curCmd = None

    if queue:
        while curCmd != 'QUIT':
            if not queue.empty():
                curCmd = queue.get()
            else:
                queue.put(s)
                sleep(.33) #running at around 3 hz
    else:
        return s


def genFreqHopping(queue = None, scannedFreqRange='30M:35M', peakPower=0, snr=10):
    """
    Generates frequency hopping transmission simulation with power center moving frequency every hopDuration seconds.
    If hopDuration or power is not provided, a random value within the proper parameters is chosen.
    The output data is a list of pairs of frequencies and power with added noise.
    :param power: the power of the transmission (in dBm)
    :param hopDuration: the duration of each hop in seconds
    :param snr: the signal-to-noise ratio of the added noise (in dB)
    :param totalDuration: the total duration of the simulation in seconds
    """

    #This is using a hard coded peak power of 0 dB at the Rx, and a channel width of nearly 12.5kHz. 
    s = responseObject()

    freqLow, freqHigh = convertFreqtoInt(scannedFreqRange)
    selectedFreq = np.random.uniform(freqLow + 50_000 , freqHigh - 50_001)

    # If peak power not selected give random
    if peakPower == 0:
        peakPower = np.random.uniform(-50, -1)

    # Create frequency array
    freqs = np.arange(freqLow, freqHigh, 100)

    width = 50000
   
    # Calculate power at each frequency using a piecewise function
    power = np.piecewise(freqs, [freqs < selectedFreq-width, 
                                 (freqs >= selectedFreq-width) & (freqs <= selectedFreq+width), 
                                 freqs > selectedFreq+width], 
                         [-70, peakPower, -70])
    
    # Decay peak power to baseline
    decay_const = 100  # Adjust as needed to control decay rate
    txCenterFreqDiff = np.absolute(freqs - int(selectedFreq))
    txCenterFreqIndex = txCenterFreqDiff.argmin()
    decay_range = np.arange(-500, 501)
    decay_func = lambda x: (peakPower - (-70)) * np.exp(-abs(x) / decay_const) + (-70)
    decay_range_left = txCenterFreqIndex + decay_range[decay_range < 0]
    decay_range_right = txCenterFreqIndex + decay_range[decay_range >= 0]
    power[decay_range_left] = [decay_func(x) for x in decay_range[decay_range < 0]]
    power[decay_range_right] = [decay_func(x) for x in decay_range[decay_range >= 0]]

    # Check if selected frequency plus width is greater than the maximum frequency
    if selectedFreq + width > freqs[-1] or selectedFreq - width < freqs[0]:
        power[freqs > selectedFreq + width] = -70
        power[freqs < selectedFreq - width] = -70

    # Add noise to power using the specified SNR
    noise = np.random.normal(0, 1, len(power))
    noise_power = np.var(power) / (10**(snr/10))
    scaled_noise = np.sqrt(noise_power) * noise
    power = power + scaled_noise
    data = list(zip(freqs, power))
    s.stdout = '\\n'.join([str(x)+' '+str(y) for x,y in data])
   
    curCmd = None

    if queue:
        while curCmd != 'QUIT':
            if not queue.empty():
                curCmd = queue.get()
            else:
                queue.put(s)
                sleep(.33) #running at around 3 hz
    else:
        return s

def genWidebandTransmission(queue = None, scannedFreqRange='30M:35M', selectedFreq1 = 31_000_000, selectedFreq2 = 32_000_000, selectedFreq3 = 33_000_000, selectedFreq4 = 34_000_000, peakPower=0, snr=10):
    '''Generates wideband transmission simulation with 4 channels centered at 
    selected frequencies with selected center power. The default behavior is 
    to select 4 random center frequencies between 300M to 1.7G at randomly selected
    center powers.
    :param channel: A list of length 4 to hold the generated center frequencies.
    :param power: A list of length 4 to hold the generated center powers.
    :param freq_range: The range of frequencies to select from. Default is (300M, 1.7G).
    :param power_range: The range of center powers to select from. Default is (0, 10).
    :return: None
    '''

    #This is using a hard coded peak power of 0 dB at the Rx, and a channel width of nearly 12.5kHz. 
    s = responseObject()

    freqLow, freqHigh = convertFreqtoInt(scannedFreqRange)

    # If Frequency not selected give random for each of the four frequencies
    if selectedFreq1 == 0:
        selectedFreq1 = np.random.uniform(freqLow + 50_000 , freqHigh - 50_001)
    if selectedFreq2 == 0:
        selectedFreq2 = np.random.uniform(freqLow + 50_000 , freqHigh - 50_001)
    if selectedFreq3 == 0:
        selectedFreq3 = np.random.uniform(freqLow + 50_000 , freqHigh - 50_001)
    if selectedFreq4 == 0:
        selectedFreq4 = np.random.uniform(freqLow + 50_000 , freqHigh - 50_001)

    # If peak power not selected give random
    if peakPower == 0:
        peakPower = np.random.uniform(-50, -1)

    # Create frequency array
    freqs = np.arange(freqLow, freqHigh, 100)

    width = 50000
   
    # Calculate power at each frequency using a piecewise function
    power = np.piecewise(freqs, [(freqs < selectedFreq1-width) | (freqs > selectedFreq1+width), 
                                 (freqs >= selectedFreq1-width) & (freqs <= selectedFreq1+width),
                                 (freqs < selectedFreq2-width) | (freqs > selectedFreq2+width), 
                                 (freqs >= selectedFreq2-width) & (freqs <= selectedFreq2+width),
                                 (freqs < selectedFreq3-width) | (freqs > selectedFreq3+width), 
                                 (freqs >= selectedFreq3-width) & (freqs <= selectedFreq3+width),
                                 (freqs < selectedFreq4-width) | (freqs > selectedFreq4+width), 
                                 (freqs >= selectedFreq4-width) & (freqs <= selectedFreq4+width)], 
                         [-70, peakPower, -70, peakPower, -70, peakPower, -70, peakPower],)
    
    # Decay peak power to baseline
    decay_const = 100  # Adjust as needed to control decay rate
    for freq in [selectedFreq1, selectedFreq2, selectedFreq3, selectedFreq4]:
        txCenterFreqDiff = np.absolute(freqs - int(freq))
        txCenterFreqIndex = txCenterFreqDiff.argmin()
        decay_range = np.arange(-500, 501)
        decay_func = lambda x: (peakPower - (-70)) * np.exp(-abs(x) / decay_const) + (-70)
        decay_range_left = txCenterFreqIndex + decay_range[decay_range < 0]
        decay_range_right = txCenterFreqIndex + decay_range[decay_range >= 0]
        power[decay_range_left] = [decay_func(x) for x in decay_range[decay_range < 0]]
        power[decay_range_right] = [decay_func(x) for x in decay_range[decay_range >= 0]]

    # Check if selected frequency plus width is greater than the maximum frequency
    for freq in [selectedFreq1, selectedFreq2, selectedFreq3, selectedFreq4]:
        if freq + width > freqs[-1] or freq - width < freqs[0]:
            power[freqs > freq + width] = -70
            power[freqs < freq - width] = -70

    # Add noise to power using the specified SNR
    noise = np.random.normal(0, 1, len(power))
    noise_power = np.var(power) / (10**(snr/10))
    scaled_noise = np.sqrt(noise_power) * noise
    power = power + scaled_noise
    data = list(zip(freqs, power))
    s.stdout = '\\n'.join([str(x)+' '+str(y) for x,y in data])
   
    curCmd = None

    if queue:
        while curCmd != 'QUIT':
            if not queue.empty():
                curCmd = queue.get()
            else:
                queue.put(s)
                sleep(.33) #running at around 3 hz
    else:
        return s

def genQuickAndDirtySimForWes(queue = None, scannedFreqRange='30M:35M', txCenterFreq = 32_000_000, peakPower=0):
    '''Wes did this so he would have something to use for mobile testing. 
    It takes the range you are scanning (in hz), the peak power (in dB) and center frequency (in hz) 
    of the modeled signal, and returns the familiar string of frequency, power comma seperated pairs
    seperated by \n in the stdout of a response object. If the queue is provided, it will loop and 
    provide an object every second. Otherwise, it will just run once.'''

    #This is using a hard coded peak power of 0 dB at the Rx, and a channel width of nearly 12.5kHz. 
    s = responseObject()

    #Figure out how long the array is. It's max freq - min freq, step size of 200 hz
    lowF, highF = convertFreqtoInt(scannedFreqRange)
    freqs = np.arange(lowF, highF+200, 200) #This is our x axis, or list of frequencies
    txCenterFreqDiff = np.absolute(freqs - int(txCenterFreq)) #Absolute Difference between center tx freq and all freq values
    txCenterFreqIndex =  txCenterFreqDiff.argmin() #This is the index of frequency at which the center freq of transmission is found
    power = np.ones(len(freqs)) * -70 + np.random.uniform(-2, 2, (1, len(freqs))) #baseline power is -70, with random noise between - and 2 db
    power = power[0]
    TxDecay = np.power(np.e, (-1/1800)*np.arange(0, 6600, 200))*36-1 #Exponential decay, peaking at 0 dB and decaying to -70 dB by 6200 hz away for a total channel width of 12400 hz
    power[txCenterFreqIndex:txCenterFreqIndex+33] = power[txCenterFreqIndex:txCenterFreqIndex+33] + TxDecay
    power[txCenterFreqIndex-32:txCenterFreqIndex+1] = power[txCenterFreqIndex-32:txCenterFreqIndex+1] + np.flip(TxDecay) #Mirror the decay for the growth side
    data = list(zip(freqs, power))
    s.stdout = '\\n'.join([str(x)+' '+str(y) for x,y in data])
   
    curCmd = None

    if queue:
        while curCmd != 'QUIT':
            if not queue.empty():
                curCmd = queue.get()
            else:
                queue.put(s)
                sleep(.33) #running at around 3 hz
    else:
        return s