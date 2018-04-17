import logging
from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants as SimulationParticipants
from zephyrus.exceptions import CoreException
from zephyrus.message import Message, Messenger


class MediatorMessenger(Messenger):
    no_parameter_messages = {
        'start': 'START',
        'reset': 'RESET',
        'finish': 'FINISH'
    }


class Mediator(Process):
    messenger_class = MediatorMessenger

    def __init__(self, participants_config, tester_alias="tester"):
        super().__init__()
        self.simulation_participants = SimulationParticipants(participants_config)
        self.participants = {}
        self.participant_sockets = {}
        self.tester_alias = tester_alias
        # TODO please, rename this
        self.sockets_participants = {}
        self._log = []

    @property
    def messenger(self):
        if getattr(self, '_messenger', None) is None:
            self._messenger = self.messenger_class('mediator')
        return self._messenger

    def run(self):
        logging.debug('Mediator is running')
        self.context = zmq.Context()
        self.socket_receive = self.context.socket(zmq.PULL)
        address = self.simulation_participants.address('mediator')
        self.socket_receive.bind(address)
        self.socket_tester = self.context.socket(zmq.PUSH)
        address = self.simulation_participants.address(self.tester_alias)
        self.socket_tester.connect(address)
        self.connect_to_participants()
        self.ready()

    def connect_to_participants(self):
        self.remove_all_participants()
        logging.debug('Mediator is connecting to all participants')
        for alias, address in self.participants.items():
            self.sockets_participants[alias] = self.context.socket(zmq.PUSH)
            self.sockets_participants[alias].connect(address)
        # time.sleep(0.4) #TODO: check if this is necessary

    def remove_all_participants(self):
        logging.debug('Mediator is removing all participants')
        # explicitly closing sockets altough GC handles it for us.
        # http://pyzmq.readthedocs.io/en/latest/api/zmq.html#zmq.Socket.close
        for socket in self.sockets_participants.values():
            pass
            # if not socket.closed:
            #    print('oi')
            #    socket.close()
        self.sockets_participants = {}

    def ready(self):
        logging.debug('Mediator is ready')
        while True:
            # TODO APL
            msg = Message.from_string(self.socket_receive.recv_string())
            if msg.type == "FINISH":
                self.broadcast(self.messenger.build_finish_message())
                break
            elif msg.type == "START":
                self.mainloop()
            elif msg.type == "CONFIG":
                self.configure(msg.content)
            else:
                # log error, unknown message
                pass

    def mainloop(self):
        active_participants = set(self.participants.keys())
        while len(active_participants) > 0:
            msg_str = self.socket_receive.recv_string()
            logging.debug('Mediator, received {}'.format(msg_str))
            msg = Message.from_string(msg_str)
            sender = msg.sender
            receiver = msg.receiver

            if sender is None or receiver is None:
                emsg = "Messages sent through Mediator must specify both sender and receiver."
                raise CoreException(emsg)

            if receiver == 'mediator':
                # TODO we must made clear the difference between FINISH and STOP
                if msg.type == 'STOP':
                    active_participants.remove(sender)
            else:
                self._log.append(msg_str)
                logging.debug('Mediator, sending it to {}'.format(receiver))
                self.sockets_participants[receiver].send_string(msg_str)
        # TODO We must improve this. Think about how badly this scales.
        msg = Message('mediator', 'tester', 'RESULT', self._log)
        self.socket_tester.send_string(str(msg))
        self._log = []

    def add_participant(self, pid: int, address: str):
        # TODO apl
        # print 'adcionou participante', pid, 'em', endereco
        self.participants[pid] = address

    def remove_particioant(self, pid: int):
        del self.participants[pid]

    def broadcast(self, message):
        raw = str(message)
        for pid in self.participants:
            self.sockets_participants[pid].send(raw)
