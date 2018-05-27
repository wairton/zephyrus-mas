import abc
import logging
from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.message import Message, Messenger


class StrategyMessenger(Messenger):
    basic_messages = ['ITERATION', 'STOP', 'EVALUATE', 'RESULT']


class Strategy(abc.ABC, Process):
    messenger_class = StrategyMessenger

    def __init__(self, address_config, component_config=None):
        super().__init__()
        # communication
        participants = Participants(address_config)
        self.address = participants.address('strategy')
        self.tester_address = participants.address('tester')
        self.socket_receive = None
        self.socket_send = None
        # internal state
        if component_config is not None:
            self.components = ComponentManager.get_component_enum(component_config)

    @property
    def messenger(self):
        if getattr(self, '_messenger', None) is None:
            self._messenger = self.messenger_class('strategy')
        return self._messenger

    def run(self):
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        self.socket_receive.bind(self.address)
        self.socket_send = context.socket(zmq.PUSH)
        self.socket_send.connect(self.tester_address)
        logging.info('Strategy: running.')
        self.ready()

    def ready(self):
        while True:
            logging.debug('Strategy is ready.')
            msg = Message.from_string(self.socket_receive.recv_string())
            logging.debug("Strategy {}".format(str(msg)))
            if msg.type == 'START':
                self.mainloop()
            elif msg.type == 'CONFIG':
                self.configure(msg.content)
            elif msg.type == 'STOP':
                logging.info("Strategy: stopping.")
                break
            else:
                logging.error("Strategy received invalid message")
                logging.debug(str(msg))

    @abc.abstractmethod
    def mainloop(self):
        pass

    @abc.abstractmethod
    def configure(self, config_data):
        pass
