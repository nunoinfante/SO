import os

def bytesFromFiles(files):
    counter = 0
    for f in files:
        counter += os.stat(f).st_size
    return counter

def linesFromFiles(files):
    counter = 0
    for f in files:
        file = open(f, 'r')
        counter += len(file.readlines())
    return counter

def getBytesFromStringList(list):
    counter = 0
    for s in list:
        counter += len(s.encode('utf8'))
    return counter

#produtor
def produtor(files):
    list = []
    i = 0
    j = 1
    for f in files:
        texto = open(f, 'r').readlines()
        for s in texto:
            list.append(s)
            i += 1
            if i == linesFromFiles(files):
                    print('BB')
                    f = open(f'file_temp_{j}.txt', 'w')
                    f.writelines(list)
            elif getBytesFromStringList(list) > bytes:
                print('AA')
                f = open(f'file_temp_{j}.txt', 'w')
                j += 1
                f.writelines(list[:-1])
                list = list[-1:]
bytes = 50
files = ['file5.txt', 'file6.txt']
# print(f'Bytes: {bytesFromFiles(files)}')
# print(f'Lines: {linesFromFiles(files)}')
produtor(files)

# counter = 0
# for i in range(3):
#     print(os.stat(f'file_temp_{i+1}.txt').st_size)
#     counter += os.stat(f'file_temp_{i+1}.txt').st_size

# print(f'Total: {counter}')