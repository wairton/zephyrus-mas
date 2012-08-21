#!/usr/bin/python
#-*-coding:utf-8-*-
import time
import sys

import zmq

from core.ambiente import Ambiente


class AmbienteAspirador(Ambiente):
	def __init__(self, mid, configEnd, configCom):
		super(AmbienteAspirador, self).__init__(mid, configEnd, configCom)

	def run(self):
		print 'Ambiente rodando!!!', time.time()
		contexto = zmq.Context()
		self.socketReceive = contexto.socket(zmq.PULL)
		
		self.socketReceive.bind(self.enderecos.endereco('ambiente'))
		self.socketSend = contexto.socket(zmq.PUSH)
		self.socketSend.connect(self.enderecos.endereco('monitor'))
		self.socketTestador = contexto.socket(zmq.SUB)
		self.socketTestador.connect(self.enderecos.endereco('testador_par'))
		self.socketTestador.setsockopt(zmq.SUBSCRIBE, self.enderecos.get('ambiente')[0])
		self.mainLoop()
		
	def mainLoop(self):
		print "Ambiente está pronto (%s)" % (self.id)
		while True:
			#print 'aqui!!!!!!!!!!!!'	
			msg = self.socketTestador.recv()
			#print 'ambiente:', msg
			msg = msg[4:].split(',')
			if len(msg) > 2:	#comprimento menor indica encerramento.
				self.reconstruir(map(int, msg[0].split()), int(msg[1]))
				self.adicionarAgente(int(msg[2]), int(msg[3]), int(msg[4]))
			else:
				print 'opa!!!!!!!!!!!'
			msg = self.socketReceive.recv()
			if msg == "@@@":
#				self.reiniciarMemoria()
				while True:
					msg = self.socketReceive.recv() #apenas um feddback (ack)
#					print 'ambiente recebeu %s' % (msg)
#					self.draw()
					requisicao = msg.split()
					agid = int(requisicao[0])
					if requisicao[2] == 'perceber':
						acao = self.checar(agid)
					elif requisicao[2] == 'mover':
						#self.draw()
						acao = self.mover(agid, int(requisicao[3]))
					elif requisicao[2] == 'limpar':
						#self.draw()
						acao = self.limpar(agid)
					elif requisicao[2] == 'recarregar':
						#self.draw()
						acao = self.recarregar(agid)
					elif requisicao[2] == 'depositar':
						#self.draw()
						acao = self.depositar(agid)
					elif requisicao[2] == 'parar':
						#self.draw()
						acao = self.parar(agid)
						#print 'em parar', self.posAgentes
						if len(self.posAgentes) == 0:
							msg = "%s %s %s" % (self.id, agid, acao)
							#print 'ambiente enviou %s' % (msg), time.time()
							self.socketSend.send(msg)
							msg = "%s %s %s" % (self.id, -1, "###")
							self.socketSend.send(msg)
							self.reiniciarMemoria()							
							break									
						#TODO: como o ambiente para?
					else:
						raise "ambiente: recebeu mensagem desconhecida"
						#print "ambiente diz ???????????" #TODO: adicionar tratamento de exceção
						pass
					msg = "%s %s %s" % (self.id, agid, acao)
					#print 'ambiente enviou %s' % (msg), time.time()
					self.socketSend.send(msg)
			elif msg == "###":
				print "Ambiente recebeu mensagem de finalização de atividades."
				break
			else:
				pass
				#print "Agente %s recebeu mensagem inválida." % (self.id)

	def reiniciarMemoria(self):
		self.estrutura = []
		self.posAgentes = {}
		
	def reconstruir(self, novaEstrutura, resolucao):
		nlinhas = ncolunas = resolucao
		for i in xrange(nlinhas):
			de, ate = ncolunas * i, ncolunas * (i+1)
			self.estrutura.append(novaEstrutura[de:ate])
		self.nlinhas, self.ncolunas = nlinhas, ncolunas
		#self.drawFile('log.txt','a')	
		
	def adicionarAgente (self, idAgente, x, y):
		#TODO: checar se a posicao do agente é válida
		#print 'AMBIENTE: adicionado agente %s em %s %s' % (idAgente,x,y)
		self.posAgentes[idAgente]  = (x, y)
		self.estrutura[x][y] = self.componentes.adicionarVarios(['AG03','AG'], self.estrutura[x][y])
	
	def mover (self, iden, direcao):
		if direcao < 0 or direcao > 3:
			#TODO: notificar passagem de valor inválido.
			print 'funcao mover recebeu parâmetro inválido'
			pass
		else:
			#não considera o caso em que o agente sai dos limites...
			x, y = None, None
			if iden in self.posAgentes.keys():
				x, y = self.posAgentes[iden]
			#print 'em', x, y
			if direcao == 0:
				#print 'para cima'
				if self.componentes.checar('PAREDEN', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x-1][y]):
					return "colidiu"
				self.posAgentes[iden] = x-1,y
				self.estrutura[x-1][y] = self.componentes.adicionar('AG', self.estrutura[x-1][y])
			elif direcao == 1:
				#print 'para direita'
				if self.componentes.checar('PAREDEL', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x][y+1]):
					return "colidiu"
				self.posAgentes[iden] = x,y+1
				self.estrutura[x][y+1] = self.componentes.adicionar('AG', self.estrutura[x][y+1])
			elif direcao == 2:
				#print 'para baixo'
				if self.componentes.checar('PAREDES', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x+1][y]):
					return "colidiu"
				self.posAgentes[iden] = x+1,y
				self.estrutura[x+1][y] = self.componentes.adicionar('AG', self.estrutura[x+1][y])
			elif direcao == 3:
				#print 'para esquerda'
				if self.componentes.checar('PAREDEO', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x][y-1]):
					return "colidiu"
				self.posAgentes[iden] = x,y-1
				self.estrutura[x][y-1] = self.componentes.adicionar('AG', self.estrutura[x][y-1])
				
			self.estrutura[x][y] = self.componentes.remover('AG',self.estrutura[x][y])
			return "moveu"
		
	def limpar (self, iden):
		x, y = self.posAgentes[iden]
		if self.componentes.checar('LIXO', self.estrutura[x][y]):
			self.estrutura[x][y] = self.componentes.remover('LIXO',self.estrutura[x][y])
			return "limpou"
		else:
			return 'nop'
	
	def checar(self, iden):
		x, y = self.posAgentes[iden]
		return self.estrutura[x][y]
			
	def recarregar(self, agid):
		x, y = self.posAgentes[agid]
		if self.componentes.checar('RECARGA', self.estrutura[x][y]):
			return "recarregou"
		else:
			return "nop"
	
	def depositar(self, agid):
		""
		x, y = self.posAgentes[agid]		
		if self.componentes.checar('LIXEIRA', self.estrutura[x][y]):
			return "depositou"
		else:
			return "nop"
		
	def parar(self,agid):
		del self.posAgentes[agid]
		return "parou"
		
	def draw(self):
		ret = ""
		for linha in self.estrutura:
			for item in linha:
				info = filter(lambda k: self.componentes.checar(k, item), ['LIXEIRA', 'LIXO', 'RECARGA','AG'])
				char = ""
				if 'AG' in info:
					char += 'a'
				else:
					char += '_'
				if 'LIXEIRA' in info:
					char += 'u'
				elif 'LIXO' in info:
					char += '*'
				elif 'RECARGA' in info:
					char += '$'
				else:
					char += '_'
				ret += char
			ret += '\n'
		ret += '\n'
		return ret
		
	def drawFile(self, filename, mode):
		log = open(filename, mode)
		for linha in self.estrutura:
			for item in linha:
				info = filter(lambda k: self.componentes.checar(k, item), ['LIXEIRA', 'LIXO', 'RECARGA','AG'])
				char = ""
				if 'AG' in info:
					char += 'a'
				else:
					char += '_'
				if 'LIXEIRA' in info:
					char += 'u'
				elif 'LIXO' in info:
					char += '*'
				elif 'RECARGA' in info:
					char += '$'
				else:
					char += '_'
				log.write(char + ' ')
			log.write('\n')
		log.write('\n')
		log.close()


if __name__ == '__main__':
    ambiente = AmbienteAspirador(0, *sys.argv[1:])
    ambiente.start()
