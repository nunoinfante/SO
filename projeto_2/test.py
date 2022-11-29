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
                    f = open(f'file_temp_{j}.txt', 'w')
                    f.writelines(list)
            elif getBytesFromStringList(list) > bytes:
                f = open(f'file_temp_{j}.txt', 'w')
                j += 1
                f.writelines(list[:-1])
                list = list[-1:]

bytes = 8000
files = ['file4.txt']

produtor(files)
print(bytesFromFiles(files))
counter = 0
for i in range(3):
    print(os.stat(f'file_temp_{i+1}.txt').st_size)
    counter += os.stat(f'file_temp_{i+1}.txt').st_size

print(f'Total: {counter}')