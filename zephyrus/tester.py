import enum
import json
import logging
import multiprocessing
import subprocess
import time
from abc import ABC, abstractmethod

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.exceptions import CoreException
from zephyrus.message import Message, Messenger


class TesterMessenger(Messenger):
    basic_messages = ['START', 'RESTART', 'STOP', 'CONFIG', 'RESULT']


# TODO we can do it better,
# TODO find a more suitable place for this
class Mode(enum.Enum):
    CENTRALIZED = 1
    DISTRIBUTED = 2

    @classmethod
    def from_string(cls, name):
        return cls.__members__.get(name)


class BaseTester(ABC, multiprocessing.Process):
    messenger_class = None

    @property
    def messenger(self):
        if getattr(self, '_messenger', None) is None:
            self._messenger = self.messenger_class(self.alias)
        return self._messenger

    @property
    def alias(self):
        return 'tester'

    def receive_message(self):
        return Message.from_string(self.socket_receive.recv_string())

    @abstractmethod
    def evaluate(self, data):
        pass

    @abstractmethod
    def report_result(self, msg):
        pass

    def build_strategy_config_message(self):
        return self.messenger.build_config_message(content=self.get_strategy_config())

    def get_strategy_config(self):
        return None

    def build_environment_config_message(self, strategy_data):
        return self.messenger.build_config_message(
            receiver='environment', content=self.get_environment_config(strategy_data))

    def get_environment_config(self, content):
        return content

    def build_agent_config_message(self):
        return self.messenger.build_config_message(content=self.get_agent_config())

    def get_agent_config(self):
        return None

    def build_mediator_config_message(self):
        return self.messenger.build_config_message(content=self.get_mediator_config())

    def get_mediator_config(self):
        return None


class Tester(BaseTester):
    messenger_class = TesterMessenger

    def __init__(self, main_config, run_config, address_config, component_config=None):
        super().__init__()
        self.config = json.load(open(main_config))
        self.run_config = json.load(open(run_config))
        self.participants = Participants(address_config)
        if component_config is not None:
            self.components = ComponentManager.get_component_enum(component_config)
        self.sockets = {}

    def initialize_participant(self, alias, cmd=None):
        if '<MANUAL>' not in self.run_config[alias]:
            # TODO add log
            if cmd is None:
                cmd = self.run_config[alias]
            # TODO Remove the SHAME!
            # os.system(' '.join(cmd) + ' &')
            # subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE).communicate()
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
        logging.info('Tester: running.')
        mode = Mode.from_string(self.config['simulation']['mode'])
        self.context = zmq.Context()
        self.socket_receive = self.context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address('tester'))
        if mode == Mode.CENTRALIZED:
            self.initialize_participants_centralized()
        elif mode == Mode.DISTRIBUTED:
            self.initialize_participants_distributed()
        else:
            msg = "Unknown mode: {}".format(mode)
            logging.error(msg)
            raise CoreException(msg)
        self.main_loop(mode)
        logging.debug('Tester: stopping.')
        time.sleep(2)

    def initialize_participants_centralized(self):
        logging.info("Tester: initializing participants")
        self.initialize_participant('strategy')
        self.initialize_participant('mediator')
        self.initialize_participant('environment')
        self.initialize_participant('agent')
        # TODO fix agent initialization

    def initialize_participants_distributed(self):
        logging.info("Tester: initializing participants")
        self.initialize_participant('strategy')
        for participant in self.participants.aliases:
            if not participant.startswith('tester_'):
                continue
            self.initialize_participant(participant)

    def stop_participants(self):
        logging.info("Tester: stopping participants")
        stop_message = str(self.messenger.build_stop_message())
        participants = ['strategy', 'mediator', 'environment', 'agent']
        for p in participants:
            self.sockets[p].send_string(stop_message)

    def main_loop(self, mode):
        result = None
        if mode == Mode.CENTRALIZED:
            result = self.main_loop_centralized()
        elif mode == Mode.DISTRIBUTED:
            result = self.main_loop_distributed()
        return result

    def main_loop_centralized(self):
        """
        """
        start_message = str(self.messenger.build_start_message())
        stop_message = str(self.messenger.build_stop_message())

        self.sockets['strategy'].send_string(str(self.build_strategy_config_message()))
        self.sockets['strategy'].send_string(start_message)
        self.sockets['mediator'].send_string(str(self.build_mediator_config_message()))
        while True:
            logging.debug('waiting message from strategy')
            msg = self.receive_message()
            logging.debug('Tester received {}'.format(str(msg)))
            if msg.sender != 'strategy':
                logging.error('received message from {} instead of strategy'.format(msg.sender))
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
                time.sleep(0.01)
                self.sockets['environment'].send_string(start_message)
                self.sockets['agent'].send_string(start_message)
                logging.debug('evaluate, waiting for mediator\'s answer')
                # a message from mediator is expected
                msg = self.receive_message()
                logging.debug('evaluate {}'.format(str(msg)[:10]))
                result = self.evaluate(msg.content)

                # TODO check if the message is from mediator or raise error
                # TODO evaluate mediators message
                logging.debug('evaluate, send answer to strategy')
                result_message = self.messenger.build_result_message(content=result)
                self.sockets['strategy'].send_string(str(result_message))
        logging.debug('tester, waiting report...')
        msg = self.receive_message()
        self.report_result(msg)


    def receive_message_from_poller(self, poller, socket, timeout):
        result = poller.poll(timeout)
        if socket in result:
            return Message.from_string(socket.recv_string())
        return None

    def main_loop_distributed(self):
        """
        """
        start_message = str(self.messenger.build_start_message())
        stop_message = str(self.messenger.build_stop_message())

        self.sockets['strategy'].send_string(str(self.build_strategy_config_message()))
        self.sockets['strategy'].send_string(start_message)


        available_testers = []

        poller = zmq.Poller()
        poller.register(self.socket_receive)

        while True:
            logging.debug('waiting message from strategy')
            msg = self.receive_message()
            logging.debug('Tester received {}'.format(str(msg)))
            if msg.sender != 'strategy':
                logging.error('received message from {} instead of strategy'.format(msg.sender))
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
        poller.unregister(self.socket_receive)

    # TODO: expandir para uma versão com roteiro
    def iniciar_simulacao(self, mode):
        # teste = self.socket_receive()

        tinicio = time.time()
        logging.debug('Teste iniciado às: ', time.strftime("%H:%M:%S", time.localtime()))

        self.configuracao = json.loads(open('configuracao.js').read())
        self.cenario_padrao = map(int, self._configuracao["cenario_padrao"].split())
        self.estrategia = self.estrategia_nsga2()
        self.estrategia.main_loop()

        tfim = time.time()
        logging.debug('Teste finalizado às: ', time.strftime("%H:%M:%S", time.localtime()))
        logging.debug("tempo consumido: ", str(tfim - tinicio) + 's')
