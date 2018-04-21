import enum
import json
import logging
import multiprocessing
import subprocess
import time
from abc import abstractmethod

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.exceptions import CoreException
from zephyrus.message import Message
from zephyrus.tester import BaseTester, TesterMessenger


class AuxiliaryTesterMessenger(TesterMessenger):
    basic_messages = []


class AuxiliaryTester(BaseTester):
    messenger_class = AuxiliaryTesterMessenger

    def __init__(self, aux_id, run_config, address_config, component_config=None):
        super().__init__()
        self.aux_id = aux_id
        self.configs = {}
        self.configs['run'] = json.load(open(run_config))
        self.participants = Participants(address_config)
        if component_config is not None:
            self.components = ComponentManager(component_config).enum
        self.sockets = {}

    def initialize_participant(self, alias, cmd=None):
        if '<MANUAL>' not in self.configs['run'][alias]:
            # TODO add log
            if cmd is None:
                # cmd = self.configs['run'][alias].split()
                cmd = self.configs['run'][alias]
            # TODO Remove the SHAME!
            # https://docs.python.org/2/library/subprocess.html#replacing-os-system
            cmd = cmd + ' &'
            subprocess.call(cmd, shell=True)
        else:
            address = self.participants.address(alias)
            logging.info('Run {} manually on {}\n'.format(alias, address))
            input('Press ENTER to continue')
        self.sockets[alias] = self.context.socket(zmq.PUSH)
        self.sockets[alias].connect(self.participants.address(alias))

    def run(self):
        logging.info('Auxiliary {} Tester: running.'.format(self.aux_id))
        mode = Mode.from_string(self.configs['simulation']['mode'])
        self.context = zmq.Context()
        self.conectarComPrincipal()
        self.socket_receive = self.context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address('tester'))
        self.initialize_participants()
        self.main_loop()
        logging.debug('Auxiliary {} Tester: stopping'.format(self.aux_id))
        time.sleep(2)

    def initialize_participants(self):
        logging.info("Auxiliary Tester: initializing participants")
        self.initialize_participant('mediator')
        self.initialize_participant('environment')
        self.initialize_participant('agent')
        # TODO fix agent initialization

    def stop_participants(self):
        logging.info("Auxiliary Tester: stopping participants")
        stop_message = str(self.messenger.build_stop_message())
        participants = ['mediator', 'environment', 'agent']
        for p in participants:
            self.sockets[p].send_string(stop_message)

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

    def main_loop(self):
        pass


if __name__ == '__main__':
    t = AuxiliaryTester(*sys.argv[1:])
    t.start()
