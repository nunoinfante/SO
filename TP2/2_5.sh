#!/bin/bash
if [ $# -gt 0 ]; then
    
    sum=0

    for i in $*
    do
        ((sum+=$i))
    done

    echo "Soma: $sum"

else 
    echo "Erro: falta um argumento"
fi