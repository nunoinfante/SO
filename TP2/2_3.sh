#!/bin/bash
if [ $# -gt 0 ]; then
    for i in $*
    do
        if [ $i -lt 0 ]; then 
            echo "$i é um numero inteiro negativo"
        elif [ $i -eq 0 ]; then 
            echo "$i é o numero zero"
        else echo "$i é um numero inteiro positivo"
        fi
    done
else echo "Erro: falta um argumento"
fi