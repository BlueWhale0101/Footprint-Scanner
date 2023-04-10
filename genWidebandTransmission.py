import numpy as np
import random

def genWidebandTransmission(queue = None, channels=[0, 0, 0, 0], power=[0,0,0,0], cmdFreq = '300M, 1.7G'):
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
    if centerPowers is None:
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