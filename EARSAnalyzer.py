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

#Start session: 2023:02:18:20:26:46
#End session:   2023:02:18:20:27:35
#The above is for test data, simulated fixed frequency tx, 0 dB, center freq at 32.5 MHz

from tables import *
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
import pdb

with open_file('EARS_DB.h5', mode="a", title="EARS Measurements Record") as h5file:
    table = h5file.root.measurement.readout
    pdb.set_trace()
    df = pd.DataFrame(table.read()) #Reading in entire table right now, which is probably dumb
