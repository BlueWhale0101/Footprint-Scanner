'''
The purpose of this module is to perform various analyses on whole sessions of recorded data
from EARS. It is not intended to be run on live data, and cannot be run while the SpectroViewer
is running. Typical use case steps are below. 

1. Retrieve the requested session's data from the database.
    ~Can also print out list of sessions
2. Process data for formatting with the Record class, which has the following attributes and methods:
Attr: (freq, power) - key dataframe formatted data
attr: 

3. Use multiple Records to try and find relationships to allow us to find important/interesting
data more quickly
'''

from tables import *
import pandas as pd
from DBManager import RetrieveBaselineData
import numpy as np
#import seaborn as sns
import matplotlib.pyplot as plt
#import datetime

plt.ion()
plt.style.use('dark_background')
plt.grid(True)

with open_file('EARS_DB.h5', mode="a", title="EARS Measurements Record") as h5file:
    dataTable = h5file.root.measurement.readout
    commandTable = h5file.root.Logs.commandLog
    baselineTable = h5file.root.baseline.readout
    '''
    Helpful notes:
    faster queries (in kernel) are performed on database with the table.where function. 
    Ex: table.where('(frequency>={}) & (frequency<={})'.format(freqMin, freqMax))
    
    to see all the unique session ID's in the data, use pd.unique(table.col('sessionID'))
    this can take some time - it loads the whole column which is easily millions of rows.

    It is probably much faster to query the command database to figure out what you want first. 
    it's going to be WAY smaller, since just a few commands are sent per session and thousands
    of RF measurements are made.
    pd.unique(commandTable.col('sessionID'))
    '''
    cmd = pd.DataFrame(commandTable.read())
    print(cmd[['command', 'time']])
    # For our case, this is the session Id: b'2cb76486-67c4-4a44-a687-8b3057a703a4'
    #This has a simulated constant fixed frequency signal
    print('\n')
    print("Using b'0f04cfdf-fe1c-4448-94e4-a89d7a48a662'")
    print('\n')
    data = pd.DataFrame(dataTable.read_where('''(sessionID == b'0f04cfdf-fe1c-4448-94e4-a89d7a48a662')'''))
    print(data)
    print('\n')

#Now get the baseline data
#Filter the baseline data to match the data we have
blData = RetrieveBaselineData(freqMin = data['frequency'].min(), freqMax = data['frequency'].max())
print('Baseline Data')
bl = pd.DataFrame(blData, columns=['frequency', 'power'])
#bl = bl.set_index('frequency')
print(bl)
print('\n\n')
'''
There are a lot of ways of looking at this data... 
1. use a sequence of dataframes which each have one measurement. then look at how one compares to the next.
2. transpose the data to a new type of dataframe, which has a column for each frequency bin. then 
    I can look at how individual frequencies change at a time.
    ~max
    ~min
    ~stddev
    ~cumsum
    ~
3. group the measurements by frequency and look at the characteristics of the frequencies like that. 

options 2 and 3 are conceptually similar but implementation very different. I think I would use
opt 2 to think about HOW to look at the data, but implement a final solution using option 3.
'''
fig, ax = plt.subplots()
data.plot(ax=ax, x='frequency', y='power')
bl.plot(ax=ax, y='power')
#Group data by frequency
groupedData = data[['frequency', 'power']].groupby('frequency')
#take the difference between the baseline data and our data
filteredData = groupedData.max().combine(bl, np.subtract, overwrite = False)
#interpolate between points. baseline has a lot less points then the measurement, so we end up with a lot of NANs
filteredData = filteredData.interpolate()
filteredData.plot(grid='on').figure.show()
plt.pause(.1)





breakpoint()


    