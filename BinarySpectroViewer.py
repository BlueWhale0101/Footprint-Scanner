import shlex
import subprocess as sb
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue
import threading
from time import sleep
import pandas as pd
from DBManager import * 
import datetime
from numpy import maximum


def processRFScan(scanData):
    data = str(scanData).strip().split('\\n')
    data = [x for x in data if '#' not in x and len(x) > 2] #Get rid of rows with comments and blank lines
    data = [(float(x), float(y)) for (x, y) in [x.split(' ') for x in data]] #Process into a list of tuples (freq, dB)
    return data

def passToDbLogger(data, simFlag):
    global logQueue
    #pass data from subprocess
    curTime = datetime.datetime.now().strftime("<%Y:%m:%d:%H:%M:%S")
    dataToPass = (curTime, data, simFlag)
    if logQueue.full():
        Warning('Log Buffer overflow. Dropping data.')
        return 'Overflow Error'
    else:
        logQueue.put(dataToPass)
        return 'Sucess'

def takeBaselineMeasurement():
    '''
    Measure power across a very broad spectrum and return the results from the stdout output.
    '''
    simFlag = False #Sim isn't implemented yet. This is hardcoded false for now. 
    cmd = 'rtl_power_fftw -f 30M:1.7G -b 500 -n 500 -g 100 -q'
    args = shlex.split(cmd)
    s = sb.run(args, stdout=sb.PIPE, stderr=sb.PIPE, shell=False)
    while not s.returncode == 0:
        if s.returncode == 1:
            #We errored out. Most likely, RTL SDR is not plugged in
            if 'No RTL-SDR' in str(s.stderr):
                print('You forgot to plug in the RTL-SDR!')
            print('Scan failed with error "{}"'.format(s.stderr))
            return
        else:
            #We need to just keep waiting to finish. This scan really does take awhile.
            sleep(.5)
    data = processRFScan(s.stdout)
    time = curTime = datetime.datetime.now().strftime("<%Y:%m:%d:%H:%M:%S")
    BLData = (time, data, simFlag)
    StoreBaselineData(pkt=BLData)

    return 'Sucess'

def convertFreqtoInt(freqStr):
    '''commanded freqs typically use an easy to read notation with prefixes. 
    for example, cmdFreq = '30M:35M'
    This utility converts them into normal strings.
    '''
    lowFreq, highFreq = freqStr.split(':')
    rep = [('M', '_000_000'), ('G', '_000_000_000'), ('K', '_000')]
    for p, i in rep:
        lowFreq = lowFreq.replace(p, i)
        highFreq = highFreq.replace(p, i)
    return (int(lowFreq), int(highFreq))

def streamScan(cmdFreq = '30M:35M'):
    simFlag = False #Sim isn't implemented yet. This is hardcoded False for now. 

    plt.ion()
    plt.style.use('dark_background')
    fig, ax = plt.subplots()
    cmd = 'rtl_power_fftw -f {0} -b 500 -n 100 -g 100 -q'.format(cmdFreq)
    args = shlex.split(cmd)
    #Start our global logging queue, max size 25. Multiple processes and threads need this. 
    #I don't really expect it to get past 1 or 2, so this should be PLENTY.
    global logQueue 
    logQueue = Queue(25)
    #Start up the logging thread
    logger = Process(target=DB_Logger, args=(logQueue,), daemon=True)
    logger.start()


    #Get the baseline data
    #Figure out the numeric equivalent of our commanded freqs
    lowF, highF = convertFreqtoInt(cmdFreq)
    blData = RetrieveBaselineData(freqMin = lowF, freqMax = highF)
    if blData is None:
        print('Blank baseline data!')
        baseline = pd.DataFrame(columns=['frequency', 'power'])
    else:
        baseline = pd.DataFrame(blData, columns=['frequency', 'power'])
    #initialize the max
    maxDF = pd.DataFrame(columns=['frequency', 'power'])

    #Actual Scanning and displaying function
    for i in range(3):
        print('Scan ', str(i))
        #Very lazy loop to see plot updates
        #I want to be able to see the data from the cmd when I want and not flood the screen.
        s = sb.run(args, stdout=sb.PIPE, stderr=sb.PIPE, shell=False)
        while not s.returncode == 0:
            if s.returncode == 1:
                #We errored out. Most likely, RTL SDR is not plugged in
                if 'No RTL-SDR' in str(s.stderr):
                    print('You forgot to plug in the RTL-SDR!')
                print('Scan failed with error "{}"'.format(s.stderr))
                return
            else:
                #We need to just keep waiting to finish. This scan really does take awhile.
                sleep(.5)
        data = processRFScan(s.stdout) #Process the bytes like object into the list of tuples we use for processing
        df = pd.DataFrame(data, columns=['frequency', 'power']) #revisit this later. Profiling showed this wasn't a big eater, but the dataframe class is way beefier than I need for just a plot
        threading.Thread(target=passToDbLogger, args=(data, simFlag)).start() #Go ahead and leave this in a different thread. This present thread should focus on processing the RF data        
        
        #Got the new data - calculate max
        df['freqCompare'] = df['frequency'].round(0)
        df = df.set_index('freqCompare')
        if maxDF.empty:
            #Initialize the max to the last measurement
            maxDF = df
        else:
            #not the first time. compare more discreet freqs by rounding
            #I basically don't care about the frequency column in maxDF, only the rounded one. 
            maxDF.combine(df, maximum, overwrite = False)


        #Draw the new plots. We have to redraw all of them right now - probably not ideal.
        ax.cla()
        maxDF.reset_index().plot(ax=ax, x='freqCompare', y='power', style='y', linewidth = .5, label='max hold', grid='On', title = 'ScanView')
        df.plot(ax=ax, x='frequency', y='power', grid='On', title = 'ScanView', label='current', alpha = .7, linewidth = .5)
        ax.fill_between(df['frequency'], df['power'], df['power'].min(), alpha = .5)
        baseline.plot(ax=ax, x='frequency', y='power', style='r-.', linewidth=.3, alpha = .7)
        plt.pause(.1)


    input('Press Enter to continue...')
    print('Closing logger...')
    logQueue.put('Quit')
    logger.join()

if __name__ == '__main__':
    #Check for baseline data

    if not checkForBaselineData():
        #Get baseline data
        print('Generating baseline data. Sit tight...')
        takeBaselineMeasurement()

    #Call main function
    streamScan()