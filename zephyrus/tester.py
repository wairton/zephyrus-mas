from abc import ABC, abstractmethod
import enum
import json
import logging
import multiprocessing
import subprocess
import time

import zmq

from zephyrus.components import ComponentManager
from zephyrus.addresses import Participants
from zephyrus.exceptions import CoreException
from zephyrus.message import Message, Messenger


class TesterMessenger(Messenger):
    no_parameter_messages = {
        'start': 'START',
        'restart': 'RESTART',
        'stop': 'STOP',
    }

    def build_config_message(self, config_data):
        return Message(self.sender, 'CONFIG', config_data)


# TODO we can do it better,
# TODO find a more suitable place for this
class Mode(enum.Enum):
    CENTRALIZED = 1
    DISTRIBUTED = 2

    @classmethod
    def from_string(cls, name):
        return cls.__members__.get(name)


class BaseTester:
    def initialize_participant(alias, cmd=None):
        if not '<MANUAL>' in self.configs['run'][alias]:
            # TODO add log
            if cmd is None:
                cmd = self.configs['run'][alias].split()
            subprocess.Popen(cmd)
        else:
            address = self.participants.address(alias)
            print('Run {} manually on {}\n'.format(alias, address))
            input('Press ENTER to continue')


class Tester(ABC, BaseTester, multiprocessing.Process):
    def __init__(self, simulation_config, run_config, address_config, config_comp):
        super().__init__()
        self.configs = {}
        self.configs['simulation'] = json.load(open(simulation_config))
        self.configs['run'] = json.load(open(run_config))
        self.participants = Participants(address_config)
        self.components = ComponentManager(component_config).enum

    def run(self):
        print('*'*20, 'Zephyrus', '*'*20)
        print('conectando...')
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
        logging.debug('finalizando os testes...')
        time.sleep(2)
        # logging.debug(>> sys.stderr, 'FIM'

    def initialize_participants_centralized(self):
        # TODO add log
        # pprint.pprint(self.configs)
        self.initialize_participant('monitor')
        self.initialize_participant('environment')
        for i, cmd in enumerate(self.configs['run']['agents']):
            self.initialize_participant("agent {}".format(i), cmd.split())
        self.initialize_participant('strategy')

    @abstractmethod
    def incializar_participantes_distribuido(self):
        pass    #TODO!

    def main_loop(self, mode):
        self.strategy_socket.send("@@@")
        self.cenario_padrao = map(int, self.configs['simulation']['cenario_padrao'].split())
        resolucao = self.configs['simulation']['resolucao']
        ncargas = self.configs['simulation']['carga']
        sujeiras = self.configs['simulation']['sujeira']
        logging.debug('-' * 100)
        logging.debug(self.participants.get('environment'))
        logging.debug('-' * 100)
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
                #logging.debug(ambiente
                resultados.append(map(float, self.socket_receive.recv().split()))
            obj1, obj2 = zip(*resultados) #unzip!!!
            medias = "%s %s" % (sum(obj1)/len(resultados), sum(obj2)/len(resultados))
            #logging.debug('medias', medias
            #medias = "%s %s" % (100 * random.random(), 100 * random.random())
            self.strategy_socket.send(medias)
            #logging.debug(self.participants.get('ambiente')[0]

    #        logging.debug('recebi', msg
    #        for resultado in resultados:
    #            log.write(str(resultado))
    #        medias = sum(map(lambda k:k[0], resultados))/len(resultados), sum(map(lambda k:k[1], resultados))/len(resultados)
    #        self.strategy_socket.send("%s %s" % (medias[0], medias[1]))
    #        return medias


    #TODO: expandir para uma versão com roteiro
    def iniciar_simulacao(self, mode):
        teste = self.socket_receive()

        tinicio = time.time()
        logging.debug('Teste iniciado às: ', time.strftime("%H:%M:%S", time.localtime()))
        #self.

        self.configuracao = json.loads(open('configuracao.js').read())
        self.cenario_padrao = map(int, self._configuracao["cenario_padrao"].split())
        self.estrategia = self.estrategia_nsga2()
        populacao = self.estrategia.main_loop()
        self.analise(populacao)

        tfim  = time.time()
        logging.debug('Teste finalizado às: ', time.strftime("%H:%M:%S", time.localtime()))
        logging.debug("tempo consumido: ",  str(tfim - tinicio) + 's')


    def avaliar_multiplos(self, cenario):
        #logging.debug('@'
        ambiente = map(self.components.juntar, cenario, self.cenario_padrao)
        #dimensao = self._configuracao["resolucao"]
        resultados = []

        log = open(self._configuracao["mainlog"],'a')
        log.write('\n@\n')
        log.write(str(ambiente))
        log.write('\n')
        #for v in ambiente:
        #   logging.debug(filter(lambda k:self.components.checar(k,v), self.components.items.keys())
        ambiente = reduce(lambda a,b: a + ' '+ b, map(str, ambiente))
        info = "%s %s %s," % (self._configuracao["resolucao"], self._configuracao["ncargas"], self._configuracao["nsujeiras"])
        msg = info + ambiente
        for socket in self.socket_auxiliares:
            socket.send(msg)
            #socket.send(str(ambiente))

        for i in xrange(self._configuracao["nauxiliares"]):
            msg = self.socket_receive.recv()
            resultados.append(map(float,msg.split()))
            #logging.debug('recebi', msg

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

