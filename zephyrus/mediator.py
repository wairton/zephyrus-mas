from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants as SimulationParticipants
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
        self._log = []

    @property
    def messenger(self):
        if getattr(self, '_messenger', None) is None:
            self._messenger = self.messenger_class('mediator')
        return self._messenger

    def run(self):
        # TODO add proper logging
        # print 'Interacao rodando!!!'
        # print self.participantes
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        address = self.simulation_participants.address('mediator')
        self.socket_receive.bind(address)
        self.socket_tester = context.socket(zmq.PUSH)
        address = self.simulation_participants.address(self.tester_alias)
        self.socket_tester.connect(address)

        for pid, address in self.participants.items():
            self.sockets_participants[pid] = context.socket(zmq.PUSH)
            self.sockets_participants[pid].connect(address)
        # time.sleep(0.4) #TODO: check if this is necessary
        self.ready()

    def ready(self):
        while True:
            # TODO APL
            msg = Message.from_string(self.socket_receive.recv_string())
            if msg.type == "FINISH":
                self.broadcast(self.messenger.build_finish_message())
                break
            elif msg.type == "START":
                self.mainloop()
            else:
                # log error, unknown message
                pass

    def mainloop(self):
        while True:
            mmsg = self.socket_receive.recv()
            # print 'interação: recebi', mmsg, len(mmsg)
            msg = mmsg.split()
            de, para, texto = int(msg[0]), int(msg[1]), msg[2:] #NOTE: o último elemento NÃO é uma string
            self._log.append((de,para,texto))
            if para == -1:
                # TODO send result to tester
                break
            #sockets_participantes[para].send("%s %s" % (de, texto[0]))
            self.sockets_participantes[para].send(mmsg)

    def add_participant(self, pid: int, address: str):
        # TODO apl
        # print 'adcionou participante', pid, 'em', endereco
        self.participants[pid] = address

    def remove_particioant(self, pid: int):
        del self.participants[pid]

    def broadcast(self, message):
        raw = str(message)
        for pid in self.participants:
            self.sockets_participantes[pid].send(raw)
