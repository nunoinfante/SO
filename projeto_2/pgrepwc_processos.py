### Grupo: SO-TI-38
### Aluno 1: Nuno Infante (fc55411)

from multiprocessing import Process, Array, Queue, Lock, Value
import argparse
import unicodedata
import os
from signal import signal, SIGINT
from time import time

stop = False

def obter_argumentos():
    """
    Obtém e processa os argumentos dados pelo stdin utilizando a biblioteca argparse
    Raises:
        Exception: Se o número de processos específicado for menor ou igual a 0
    Returns:
        Um objeto da classe ArgumentParser com os argumentos dados pelo utilizador
    """

    #Criação do objeto parser para definir os argumentos dados pelo utilizador
    parser = argparse.ArgumentParser()

    #Argumentos opcionais com valores default False
    #Caso sejam específicados o valor passa a True
    parser.add_argument("-c", action="store_true")
    parser.add_argument("-l", action="store_true")
    parser.add_argument("-p", "--processos", default=1, type=int, required=False)
    parser.add_argument("-e", "--bytes", type=int)
    
    #Argumentos posicionais
    #No argumento 'palavra' é guardada uma string e no argumento 'ficheiros' é guardada uma ou várias strings numa lista
    parser.add_argument("palavra")
    parser.add_argument("ficheiros", nargs="*")

    #Guardar os valores dos argumentos dados no objeto args
    args = parser.parse_args()

    #Caso o número de processos específicado seja menor ou igual a 0, levanta-se uma exceção
    if args.processos <= 0:
        raise Exception('Invalid number of processes')

    #Se não forem dados ficheiros, lê-mos ficheiros pelo stdin
    while len(args.ficheiros) == 0:
        ficheiros_input = input("Digite os ficheiros, separados por um espaço onde pretende efetuar a procura:")
        if ficheiros_input != "":
            args.ficheiros = ficheiros_input.split()

    return args

def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode("utf-8").lower()

def encontrar_palavras(palavra, texto):
    """
    Procura num ficheiro a palavra
    Args:
        palavra: string, onde é a palavra que vamos pesquisar
        ficheiro: string, ficheiro onde vamos pesquisar
    Returns:
        Um tuplo com as linhas onde foram encontradas palavras, o número de ocorrências da palavra
        e o número de linhas encontradas
    """

    linhas_com_palavra = []
    numero_palavras = 0

    for s in texto:
        s = remover_acentos(s)
        if remover_acentos(palavra) in s:
            linhas_com_palavra.append(s)
            numero_palavras += s.count(remover_acentos(palavra))

    return (linhas_com_palavra, numero_palavras, len(linhas_com_palavra))

def grepwc(args, palavras_encontradas, linhas_encontradas, ficheiros=[], texto=''):
    """
    Imprime as linhas encontradas de cada ficheiro, bem como o número de ocorrências da palavra e o número de linhas encontradas
    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
        ficheiros: lista de strings, com o nome dos ficheiros onde vamos procurar
        palavras_encontradas: ista com o número de ocorrências para cada ficheiro
                              Este argumento está alocado na memória partilhada
        linhas_encontradas: lista com o número de linhas encontradas para cada ficheiro
                            Este argumento está alocado na memória partilhada
    """
    if args.bytes:
        linhas_com_palavra, numero_palavras, numero_linhas = encontrar_palavras(args.palavra, texto)

        palavras_encontradas.value += numero_palavras
        linhas_encontradas.value += numero_linhas

    else:
        for f in ficheiros:
            print(f)
            texto = open(f, 'r').readlines()

            linhas_com_palavra, numero_palavras, numero_linhas = encontrar_palavras(args.palavra, texto)
            palavras_encontradas.value += numero_palavras
            linhas_encontradas.value += numero_linhas

            if stop:
                break

    # for linha in linhas_com_palavra:
    #     linha = linha.replace('\n', '')
    #     print(f"\n{linha}")

             
###########################################################
def get_size_process(tarefas, dict):
    res = []
    for p in tarefas:
        counter = 0
        if len(p) == 0:
            res.append(0)
        else:
            for f in p:
                counter += dict.get(f)
            res.append(counter)
    return res.index(min(res))

def dividir_tarefas(args):
    """
    Distribui os ficheiros a serem procurados pelo número de processos.
    Os ficheiros são distribuídos uniformemente por cada processo. Por exemplo, dados 3 ficheiros e 2 processos, 
    os ficheiros 1 e 2 vão para o primeiro processo e o ficheiro 3 vai para o segundo processo    
    
    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
    Returns: 
        lista com várias listas contendo strings dos nomes dos ficheiros a serem procurados, para cada processo
    """

    ###############################################
    num_ficheiros = len(args.ficheiros)
    num_processos = args.processos
    tarefas =  [[]*num_processos for i in range(num_processos)]

    #Se o número de processos for maior ou igual que o número de ficheiros então o número de processos é o número de ficheiros a pesquisar
    if num_processos >= num_ficheiros:
        args.processos = num_ficheiros
        tarefas = [[ficheiro] for ficheiro in args.ficheiros]

    ###########################################################
    elif num_processos < num_ficheiros:
        dict = {}
        for f in args.ficheiros:
            dict[f] = os.stat(f).st_size
        dict = {k: v for k, v in sorted(dict.items(), key=lambda item: item[1])}
        dict2 = dict.copy()
        
        while len(dict) != 0:
            index_min = get_size_process(tarefas, dict2)
            tarefas[index_min].append(list(dict.keys())[-1])
            dict.popitem()

    return tarefas

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

# FALTA FAZER COM QUE A QUEUE NAO TENHA MAIS QUE 1MB
def produtor(files, queue, maxBytes, STOP_TOKEN, queueSize):

    break_out_flag = False
    i = 0
    list = []
    for f in files:
        texto = readFile(f)
        for s in texto:
            list.append(s)
            i += 1
            if numberBytesStringList(list) > maxBytes:
                while queueSize.value > 1000000:
                    # print('BBBB')
                    pass
                queueSize.value += numberBytesStringList(list[:-1])
                print(queueSize.value)
                queue.put((list[:-1]))
                list = list[-1:]
            if stop:
                break_out_flag = True
                break
        if break_out_flag:
            break
        if i == numberLinesFiles(files):
                queue.put((list))
                queueSize.value += numberBytesStringList(list)
    print('AWIDAWKHDNKJAWHDAW')
    queue.put(STOP_TOKEN)
    

def consumidor(queue, lock, args, palavras_encontradas, linhas_encontradas, STOP_TOKEN, queueSize):
    while True:
        item = queue.get()
        lock.acquire()
        queueSize.value -= numberBytesStringList(item)
        print(f'{queueSize.value}\n')
        lock.release()
        if item == STOP_TOKEN:
            queue.put(STOP_TOKEN) #Põe se de volta na queue para informar os outros consumidores
            break
        else:
            lock.acquire()
            grepwc(args, palavras_encontradas, linhas_encontradas, texto=item)
            lock.release()
    

def interval():
    pass

def sigint(sig, null):
    global stop
    stop = True

def pgrepwc(args, palavras_encontradas, linhas_encontradas):
    """
    Executa a função grepwc de forma paralela criando o número de processos filho indicado nos argumentos dados pelo utilizador
    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
        palavras_encontradas: caso a opção -e esteja específicada então palavras_encontradas vai ser um int,
                              caso contrário vai ser uma lista com o número de ocorrências para cada ficheiro
                              Este argumento está alocado na memória partilhada
        linhas_encontradas: caso a opção -e esteja específicada então linhas_encontradas vai ser um int,
                            caso contrário vai ser uma lista com o número de linhas encontradas para cada ficheiro
                            Este argumento está alocado na memória partilhada
    """

    processos_filho = []

    if args.bytes:
        queue = Queue()

        queueSize = Value('i', 0)

        STOP_TOKEN = 'STOP'

        processos_filho = []
        lock = Lock()

        for i in range(args.processos):
            processos_filho.append(Process(target=consumidor, args = (queue, lock, args, palavras_encontradas, linhas_encontradas, STOP_TOKEN, queueSize)))
        
        prod = Process(target=produtor, args = (args.ficheiros, queue, args.bytes, STOP_TOKEN, queueSize))

        prod.start()
        
        for cons in processos_filho:
            cons.start()

        prod.join()
        for cons in processos_filho:
            cons.join()

    else:
        tarefas = dividir_tarefas(args)
        for i in range(args.processos):
            processos_filho.append(Process(target=grepwc,
                                        args = (args, palavras_encontradas, linhas_encontradas, tarefas[i])))

        for i in range(args.processos):
            processos_filho[i].start()
        for i in range(args.processos):
            processos_filho[i].join()

def main():
    inicio = time()
    print('Programa: pgrepwc_processos.py')

    args = obter_argumentos()

    signal(SIGINT, sigint)

    #Criamos dois arrays que vão estar na memória partilhada para cada ficheiro a ser pesquisado,
    #um para as palavras encontradas e outro para as linahs encontradas 
    palavras_encontradas = Value('i', 0)
    linhas_encontradas = Value('i', 0)

    #Se o número de processos for igual a 1 então o processo pai faz a pesquisa
    if args.processos == 1:
        grepwc(args, palavras_encontradas, linhas_encontradas, ficheiros = args.ficheiros)
    else:   
        pgrepwc(args, palavras_encontradas, linhas_encontradas)


    print("\nNo total, em todos os ficheiros foram encontradas:")

    if args.c:
        print(f"{palavras_encontradas.value} ocorrencias da palavra {args.palavra}")
    if args.l: 
        print(f"{linhas_encontradas.value} linhas com a palavra {args.palavra}")  

    print(f'Tempo de execucao: {time()-inicio}')
if __name__ == "__main__":
    main()