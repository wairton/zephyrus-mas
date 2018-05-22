import enum
import json
import logging
import multiprocessing
import random
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
        self.configs = {
            'run': json.load(open(run_config))
        }
        self.participants = Participants(address_config)
        if component_config is not None:
            self.components = ComponentManager.get_component_enum(component_config)
        self.sockets = {}

    @property
    def alias(self):
        return 'tester_{}'.format(self.aux_id)

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

    def run2(self):
        logging.info('Auxiliary {} Tester: running.'.format(self.aux_id))
        self.context = zmq.Context()
        self.conectarComPrincipal()
        self.socket_receive = self.context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address(self.alias))
        self.initialize_participants()
        self.main_loop()
        logging.debug('Auxiliary {} Tester: stopping'.format(self.aux_id))
        time.sleep(2)

    def run(self):
        logging.info('Auxiliary {} Tester: running.'.format(self.aux_id))
        self.context = zmq.Context()
        self.socket_receive = self.context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address(self.alias))
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

    def connect_foo(self):
        self.socketReceive = contexto.socket(zmq.PULL)
        eauxiliar = self.configuracao["eauxiliares"][self.auxId]
        pauxiliar = str(self._configuracao["pauxiliares"])
        self.socketReceive.bind("tcp://"+ eauxiliar + ':' + pauxiliar)

        self.socketSend = contexto.socket(zmq.PUSH)
        self.socketSend.connect("tcp://"+ self._configuracao["eprincipal"])

        self.socketSend = contexto.socket(zmq.PUSH)
        self.socketSend.bind('tcp://' + self.configuracao['testador'])
        self.socketReceive = contexto.socket(zmq.PULL)
        self.socketConfigure = contexto.socket(zmq.PUB)

    def main_loop(self):
        start_message = str(self.messenger.build_start_message())
        stop_message = str(self.messenger.build_stop_message())

        while True:
            logging.debug('waiting message from main tester')
            msg = self.receive_message()
            logging.debug('Auxiliary Tester {}: received {}'.format(self.aux_id, str(msg)))
            if msg.sender != 'tester':
                logging.error('received message from {} instead of tester'.format(msg.sender))
                # we shouldn't been receiving messages from any other sender at this point...
                break
            if msg.type == 'STOP':
                logging.debug('stop participants')
                break
            elif msg.type == 'EVALUATE':
                result = random.random()
                result_message = self.messenger.build_result_message(content=result)
                self.socket_main.send_string(str(result_message))


    def main_loop2(self):
        start_message = str(self.messenger.build_start_message())
        stop_message = str(self.messenger.build_stop_message())

        self.sockets['mediator'].send_string(str(self.build_mediator_config_message()))
        while True:
            logging.debug('waiting message from main tester')
            msg = self.receive_message()
            logging.debug('Auxiliary Tester {}: received {}'.format(self.aux_id, str(msg)))
            if msg.sender != 'tester':
                logging.error('received message from {} instead of tester'.format(msg.sender))
                # we shouldn't been receiving messages from any other sender at this point...
                break
            if msg.type == 'STOP':
                logging.debug('stop participants')
                self.stop_participants()
                break
            elif msg.type == 'EVALUATE':
                logging.debug('evaluate, lets configure environment')
                environ_config = self.build_environment_config_message(msg.content)
                self.sockets['environment'].send_string(str(environ_config))
                # TODO this must work for multiple agents
                logging.debug('evaluate, lets configure agent')
                self.sockets['agent'].send_string(str(self.build_agent_config_message()))
                self.sockets['mediator'].send_string(start_message)
                self.sockets['agent'].send_string(start_message)
                self.sockets['environment'].send_string(start_message)
                logging.debug('evaluate, waiting for mediator\'s answer')
                # a message from mediator is expected
                msg = self.receive_message()
                logging.debug('evaluate {}'.format(str(msg)))
                result = self.evaluate(msg.content)

                # TODO check if the message is from mediator or raise error
                # TODO evaluate mediators message
                logging.debug('evaluate, send answer to strategy')
                result_message = self.messenger.build_result_message(content=result)
                self.sockets['strategy'].send_string(str(result_message))
        logging.debug('tester, waiting report...')
        msg = self.receive_message()
        self.report_result(msg)


if __name__ == '__main__':
    t = AuxiliaryTester(*sys.argv[1:])
    t.start()
