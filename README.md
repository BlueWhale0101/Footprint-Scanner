# Footprint-Scanner
The BatHunter system is a Raspberry Pi based spectrum analyzer which specifically monitors the RF spectrum in the military bands to perform three functions:

1. Wideband power monitoring and logging, for post operation analysis.
2. Provide insight into the RF visibility of the using unit local to the operator.
3. Provide indications and warnings of RF jamming.

Usage:

Start the program from the icon on the desktop. Choose the option for performing a VHF Scan, UHF scan, or full scan (UHF + VHF). Calibration will perform a long read of each section of the spectrum and provide an average noise value for comparing data to.

While the scan is ongoing, a plot of current data will stream along the page.



######################################################################

To Do:

1. Process data stream for each bin.
2. Spectrogram/waterfall display, column/bin. Time is down, so the most recent scan is on top.
3. Integrate baseline differencing.
4. Smooth data with moving average in bin.

######################################################################

Helpful links and notes:

Build RTL-SDR on your Mac: https://gist.github.com/jheasly/9477732

Usage for rtl-power, included in rtl-sdr:
http://kmkeen.com/rtl-power/

We still should try and get rtl-power-fftw working, since it is much faster apparently. But this should work for this week.

Other helpful sites
https://pyrtlsdr.readthedocs.io/en/latest/Overview.html#pyrtlsdr

https://github.com/steve-m/librtlsdr

https://osmocom.org/projects/rtl-sdr/wiki

https://github.com/roger-/pyrtlsdr
