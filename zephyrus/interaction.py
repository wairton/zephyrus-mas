from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants as SimulationParticipants
from zephyrus.message import Messenger


class InteractionMessenger(Messenger):
    no_parameter_messages = {
        'start': 'START',
        'reset': 'RESET',
        'finish': 'FINISH'
    }


#nome provisório, a classe representa o conjunto de interações
class Interaction(Process):
    def __init__(self, participants_config, tester_alias):
        super().__init__()
        self.simulation_participants = SimulationParticipants(participants_config)
        self.participants = {}
        self.participant_sockets = {}
        self.tester_alias = tester_alias
        self._log = []
        self.messenger = InteractionMessenger('interaction')
    def run(self):
        # TODO add proper logging
        # print 'Interacao rodando!!!'
        # print self.participantes
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        address = self.simulation_participants.addresses('interaction')
        self.socket_receive.bind(address)
        self.socket_tester = context.socket(zmq.PUSH)
        address = self.simulation_participants.addresses(self.tester_alias)
        self.socket_tester.connect(address)

        for pid, address in self.participantes.items():
            self.sockets_participants[pid] = context.socket(zmq.PUSH)
            self.sockets_participants[pid].connect(address)
        # time.sleep(0.4) #TODO: check if this is necessary
        self.ready()

    def ready(self):
        while True:
            # TODO APL
            msg = self.socket_tester.recv()
            content = msg['content']
            if content == "FINISH":
                self.broadcast(self.messenger.build_finish_message())
                break
            elif content == "START":
                self.handle_start_message(content)
            else:
                # log error, unknown message
                pass

    def handle_start_message(self, content):
        resolucao, ncargas = None, None
        if len(msg_testador) > 1:
            resolucao = int(msg_testador[1])
            ncargas = int(msg_testador[2])
            nsujeiras = int(msg_testador[3])
        self._log = []
        self.broadcast(self.messenger.build_reset_message())
        self.mainloop()

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
