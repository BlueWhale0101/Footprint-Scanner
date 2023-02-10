'''
Contains pytables tutorial from https://www.pytables.org/usersguide/tutorials.html
'''

from tables import *
import time

class Particle(IsDescription):
    name      = StringCol(16)   # 16-character String
    idnumber  = Int64Col()      # Signed 64-bit integer
    ADCcount  = UInt16Col()     # Unsigned short integer
    TDCcount  = UInt8Col()      # unsigned byte
    grid_i    = Int32Col()      # 32-bit integer
    grid_j    = Int32Col()      # 32-bit integer
    pressure  = Float32Col()    # float  (single-precision)
    energy    = Float64Col()    # double (double-precision)


'''
open_file will make the file if it doesnt exist. 
The create_group commands and create_table commands are only required the first time.
'''

h5file = open_file("tutorial1.h5", mode="w", title="Test file")
group = h5file.create_group("/", 'detector', 'Detector information')
table = h5file.create_table(group, 'readout', Particle, "Readout example")

#The table.row class always points to the next row of the table. table could also have been table = h5file.root.detector.readout
particle = table.row
for i in range(100000):
    particle['name']  = f'Particle: {i:6d}'
    particle['TDCcount'] = i % 256
    particle['ADCcount'] = (i * 256) % (1 << 16)
    particle['grid_i'] = i
    particle['grid_j'] = 10 - i
    particle['pressure'] = float(i*i)
    particle['energy'] = float(particle['pressure'] ** 4)
    particle['idnumber'] = i * (2 ** 34)
    # Insert a new particle record
    particle.append()
    if i % 50 == 0:
        table.flush()
        print('~~FLUSH~~ ', i)

#Now switch to selecting data from our table
table = h5file.root.detector.readout
#This is a very natural python method, a list comprehension iterating over every row.
t1 = time.perf_counter()
pressure = [x['pressure'] for x in table.iterrows() if x['TDCcount'] > 3 and 20 <= x['pressure'] < 50]
print(pressure)
t2 = time.perf_counter()
#This is a more powerful compiled method, which gets the names column applying the same filter
names = [ x['name'] for x in table.where("""(TDCcount > 3) & (20 <= pressure) & (pressure < 50)""") ]
print(names)
t3 = time.perf_counter()

print('Time for first query was ', str(t2-t1))
print('Time for second query was ', str(t3-t2))
input('Press Enter to continue')