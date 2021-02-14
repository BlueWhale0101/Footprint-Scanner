from create_baselines import *
import os

command = makeCommand(fileName="Data/test_data.csv", hzLow = "30M", hzHigh = "90M", binSize = "10k", gain = "50", interval = "5", exitTimer = "5M")
os.system(command)
