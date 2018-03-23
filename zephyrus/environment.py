import abc
import logging
from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.message import Message


class Environment(abc.ABC, Process):
    def __init__(self, mid, participants_config, components_config=None):
        super().__init__()
        # TODO: give a better name
        self.places = []
        self.agent_positions = {}
        self.id = mid
        self.participants = Participants(participants_config)
        if components_config is not None:
            self.components = ComponentManager(components_config).enum

    def run(self):
        # TODO add log
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address('environment'))
        self.socket_send = context.socket(zmq.PUSH)
        # connect with interaction
        self.socket_send.connect(self.participants.address('monitor'))
        self.ready()
        # time.sleep(0.4) # TODO: checar se é necessário

    def ready(self):
        logging.info('Environmnent {} is ready.'.format(self.id))
        while True:
            msg = Message.from_string(self.socket_receive.recv_string())
            if msg.type == "START":
                self.mainloop()
            elif msg.type == "STOP":
                logging.info("Agente %s recebeu mensagem de finalização de atividades." % (self.id))
                break
            elif msg.type == "CONFIG":
                self.configure(msg.content)
            else:
                logging.warning("Agente %s recebeu mensagem inválida." % (self.id))

    @abc.abstractmethod
    def mainloop(self):
        pass

    @abc.abstractmethod
    def configure(self):
        pass

    def __str__(self):
        return 'Environ: ' + ' '.join(self.places[:])

    def add_agent(self, agent_id, line, col):
        if not 0 <= line < self.nlines or 0 <= col < self.ncols:
            raise ValueError("Invalid line or col provided")
        self.agent_pos[agent_id] = (line, col)
        return len(self.agent_pos)
