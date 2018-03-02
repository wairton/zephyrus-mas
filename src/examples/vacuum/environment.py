#!/usr/bin/python
import pprint
import sys
import time

import zmq

from core.environment import Environment
from core.message import Message


class EnvironmentMessenger:
    def __init__(self, sender: str):
        self.sender = sender

    def build_cleaned_message(self):
        return Message(self.sender, "CLEANED")

    def build_stopped_messsage(self):
        return Message(self.sender, "STOPPED")

    def build_nop_messsage(self):
        return Message(self.sender, "NOP")

    def build_deposited_messsage(self):
        return Message(self.sender, "DEPOSITED")




class VacuumEnvironment(Environment):
    def __init__(self, mid, participants_config, components_config):
        super().__init__(mid, participants_config, components_config)

    def run(self):
        context = zmq.Context()
        self.socket_receive = contexto.socket(zmq.PULL)

        self.messenger = EnvironmentMessenger('environment')
        self.socket_receive.bind(self.participants.address('environment'))
        self.socket_send = contexto.socket(zmq.PUSH)
        self.socket_send.connect(self.participants.address('monitor'))
        self.socket_tester = contexto.socket(zmq.SUB)
        self.socket_tester.connect(self.participants.address('tester_par'))
        # FIXME
        self.socket_tester.setsockopt(zmq.SUBSCRIBE, str(self.participants.get('environment')['alias']))
        # TODO add proper logging
        # print 'Ambiente rodando!!!', time.time()
        self.main_loop()

    def main_loop(self):
        # TODO add proper logging
        # print "Ambiente está pronto (%s)" % (self.id)
        while True:
            msg = self.socket_tester.recv()
            msg = msg[4:].split(',')
            if len(msg) > 2:    #comprimento menor indica encerramento.
                self.reconstruir(map(int, msg[0].split()), int(msg[1]))
                self.adicionarAgente(int(msg[2]), int(msg[3]), int(msg[4]))
            else:
                print 'opa!!!!!!!!!!!'
            msg = self.socket_receive.recv()
            if msg == "@@@":
                while True:
                    msg = self.socket_receive.recv() #apenas um feddback (ack)
                    requisicao = msg.split()
                    agid = int(requisicao[0])
                    if requisicao[2] == 'perceber':
                        acao = self.checar(agid)
                    elif requisicao[2] == 'mover':
                        acao = self.mover(agid, int(requisicao[3]))
                    elif requisicao[2] == 'limpar':
                        acao = self.limpar(agid)
                    elif requisicao[2] == 'recarregar':
                        acao = self.recarregar(agid)
                    elif requisicao[2] == 'depositar':
                        acao = self.depositar(agid)
                    elif requisicao[2] == 'parar':
                        acao = self.parar(agid)
                        if len(self.agent_positions) == 0:
                            msg = "%s %s %s" % (self.id, agid, acao)
                            self.socket_send.send(msg)
                            msg = "%s %s %s" % (self.id, -1, "###")
                            self.socket_send.send(msg)
                            self.restart_memory()
                            break
                        #TODO: como o ambiente para?
                    else:
                        raise "ambiente: recebeu mensagem desconhecida"
                        pass
                    msg = "%s %s %s" % (self.id, agid, acao)
                    self.socket_send.send(msg)
            elif msg == "###":
                print "Ambiente recebeu mensagem de finalização de atividades."
                break
            else:
                pass

    def restart_memory(self):
        self.places = []
        self.agent_positions = {}

    def reconstruir(self, novaEstrutura, resolucao):
        nlinhas = ncolunas = resolucao
        for i in xrange(nlinhas):
            de, ate = ncolunas * i, ncolunas * (i+1)
            self.places.append(novaEstrutura[de:ate])
        self.nlinhas, self.ncolunas = nlinhas, ncolunas

    def adicionarAgente (self, idAgente, x, y):
        #TODO: checar se a posicao do agente é válida
        self.agent_positions[idAgente]  = (x, y)
        self.places[x][y] = self.componentes.adicionarVarios(['AG03','AG'], self.estrutura[x][y])

    def mover (self, iden, direcao):
        if direcao < 0 or direcao > 3:
            #TODO: notificar passagem de valor inválido.
            print 'funcao mover recebeu parâmetro inválido'
            pass
        else:
            #não considera o caso em que o agente sai dos limites...
            x, y = None, None
            if iden in self.agent_positions.keys():
                x, y = self.agent_positions[iden]
            if direcao == 0:
                if self.componentes.checar('PAREDEN', self.places[x][y]) or self.componentes.checar('AG', self.estrutura[x - 1][y]):
                    return "colidiu"
                self.agent_positions[iden] = x-1,y
                self.places[x-1][y] = self.componentes.adicionar('AG', self.estrutura[x-1][y])
            elif direcao == 1:
                if self.componentes.checar('PAREDEL', self.places[x][y]) or self.componentes.checar('AG', self.estrutura[x][y+1]):
                    return "colidiu"
                self.agent_positions[iden] = x,y+1
                self.places[x][y+1] = self.componentes.adicionar('AG', self.estrutura[x][y+1])
            elif direcao == 2:
                if self.componentes.checar('PAREDES', self.places[x][y]) or self.componentes.checar('AG', self.estrutura[x+1][y]):
                    return "colidiu"
                self.agent_positions[iden] = x+1,y
                self.places[x+1][y] = self.componentes.adicionar('AG', self.estrutura[x+1][y])
            elif direcao == 3:
                if self.componentes.checar('PAREDEO', self.places[x][y]) or self.componentes.checar('AG', self.estrutura[x][y-1]):
                    return "colidiu"
                self.agent_positions[iden] = x,y-1
                self.places[x][y-1] = self.componentes.adicionar('AG', self.estrutura[x][y-1])

            self.places[x][y] = self.componentes.remover('AG',self.estrutura[x][y])
            return "moveu"

    def clean(self, iden):
        x, y = self.agent_positions[iden]
        if self.componentes.checar('LIXO', self.places[x][y]):
            self.places[x][y] = self.componentes.remover('LIXO',self.estrutura[x][y])
            return "limpou"
        else:
            return 'nop'

    def checar(self, iden):
        x, y = self.agent_positions[iden]
        return self.places[x][y]

    def recarregar(self, agid):
        x, y = self.agent_positions[agid]
        if self.componentes.checar('RECARGA', self.places[x][y]):
            return self.messenger
        return self.messenger.build_nop_messsage()

    def depositar(self, agid):
        ""
        x, y = self.agent_positions[agid]
        if self.componentes.checar('LIXEIRA', self.places[x][y]):
            return "depositou"
        return self.messenger.build_nop_messsage()

    def parar(self,agid):
        del self.agent_positions[agid]
        return self.messenger.build_stopped_messsage()

    def draw(self):
        ret = ""
        for linha in self.places:
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
        for linha in self.places:
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
    environment = VacuumEnvironment(0, *sys.argv[1:])
    environment.start()
