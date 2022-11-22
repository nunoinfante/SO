### Grupo: SO-TI-38
# Aluno 1: Nuno Infante (fc55411)

### Exemplos de comandos para executar o pgrepwc:
1) ./pgrepwc -c -l -p 2 gerenciamento file4.txt
2) ./pgrepwc -c -p 3 -e -t arthur file3.txt
3) ./pgrepwc -l -p 3 -e holmes file2.txt file3.txt

### Abordagem para a divisão dos ficheiros:
- Os ficheiros são repartidos de forma igual pelos processos/threads.
- Caso hajam mais processos que ficheiros então o número de processos vai ser o número de ficheiros
- Caso contrário, os primeiros processos/threads ficam com os primeiros ficheiros de forma assimétrica

- Exemplo:
    5 ficheiros - {f1, f2, f3, f4, f5}
    3 processos - {p1, p2, p3}

    Divisão:
        p1 - {f1, f2}
        p2 - {f3, f4}
        p3 - {f5}


- Caso o argumento -e seja específicado então o ficheiro é dividido pelo número de processos

- Exemplo:
    1 ficheiro - {f1} (500 linhas)
    3 processos - {p1, p2, p3}

    Divisão:
        p1 - f1_1 (167 linhas)
        p2 - f1_2 (167 linhas)
        p3 - f1_3 (166 linhas)

### Outras informações pertinentes:
Dado o email enviado no dia 27 de Outubro foi-me pedido explicar a situação com o meu grupo. No dia 24 de Outubro, 
mandei uma mensagem ao meu grupo a dizer que já adientei um pouco do trabalho. Devido a ter 4 avaliações entre os dias 28/10 a 4/11, 
decidi continuar a fazer o projeto enquanto estudava para a frequência de SO no dia 28/10, quase acabado (faltando o tratamento de erros, os cometários e o README). 
Enviei um email para os docentes a explicar a situação e se era possível fazer o trabalho individualmente. Apenas no dia 5 de Novembro 
é que obtive resposta de um dos meus colegas a dizer que esteve ocupada e que só ia começar a ver do trabalho nesse dia (5). 
Respondi que já tinha o trabalho feito e que não os iria incluir no projeto.