#!/bin/bash
if [ $# -gt 0 ]; then 
    if [ $1 -lt 0 ]; then 
        echo "$1 é um numero inteiro negativo"
    elif [ $1 -eq 0 ]; then 
        echo "$1 é   o numero zero"
    else echo "$1 é um numero inteiro positivo"
    fi
else echo "Erro: falta um argumento"
fi