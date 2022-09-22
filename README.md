# Footprint-Scanner

Baseline calibration calculation function is written
Main GUI is written, but doesn't call any RF Functions.


Build RTL-SDR on your Mac: https://gist.github.com/jheasly/9477732

Usage for rtl-power, included in rtl-sdr:
http://kmkeen.com/rtl-power/

rtl-power-fftw github.
https://github.com/AD-Vega/rtl-power-fftw

The above rtl-power-fftw depends on lib fftw3f. This is the single precision float variety of fftw3. You should install both the standard and single precision variety. Follow instructions here: http://www.fftw.org/
Then follow the instructions here: https://stackoverflow.com/questions/37267441/configure-warning-fftw3f-library-not-found-the-slower-fftpack-library-will-be
summarized as running the typical sequence, then at then end, from build, running "sudo ../configure --enable-float --enable-sse && sudo make install"

#########################
Typical install pattern
git clone <repo>
cd <repo>
mkdir Build
cd Build
cmake ..
make install
#######################

Other helpful sites
https://pyrtlsdr.readthedocs.io/en/latest/Overview.html#pyrtlsdr

https://github.com/steve-m/librtlsdr

https://osmocom.org/projects/rtl-sdr/wiki

https://github.com/roger-/pyrtlsdr
