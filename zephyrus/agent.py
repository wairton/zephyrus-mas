import abc
import logging
from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.message import Message


class Agent(abc.ABC, Process):
    def __init__(self, ag_id, address_config, component_config=None):
        super().__init__()
        self.id = ag_id
        # communication
        participants = Participants(address_config)
        self.address = participants.address('agent')
        self.monitor_address = participants.address('monitor')
        self.socket_receive = None
        self.socket_send = None
        # internal state
        if component_config is not None:
            self.components = c = ComponentManager(component_config).enum

    @abc.abstractmethod
    def perceive(self, perceived_data):
        return self.act(perceived_data)

    def run(self):
        logging.debug('Agent {} is running.'.format(self.id))
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        self.socket_receive.bind(self.address)
        self.socket_send = context.socket(zmq.PUSH)
        self.socket_send.connect(self.monitor_address)
        self.ready()

    def ready(self):
        logging.info('Agent {} is ready.'.format(self.id))
        while True:
            msg = Message.from_string(self.socket_receive.recv_string())
            if msg.type == 'START':
                self.mainloop()
            elif msg.type == 'STOP':
                logging.info("Agente %s recebeu mensagem de finalização de atividades." % (self.id))
                break
            else:
                logging.warning("Agente %s recebeu mensagem inválida." % (self.id))

    @abc.abstractmethod
    def mainloop(self):
        pass

    @abc.abstractmethod
    def act(self, perceived):
        pass
