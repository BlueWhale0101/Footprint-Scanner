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

def genFixedFreq(queue = None, cmdFreq = '62M:67M', selectedFreq=65_000_000, power=-30, snr=10):
    '''Generates fixed frequency transmission simulation with power centered on 
    selected frequency. The default behavior is to select a random center frequency
    between 30 and 88MHz
    :param selectedFreq: the center frequency of the transmission (in MHz)
    :param power: the power of the transmission (in dBm)
    :param snr: the signal-to-noise ratio of the added noise (in dB)
    '''

    s = responseObject()

    #3/5 There are really two frequency concepts you need in this function:
    #The frequecy range we are sweeping and the center frequency where the power is 
    #observed. It looks like the intent of selectedFreq is to be the center frequency, 
    #so I've added a parameter for the commanded fequency range, cmdFreq. This mirrors
    #the real scanning function and us to re-use syntax from our hardware commanding for 
    #our sim commanding.

    #3/5 Let's set a reasonable default value instead of randomly selecting as the default 
    #behavior. Leave this snippet here, however so that explicitly passing a value of 0
    #(which would normally result in undefined behavior) will select a random f_center
    #I've selected 66MHz as the default.
    if selectedFreq == 0:
        selectedFreq = np.random.uniform(30_000_000, 88_000_000)
    
    #3/5 This function will take the same format that the hardware driver takes and return
    #two integers we can use as our commanded frequency sweep limits.
    freqLow, freqHigh = convertFreqtoInt(cmdFreq)
    #3/5 Similar to f_center, I've changed the defualt value to a reasonable value of 
    #-30 dB. Note that the units are not really dBm, as the comparison value is not 
    #calibrated at all. So, while dB is accurate, the units can't be meaningfully converted
    #to absolute values.
    if power == 0:
        power = np.random.uniform(-100, 0)
    breakpoint()
    #3/5 Generate samples across the entire swept frequency range. The units are Hz, 
    #typically 200hz wide samples.
    # Generate signal power at the specified frequency
    freqs = np.arange(freqLow, freqHigh, 200)
    signal_power = np.ones_like(freqs) * 10 ** (power / 10)
    
    # Generate random noise samples with Gaussian distribution
    noise_power = signal_power / (10 ** (snr / 10))
    noise = np.random.normal(0, np.sqrt(noise_power))
    
    # Add noise to the signal
    signal = signal_power + noise
    
    # Combine signal and frequency data
    data = list(zip(freqs, signal))
    s.stdout = '\\n'.join([str(x)+' '+str(y) for x,y in data])
   
    curCmd = None

    if queue:
        #Minor syntax update 3/5
        while curCmd != 'QUIT':
            if not queue.empty():
                curCmd = queue.get()
            else:
                queue.put(s)
                sleep(.33) #running at around 3 hz
    else:
        return s


def genFreqHopping(queue = None, power=0, hopDuration=0, snr=10, totalDuration=10):
    """
    Generates frequency hopping transmission simulation with power center moving frequency every hopDuration seconds.
    If hopDuration or power is not provided, a random value within the proper parameters is chosen.
    The output data is a list of pairs of frequencies and power with added noise.

    :param power: the power of the transmission (in dBm)
    :param hopDuration: the duration of each hop in seconds
    :param snr: the signal-to-noise ratio of the added noise (in dB)
    :param totalDuration: the total duration of the simulation in seconds
    """
    s = responseObject()
    if hopDuration == 0:
        hopDuration = np.random.uniform(0.05, 0.25)
    if power == 0:
        power = np.random.uniform(-100, 0)
    
    freqs = np.arange(30_000_000, 88_000_000, 0.01)
    center_freq = np.random.choice(freqs)
    time = 0
    data = []
    
    while True:
        # Generate signal power at the specified frequency
        signal_power = np.ones_like(freqs) * 10 ** (power / 10)
        
        # Generate random noise samples with Gaussian distribution
        noise_power = signal_power / (10 ** (snr / 10))
        noise = np.random.normal(0, np.sqrt(noise_power))
        
        # Add noise to the signal
        signal = signal_power + noise
        
        # Shift the center frequency to simulate hopping
        freq_offset = np.random.uniform(-0.5, 0.5)
        center_freq += freq_offset
        
        # Combine signal and frequency data
        data += list(zip(freqs, signal))
        
        # Check if the total duration has been exceeded
        time += hopDuration
        if totalDuration and time >= totalDuration:
            break
        
        # Wait for the next hop duration
        time.sleep(hopDuration)
    
    s.stdout = '\\n'.join([str(x)+' '+str(y) for x,y in data])
   
    curCmd = None

    if queue:
        #3/5 Minor syntax update
        while curCmd != 'QUIT':
            if not queue.empty():
                curCmd = queue.get()
            else:
                queue.put(s)
                sleep(.33) #running at around 3 hz
    else:
        return s

import numpy as np
import random

def genWidebandTransmission(queue = None, channels=[0, 0, 0, 0], power=[0,0,0,0], cmdFreq = '300M, 1.7G', snr = 10):
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

    '''
    4/6 Overall, I can see where you are going but it looks like there are some misunderstandings
    in both the design and implementation of the code. I've dropped some notes below to help guide
    where you should be going, and I think the comments and actual code in both Kaleb's 
    fixed frequency sim as well as genQuickAndDirtySimForWes in StreamSim.py. 
    '''



    s = responseObject()

    # Convert commanded frequency range to integers
    freqLow, freqHigh = convertFreqtoInt(cmdFreq)

    '''
    4/6 Doesn't look like centerPowers is a provided parameter, so this will always default to the None behavior. 
    I see where you are going here, but i'm not sure if you want that to happen. If you meant 'power',
    then this will never occur unless the user actually passes 'None' into that param (which would
    definitely be weird). I think you mean:
    if power = [0,0,0,0].

    That being said, I think using 0 db as the defaul power of the centers of the transmitting channels
    is a reasonable assumption, whereas using a random range between 0, -100 is not. Unless you have a
    good reason for this behavior, I would nix these lines. 
    '''
    # Set default center powers if none are provided
    if power == [0,0,0,0]:
        centerPowers = np.random.uniform(-100, 0, size=4)

    # Generate samples across the entire swept frequency range
    freqs = np.arange(freqLow, freqHigh, 200)

    '''
    4/6 The code below will ignore the channel information that is passed in by the user entirely.
    That means, no matter what, the channels will be at random frequencies instead of being commandable.
    Definitely change it so that the commanded center frequencies are used. The default behavior if either 
    all zeros or None is passed in should be to select random frequencies, but that defintely shouldn't be the
    only possible behavior. 
    '''
    # Generate signal power for each of the 4 channels
    signal_power = np.zeros_like(freqs)
    for centerFreq, centerPower in zip(np.random.uniform(300_000_000, 1_700_000_000, size=4), centerPowers):
        signal_power += np.exp(-(freqs - centerFreq) ** 2 / (2 * (20e6) ** 2)) * 10 ** (centerPower / 10)


    '''
    4/6 Definitely need to define SNR here... That isn't a global in StreamSim. 
    This could be a user defined param with a reasonable default value if you want to make this more configurable.
    '''
    # Generate random noise samples with Gaussian distribution
    noise_power = signal_power / (10 ** (snr / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), size=len(freqs))

    # Add noise to the signal
    signal = signal_power + noise

    # Combine signal and frequency data
    data = list(zip(freqs, signal))
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
