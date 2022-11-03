### Grupo: SO-TI-XX
### Aluno 1: Nuno Infante (fc55411)

from multiprocessing import Process, Array
import argparse
import unicodedata
import os

def obter_argumentos():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", action="store_true")
    parser.add_argument("-l", action="store_true")
    parser.add_argument("-p", "--processos", default=1, type=int, required=False)
    parser.add_argument("-e", action="store_true")
    parser.add_argument("-t", action="store_true")
    parser.add_argument("palavra")
    parser.add_argument("ficheiros", nargs="*")

    args = parser.parse_args()

    if len(args.ficheiros) > 1:
        args.e = False

    if args.processos <= 0:
        raise Exception("Invalid number of processes specified")

    while len(args.ficheiros) == 0:
        ficheiros_input = input("Digite os ficheiros, separados por um espaço onde pretende efetuar a procura:")

        if ficheiros_input != "":
            args.ficheiros = ficheiros_input.split()

    return args

def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode("utf-8").lower()

def encontrar_palavras(palavra, ficheiro):
    f = open(ficheiro, 'r')

    linhas_com_palavra = []
    numero_palavras = 0
    numero_linhas = 0

    for linha in f:
        palavra = remover_acentos(palavra)
        linha_split = remover_acentos(linha).split()

        for p in linha_split:
            if p == palavra:
                numero_palavras += 1

        if palavra in linha_split:
            numero_linhas += 1
            linhas_com_palavra.append(linha)

    return (linhas_com_palavra, numero_palavras, numero_linhas)

def grepwc(args, ficheiros, palavras_encontradas, linhas_encontradas):
    for ficheiro in ficheiros:

        linhas_com_palavra, numero_palavras, numero_linhas = encontrar_palavras(args.palavra, ficheiro)


        if args.e:
            palavras_encontradas[0] += numero_palavras
            linhas_encontradas[0] += numero_linhas
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

def divide_ficheiro(args):
    ficheiro = args.ficheiros[0]

    num_linhas_ficheiro = sum(1 for _ in open(ficheiro))

    linhas_processo = [num_linhas_ficheiro // args.processos for _ in range(args.processos)]
    linhas_extra = num_linhas_ficheiro % args.processos
    for i in range(linhas_extra):
        linhas_processo[i] += 1 

    ficheiro_split = ficheiro.split('.')
    novos_ficheiros = [[f'{ficheiro_split[0]}_{i+1}.{ficheiro_split[1]}'] for i in range(args.processos)]

    f = open(ficheiro, 'r')
    texto = f.readlines()

    count = 0
    for i, novo_ficheiro in enumerate(novos_ficheiros):
        with open(novo_ficheiro[0], 'w') as out_f:
            for _ in range(linhas_processo[i]):
                out_f.write(texto[count])
                count += 1
            out_f.close()

    return novos_ficheiros
                

def dividir_tarefas(args):
    
    if args.e:
        tarefas = []
        tarefas = divide_ficheiro(args)

    else:
        num_ficheiros = len(args.ficheiros)
        num_processos = args.processos
        tarefas =  [ []*num_processos for i in range(num_processos)]

        if num_processos >= num_ficheiros:
            args.processos = num_ficheiros
            tarefas = [[ficheiro] for ficheiro in args.ficheiros]

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
    tarefas = dividir_tarefas(args)
    processos_filho = []

    for i in range(args.processos):
        processos_filho.append(Process(target=grepwc,
                                       args = (args, tarefas[i], palavras_encontradas, linhas_encontradas)))

    for i in range(args.processos):
        processos_filho[i].start()
    for i in range(args.processos):
        processos_filho[i].join()

    if args.e:
        for file in tarefas:
            os.remove(file[0])


def main():
    print('Programa: pgrepwc_processos.py')
    
    args = obter_argumentos()
    
    palavras_encontradas = Array('i', len(args.ficheiros))
    linhas_encontradas = Array('i', len(args.ficheiros))

    if args.processos == 1:
        grepwc(args, args.ficheiros, palavras_encontradas, linhas_encontradas)
    else:
        pgrepwc(args, palavras_encontradas, linhas_encontradas)

    palavras_total = 0
    linhas_total = 0

    for i in range(len(args.ficheiros)):
        palavras_total += palavras_encontradas[i]
        linhas_total += linhas_encontradas[i]

    if len(args.ficheiros) > 1 or args.e and args.processos > 1:
        print("\nNo total, em todos os ficheiros foram encontradas:")
        
        if args.c:
            print(f"{palavras_total} ocorrencias da palavra {args.palavra}")
        if args.l: 
            print(f"{linhas_total} linhas com a palavra {args.palavra}")  

if __name__ == "__main__":
    main()