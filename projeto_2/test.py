import os

files = ['file4.txt', 'file5.txt', 'file3.txt']
dict = {}

for f in files:
    dict[f] = os.stat(f).st_size / 1000

dict = {k: v for k, v in sorted(dict.items(), key=lambda item: item[1], reverse=True)}

print(dict)