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


###profiling stuff
import pdb
# import cProfile, pstats, io
# from pstats import SortKey

# pr = cProfile.Profile()
# pr.enable()
############

def passToDbLogger(data):
    global logQueue
    #pass data from subprocess
    curTime = datetime.datetime.now().strftime("<%Y:%m:%d:%H:%M:%S")
    dataToPass = (curTime, data)
    if logQueue.full():
        Warning('Log Buffer overflow. Dropping data.')
        return 
    else:
        logQueue.put(dataToPass)

def main():
    plt.ion()
    plt.style.use('dark_background')
    fig, ax = plt.subplots()
    cmd = 'rtl_power_fftw -f 30M:280M -b 500 -n 100 -g 100 -q'
    args = shlex.split(cmd)

    #Start our logging queue, max size 25. I don't really expect it to get past 1 or 2, so this should be PLENTY.
    logQueue = Queue(25)
    #Start up the logging thread
    logger = Process(target=DB_Logger, args=(logQueue,), daemon=True)
    logger.start()


    #Get the baseline data
    #Definig what the baseline is might be tricky, depending on how much we let the user control. 
    #For now, baseline is going to be a red horizontal line. 

    #initialize the max
    maxDF = pd.DataFrame(columns=['frequency', 'power'])

    #Actual Scanning and displaying function
    for i in range(3):
        #Very lazy loop to see 5 plot updates
        #I want to be able to see the data from the cmd when I want and not flood the screen.
        s = sb.run(args, stdout=sb.PIPE, shell=False)
        while not s.returncode == 0:
            sleep(.5)
        #This should give a quick message to the user, then I should be able to get the values I want periodically
        data = str(s.stdout).strip().split('\\n')
        data = [x for x in data if '#' not in x and len(x) > 2] #Get rid of rows with comments and blank lines
        data = [(float(x), float(y)) for (x, y) in [x.split(' ') for x in data]] #Process into a list of tuples (freq, dB)
        df = pd.DataFrame(data, columns=['frequency', 'power']) #revisit this later. Profiling showed this wasn't a big eater, but the dataframe class is way beefier than I need for just a plot
        threading.Thread(target=passToDbLogger, args=(data, )) #Go ahead and leave this in another thread. This thread should focus on processing the RF data        
        
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
        maxDF.reset_index().plot(ax=ax, x='freqCompare', y='power', style='y', label='max hold', grid='On', title = 'ScanView')
        df.plot(ax=ax, x='frequency', y='power', grid='On', title = 'ScanView', label='current', alpha = .7)
        ax.fill_between(df['frequency'], df['power'], df['power'].min(), alpha = .5)
        plt.hlines(df['power'].min()+2, xmax= df['frequency'].max(), xmin=df['frequency'].min(), colors='r', linestyles='dotted')
        plt.pause(.1)


    ###Profiling stuff#######
    # pr.disable()
    # s = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print(s.getvalue())
    ###########
    input('Press Enter to continue...')
    print('Closing Logger')
    logQueue.put(('QUIT'))
    logger.join()

if __name__ == '__main__':
    #Honestly, this is just here because multiprocessing needs it.
    main()