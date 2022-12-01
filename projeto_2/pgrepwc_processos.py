### Grupo: SO-TI-38
### Aluno 1: Nuno Infante (fc55411)

from multiprocessing import Process, Array, Queue, Lock, Value
import argparse
import unicodedata
import os

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

    for linha in texto:
        palavra = remover_acentos(palavra)
        linha_split = remover_acentos(linha).split()

        #Se para cada palavra em linha_split for igual à palavra que estamos a procurar então somamos 1 ao número ocorrências dessa palavra
        for p in linha_split:
            if p == palavra:
                numero_palavras += 1

        #Se a palavra estiver na lista linha_split então damos append dessa linha
        if palavra in linha_split:
            linhas_com_palavra.append(linha)

    return (linhas_com_palavra, numero_palavras, len(linhas_com_palavra))

def grepwc(args, ficheiros, palavras_encontradas, linhas_encontradas):
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
    for ficheiro in ficheiros:

        texto = open(ficheiro, 'r')

        linhas_com_palavra, numero_palavras, numero_linhas = encontrar_palavras(args.palavra, texto)

        #Devido a ter a opção -e específicada, vamos ter apenas um ficheiro, este dividido pelo número de processos em ficheiros mais pequenos. 
        #Assim somamos os valores do número das ocorrências e do número de linhas encontradas para as variáveis partilhadas
        if args.bytes:
            palavras_encontradas[0 ] += numero_palavras
            linhas_encontradas[0] += numero_linhas

        #Devido a termos mais que um ficheiro, guardamos os valores do número das ocorrências e do número de linhas encontradas no índice correspondente ao ficheiro na lista args.ficheiros
        else:
            indice_ficheiro = args.ficheiros.index(ficheiro)
            palavras_encontradas[indice_ficheiro] = numero_palavras
            linhas_encontradas[indice_ficheiro] = numero_linhas

        for linha in linhas_com_palavra:
            linha = linha.replace('\n', '')
            print(f"\n{linha}")

        print(f"\nNo ficheiro {ficheiro} foram encontradas:")
        
        if args.c:
            print(f"{numero_palavras} ocorrencias da palavra {args.palavra}")

        if args.l: 
            print(f"{numero_linhas} linhas com a palavra {args.palavra}")

    # Caso a opção -e seja específicada, então removemos os ficheiros criados pelo produtor
    if args.bytes:
        for file in ficheiros:
            os.remove(file)         
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
    if args.bytes:
        pass
    else:
        num_ficheiros = len(args.ficheiros)
        num_processos = args.processos
        tarefas =  [ []*num_processos for i in range(num_processos)]

        #Se o número de processos for maior ou igual que o número de ficheiros então o número de processos é o número de ficheiros a pesquisar
        if num_processos >= num_ficheiros:
            args.processos = num_ficheiros
            tarefas = [[ficheiro] for ficheiro in args.ficheiros]

        ###########################################################
        elif num_processos < num_ficheiros:
            dict = {}
            for f in args.ficheiros:
                dict[f] = os.stat(f).st_size / 1000
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

def produtor(files, queue, maxBytes, STOP_TOKEN):
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

def consumidor(queue, lock, i, args, palavras_encontradas, linhas_encontradas, STOP_TOKEN):
    novos_ficheiros = []
    while True:
        lock.acquire()
        item = queue.get()
        i.value += 1
        lock.release()
        if item == STOP_TOKEN:
            queue.put(STOP_TOKEN) #Põe se de volta na queue para informar os outros consumidores
            break
        else:
            lock.acquire()
            with open(f'file_temp_{i.value}.txt', 'w') as input:
                input.writelines(item)
                novos_ficheiros.append(f'file_temp_{i.value}.txt')
            lock.release()

    lock.acquire()
    grepwc(args, novos_ficheiros, palavras_encontradas, linhas_encontradas)
    lock.release()

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

        STOP_TOKEN = 'STOP'

        processos_filho = []
        lock = Lock()
        myVar = Value("i", 0)

        for i in range(args.processos):
            processos_filho.append(Process(target=consumidor, args = (queue, lock, myVar, args, palavras_encontradas, linhas_encontradas, STOP_TOKEN)))
        
        prod = Process(target=produtor, args = (args.ficheiros, queue, args.bytes, STOP_TOKEN))

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
                                        args = (args, tarefas[i], palavras_encontradas, linhas_encontradas)))

        for i in range(args.processos):
            processos_filho[i].start()
        for i in range(args.processos):
            processos_filho[i].join()

    


def main():
    print('Programa: pgrepwc_processos.py')

    args = obter_argumentos()

    #Criamos dois arrays que vão estar na memória partilhada para cada ficheiro a ser pesquisado,
    #um para as palavras encontradas e outro para as linahs encontradas 
    palavras_encontradas = Array('i', len(args.ficheiros))
    linhas_encontradas = Array('i', len(args.ficheiros))

    #Se o número de processos for igual a 1 então o processo pai faz a pesquisa
    if args.processos == 1:
        grepwc(args, args.ficheiros, palavras_encontradas, linhas_encontradas)
    else:
        pgrepwc(args, palavras_encontradas, linhas_encontradas)

    #Se o número de ficheiros for maior que 1 então calculamos as palavras e as linhas totais encontradas.
    #Também se aplica caso a opção -e seja específicada
    if len(args.ficheiros) > 1 or args.bytes and args.processos > 1:

        palavras_total = 0
        linhas_total = 0

        for i in range(len(args.ficheiros)):
            palavras_total += palavras_encontradas[i]
            linhas_total += linhas_encontradas[i]
    
        print("\nNo total, em todos os ficheiros foram encontradas:")

        if args.c:
            print(f"{palavras_total} ocorrencias da palavra {args.palavra}")
        if args.l: 
            print(f"{linhas_total} linhas com a palavra {args.palavra}")  

if __name__ == "__main__":
    main()