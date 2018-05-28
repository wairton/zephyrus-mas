import abc
import logging
import time
from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.message import Message


class Environment(abc.ABC, Process):
    messenger_class = None

    def __init__(self, participants_config, components_config=None):
        super().__init__()
        # TODO: give a better name
        self.places = []
        self.agent_positions = {}
        self.participants = Participants(participants_config)
        self._messenger = None
        if components_config is not None:
            self.components = ComponentManager.get_component_enum(components_config)

    @property
    def messenger(self):
        if self._messenger is None:
            if self.messenger_class is None:
                raise ZephyrusException("Calling 'messenger' without defining 'messenger_class'")
            self._messenger = self.messenger_class('environment')
        return self._messenger

    def run(self):
        # TODO add log
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address('environment'))
        self.socket_send = context.socket(zmq.PUSH)
        # connect with interaction
        self.socket_send.connect(self.participants.address('mediator'))
        logging.info("Environment: running.")
        self.ready()

    def ready(self):
        while True:
            logging.debug('Environmnent is ready.')
            msg = Message.from_string(self.socket_receive.recv_string())
            if msg.type == "START":
                time.sleep(0.25)
                self.mainloop()
            elif msg.type == "STOP":
                logging.info("Environment: stopping.")
                break
            elif msg.type == "CONFIG":
                self.configure(msg.content)
            else:
                logging.error("Environmnent received an invalid message.")

    @abc.abstractmethod
    def mainloop(self):
        pass

    @abc.abstractmethod
    def configure(self, config_data):
        pass

    def __str__(self):
        return 'Environ: ' + ' '.join(self.places[:])

    def add_agent(self, agent_id, line, col):
        if not 0 <= line < self.nlines or 0 <= col < self.ncols:
            raise ValueError("Invalid line or col provided")
        self.agent_pos[agent_id] = (line, col)
        return len(self.agent_pos)
