#-*-coding:utf-8-*-
from roteiro import Roteiro
from componentes import Componentes
import sys

def createDefaultScenario(resolution):
	c = Componentes('componentes.js')
	ret = []
	ret.append(c.adicionarVarios(['PAREDEN','PAREDEO'], 0))
	ret.extend([c.adicionar('PAREDEN',0) for i in xrange(resolution-2)])
	ret.append(c.adicionarVarios(['PAREDEN','PAREDEL'],0))
	for i in xrange(resolution-2):
		ret.append(c.adicionar('PAREDEO', 0))
		ret.extend([0] * (resolution-2))
		ret.append(c.adicionar('PAREDEL', 0))
	ret.append(c.adicionarVarios(['PAREDES','PAREDEO'], 0))
	ret.extend([c.adicionar('PAREDES',0) for i in xrange(resolution-2)])
	ret.append(c.adicionarVarios(['PAREDES','PAREDEL'],0))
	return reduce(lambda a,b: a + ' ' + b, map(str, ret))

def makeActivity():
	ret = {}
	ret["mainlog"] = raw_input('log principal (str): ')
	ret["poplog"] = raw_input('log população (str): ')
	ret["popfinal"] = raw_input('log população final (str): ')
	ret["ngeracoes"] = int(raw_input('quantas gerações (int): '))
	ret["npopulacao"] = int(raw_input('tamanho da população (int): '))
	ret["crossover"] = float(raw_input('taxa de crossover (float): '))
	ret["mutacao"] = float(raw_input('taxa de mutação (float): '))
	ret["nsujeiras"] = int(raw_input('quantidade de sujeira (int): '))
	ret["ndepositos"] = int(raw_input('pontos de depósito (int): '))
	ret["ncargas"] = int(raw_input('pontos de recarga (int): '))
	ret["resolucao"] = int(raw_input('resolução (int): '))
	ret["cenarioPadrao"] = createDefaultScenario(ret["resolucao"])
	print 'configuração criada', ret
	return ret

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'uso: criarRoteiro.py nomeRoteiro nActivities'
		sys.exit(1)
	r = Roteiro(sys.argv[1])
	for i in xrange(int(sys.argv[2])):
		r.add(makeActivity())
	r.save()
	print 'roteiro criado: '
	r.listItems()
