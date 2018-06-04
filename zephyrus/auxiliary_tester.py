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
        self.run_config = json.load(open(run_config))
        self.participants = Participants(address_config)
        if component_config is not None:
            self.components = ComponentManager.get_component_enum(component_config)
        self.sockets = {}

    @property
    def alias(self):
        return 'aux_{}'.format(self.aux_id)

    def run(self):
        logging.info('Auxiliary {}: running.'.format(self.aux_id))
        self.context = zmq.Context()
        # connect to main
        self.socket_main = self.context.socket(zmq.PUSH)
        self.socket_main.connect(self.participants.address('tester'))
        self.socket_receive = self.context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address(self.alias))
        self.initialize_participants()
        self.main_loop()
        logging.debug('Auxiliary {}: stopping'.format(self.aux_id))
        time.sleep(2)

    def initialize_participants(self):
        logging.info("Auxiliary Tester: initializing participants")
        for alias in self.run_config.keys():
            self.initialize_participant(alias)

    def stop_participants(self):
        logging.info("Tester: stopping participants")
        stop_message = str(self.messenger.build_stop_message())
        for alias in self.run_config.keys():
            self.sockets[alias].send_string(stop_message)

    def main_loop(self):
        start_message = str(self.messenger.build_start_message())
        stop_message = str(self.messenger.build_stop_message())

        self.sockets['mediator'].send_string(str(self.build_mediator_config_message()))
        while True:
            logging.debug('Auxiliary {}: waiting message from strategy'.format())
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
                self.sockets['mediator'].send_string(start_message)
                time.sleep(.01)
                logging.debug('Auxiliary: lets configure environment')
                evaluation_id = msg.content.get('id')
                environ_config = self.build_environment_config_message(msg.content)
                self.sockets['environment'].send_string(str(environ_config))
                self.sockets['environment'].send_string(start_message)
                # TODO this must work for multiple agents
                logging.debug('Auxiliary: lets configure agent(s)')
                for agent_alias in self.get_agents_aliases():
                    self.sockets[agent_alias].send_string(str(self.build_agent_config_message()))
                    self.sockets[agent_alias].send_string(start_message)
                logging.debug('Auxiliary: waiting for mediator\'s answer')
                msg = self.receive_message()
                logging.debug('Auxiliary: evaluate {}'.format(str(msg)[:50]))
                result = {
                    'id': evaluation_id,
                    'data': self.evaluate(msg.content)
                }

                # TODO check if the message is from mediator or raise error
                logging.debug('Auxiliary: send answer to strategy')
                result_message = self.messenger.build_result_message(receiver='tester', content=result)
                self.socket_main.send_string(str(result_message))
