#-*-coding:utf-8-*-
import json
import os
from testador import TestadorAspirador
from roteiro import Roteiro
import sys


if __name__ == '__main__':
	roteiro = Roteiro('batata')
	roteiro.load(sys.argv[1])
	testador = TestadorAspirador()
	testador.inicializarSimulacao(roteiro)
	
