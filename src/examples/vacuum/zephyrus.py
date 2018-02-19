#-*-coding:utf-8-*-
import os
import sys
import json

from roteiro import Roteiro
from testador import TestadorAspirador


if __name__ == '__main__':
    roteiro = Roteiro()
    roteiro.load(sys.argv[1])
    testador = TestadorAspirador()
    testador.inicializarSimulacao(roteiro)
