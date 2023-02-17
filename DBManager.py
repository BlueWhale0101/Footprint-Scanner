from tables import *
import os
from time import sleep

class RFMeasurements(IsDescription):
    #Define columns of our table
    time      = StringCol(20)   # 20-character String
    frequency  = Float32Col()    # float  (single-precision)
    power  = Float32Col()    # float  (single-precision)
    simulated = BoolCol() #Boolean

def DB_Logger(queue=None, DB_Name="EARS_DB.h5"):
    print("Starting Logger")
    if not queue:
        Warning('No queue provided! Closing db manager.')
        return
    
    if not os.path.isfile(DB_Name):
        #Check db file exists
        h5file = open_file(DB_Name, mode="w", title="EARS Measurements Record")
        group = h5file.create_group("/", 'measurement', 'RF Power information')
        table = h5file.create_table(group, 'readout', RFMeasurements, "Measurements Record")
    with open_file(DB_Name, mode="a", title="EARS Measurements Record") as h5file:
        #Check that the table has already been made. If not, make it. 
        if not 'measurement' in str(h5file.list_nodes('/')):
            group = h5file.create_group("/", 'measurement', 'RF Power information')
            table = h5file.create_table(group, 'readout', RFMeasurements, "Measurements Record")
    while True:
        #Just keep going until the task is killed. If nothing is put in the queue, or if the queue is closed, 
        #this task should close the db file and close out. 
        if not queue.empty():
            try:
                pkt = queue.get()
            except ValueError as e:
                #Pipe was closed and we didn't catch it for some reason. 
                #That's annoying, but probably fine. Just give a grumpy warning and close the logger
                Warning('LogQueue was closed before stopping the logger!')
                return
            if pkt == 'Quit':
                #This is a daemon function, so just killing it is fine. 
                #However, gracefully shutting down is quite nice too. 
                print('Logger got Quit')
                #Flush the queue before ending
                while not queue.empty():
                    flush = queue.get()
                queue.close()
                return
            #Got data, get handle to DB
            with open_file(DB_Name, mode="a", title="EARS Measurements Record") as h5file:
                #table handles are retrieved from the file handle with the format file_handle.mount_point.group_handle.table_handle
                table = h5file.root.measurement.readout
                measurement = table.row
                '''
                The expected format of these measurements is a tuple (time, data, simFlag) where time is a 20 char string
                and data is a list of tuples containing (frequency, power). simFlag is a bool indicating whether 
                this data was simulated.
                '''
                for reading in pkt[1]:
                    measurement['time'] = pkt[0] #Should be a 20 char string
                    measurement['frequency'] = reading[0]
                    measurement['power'] = reading[1]
                    measurement['simulated'] = pkt[2]
                    measurement.append()
                table.flush()
        else:
            #If there isn't anything in the queue, we can wait a pretty long time. 
            #This doesn't need to be very fast. 1Hz is plenty.
            sleep(1)


def DB_Retrieval(DB_Name="EARS_DB.h5", cols=['frequency', 'power'], query_string=None):
    '''
    This is intended to provide an interface for our EARS database so that direct 
    pytables calls are not necessary in other modules. 
    This is likely to be an IO bound task, so good for concurrency/threading
    '''
    if not query_string:
        Warning('No query provided to DB_Retrieval')
        return 
    #If the database file doesn't exist, this will fail
    if not os.path.isfile(DB_Name):
        Warning("Provided DB file doesn't exist.")
        return "Error"
    
    with open_file(DB_Name, mode="r", title="EARS Measurements Record") as h5file:
        #table handles are retrieved from the file handle with the format file_handle.mount_point.group_handle.table_handle
        table = h5file.root.measurement.readout
        #names = [ x['name'] for x in table.where("""(power > 3) & (20 <= frequency) & (frequency < 50) & (simulation == False)""") ]
        try:
            #unfortunately, to make this sufficiently flexible, return a dictionary of tuples
            result = {}
            for key in cols:
                result[key] = ( x[key] for x in table.where(query_string) )
            return result
        except:
            Warning('Invalid query submitted')
            print('Did you make sure to format any string comparisons as bytes?')
            return 'Error'

def RetrieveBaselineData(queue=None, DB_Name="EARS_DB.h5", freqMin = 30_000_000, freqMax = 88_000_000):
    '''
    Special case of retrieval function which returns the baseline data between two freqs as list of tuples.
    '''
    if not checkForBaselineData(DB_Name):
        #No baseline data available. Return none
        return None
    with open_file(DB_Name, mode="r", title="EARS Measurements Record") as h5file:
        #table handles are retrieved from the file handle with the format file_handle.mount_point.group_handle.table_handle
        table = h5file.root.baseline.readout 
        return  [(x['frequency'], x['power']) for x in table.where('(frequency>={}) & (frequency<={})'.format(freqMin, freqMax))]

def archiveDataBase(zipname=None, clearDB = False):
    ''' TODO
    Utility for archiving the database. This will zip the current database up and put it in the archives
    folder, then optionally delete just the measurements table of the current database so that memory is
    cleared up.

    from zipfile import ZipFile
    with ZipFile('spam.zip', 'w') as myzip:
        myzip.write('eggs.txt')
    '''
    pass

def checkForBaselineData(DB_Name="EARS_DB.h5"):
    '''Check for baseline group in database file'''
    if not os.path.isfile(DB_Name):
        #The file doesn't exist... so no baseline data
        return False
    with open_file(DB_Name, mode="a", title="EARS Measurements Record") as h5file:
        return 'baseline' in str(h5file.list_nodes('/'))

def StoreBaselineData(pkt = None, queue=None, DB_Name="EARS_DB.h5"):
    '''
    Stores baseline data in the same database as the archive for retrieval later. 
    ~If there is no DB file, make a new file. 
    ~If there is a DB file, overwrite the Baseline table.
    ~Just store whatever we get in there. 

    WARNING: HDF5 is not thread safe! If this get's called while logger is running it could corrupt database!

    I COULD make this a totally seperate file, or it could just be a different table in the same file/group. 
    That's what I'm thinking right now. 
    '''
    print("Storing baseline data")
    if not queue and not pkt:
        Warning('No data or queue provided! Closing db.')
        return
    if queue:
        pkt = queue.get(timeout = 30) #Wait up to 30 seconds for something from the queue. Otherwise, error out. 
    #Check that our file exists. We can wipe out the old baseline node.
    if not os.path.isfile(DB_Name):
        h5file = open_file(DB_Name, mode="w", title="EARS Measurements Record")
    else:
        h5file = open_file(DB_Name, mode="a", title="EARS Measurements Record")
    #We need to delete the old baseline data if it's there. just delete the group, start clean
    if 'baseline' in str(h5file.list_nodes('/')):
         h5file.remove_node('/baseline', recursive=True)
    group = h5file.create_group("/", 'baseline', 'RF Power baseline information')
    table = h5file.create_table(group, 'readout', RFMeasurements, "Baseline Record")
    measurement = table.row
        #table handles are retrieved from the file handle with the format file_handle.mount_point.group_handle.table_handle
    '''
    The expected format of these measurements is a tuple (time, data, simFlag) where time is a 20 char string
    and data is a list of tuples containing (frequency, power). simFlag is a bool indicating whether 
    this data was simulated.
    '''
    for reading in pkt[1]:
        measurement['time'] = pkt[0] #Should be a 20 char string
        measurement['frequency'] = reading[0]
        measurement['power'] = reading[1]
        measurement['simulated'] = pkt[2]
        measurement.append()
    table.flush()
    h5file.close()