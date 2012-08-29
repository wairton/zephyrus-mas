#-*-coding:utf-8-*-
#This work is under LGPL license, see the LICENSE.LGPL file for further details.
import sys
import time
from math import log

import json
import zmq

from core.monitor import Monitor
from core.enderecos import Enderecos


class MonitorAspirador(Monitor):
    def __init__(self, arqEndereco, arqEstrategia):
        super(MonitorAspirador, self).__init__()
        self.enderecos = Enderecos(arqEndereco)
        self.endereco = self.enderecos.endereco('monitor')
        self.participantes = {}
        self._log = []
        self.configuracao = json.load(open(arqEstrategia))
    
    @property
    def log(self):
        return self._log[:]
    
    def pronto(self):
        while True:
            msgTestador = self.socketReceive.recv().split()
            if msgTestador[0] == "###":
                for pid in self.participantes.keys():
                    self.socketsParticipantes[pid].send("###")
                break
            elif msgTestador[0] == "@@@":
                self.simulationLoop(msgTestador)
            else:
                print "Monitor: Mensagem '", msgTestador, "' desconhecida"

    def simulationLoop(self, msgTestador):
        resolucao, ncargas = None, None
        if len(msgTestador) > 1:
            resolucao = int(msgTestador[1])
            ncargas = int(msgTestador[2])
            nsujeiras = int(msgTestador[3])
        self._log = []
        for pid in self.participantes.keys():
            self.socketsParticipantes[pid].send("@@@")
        while True:
            mmsg = self.socketReceive.recv()
            msg = mmsg.split()
            de, para, texto = int(msg[0]), int(msg[1]), msg[2:] #NOTE: o último elemento NÃO é uma string
            self._log.append((de,para,texto))
            if para == -1:
                self.avaliar(1, resolucao, ncargas, nsujeiras)
                break
            self.socketsParticipantes[para].send(mmsg)


    def avaliar(self, agid, resolucao=None, ncargas = None, nsujeiras = None):
        nmovimentos = 0
        nrecolhidos = 0
        consumo = 0
        consumoMax = 0
        for de,para,texto in self._log:
            if para == agid:
                if texto[0] == 'moveu':
                    nmovimentos += 1
                elif texto[0] == 'limpou':
                    nrecolhidos += 1
                elif texto[0] == "recarregou":
                    consumo -= 10
            elif de == agid and texto[0] != 'perceber':
                consumo += 1
                if consumo > consumoMax:
                    consumoMax = consumo
                    
        fatorx = nrecolhidos / float(nsujeiras)
        
        tamanho = 0.0
        if resolucao == None:
            tamanho = float(self.configuracao["resolucao"] ** 2)
        else:
            tamanho = float(resolucao ** 2)
        consumoMin = 0.0
        if ncargas == None:
            consumoMin = (tamanho + nrecolhidos) / float(self.configuracao["carga"])
        else:
            consumoMin = (tamanho + nrecolhidos) / float(ncargas)
            
        if nmovimentos < tamanho:
            obj1 = 50.0 * fatorx
        else:
            obj1 = 100.0 / 2 ** (log(nmovimentos/tamanho,3.5))
        if consumoMax < consumoMin: #caso em que o agente parou no caminho
            obj2 = 0.0
        else:
            obj2 = fatorx * (100.0 / 2 ** (log(consumoMax/consumoMin,4.5)))
        
        #print (obj1, obj2)
        self.socketTestador.send("%s %s" %(obj1,obj2))
    

    def run(self):
        contexto = zmq.Context()
        self.socketReceive = contexto.socket(zmq.PULL)
        self.socketReceive.bind(self.endereco)
        self.socketTestador = contexto.socket(zmq.PUSH)
        self.socketTestador.connect(self.enderecos.endereco('testador'))
        self.socketsParticipantes   = {}
        for chave in self.participantes.keys():
            self.socketsParticipantes[chave] = contexto.socket(zmq.PUSH)
            self.socketsParticipantes[chave].connect(self.participantes[chave])
        
        self.pronto()
        time.sleep(1) #este tempo é necessário para garantir o envio das mensagens para os participantes
        print 'monitor finalizando...'
            
                    
    def adicionarParticipante(self, pid, endereco):
        """
        participante -> tupla contendo referência ao agente e o seu apelido.
        """
        self.participantes[pid] = endereco
        
            
    def removerParticipante(self, pid):
        del self.participantes[pid]
        
    

if __name__ == '__main__':
    m = MonitorAspirador(*sys.argv[1:])
    m.adicionarParticipante(0, m.enderecos.endereco('ambiente'))
    m.adicionarParticipante(1, m.enderecos.endereco('agente'))
    m.start()
