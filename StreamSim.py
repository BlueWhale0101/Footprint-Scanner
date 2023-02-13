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