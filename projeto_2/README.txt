### Grupo: SO-TI-38
# Aluno 1: Nuno Infante (fc55411)

### Exemplos de comandos para executar o pgrepwc:
1) ./pgrepwc -c -l -p 2 gerenciamento file4.txt
2) ./pgrepwc -c -p 3 -e -t Arthur file3.txt
3) ./pgrepwc -l -p 3 -e Holmes file2.txt file3.txt

### Abordagem para a divisão dos ficheiros:
- Os ficheiros são repartidos pelos processos, tendo em conta o tamanho dos ficheiros.
- Caso hajam mais processos que ficheiros então o número de processos vai ser o número de ficheiros

- Exemplo:
    5 ficheiros - {f1(30 kB), f2(10 kB), f3(60 kB), f4(100 kB), f5(40 kB)}
                    f2
    3 processos - {p1, p2, p3}

    Divisão:
        p1 - {f4} 
        p2 - {f3, f2} 
        p3 - {f5, f1} 


- Caso a opção [-e x] seja utilizado, o produtor produz blocos com um número máximo de bytes x, para n consumidores fazerem a pesquisa a partir desses blocos

### Outras informações pertinentes:
Alterei a forma como é feita a pesquisa das palavras, que agora é case-sensitive
Já não são criados ficheiros temporários no -e

Os meus colegas não me disseram nada desde que disse que ia entregar a primeira entrega sozinho, portanto decidi fazer esta estrega também sozinho