import shlex
import subprocess as sb
import matplotlib.pyplot as plt
from multiprocessing import Process
from time import sleep
import pandas as pd
import pdb

plt.ion()
plt.style.use('dark_background')
fig, ax = plt.subplots()
cmd = 'rtl_power_fftw -f 30M:88M -b 500 -n 100 -g 100'
args = shlex.split(cmd)

for i in range(5):
    #Very lazy loop to see 5 plot updates
    #I want to be able to see the data from the cmd when I want and not flood the screen.
    s = sb.run(args, stdout=sb.PIPE, shell=False)
    while not s.returncode == 0:
        sleep(.5)
    #This should give a quick message to the user, then I should be able to get the values I want periodically
    data = str(s.stdout).strip().split('\\n')
    data = [x for x in data if '#' not in x and len(x) > 2] #Get rid of rows with comments and blank lines
    data = [(float(x), float(y)) for (x, y) in [x.split(' ') for x in data]] #Process into a list of tuples (freq, dB)
    df = pd.DataFrame(data, columns=['frequency', 'power'])
    #pdb.set_trace()
    ax.cla()
    df.plot(x='frequency', y='power', ax=ax, grid=True)
    plt.pause(.1)

input('Press Enter to continue...')