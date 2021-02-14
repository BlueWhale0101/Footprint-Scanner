import io

with io.FileIO('Data/test_data.csv', mode='r') as stream:
    currentData = stream.read()
    while currentData is not b'':
        print(currentData)
        currentData = stream.read()
