#Run the rtl_power script, and get the output from the script in a stream.

import os

stream = os.popen("rtl_power -f 30M:40M:10k -g 50 -i 1 -e 1s")


print('outputting stream')
output = stream.read()
output
