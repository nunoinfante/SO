### Grupo: SO-TI-38
### Aluno 1: Nuno Infante (fc55411)

from multiprocessing import Process, Array
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
    parser.add_argument("-e", action="store_true")
    parser.add_argument("-t", action="store_true")
    
    #Argumentos posicionais
    #No argumento 'palavra' é guardada uma string e no argumento 'ficheiros' é guardada uma ou várias strings numa lista
    parser.add_argument("palavra")
    parser.add_argument("ficheiros", nargs="*")

    #Guardar os valores dos argumentos dados no objeto args
    args = parser.parse_args()

    #Caso o número de processos específicado seja menor ou igual a 0, levanta-se uma exceção
    if args.processos <= 0:
        raise Exception('Invalid number of processes')

    #Se a opção -e for específicada e forem dados mais que um ficheiro, ignoramos a opção -e
    if len(args.ficheiros) > 1:
        args.e = False

    #Se não forem dados ficheiros, lê-mos ficheiros pelo stdin
    while len(args.ficheiros) == 0:
        ficheiros_input = input("Digite os ficheiros, separados por um espaço onde pretende efetuar a procura:")
        if ficheiros_input != "":
            args.ficheiros = ficheiros_input.split()

    return args

def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode("utf-8").lower()

def encontrar_palavras(palavra, ficheiro):
    """
    Procura num ficheiro a palavra

    Args:
        palavra: string, onde é a palavra que vamos pesquisar
        ficheiro: string, ficheiro onde vamos pesquisar

    Returns:
        Um tuplo com as linhas onde foram encontradas palavras, o número de ocorrências da palavra
        e o número de linhas encontradas
    """

    f = open(ficheiro, 'r')

    linhas_com_palavra = []
    numero_palavras = 0

    for linha in f:
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

        linhas_com_palavra, numero_palavras, numero_linhas = encontrar_palavras(args.palavra, ficheiro)

        #Devido a ter a opção -e específicada, vamos ter apenas um ficheiro, este dividido pelo número de processos em ficheiros mais pequenos. 
        #Assim somamos os valores do número das ocorrências e do número de linhas encontradas para as variáveis partilhadas
        if args.e:
            palavras_encontradas[0  ] += numero_palavras
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

def dividir_ficheiro(args):
    """
    Caso a opção -e esteja específicada, dividimos o ficheiro principal pelo número de processos específicados.
    Por exemplo, se um ficheiro tiver 29 linhas e se forem específicados 2 processos, o primeiro processo vai ficar com as 15 primeiras linhas 
    enquanto que o outro processo vai ficar com 14 linhas
    
    Args:
        args: objeto da classe ArgumentParser, com os argumentos dados pelo utilizador

    Returns:
        Lista de strings com o nome dos novos ficheiros criados a partir do ficheiro dado pelo utilizador
    """
    ficheiro = args.ficheiros[0]

    #Número de linhas do ficheiro principal
    num_linhas_ficheiro = sum(1 for _ in open(ficheiro))

    #Atribuição do número linhas para cada processo
    linhas_processo = [num_linhas_ficheiro // args.processos for _ in range(args.processos)]
    linhas_extra = num_linhas_ficheiro % args.processos
    for i in range(linhas_extra):
        linhas_processo[i] += 1 

    #Criação dos novos ficheiros
    ficheiro_split = ficheiro.split('.')
    novos_ficheiros = [[f'{ficheiro_split[0]}_{i+1}.{ficheiro_split[1]}'] for i in range(args.processos)]

    f = open(ficheiro, 'r')
    texto = f.readlines()

    #Escrita das linhas do ficheiro principal nos novos ficheiros
    count = 0
    for i, novo_ficheiro in enumerate(novos_ficheiros):
        with open(novo_ficheiro[0], 'w') as out_f:
            for _ in range(linhas_processo[i]):
                out_f.write(texto[count])
                count += 1
            out_f.close()

    return novos_ficheiros
                

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

    #Caso a opção -e seja específicada, então dividimos o ficheiro em ficheiros mais pequenos usando a função dividir_ficheiro.
    if args.e:
        tarefas = []
        tarefas = dividir_ficheiro(args)

    else:
        num_ficheiros = len(args.ficheiros)
        num_processos = args.processos
        tarefas =  [ []*num_processos for i in range(num_processos)]

        #Se o número de processos for maior ou igual que o número de ficheiros então o número de processos é o número de ficheiros a pesquisar
        if num_processos >= num_ficheiros:
            args.processos = num_ficheiros
            tarefas = [[ficheiro] for ficheiro in args.ficheiros]

        #Se o número de processso for menor que o número de ficheiros então distribuímos os ficheiros aos processos uniformemente
        elif num_processos < num_ficheiros:
            tarefas_processo = [num_ficheiros // num_processos for _ in range(num_processos)]
            tarefas_extra = num_ficheiros % num_processos
            for i in range(tarefas_extra):
                tarefas_processo[i] += 1 

            count = 0
            for i in range(num_processos):
                for _ in range(tarefas_processo[i]):
                    tarefas[i].append(args.ficheiros[count])
                    count += 1
                    

    return tarefas

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

    tarefas = dividir_tarefas(args)
    processos_filho = []

    for i in range(args.processos):
        processos_filho.append(Process(target=grepwc,
                                       args = (args, tarefas[i], palavras_encontradas, linhas_encontradas)))

    for i in range(args.processos):
        processos_filho[i].start()
    for i in range(args.processos):
        processos_filho[i].join()

    #Caso a opção -e seja específicada, então removemos os ficheiros criados pela função dividir_ficheiro
    if args.e:
        for file in tarefas:
            os.remove(file[0])


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
    if len(args.ficheiros) > 1 or args.e and args.processos > 1:

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