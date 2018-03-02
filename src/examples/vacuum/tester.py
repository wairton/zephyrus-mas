import enum
import os
import pprint
import random #for debug purpose only
import sys
import time
from multiprocessing import Process
from subprocess import Pope
from time import sleep, time, strftime, localtime

import json
import zmq

from zephyrus.components import ComponentManager
from zephyrus.address import Participants
from zephyrus.exceptions import CoreException


# TODO we can do it better,
# TODO find a more suitable place for this
class Mode(Enum):
    CENTRALIZED = 1
    DISTRIBUTED = 2

    @classmethod
    def from_string(cls, name):
        return cls.__members__.get(name)


class VacuumTester(Process):
    def __init__(self, simulation_config, run_config, address_config, config_comp):
        super().__init__()
        self.configs = {}
        self.configs['simulation'] = json.load(open(simulation_config))
        self.configs['run'] = json.load(open(run_config))
        self.participants = Participants(address_config)
        self.components = ComponentManager(component_config).enum

    def run(self):
        print '*'*20, 'Zephyrus', '*'*20
        print 'conectando...'
        mode = Mode.from_string(self.configs['simulation']['mode'])
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address('tester'))
        if mode == Mode.CENTRALIZED:
            self.inicializar_participantes_centralizado()
            self.socket_monitor = context.socket(zmq.PUSH)
            self.socket_monitor.connect(self.participants.address('monitor'))
            self.socket_configuracoes = context.socket(zmq.PUB)
            self.socket_configuracoes.bind(self.participants.address('tester_par'))
        elif mode == Mode.DISTRIBUTED:
            self.incializar_participantes_distribuido()
            #...
        else:
            raise CoreException("Unknown mode: %s" % mode)
        self.strategy_socket = context.socket(zmq.PUSH)
        self.strategy_socket.connect(self.participants.address('strategy'))
        self.main_loop(mode)
        print 'finalizando os testes...'
        time.sleep(2)
        print >> sys.stderr, 'FIM'

    def inicializar_participantes_centralizado(self):
        if not '<MANUAL>' in self.configs['run']['monitor']: #monitor
            print self.configs['run']['monitor'].split()
            Popen(self.configs['run']['monitor'].split())
        else:
            endereco = self.participants.address('monitor')
            #endereco = self.configs['end']['monitor'].split(',')[-1]
            print 'execute o monitor manualmente, esperado em: ', endereco
            raw_input('\npressione enter para continuar')

        pprint.pprint(self.configs)
        if not '<MANUAL>' in self.configs['run']['environment']: #ambiente
            Popen(self.configs['run']['environment'].split())
        else:
            endereco = self.participants.address('environment')
            #endereco = self.configs['end']['ambiente'].split(',')[-1]
            print 'execute o ambiente manualmente, esperado em: ', endereco
            raw_input('\npressione enter para continuar')
        for i, agente in enumerate(self.configs['run']['agents']): #agentes
            if not '<MANUAL>' in agente:
                Popen(agente.split())
            else:
                endereco = self.participants.address('agent')
                #endereco = self.configs['end']['agentes'][i].split(',')[-1]
                print 'execute o agente manualmente, esperado em: ', endereco
                raw_input('\npressione enter para continuar')
        if not '<MANUAL>' in self.configs['run']['strategy']: #estratégia
            Popen(self.configs['run']['strategy'].split())
        else:
            endereco = self.participants.address('strategy')
            #endereco = self.configs['end']['estrategia'].split(',')[-1]
            print 'execute o estratégia manualmente, esperado em: ', endereco
            raw_input('\npressione enter para continuar')

    def incializar_participantes_distribuido(self):
        pass    #TODO!

    def main_loop(self, mode):
        self.strategy_socket.send("@@@")
        self.cenario_padrao = map(int, self.configs['simulation']['cenario_padrao'].split())
        resolucao = self.configs['simulation']['resolucao']
        ncargas = self.configs['simulation']['carga']
        sujeiras = self.configs['simulation']['sujeira']
        print '-' * 100
        print self.participants.get('environment')
        print '-' * 100
        # nome_ambiente = self.participants.get('environment')[0]
        nome_ambiente = self.participants('environment')['alias']
        while True:
            msg = self.socket_receive.recv()
            if "###" in msg:
                self.socket_configuracoes.send('%s ,' % nome_ambiente)
                self.socket_monitor.send("###")
                break
            iagente = 1
            linha = 0
            coluna = 0
            ambiente = map(self.components.juntar, map(int, msg.split()), self.cenario_padrao)
            for i, position in enumerate(ambiente):
                agentes = filter(lambda k:self.components.checar(k, position), ['AG01', 'AG02', 'AG03', 'AG04'])
                if len(agentes) > 0:
                    linha, coluna = i / resolucao, i % resolucao
            ambiente = ' '.join(map(str, ambiente))
            resultados = []
            for i in range(self.configs['simulation']['repeat']):
                message = '%s %s,%s,%s,%s,%s' % (nome_ambiente, ambiente, resolucao,iagente,linha,coluna)
                self.socket_configuracoes.send(message.encode('ascii'))
                self.socket_monitor.send("@@@ %s %s %s" % (resolucao, ncargas, sujeiras))
                #print ambiente
                resultados.append(map(float, self.socket_receive.recv().split()))
            obj1, obj2 = zip(*resultados) #unzip!!!
            medias = "%s %s" % (sum(obj1)/len(resultados), sum(obj2)/len(resultados))
            #print 'medias', medias
            #medias = "%s %s" % (100 * random.random(), 100 * random.random())
            self.strategy_socket.send(medias)
            #print self.participants.get('ambiente')[0]

    #        print 'recebi', msg
    #        for resultado in resultados:
    #            log.write(str(resultado))
    #        medias = sum(map(lambda k:k[0], resultados))/len(resultados), sum(map(lambda k:k[1], resultados))/len(resultados)
    #        self.strategy_socket.send("%s %s" % (medias[0], medias[1]))
    #        return medias


    #TODO: expandir para uma versão com roteiro
    def iniciar_simulacao(self, mode):
        teste = self.socket_receive()

        tinicio = time()
        print 'Teste iniciado às: ', strftime("%H:%M:%S", localtime())
        #self.

        self.configuracao = json.loads(open('configuracao.js').read())
        self.cenario_padrao = map(int, self._configuracao["cenario_padrao"].split())
        self.estrategia = self.estrategia_nsga2()
        populacao = self.estrategia.main_loop()
        self.analise(populacao)

        tfim  = time()
        print 'Teste finalizado às: ', strftime("%H:%M:%S", localtime())
        print "tempo consumido: ",  str(tfim - tinicio) + 's'


    def avaliar_multiplos(self, cenario):
        #print '@'
        ambiente = map(self.components.juntar, cenario, self.cenario_padrao)
        #dimensao = self._configuracao["resolucao"]
        resultados = []

        log = open(self._configuracao["mainlog"],'a')
        log.write('\n@\n')
        log.write(str(ambiente))
        log.write('\n')
        #for v in ambiente:
        #   print filter(lambda k:self.components.checar(k,v), self.components.items.keys())
        ambiente = reduce(lambda a,b: a + ' '+ b, map(str, ambiente))
        info = "%s %s %s," % (self._configuracao["resolucao"], self._configuracao["ncargas"], self._configuracao["nsujeiras"])
        msg = info + ambiente
        for socket in self.socket_auxiliares:
            socket.send(msg)
            #socket.send(str(ambiente))

        for i in xrange(self._configuracao["nauxiliares"]):
            msg = self.socket_receive.recv()
            resultados.append(map(float,msg.split()))
            #print 'recebi', msg

        for resultado in resultados:
            log.write(str(resultado))
        log.write('\n')
        medias = sum(map(lambda k:k[0], resultados))/len(resultados), sum(map(lambda k:k[1], resultados))/len(resultados)
        log.write(str(medias))
        log.close()
        return medias

    def analise(self, populacao):
        cenarios = []
        for i in populacao:
            individuo = i.decodificar(self.components)
            cenarios.append(map(self.components.juntar, individuo, self.cenario_padrao))
        with open(self._configuracao['popfinal'], 'w') as a:
            for cenario in cenarios:
                for elemento in cenario:
                    a.write(str(elemento) + ' ')
                a.write('\n')


if __name__ == '__main__':
    t = VacuumTester(*sys.argv[1:])
    t.start()
