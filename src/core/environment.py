from multiprocessing import Process

import zmq

from core.componentes import Componentes
from core.address import Participants


class Environment(Process):
    def __init__(self, mid, participants_config, components_config):
        super().__init__()
        # TODO: give a better name
        self.places = []
        self.posAgentes = {}
        self.id = mid
        self.participants = Participants(participants_config)
        self.component_manager = ComponentManager(components_config)
        self.components = self.component_manager.enum

    def run(self):
        raise NotImplementedError

    def carregarArquivo(self, configuracao, componentes):
        """
        carrega o o ambiente a partir de um arquivo de texto
        """
        linhas = []
        try:
            linhas = open(configuracao, 'r').readlines()
        except:
            print "Erro durante a abertura do arquivo de configuração do ambiente."
            exit()

        for linha in linhas:
            if linha[-1] == '\n': linha = linha[:-1]    #pensar numa maneira melhor... #em ruby e.chomp
            self.places.append(map(int, linha.split()))
        #TODO: verificar  a necessidade de fechar o arquivo(que arquivo? =) )
        #arq.close()
        self.nlinhas, self.ncolunas = len(self.places), len(self.locations[0])
        self.componentes = componentes

    def carregarArray(self, array, componentes):
        """
        Carrega o ambiente a partir de uma lista.
        Os dois primeiros valores são nlinhas e ncolunas
        """
        self.places = []
        self.posAgentes = {} #NOTE: esse comando deveria ser aqui?
        array = array.split()
        nlinhas = int(array[0])
        ncolunas = int(array[1])
        for i in range(nlinhas):
            de, ate = 2 + ncolunas * i, 2 + ncolunas * (i+1)
            #TODO: Testar, essa linha!!!
            self.places.append(map(int, array[de:ate]))
        self.nlinhas, self.ncolunas = nlinhas, ncolunas
        self.componentes = componentes

    def imprimir(self):
        print self.places

    def adicionarAgente(self, idAgente, x, y):
        #TODO: checar se a posicao do agente é válida
        self.posAgentes[idAgente]  = (x, y)
        return len(self.posAgentes ) - 1

    def imprimirAgente(self, idAgente = None):
        """
        Envia para saída padrão informações sobre o agente indicado
        por idAgente.
        idAgente == None siginifica todos os agentes.
        """
        if len(self.posAgentes) == 0:
            print 'O cenário não possui agentes aspiradores!'
        elif (idAgente != None):
            for ida, px,py in self.posAgentes:
                if idAgente == ida:
                    print idAgente, px, py
        else:
            for ag in self.posAgentes:
                print ag
