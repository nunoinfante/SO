#!/bin/bash
if [ $# -gt 0 ]; then

    positivos=0
    negativos=0
    zeros=0

    for i in $*
    do
        if [ $i -eq 0 ]; then
            ((zeros++))
        elif [ $i -gt 0 ]; then
            ((positivos++))
        else 
            ((negativos++))
        fi
    done

    echo "Positivos: $positivos"
    echo "Negativos: $negativos"
    echo "Zeros: $zeros"

else 
    echo "Erro: falta um argumento"
fi