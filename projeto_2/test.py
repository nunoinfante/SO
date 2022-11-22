import os

def get_size_process(tarefas, dict):
    res = [[]*len(tarefas) for i in range(len(tarefas))]
    for p in tarefas:
        counter = 0
        if len(p) == 0:
            res.append(0)
        else:
            for f in p:
                counter += dict.get(f)
            res.append(counter)
    return res

files = ['file4.txt', 'file5.txt', 'file3.txt', 'file2.txt']

#1
num_processos = 3
tarefas = [[]*num_processos for i in range(num_processos)]

#2
dict = {}
for f in files:
    dict[f] = os.stat(f).st_size / 1000
dict = {k: v for k, v in sorted(dict.items(), key=lambda item: item[1])}

#3
while len(dict) != 0:
    index_min = tarefas.index(min(tarefas))
    tarefas[index_min].append(list(dict.values())[-1])
    dict.popitem()
    
print(tarefas)