<<<<<<< HEAD
from pylab import *
from rtlsdr import RtlSdr

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.4e6
sdr.center_freq = 95e6
sdr.gain = 4

samples = sdr.read_samples(256*1024)
sdr.close()

# use matplotlib to estimate and plot the PSD
psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
xlabel('Frequency (MHz)')
ylabel('Relative power (dB)')

show()
=======
#Run the rtl_power script, and get the output from the script in a stream.

import os

stream = os.popen("rtl_power -f 30M:40M:10k -g 50 -i 1 -e 1s")


print('outputting stream')
output = stream.read()
output
>>>>>>> 92144a5e32a948d2be25107b5c3feff3c09fb8ae
