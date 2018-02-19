# This work is under LGPL license, see the LICENSE.LGPL file for further details.
import json
import math
import sys
import time

import zmq

from zephyrus.monitor import Monitor
from zephyrus.address import Participants


class MonitorAspirador(Monitor):
    def __init__(self, address_config, strategy_config):
        super().__init__()
        self.enderecos = Participants(address_config)
        self.endereco = self.enderecos.endereco('monitor')
        self.participantes = {}
        self._log = []
        self.configuracao = json.load(open(strategy_config))

    @property
    def log(self):
        return self._log[:]

    def pronto(self):
        while True:
            msg_testador = self.socket_receive.recv().split()
            if msg_testador[0] == "###":
                for pid in self.participantes.keys():
                    self.sockets_participantes[pid].send("###")
                break
            elif msg_testador[0] == "@@@":
                self.simulation_loop(msg_testador)
            else:
                print "Monitor: Mensagem '", msg_testador, "' desconhecida"

    def simulation_loop(self, msg_testador):
        resolucao, ncargas = None, None
        if len(msg_testador) > 1:
            resolucao = int(msg_testador[1])
            ncargas = int(msg_testador[2])
            nsujeiras = int(msg_testador[3])
        self._log = []
        for pid in self.participantes.keys():
            self.sockets_participantes[pid].send("@@@")
        while True:
            mmsg = self.socket_receive.recv()
            msg = mmsg.split()
            de, para, texto = int(msg[0]), int(msg[1]), msg[2:] #NOTE: o último elemento NÃO é uma string
            self._log.append((de,para,texto))
            if para == -1:
                self.avaliar(1, resolucao, ncargas, nsujeiras)
                break
            self.sockets_participantes[para].send(mmsg)


    def avaliar(self, agid, resolucao=None, ncargas = None, nsujeiras = None):
        nmovimentos = 0
        nrecolhidos = 0
        consumo = 0
        consumo_max = 0
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
                if consumo > consumo_max:
                    consumo_max = consumo

        fatorx = nrecolhidos / float(nsujeiras)

        tamanho = 0.0
        if resolucao == None:
            tamanho = float(self.configuracao["resolucao"] ** 2)
        else:
            tamanho = float(resolucao ** 2)
        consumo_min = 0.0
        if ncargas == None:
            consumo_min = (tamanho + nrecolhidos) / float(self.configuracao["carga"])
        else:
            consumo_min = (tamanho + nrecolhidos) / float(ncargas)

        if nmovimentos < tamanho:
            obj1 = 50.0 * fatorx
        else:
            obj1 = 100.0 / 2 ** (math.log(nmovimentos/tamanho,3.5))
        if consumo_max < consumo_min: #caso em que o agente parou no caminho
            obj2 = 0.0
        else:
            obj2 = fatorx * (100.0 / 2 ** (math.log(consumo_max/consumo_min,4.5)))

        #print (obj1, obj2)
        self.socket_testador.send("%s %s" %(obj1,obj2))


    def run(self):
        contexto = zmq.Context()
        self.socket_receive = contexto.socket(zmq.PULL)
        self.socket_receive.bind(self.endereco)
        self.socket_testador = contexto.socket(zmq.PUSH)
        self.socket_testador.connect(self.enderecos.endereco('tester'))
        self.sockets_participantes   = {}
        print '?' * 100
        print self.participantes
        for chave in self.participantes.keys():
            self.sockets_participantes[chave] = contexto.socket(zmq.PUSH)
            self.sockets_participantes[chave].connect(self.participantes[chave])

        self.pronto()
        time.sleep(1) #este tempo é necessário para garantir o envio das mensagens para os participantes
        print 'monitor finalizando...'


    def adicionar_participante(self, pid, endereco):
        """
        participante -> tupla contendo referência ao agente e o seu apelido.
        """
        self.participantes[pid] = endereco


    def remover_participante(self, pid):
        del self.participantes[pid]



if __name__ == '__main__':
    m = MonitorAspirador(*sys.argv[1:])
    m.adicionar_participante(0, m.enderecos.endereco('environment'))
    m.adicionar_participante(1, m.enderecos.endereco('agent'))
    m.start()
