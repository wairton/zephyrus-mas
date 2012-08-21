#-*-coding:utf-8-*-
from ambiente import AmbienteAspirador
from agente import AspiradorIII
from interacao import Interatividade
from componentes import Componentes
from multiprocessing import Pipe
import zmq
from time import sleep
import json
import sys


class TestadorAuxiliarAspirador(Process):
    def __init__(self, auxId, configuracao):
        self.configuracao = json.load(open(configuracao))
        self.auxId = auxId
        
    def run(self):
        self.conectarComPrincipal()
        
    def inicializarParticipantes(self):
        subp.Popen("") #estratégia
        subp.Popen("") #monitor
        subp.Popen("") #ambiente
        subp.Popen("") #agentes

    def prepararSimulacao(self):
        #TODO: este método funciona APENAS para o agente aspirador!
        #NOTE: Além de ser específica, está inflexível(experimente adicionar outro tipo de agente)
        if self.configuracao == None:
            print 'Nenhuma configuração foi fornecida ao testador'
            #TODO: tratamento de exceção!
            return None

        self.componentes = Componentes(self._configuracao["componentes"])
        self.interacao = Interatividade(self._configuracao["enderecoInteracao"], self._configuracao, self.pipeTesteInteracaoB)

        self.desempenhoAgentes = {} #TODO: é Necessário declará-la aqui!

        endereco, base = self._configuracao["enderecoBase"], self._configuracao["portaBase"]
        self.ambiente = AmbienteAspirador(0, endereco + str(base), self._configuracao["enderecoInteracao"], self.componentes,self.pipeTesteAmbienteB)
        #TODO: isso vai pra ode?
        #self.ambiente.carregarArray(self.cenario, self.componentes)
        self.interacao.adicionarParticipante(self.ambiente.id, endereco + str(base))

        self.agentes = []
        nagentes = self._configuracao["nagentes"]

        for i in range(nagentes):
            self.agentes.append(AspiradorIII(i+1, endereco + str(base + i + 1 ), self._configuracao["enderecoInteracao"], self.componentes))
            self.interacao.adicionarParticipante(i+1, endereco + str(base + i + 1 ))

    def avaliar(self):
        while True:
            msg = self.socketReceive.recv()
            #dimensao = self._configuracao["resolucao"]
            #ambiente = msg
            msg = msg.split(',')
            dimensao, ncargas, nsujeiras = map(int, msg[0].split())
            ambiente = map(int, msg[1].split())

            self.pipeTesteAmbienteA.send((ambiente, dimensao))
            iagente = 1 #TODO: elaborar uma maneira mais completa de determinar qual agente foi encontrado.
            for i in xrange(len(ambiente)):
                agentes = filter(lambda k:self.componentes.checar(k, ambiente[i]), ['AG01', 'AG02', 'AG03', 'AG04'])
                if len(agentes) > 0:
                    linha, coluna = i/dimensao, i%dimensao
                    self.pipeTesteAmbienteA.send((iagente, linha, coluna))
                    #self.ambiente.adicionarAgente(iagente, linha, coluna)
            self.pipeTesteInteracaoA.send("iniciar " + "%s %s %s" % (dimensao, ncargas, nsujeiras))
            msg = self.pipeTesteInteracaoA.recv()

            print 'vou enviar: ', msg
            self.socketSend.send(msg)

    def inicializarSimulacao(self):
        self.prepararSimulacao()
        self.interacao.start()
        sleep(0.2)
        self.ambiente.start()
        sleep(0.2)
        [ag.start() for ag in self.agentes]

        self.conectarComPrincipal()

        self.avaliar()

    def conectarComPrincipal(self):
        contexto = zmq.Context()

        self.socketReceive = contexto.socket(zmq.PULL)
        eauxiliar = self.configuracao["eauxiliares"][self.auxId]
        pauxiliar = str(self._configuracao["pauxiliares"])
        print "bind em: " + "tcp://"+ eauxiliar + ':' + pauxiliar
        self.socketReceive.bind("tcp://"+ eauxiliar + ':' + pauxiliar)

        self.socketSend = contexto.socket(zmq.PUSH)
        self.socketSend.connect("tcp://"+ self._configuracao["eprincipal"])

        print "respostas para: " + "tcp://"+ self._configuracao["eprincipal"]

        self.pipeTesteInteracaoA, self.pipeTesteInteracaoB = Pipe()
        self.pipeTesteAmbienteA, self.pipeTesteAmbienteB = Pipe()
        
        contexto = zmq.Context()
        self.socketSend = contexto.socket(zmq.PUSH)
        self.socketSend.bind('tcp://' + self.configuracao['testador'])
        self.socketReceive = contexto.socket(zmq.PULL)
        self.socketConfigure = contexto.socket(zmq.PUB)

if __name__ == '__main__':
    t = TestadorAuxiliar()
    t.start()
