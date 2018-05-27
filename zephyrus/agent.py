import abc
import logging
import time
from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.exceptions import ZephyrusException
from zephyrus.message import Message


class Agent(abc.ABC, Process):
    messenger_class = None

    def __init__(self, ag_id, address_config, component_config=None):
        super().__init__()
        self.id = ag_id
        # communication
        participants = Participants(address_config)
        self.address = participants.address('agent')
        self.mediator_address = participants.address('mediator')
        self.socket_receive = None
        self.socket_send = None
        self._messenger = None
        # internal state
        if component_config is not None:
            self.components = ComponentManager.get_component_enum(component_config)

    @property
    def alias(self):
        return "agent_{}".format(self.id)

    @property
    def messenger(self):
        if self._messenger is not None:
            return self._messenger
        elif self.messenger_class is None:
            raise ZephyrusException("messenger_class must be defined")
        else:
            self._messenger = self.messenger_class(self.alias)
        return self._messenger

    @abc.abstractmethod
    def perceive(self, perceived_data):
        return self.act(perceived_data)

    def run(self):
        logging.info('Agent {}: running.'.format(self.id))
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        self.socket_receive.bind(self.address)
        self.socket_send = context.socket(zmq.PUSH)
        self.socket_send.connect(self.mediator_address)
        self.ready()

    def ready(self):
        time.sleep(0.25)
        while True:
            logging.debug('Agent {} is ready.'.format(self.id))
            msg = Message.from_string(self.socket_receive.recv_string())
            logging.debug('Agent received {}'.format(str(msg)))
            if msg.type == 'START':
                self.mainloop()
            elif msg.type == 'CONFIG':
                self.configure(msg.content)
            elif msg.type == 'STOP':
                logging.info("Agent {}: stopping.".format(self.id))
                break
            else:
                logging.warning("Agent {} received invalid message.".format(self.id))

    @abc.abstractmethod
    def mainloop(self):
        pass

    @abc.abstractmethod
    def act(self, perceived):
        pass

    @abc.abstractmethod
    def configure(self, config_data):
        pass
