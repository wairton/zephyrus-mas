from multiprocessing import Process

import zmq

from zephyrus.addresses import Participants as SimulationParticipants


#nome provisório, a classe representa o conjunto de interações
class Interaction(Process):
    def __init__(self, participants_config, tester_alias):
        super().__init__()
        self.simulation_participants = SimulationParticipants(participants_config)
        self.participants = {}
        self.participant_sockets = {}
        self.tester_alias = tester_alias
        self._log = []

    def ready(self):
        while True:
            #print 'interação esperando...'
            msg_testador = self.pipe_testador.recv().split()
            print 'oi eu sou testador, recebi a mensagem', msg_testador
            if msg_testador[0] == "terminar":
                print "Interacao Encerrando"
                for pid in self.participantes.keys():
                    self.sockets_participantes[pid].send("###")
                break
            if msg_testador[0] == "iniciar":
                resolucao, ncargas = None, None
                if len(msg_testador) > 1:
                    resolucao = int(msg_testador[1])
                    ncargas = int(msg_testador[2])
                    nsujeiras = int(msg_testador[3])
                self._log = []
                for pid in self.participantes.keys():
                    self.sockets_participantes[pid].send("@@@")
                while True:
                    mmsg = self.socket_receive.recv()
#					print 'interação: recebi', mmsg, len(mmsg)
                    msg = mmsg.split()
                    de, para, texto = int(msg[0]), int(msg[1]), msg[2:] #NOTE: o último elemento NÃO é uma string
                    self._log.append((de,para,texto))
                    if para == -1:
                        # TODO send result to tester
                        break
                    #sockets_participantes[para].send("%s %s" % (de, texto[0]))
                    self.sockets_participantes[para].send(mmsg)
            elif msg_testador[0] == '':
                pass

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

    def add_participant(self, pid: int, address: str):
        # TODO apl
        # print 'adcionou participante', pid, 'em', endereco
        self.participants[pid] = address

    def remove_particioant(self, pid: int):
        del self.participants[pid]
