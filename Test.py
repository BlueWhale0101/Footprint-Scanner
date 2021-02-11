from pylab import *
from rtlsdr import *

sdr = RtlSdr()

#Take samples in a loop
FreqRange = range(80, 90, 1)
samples = []
for CenterFreq in FreqRange:
    # configure device
    sdr.sample_rate = 2.4e6
    sdr.center_freq = CenterFreq*10**6
    sdr.gain = 4

    samples = samples + sdr.read_samples(256*1024)
sdr.close()

# use matplotlib to estimate and plot the PSD
specgram(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
xlabel('Frequency (MHz)')
ylabel('Relative power (dB)')

show()
