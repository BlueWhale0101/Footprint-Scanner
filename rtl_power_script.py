import os
import schedule
import time
from datetime import datetime, timedelta, date

#rtl_power -f 674.230M:674.233M:1 -g 50 -i 1 -e 1h radar.csv

def makeCommand(fileName):
	answer = "rtl_power "
	fileName = fileName
	hzLow = "118M"
	hzHigh = "137M"
	binSize = "8k"
	gain = "50"
	interval = "10"
	exitTimer = "1m"
	answer += " -f "
	answer += hzLow + ":" + hzHigh + ":" + binSize + " -g " + gain + " -i " + interval + " -e " + exitTimer + " " + fileName
	return answer


# def job():

# 	if file_size > 0:
# 		os.system('')

# schedule.every().day.at("20:53").do(job)


count = 0
while count < 5:
	curTime = datetime.now().strftime("%m%d%H%M")
	fileName = curTime+".csv"
	command = makeCommand(fileName)
	os.system(command)
	count += 1

