### Grupo: SO-TI-38
### Aluno 1: Nuno Infante (fc55411)

import unicodedata
import argparse
import os
from signal import signal, SIGINT, setitimer, SIGALRM, ITIMER_REAL
from multiprocessing import Process, Queue, Lock, Value
from re import findall, compile
from functools import partial
from time import time

from colorama import Fore, init, ansi
init() # Inicialização colorama

inicio = time()
end = Value('i', 0)
STOP_TOKEN = 'STOP'
lock = Lock()

palavras_encontradas = Value('i', 0) #Variável em memória partilhada com o número de ocorrências isoladas
linhas_encontradas = Value('i', 0) #Variável em memória partilhada com o número de linhas em que houve ocorrências
files_done = Value('i', 0) #Variável em memória partilhada com o número de ficheiros completamente processados


def seconds_to_micro(sec):
    """
    Obtém segundos e retorna em microsegundos
    Args:
        sec: número em segundos
    Returns:
        Número em microsegundos
    """
    return int(sec*1000000)


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

    #Caso seja usada a opção args.bytes e seja definida 1 processo (omissão)
    if args.processos <= 1 and args.bytes:
        raise Exception('Invalid number of processes')

    #Caso o número de processos específicado seja menor ou igual a 0, levanta-se uma exceção
    if args.processos <= 0:
        raise Exception('Invalid number of processes')

    #Se não forem dados ficheiros, lê-se ficheiros pelo stdin
    while len(args.ficheiros) == 0:
        ficheiros_input = input("Digite os ficheiros, separados por um espaço onde pretende efetuar a procura:")
        if ficheiros_input != "":
            args.ficheiros = ficheiros_input.split()

    return args


def remover_acentos(texto):
    """
    Remove acentos a uma string
    Args:
        texto: string com o texto a ser pesquisado
    Returns:
        string do texto sem acentos
    """
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode("utf-8")


def pesquisa_palavras(palavra, texto):
    """
    Procura num ficheiro a palavra
    Args:
        palavra: string, onde é a palavra que vamos pesquisar
        ficheiro: string, ficheiro onde vamos pesquisar
    Returns:
        Um tuplo com o número de ocorrências isoladas e o número de linhas em que 'palavra' ocorreu
    """

    linhas = []
    palavras = []

    #Compila a palavra numa expressão regular
    regex = compile(f'\\b{remover_acentos(palavra)}\\b')

    for linha in texto:
        #Se o SIGINT (CTRL+C) tiver sido pressionado anteriormente, é feita a pesquisa até ao ficheiro a que está a ser processado
        if end.value == 1:
            break

        linha = remover_acentos(linha)
        #Pesquisa em linha usando a expressão regular
        palavras_encontradas.value += len(regex.findall(linha))
        #Se a palavra estiver em linha damos append
        if palavra in linha:
            linhas_encontradas.value += 1

        
def grepwc(args, ficheiros=[], texto=''):
    """
    Faz a pesquisa, caso -e seja utilizado, com um texto recebido pela queue. Caso contrário itera sobre os ficheiros dados e faz a pesquisa
    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
        ficheiros: lista de strings, com o nome dos ficheiros onde vamos procurar. Se -e não seja utilizado
        texto: lista de strings, com o contéudo do(s) ficheiro(s) a pesquisar. Se -e for utilizado
    """

    #Se -e for utilizado
    if args.bytes:

        lock.acquire()
        pesquisa_palavras(args.palavra, texto)
        lock.release()

    else:
        for f in ficheiros:

            print(f'{Fore.LIGHTBLACK_EX} {f} em processamento {Fore.RESET}\n')

            texto = read_file(f)

            lock.acquire()
            pesquisa_palavras(args.palavra, texto)
            lock.release()

            #Após o ficheiro ser processado completamente, somamos à variável em memória partilhada para ser usada na impressão de resultados
            files_done.value += 1

            #Se o SIGINT (CTRL+C) tiver sido pressionado anteriormente, é feita a pesquisa até ao ficheiro a que está a ser processado
            if end.value == 1:
                break
             

def min_bytes_processo(tarefas, dict):
    """
    Obter o index do processo com menor tamanho total de ficheiros

    Args:
        tarefas: lista com listas com o nome de ficheiros associado a cada processo
        dict: dicionário com pares ficheiro:tamanho de todos os ficheiros dados
    Returns:
        Index do processo
    """
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
    Distribui os ficheiros a serem procurados pelo número de processos, tendo em conta o seu tamanho.
    
    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
    Returns: 
        lista com listas com o nome de ficheiros associado a cada processo
    """

    num_ficheiros = len(args.ficheiros)
    num_processos = args.processos
    tarefas = [[]*num_processos for i in range(num_processos)]

    #Se o número de processos for maior ou igual que o número de ficheiros então o número de processos é o número de ficheiros a pesquisar
    if num_processos >= num_ficheiros:
        args.processos = num_ficheiros
        tarefas = [[ficheiro] for ficheiro in args.ficheiros]

    #Se o número de processos for menor que o número de ficheiros
    elif num_processos < num_ficheiros:
        dict = {}
        for f in args.ficheiros:
            dict[f] = os.stat(f).st_size #Associar cada ficheiro ao seu tamanho em bytes
        dict = {k: v for k, v in sorted(dict.items(), key=lambda item: item[1])} #Ordenar o dicionário do menor para o maior
        dict2 = dict.copy() #Copia do dicionário
        
        while len(dict) != 0:
            index_min = min_bytes_processo(tarefas, dict2) #Index do processo com menor tamanho total de ficheiros
            tarefas[index_min].append(list(dict.keys())[-1]) #Acrescentar ao index obtido o nome do ficheiro com menor tamanho
            dict.popitem() # Retirar o par key:value com maior tamanho

    return tarefas


def read_file(file):
    """
    Lê um ficheiro

    Args:
        file: ficheiro a ser lido
    Returns:
        lista com strings com cada linha do ficheiro
    """
    with open(file, 'r') as input:
        return input.readlines()


def calcula_numero_linhas(files):
    """
    Cálcula o número de linhas para todos os ficheiros dados

    Args:
        files: lista com ficheiros dados pelo utilizador 
    Returns:
        Número de linhas dos ficheiros
    """
    counter = 0
    for f in files:
        counter += len(read_file(f))
    return counter


def size_string_bytes(lista):
    """
    Cálcula o número de bytes totais de uma lista de strings

    Args:
        lista: lista de strings
    Returns:
        Número de bytes 
    """
    counter = 0
    for string in lista:
        counter += len(string.encode('utf-8'))
    return counter


def produtor(args, queue, queue_size):
    """
    Produz blocos de trabalho para os consumidores os processarem

    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
        queue: fila onde vão ser empurrados os blocos de trabalhos
        queue_size: tamanho da queue em bytes
    """
    list = []

    for f in args.ficheiros:

        print(f'{Fore.LIGHTBLACK_EX} {f} em processamento {Fore.RESET}\n')

        texto = read_file(f)

        for s in texto:
            list.append(s)
            #Se a lista de strings tiver mais que o número máximo de bytes
            if size_string_bytes(list) > args.bytes:
                #Enquanto a queue tiver mais que 1MB em tamanho
                while queue_size.value > 1000000:
                    pass

                queue_size.value += size_string_bytes(list[:-1])
                queue.put(list[:-1]) #Inserir na queue a lista exceto a última linha (que originou o bloco de trabalho a ter mais que o número máximo de bytes)
                list = list[-1:] #Inicializa a lista apenas com a linha

            #Se o SIGINT (CTRL+C) tiver sido pressionado anteriormente, é feita a pesquisa até ao último bloco
            if end.value == 1:
                queue.put(list)
                break
        if end.value == 1:
            break

        queue.put(list)
        queue_size.value += size_string_bytes(list)

        files_done.value += 1
    
    #Quando acaba ou SIGINT é ativado, empurra um aviso para os consumidores
    queue.put(STOP_TOKEN)
    

def consumidor(args, queue, queue_size):
    """
    Faz a pesquisa dos blocos de trabalho produzidos pelo produtor

    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
        queue: fila onde vão ser empurrados os blocos de trabalhos
        lock: 
        queue_size: tamanho da queue em bytes
    """
    while True:
        item = queue.get()
        lock.acquire()
        queue_size.value -= size_string_bytes(item)
        lock.release()
        if item == STOP_TOKEN:
            queue.put(STOP_TOKEN) #Põe se de volta na queue para informar os restantes consumidores
            break
        else:
            grepwc(args, texto=item)


def interval(args, sig, null):
    """
    Impressão dos resultados de 3 em 3 segundos

    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
        sig: obrigatório pelo sinal
        null: obrigatório pelo sinal
    """
    if args.c:
        print(f'{Fore.GREEN}{palavras_encontradas.value}{Fore.RESET} ocorrências da palavra {Fore.CYAN}{args.palavra}{Fore.RESET}')
    if args.l:
        print(f'{Fore.GREEN}{linhas_encontradas.value}{Fore.RESET} linhas em que ocorre a palavra {Fore.CYAN}{args.palavra}{Fore.RESET}')

    print(f'{Fore.LIGHTRED_EX}{files_done.value}{Fore.RESET} ficheiros completamente processados')
    print(f'{Fore.LIGHTRED_EX}{len(args.ficheiros) - files_done.value}{Fore.RESET} ficheiros ainda em processamento')
    print(f'{Fore.LIGHTYELLOW_EX}{seconds_to_micro(time() - inicio)}{Fore.RESET} μs desde o início da execução\n')


def sigint(sig, null):
    """
    Altera o valor de end, para parar o processamento do resto dos ficheiros

    Args:
        sig: obrigatório pelo sinal
        null: obrigatório pelo sinal
    """
    end.value = 1


def pgrepwc(args):
    """
    Executa a função grepwc de forma paralela criando o número de processos filho indicado nos argumentos dados pelo utilizador
    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador
    """

    processos_filho = []

    #Se a opção -e for utilizada
    if args.bytes:
        queue = Queue()
        queue_size = Value('i', 0) #Valor para verificar que o tamanho da queue

        for i in range(args.processos):
            processos_filho.append(Process(target=consumidor, args = (args, queue, queue_size)))
        
        for cons in processos_filho:
            cons.start()
        
        produtor(args, queue, queue_size)

    else:
        tarefas = dividir_tarefas(args)

        for i in range(args.processos):
            processos_filho.append(Process(target=grepwc, args = (args, tarefas[i])))

        for i in range(args.processos):
            processos_filho[i].start()

        for i in range(args.processos):
            processos_filho[i].join()


def main():
    print('Programa: pgrepwc_processos.py\n')

    args = obter_argumentos()
    
    #Alarme que permite fazer a impressão dos resultados de 3 em 3 segundos
    signal(SIGALRM, partial(interval, args))
    setitimer(ITIMER_REAL, 3, 3)

    #Quando o SIGINT (CTRL+C) é pressionado
    signal(SIGINT, sigint)

    #Se o número de processos for igual a 1 então o processo pai faz a pesquisa
    if args.processos == 1:
        grepwc(args, ficheiros = args.ficheiros)
    else:   
        pgrepwc(args)

    #No fim da execução, imprime-se o resultado final da pesquisa
    print(f'{Fore.LIGHTMAGENTA_EX}Resultado:{Fore.RESET}')
    if args.c:
        print(f' {Fore.GREEN}{palavras_encontradas.value}{Fore.RESET} ocorrências da palavra {Fore.CYAN}{args.palavra}{Fore.RESET}')
    if args.l:
        print(f' {Fore.GREEN}{linhas_encontradas.value}{Fore.RESET} linhas em que ocorre a palavra {Fore.CYAN}{args.palavra}{Fore.RESET}')

    print(f' {Fore.LIGHTRED_EX}{files_done.value}{Fore.RESET} ficheiros completamente processados')
    print(f' {Fore.LIGHTRED_EX}{len(args.ficheiros) - files_done.value}{Fore.RESET} ficheiros ainda em processamento')
    print(f' {Fore.LIGHTYELLOW_EX}{seconds_to_micro(time() - inicio)}{Fore.RESET} μs desde o início da execução\n')

if __name__ == "__main__":
    main()