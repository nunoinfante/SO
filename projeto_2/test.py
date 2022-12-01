import os
import time
from multiprocessing import Lock, Semaphore, Process, Queue, Value, Array

def readFile(file):
    with open(file, 'r') as input:
        return input.readlines()

def numberLinesFiles(files):
    counter = 0
    for f in files:
        counter += len(readFile(f))
    return counter

def numberBytesStringList(l):
    counter = 0
    for s in l:
        counter += len(s.encode('utf-8'))
    return counter

def produtor(files, queue, maxBytes):
    i = 0
    list = []
    for f in files:
        texto = readFile(f)
        for s in texto:
            list.append(s)
            i += 1
            if numberBytesStringList(list) > maxBytes:
                queue.put(list[:-1])
                list = list[-1:]
        if i == numberLinesFiles(files):
            queue.put(list)
    queue.put(STOP_TOKEN)

def consumidor(queue, i, args, palavras_encontradas, linhas_encontradas):
    while True:
        lock.acquire()
        item = queue.get()
        i.value += 1
        print(i.value)
        lock.release()
        if item == STOP_TOKEN:
            queue.put(STOP_TOKEN) #Põe se de volta na queue para informar os outros consumidores
            break
        else:
            with open(f'file_temp_{i.value}.txt', 'w') as input:
                input.writelines(item)
    grepwc(args, args.ficheiros, palavras_encontradas, linhas_encontradas)

files = ['file5.txt', 'file6.txt']
maxBytes = 50

queue = Queue()

STOP_TOKEN = 'STOP'

processos_filho = []
lock = Lock()
myVar = Value("i", 0)

for i in range(3):
    processos_filho.append(Process(target=consumidor, args = (queue, myVar)))

prod = Process(target=produtor, args = (files, queue, maxBytes))

prod.start()
for cons in processos_filho:
    cons.start()
prod.join()
for cons in processos_filho:
    cons.join()


for i in range(7):
    print(os.stat(f'file_temp_{i+1}.txt').st_size)

