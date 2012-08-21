#-*-coding:utf-8-*-
import json
import os
from testadorAuxiliar import TestadorAuxiliarAspirador

if __name__ == '__main__':
	try:
		configuracao = json.loads(open('configuracao.js').read())
	except:
		print "Erro ao abrir arquivo de configuração: 'configuracao.js'"
		exit(1)	
	testador = TestadorAuxiliarAspirador(_)
	testador.configuracao = configuracao
	testador.inicializarSimulacao()
	
