from tables import *
import os
from time import sleep

class RFMeasurements(IsDescription):
    #Define columns of our table
    time      = StringCol(20)   # 16-character String
    frequency  = Float32Col()    # float  (single-precision)
    power  = Float32Col()    # float  (single-precision)

def DB_Logger(queue=None, DB_Name="EARS_DB.h5"):
    print("Starting Logger")
    if not queue:
        Warning('No queue provided! Closing db manager.')
        return
    
    if not os.path.isfile(DB_Name):
        h5file = open_file(DB_Name, mode="w", title="EARS Measurements Record")
        group = h5file.create_group("/", 'measurement', 'RF Power information')
        table = h5file.create_table(group, 'readout', RFMeasurements, "Measurements Record")
    else:
        h5file = open_file(DB_Name, mode="a", title="EARS Measurements Record")
        #table handles are retrieved from the file handle with the format file_handle.mount_point.group_handle.table_handle
        table = h5file.root.measurement.readout
    measurement = table.row

    while True:
        #Just keep going until the task is killed. If nothing is put in the queue, or if the queue is closed, 
        #this task should close the db file and close out. 
        if not queue.empty():
            pkt = queue.get()

            if pkt[0] == 'QUIT':
                #Terminate the process! All clean up goes here.
                h5file.close()
                print('Logger going down!')
                return
            
            '''
            The expected format of these measurements is a tuple (time, data) where time is a 20 char string
            and data is a list of tuples containing (frequency, power)
            '''
            for reading in pkt[1]:
                measurement['time'] = pkt[0] #Should be a 20 char string
                measurement['frequency'] = reading[0]
                measurement['power'] = reading[1]
                measurement.append()
            table.flush()
        else:
            #If there isn't anything in the queue, we can wait a pretty long time. 
            #This doesn't need to be very fast. 1Hz is plenty.
            sleep(1)


def DB_Retrieval(DB_Name="EARS_DB.h5", cols=None, query_string=None):
    '''
    This is intended to provide an interface for our EARS database so that direct 
    pytables calls are not necessary in other modules. 
    This is likely to be an IO bound task, so good for concurrency/threading
    '''
    if not query_string:
        Warning('No query provided to DB_Retrieval')
        return 
    if not cols:
        #Default is to return power and frequency, but not time.
        cols = ['frequency', 'power']
    #If the database file doesn't exist, this fail
    if os.path.isfile(DB_Name):
        h5file = open_file(DB_Name, mode="r", title="EARS Measurements Record")
    else:
        Warning("Provided DB file doesn't exist.")
        return "Error"
    #table handles are retrieved from the file handle with the format file_handle.mount_point.group_handle.table_handle
    table = h5file.root.measurement.readout
    #names = [ x['name'] for x in table.where("""(power > 3) & (20 <= frequency) & (frequency < 50)""") ]
    try:
        #unfortunately, to make this sufficiently flexible, return a dictionary of tuples
        result = {}
        for key in cols:
            result[key] = ( x[key] for x in table.where(query_string) )
        return result
    except:
        Warning('Invalid query submitted')
        return 'Error'
