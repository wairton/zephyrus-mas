import os
import enum
import json
import logging
import multiprocessing
import subprocess
import time
from abc import ABC, abstractmethod
from collections import deque

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.config import load as load_config
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
            # os.system('read -r -p "Press ENTER to continue" key')
            # input('Press ENTER to continue')
            os.system('python -m "zephyrus.pause"')
        self.sockets[alias] = self.context.socket(zmq.PUSH)
        self.sockets[alias].connect(self.participants.address(alias))

    def get_agents_aliases(self):
        return [a for a in self.participants.aliases if a.startswith('agent')]


class Tester(BaseTester):
    messenger_class = TesterMessenger

    def __init__(self, main_config, run_config, address_config, component_config=None):
        super().__init__()
        self.config = load_config(main_config)
        self.run_config = load_config(run_config, self.config['simulation']['variables'])
        self.participants = Participants(address_config)
        if component_config is not None:
            self.components = ComponentManager.get_component_enum(component_config)
        self.sockets = {}

    @property
    def alias(self):
        return 'tester'

    def run(self):
        logging.info('Tester: running.')
        mode = Mode.from_string(self.config['simulation']['mode'])
        self.context = zmq.Context()
        self.socket_receive = self.context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address('tester'))
        self.initialize_participants()
        self.main_loop(mode)
        logging.debug('Tester: stopping.')
        time.sleep(2)

    def initialize_participants(self):
        logging.info("Tester: initializing participants")
        for alias in self.run_config.keys():
            self.initialize_participant(alias)

    def initialize_participants_distributed(self):
        logging.info("Tester: initializing participants")
        self.initialize_participant('strategy')
        self.config['auxiliares'].keys()
        for participant in self.participants.aliases:
            if not participant.startswith('tester_'):
                continue
            self.initialize_participant(participant)

    def stop_participants(self):
        logging.info("Tester: stopping participants")
        stop_message = str(self.messenger.build_stop_message())
        for alias in self.run_config.keys():
            self.sockets[alias].send_string(stop_message)

    def main_loop(self, mode):
        result = None
        if mode == Mode.CENTRALIZED:
            result = self.main_loop_centralized()
        elif mode == Mode.DISTRIBUTED:
            result = self.main_loop_distributed()
        else:
            msg = "Unknown mode: {}".format(mode)
            logging.error(msg)
            raise CoreException(msg)
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
            logging.debug('Tester: waiting message from strategy')
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
                time.sleep(.01)
                self.sockets['mediator'].send_string(start_message)
                logging.debug('Tester: lets configure environment')
                evaluation_id = msg.content.get('id')
                environ_config = self.build_environment_config_message(msg.content)

                self.sockets['environment'].send_string(str(environ_config))
                self.sockets['environment'].send_string(start_message)
                # TODO this must work for multiple agents
                logging.debug('Tester: lets configure agent(s)')
                for agent_alias in self.get_agents_aliases():
                    self.sockets[agent_alias].send_string(str(self.build_agent_config_message()))
                    self.sockets[agent_alias].send_string(start_message)
                logging.debug('Tester: waiting for mediator\'s answer')
                msg = self.receive_message()
                logging.debug('Tester evaluate {}'.format(str(msg)[:50]))
                result = {
                    'id': evaluation_id,
                    'data': self.evaluate(msg.content)
                }
                # TODO check if the message is from mediator or raise error
                logging.debug('Tester: send answer to strategy {}'.format(result))
                result_message = self.messenger.build_result_message(receiver='strategy', content=result)
                self.sockets['strategy'].send_string(str(result_message))
        logging.debug('Tester: waiting report...')
        msg = self.receive_message()
        self.report_result(msg)

    def receive_message_from_poller(self, poller, socket, timeout):
        result = poller.poll(timeout)
        if socket in result:
            return Message.from_string(socket.recv_string())
        return None

    def get_auxiliary_testers_aliases(self):
        return [a for a in self.run_config.keys() if a.startswith('aux')]

    def main_loop_distributed(self):
        start_message = str(self.messenger.build_start_message())
        stop_message = str(self.messenger.build_stop_message())

        self.sockets['strategy'].send_string(str(self.build_strategy_config_message()))
        self.sockets['strategy'].send_string(start_message)

        eval_buffer = deque()
        available_testers = set(self.get_auxiliary_testers_aliases())
        working_testers = set()
        poller = zmq.Poller()
        poller.register(self.socket_receive, zmq.POLLIN)
        should_stop = False
        while not should_stop or len(working_testers) > 0:
            socket = dict(poller.poll(100))
            if self.socket_receive in socket:
                msg = Message.from_string(self.socket_receive.recv_string())
                if msg.sender == 'strategy':
                    if msg.type == 'EVALUATE':
                        eval_buffer.append(msg)
                    elif msg.type == 'STOP':
                        should_stop = True
                elif msg.sender.startswith('aux'):
                    working_testers.remove(msg.sender)
                    available_testers.add(msg.sender)
                    self.sockets['strategy'].send_string(str(msg))

            while len(available_testers) > 0 and len(eval_buffer) > 0:
                msg = eval_buffer.popleft()
                # handle stop message
                tester = available_testers.pop()
                working_testers.add(tester)
                # TODO
                msg.sender = 'tester'
                self.sockets[tester].send_string(str(msg))
        time.sleep(2)
        self.stop_participants()
        logging.debug('tester, waiting report...')
        msg = self.receive_message()
        self.report_result(msg)
        poller.unregister(self.socket_receive)
