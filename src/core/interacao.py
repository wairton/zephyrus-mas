#-*-coding:utf-8-*-
from multiprocessing import Process
import zmq
import time
from math import log

#nome provisório, a classe representa o conjunto de interações
class Interatividade(Process):
    def __init__(self, endereco, configuracao, pipeTestador):
        super(Interatividade, self).__init__()
        self.idAtual = 0 #identificador das ids dos participantes
        self.endereco = endereco
        self.participantes = {}
#		self.socketsParticipantes = {}
        self._log = []
        self.pipeTestador = pipeTestador
        self.configuracao = configuracao #TODO: resolvendo-se o TODO referente ao avaliar() este atributo se torna desnecessário

    @property
    def log(self):
        return self._log[:]

    def pronto(self):
        while True:
            #print 'interação esperando...'
            msgTestador = self.pipeTestador.recv().split()
            print 'oi eu sou testador, recebi a mensagem', msgTestador
            if msgTestador[0] == "terminar":
                print "Interacao Encerrando"
                for pid in self.participantes.keys():
                    self.socketsParticipantes[pid].send("###")
                break
            if msgTestador[0] == "iniciar":
                resolucao, ncargas = None, None
                if len(msgTestador) > 1:
                    resolucao = int(msgTestador[1])
                    ncargas = int(msgTestador[2])
                    nsujeiras = int(msgTestador[3])
                self._log = []
                for pid in self.participantes.keys():
                    self.socketsParticipantes[pid].send("@@@")
                while True:
                    mmsg = self.socketReceive.recv()
#					print 'interação: recebi', mmsg, len(mmsg)
                    msg = mmsg.split()
                    de, para, texto = int(msg[0]), int(msg[1]), msg[2:] #NOTE: o último elemento NÃO é uma string
                    self._log.append((de,para,texto))
                    if para == -1:
                        self.avaliar(1, resolucao, ncargas, nsujeiras)
                        break
                    #socketsParticipantes[para].send("%s %s" % (de, texto[0]))
                    self.socketsParticipantes[para].send(mmsg)
            elif msgTestador[0]	== '':
                pass

    #TODO: essa avaliacao deve ser feita pelo testador, está aqui provisoriamente
    def avaliar(self, agid, resolucao=None, ncargas = None, nsujeiras = None):
        #print 'avaliando log', len(self._log),
#		print 'avaliando ', resolucao, ncargas
        nmovimentos = 0
        nrecolhidos = 0
        consumo = 0
        consumoMax = 0
        for de,para,texto in self._log:
            if para == agid:
                if texto[0] == 'moveu':
                    nmovimentos += 1
                elif texto[0] == 'limpou':
                    nrecolhidos += 1
                elif texto[0] == "recarregou":
                    consumo -= 10
            elif de == agid and texto[0] != 'perceber':
                consumo += 1
                if consumo > consumoMax:
                    consumoMax = consumo

        fatorx = nrecolhidos / float(nsujeiras) #=)

        tamanho = 0.0
        if resolucao == None:
            tamanho = float(self.configuracao["resolucao"] ** 2)
        else:
            tamanho = float(resolucao ** 2)
        consumoMin = 0.0
        if ncargas == None:
            consumoMin = (tamanho + nrecolhidos) / float(self.configuracao["ncargas"])
        else:
            consumoMin = (tamanho + nrecolhidos) / float(ncargas)

        if nmovimentos < tamanho:
            obj1 = 50.0 * fatorx
        else:
            obj1 = 100.0 / 2 ** (log(nmovimentos/tamanho,3.0))
        if consumoMax < consumoMin: #caso em que o agente parou no caminho
            obj2 = 0.0
        else:
            obj2 = fatorx * (100.0 / 2 ** (log(consumoMax/consumoMin,2.5)))

        print (obj1, obj2)
        self.pipeTestador.send("%s %s" %(obj1,obj2))

    def run(self):
        print 'Interacao rodando!!!'
        print self.participantes
        contexto = zmq.Context()
        self.socketReceive = contexto.socket(zmq.PULL)
        self.socketReceive.bind(self.endereco)
        self.socketsParticipantes = {}
        for chave in self.participantes.keys():
            self.socketsParticipantes[chave] = contexto.socket(zmq.PUSH)
            self.socketsParticipantes[chave].connect(self.participantes[chave])
        #time.sleep(0.4) #TODO: checar se é necessário
        self.pronto()

    def adicionarParticipante(self, pid, endereco):
        """
        participante -> tupla contendo referência ao agente e o seu apelido.
        """
        print 'adcionou participante', pid, 'em', endereco
        self.participantes[pid] = endereco

    def removerParticipante(self, pid):
        del self.participantes[pid]

    def comunicar(self, de, para, mensagem):
        """
        Representa a comunicação entre agentes
        """
        pass
