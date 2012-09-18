#-*-coding:utf-8-*-
#This work is under LGPL license, see the LICENSE.LGPL file for further details.

from time import sleep, time, strftime, localtime
from multiprocessing import Process
import sys
import random #for debug purpose only
import time
import os

#from componentes import Componentes

import subprocess as subp

from core.componentes import Componentes
from core.enderecos import Enderecos
from core.exceptions import CoreException

import json
import zmq

class TestadorAspirador(Process):
    def __init__(self, configSim, configExe, configEnd, configComp):
        super(TestadorAspirador, self).__init__()
        self.configs = {}
        self.configs['sim'] = json.load(open(configSim))
        self.configs['exe'] = json.load(open(configExe))
        self.enderecos = Enderecos(configEnd)
        self.componentes = Componentes(configComp)
        
    def run (self):
        print '*'*20, 'Zephyrus', '*'*20
        print 'conectando...'
        modo = self.configs['sim']['mode']
        contexto = zmq.Context()
        self.socketReceive = contexto.socket(zmq.PULL)
        self.socketReceive.bind(self.enderecos.endereco('testador'))
        if modo == 'cent': #um testador
            self.inicializarParticipantesCentralizado()
            self.socketMonitor = contexto.socket(zmq.PUSH)
            self.socketMonitor.connect(self.enderecos.endereco('monitor'))
            self.socketConfiguracoes = contexto.socket(zmq.PUB)
            self.socketConfiguracoes.bind(self.enderecos.endereco('testador_par'))
        elif modo == 'dist':
            self.incializarParticipantesDistribuido()
            #...
        else:
            raise CoreException("Modo de funcionamento desconhecido: %s" % modo)
        self.socketEstrategia = contexto.socket(zmq.PUSH)
        self.socketEstrategia.connect(self.enderecos.endereco('estrategia'))
        self.loopPrincipal(modo)
        print 'finalizando os testes...'
        time.sleep(2)
        print >> sys.stderr, 'FIM'

    def inicializarParticipantesCentralizado(self):
        if not '<MANUAL>' in self.configs['exe']['monitor']: #monitor
            subp.Popen(self.configs['exe']['monitor'].split())
        else:
            endereco = self.enderecos.endereco('monitor')
            #endereco = self.configs['end']['monitor'].split(',')[-1]
            print 'execute o monitor manualmente, esperado em: ', endereco
            raw_input('\npressione enter para continuar')
        if not '<MANUAL>' in self.configs['exe']['ambiente']: #ambiente
            subp.Popen(self.configs['exe']['ambiente'].split())
        else:
            endereco = self.enderecos.endereco('ambiente')
            #endereco = self.configs['end']['ambiente'].split(',')[-1]
            print 'execute o ambiente manualmente, esperado em: ', endereco
            raw_input('\npressione enter para continuar')
        for i, agente in enumerate(self.configs['exe']['agentes']): #agentes
            if not '<MANUAL>' in agente:
                subp.Popen(agente.split())
            else:
                endereco = self.enderecos.endereco('agente')
                #endereco = self.configs['end']['agentes'][i].split(',')[-1]
                print 'execute o agente manualmente, esperado em: ', endereco
                raw_input('\npressione enter para continuar')                
        if not '<MANUAL>' in self.configs['exe']['estrategia']: #estratégia
            subp.Popen(self.configs['exe']['estrategia'].split())
        else:
            endereco = self.enderecos.endereco('estrategia')
            #endereco = self.configs['end']['estrategia'].split(',')[-1]
            print 'execute o estratégia manualmente, esperado em: ', endereco
            raw_input('\npressione enter para continuar')

    def incializarParticipantesDistribuido(self):
        pass    #TODO!

    
    def loopPrincipal(self, modo):
        self.socketEstrategia.send("@@@")
        self.cenarioPadrao = map(int, self.configs['sim']['cenarioPadrao'].split())
        resolucao = self.configs['sim']['resolucao']
        ncargas = self.configs['sim']['carga']
        sujeiras = self.configs['sim']['sujeira']
        nomeAmbiente = self.enderecos.get('ambiente')[0]
        while True:
            msg = self.socketReceive.recv()
            if "###" in msg:
                self.socketConfiguracoes.send('%s ,' % nomeAmbiente)
                self.socketMonitor.send("###")
                break
            iagente = 1
            linha = 0
            coluna = 0
            ambiente = map(self.componentes.juntar, map(int, msg.split()), self.cenarioPadrao)
            for i in xrange(len(ambiente)):
                agentes = filter(lambda k:self.componentes.checar(k, ambiente[i]), ['AG01', 'AG02', 'AG03', 'AG04'])
                if len(agentes) > 0:
                    linha, coluna = i/resolucao, i%resolucao
            ambiente = ' '.join(map(str,ambiente))
            resultados = []
            for i in range(self.configs['sim']['repeat']):
                self.socketConfiguracoes.send('%s %s,%s,%s,%s,%s' % (nomeAmbiente, ambiente, resolucao,iagente,linha,coluna))
                self.socketMonitor.send("@@@ %s %s %s" % (resolucao, ncargas, sujeiras))
                #print ambiente
                resultados.append(map(float, self.socketReceive.recv().split()))
            obj1, obj2 = zip(*resultados) #unzip!!!
            medias = "%s %s" % (sum(obj1)/len(resultados), sum(obj2)/len(resultados))
            #print 'medias', medias
            #medias = "%s %s" % (100 * random.random(), 100 * random.random())
            self.socketEstrategia.send(medias)
            #print self.enderecos.get('ambiente')[0]
            
    #        print 'recebi', msg
    #        for resultado in resultados:
    #            log.write(str(resultado))
    #        medias = sum(map(lambda k:k[0], resultados))/len(resultados), sum(map(lambda k:k[1], resultados))/len(resultados)
    #        self.socketEstrategia.send("%s %s" % (medias[0], medias[1]))
    #        return medias
        
    
    #TODO: expandir para uma versão com roteiro
    def iniciarSimulacao(self, modo):
        teste = self.socketReceive()

        tinicio = time()
        print 'Teste iniciado às: ', strftime("%H:%M:%S", localtime())
        #self.
        
        self.configuracao = json.loads(open('configuracao.js').read())
        self.cenarioPadrao = map(int, self._configuracao["cenarioPadrao"].split())
        self.estrategia = self.estrategiaNsga2()
        populacao = self.estrategia.mainLoop()
        self.analise(populacao)
        
        tfim  = time()
        print 'Teste finalizado às: ', strftime("%H:%M:%S", localtime())
        print "tempo consumido: ",  str(tfim - tinicio) + 's'
    
            
    def avaliarMultiplos(self, cenario):
        #print '@'
        ambiente = map(self.componentes.juntar, cenario, self.cenarioPadrao)
        #dimensao = self._configuracao["resolucao"]
        resultados = []
        
        log = open(self._configuracao["mainlog"],'a')
        log.write('\n@\n')
        log.write(str(ambiente))
        log.write('\n')
        #for v in ambiente:
        #   print filter(lambda k:self.componentes.checar(k,v), self.componentes.items.keys())
        ambiente = reduce(lambda a,b: a + ' '+ b, map(str, ambiente))
        info = "%s %s %s," % (self._configuracao["resolucao"], self._configuracao["ncargas"], self._configuracao["nsujeiras"])
        msg = info + ambiente
        for socket in self.socketAuxiliares:
            socket.send(msg)
            #socket.send(str(ambiente))
        
        for i in xrange(self._configuracao["nauxiliares"]):
            msg = self.socketReceive.recv()
            resultados.append(map(float,msg.split()))
            #print 'recebi', msg
            
        for resultado in resultados:
            log.write(str(resultado))
        log.write('\n')
        medias = sum(map(lambda k:k[0], resultados))/len(resultados), sum(map(lambda k:k[1], resultados))/len(resultados)
        log.write(str(medias))
        log.close()
        return medias

        
    def analise(self, populacao):
        cenarios = []
        for i in populacao:
            individuo = i.decodificar(self.componentes)
            cenarios.append(map(self.componentes.juntar, individuo, self.cenarioPadrao))
        with open(self._configuracao['popfinal'], 'w') as a:
            for cenario in cenarios:
                for elemento in cenario:
                    a.write(str(elemento) + ' ')
                a.write('\n')


if __name__ == '__main__':
    t = TestadorAspirador(*sys.argv[1:])
    t.start()