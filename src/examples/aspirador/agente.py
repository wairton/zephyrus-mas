#!/usr/bin/python
#-*-coding:utf-8-*-
import time
import sys
from random import choice
from collections import deque
from multiprocessing import Process


import zmq

from core.componentes import Componentes
from core.enderecos import Enderecos


class AspiradorIII(Process):
    def __init__(self, agId, configEnd, configCom):
        super(AspiradorIII, self).__init__()
        
        self.mid = agId
        self.enderecos = Enderecos(configEnd)
        self.endereco = self.enderecos.endereco('agente')
        self.enderecoMonitor = self.enderecos.endereco('monitor')
        self.componentes  = Componentes(configCom)
        
        self.socketReceive = None
        self.socketSend = None
    
        self.enviar = True #True se agente deve enviar mensagem, False caso esteja esperando resposta 
        self.agindo = True #False para enviar ação de perceber          
        self.ENERGIAMAX = 80.0
        self.limiteRecarga = 0.25
                    
        self.RESERVATORIOMAX = 4
        self.PLANO_EXPLORAR = 0
        self.PLANO_RECARREGAR = 1
        self.PLANO_DEPOSITAR = 2
        self.PLANO_SUJEIRA = 3
        self.tiposPlano = (self.PLANO_EXPLORAR, self.PLANO_RECARREGAR, self.PLANO_DEPOSITAR, self.PLANO_SUJEIRA)    
        
        self.reiniciarMemoria()
            
        
    def perceber(self, percebido):
        #print 'AGENTE percebeu: ', percebido
        #define o momento em que o agente enxerga o ambiente captando informações sobre 
        #existência de obstáculos e de sujeira.
        
        itens = ['PAREDEN', 'PAREDEL', 'PAREDES', 'PAREDEO', 'LIXO', 'LIXEIRA','RECARGA']
        #posições: N, L, S ,O e 'sujo' (True indica presença de parede/sujeira).
        st = map(lambda item:self.componentes.checar(item, percebido),itens)
        #print st
        #print 'AGENTE percebeu: ', percebido, st       
        return self.agir(st)
        
    def reiniciarMemoria(self):
        self.visitados = {}
        self.nvisitados = []
        self.lixeiras = [] #posição de pontos de depósito de lixo
        self.recargas = [] #posição de pontos de recarga
        self.sujeiras = set() #posição de sujeiras encontradas
                    
        self.x, self.y = 0, 0
        self.percebido = None
        self.px, self.py = 0, 0
        self.DELTA_POS = ((-1, 0), (0, 1), (1, 0), (0, -1)) #auxiliar em várias operações
        self.energia = self.ENERGIAMAX
    
    #           self.limiteRecarga = 0.4
        self.reservatorio = 0
    
        self.plano = None #qual tipo de plano atualmente sendo executado
        self.movimentar = [] #sequência de movimentos a serem realizados
        self.nrecargas = 0 #usada durante a execução do plano de recarga
        self.recuperarMovimento = 0 #armazena um movimento tentado para recuperá-lo em caso de falha.
        
    def run(self):
        print 'Agente rodando!!!'
        contexto = zmq.Context()
        self.socketReceive = contexto.socket(zmq.PULL)
        self.socketReceive.bind(self.endereco)
        self.socketSend = contexto.socket(zmq.PUSH)
        self.socketSend.connect(self.enderecoMonitor)
        self.pronto()
        #time.sleep(0.4) #TODO: checar se é necessário
        #representa o ciclo percepção ação          
    
    def pronto(self):
        print "Agente %s está pronto." % (self.mid)
        while True:
            msg = self.socketReceive.recv()
            if msg == "@@@":
                self.reiniciarMemoria()
                self.enviar = True
                self.agindo = False
                while True:
                    if self.enviar:
                        if self.agindo == False:
                            self.socketSend.send("%s %s perceber" % (self.mid, 0))
                            #print "agente enviou: %s %s perceber" % (self.mid, 0)
                            #print time.time()
                            self.enviar = False
                        else:
                            acao = self.perceber(self.percebido)
                            msg = "%s %s " % (self.mid, 0)
                            #TODO: tratar o caso PARAR
                            #print "agente enviou: %s" % (msg + acao)
                            #print time.time()                  
                            self.socketSend.send(msg + acao)                                
                            self.enviar = False
                            pass
                    else:
                        if self.agindo == False:
                            msg = self.socketReceive.recv()
                            #print "agente recebeu:", msg
                            #print time.time()
                            self.enviar = True
                            self.agindo = True
                            self.percebido = int(msg.split()[2])
                        else:
                            msg = self.socketReceive.recv() #apenas um feddback (ack)
                            #print 'agente %s recebeu %s' % (self.mid, msg)
                            retorno = msg.split()[-1]
                            if retorno == 'moveu':
                                self.mover()
                            elif retorno == 'limpou':
                                self.limpar()
                            elif retorno == 'recarregou':
                                self.carregar()
                            elif retorno == 'depositou':
                                self.depositar()
                            elif retorno == 'colidiu':
                                self.colidir()
                            elif retorno == 'parou':
                                break
                            elif retorno == 'nop':
                                self.nop()
                            else:
                                pass    
                            self.enviar = True
                            self.agindo = False 
            elif msg == "###":
                print "Agente %s recebeu mensagem de finalização de atividades." % (self.mid)
                break
            else:
                print "Agente %s recebeu mensagem inválida." % (self.mid)
            
    
    def agir(self, st):
        #self.info()
        self.memorizarAmbiente(st)
        #print 'AGIR', self.energia, self.reservatorio, self.plano, self.movimentar, self.visitados, self.nvisitados, st
        """
        print '!!!'
        for i in range(20,0,-1):
            print i
            time.sleep(1)
        resposta = open("gamb.txt").readlines()[0]
        print '???'
        if resposta.split()[0] == 'mover':
            direcao = int(resposta.split()[1])
            self.px, self.py = self.DELTA_POS[direcao]
        
        return resposta"""
        if self.energia <= 0:
            return 'parar'
        if self.plano != None:
            #print 'AGENTE: tenho um plano!'
            #print self.plano, self.movimentar,  self.energia, self.reservatorio
            #time.sleep(1)
            if self.plano == self.PLANO_EXPLORAR:
                #print 'AGENTE: vai explorar!'
                if len(self.movimentar) > 0:
                    self.recuperarMovimento = self.movimentar.pop(0)
                    self.px, self.py = self.DELTA_POS[self.recuperarMovimento]
                    if len(self.movimentar) == 0:
                        self.plano = None
                    return "mover %s" % self.recuperarMovimento
                else:
                    print 'erro na função agir' #TODO: transformar isso em execeção             
            elif self.plano == self.PLANO_DEPOSITAR:
                #print 'AGENTE: vai depositar!'
                if len(self.movimentar) > 0:
                    self.recuperarMovimento = self.movimentar.pop(0)
                    self.px, self.py = self.DELTA_POS[self.recuperarMovimento]
                    self.energia -= 1
                    return "mover %s" % self.recuperarMovimento
                else:
                    self.plano = None
                    return "depositar"                  
            elif self.plano == self.PLANO_RECARREGAR:
                #print 'AGENTE: vai recarregar!'
                if len(self.movimentar) > 0:
                    self.recuperarMovimento = self.movimentar.pop(0)
                    self.px, self.py = self.DELTA_POS[self.recuperarMovimento]
                    self.energia -= 1
                    return "mover %s" % self.recuperarMovimento
                else:
                    self.nrecargas -= 1
                    #print 'nrecargas', self.nrecargas
                    if self.nrecargas == 0:
                        self.plano = None
                    return "recarregar"
            elif self.plano == self.PLANO_SUJEIRA:
                #print 'AGENTE: vai limpar!'
                if len(self.movimentar) > 0:
                    self.recuperarMovimento = self.movimentar.pop(0)
                    self.px, self.py = self.DELTA_POS[self.recuperarMovimento]
                    self.energia -= 1
                    return "mover %s" % self.recuperarMovimento
                else:
                    self.plano = None
                    return "limpar"     
            else:
                print "plano desconhecido" #TODO: transformar em exceção
                
        elif (self.energia / self.ENERGIAMAX) < self.limiteRecarga:
            return self.tracarPlanoRecarga(st)
        elif self.reservatorio == self.RESERVATORIOMAX:
            return self.tracarPlanoDeposito(st)
        elif st[4] == True:
            self.energia -= 3 #consome energia independente de limpar ou não de verdade
            return  'limpar'
        else:
            return self.escolherDirecao(st[:4])
    
    #Atualiza o conhecimento do agente em relação as salas que já foram visitadas, bem como suas características, e das
    #sala que o agente sabe não ter visitado.
    def memorizarAmbiente (self,st):
        if (self.x, self.y) in self.nvisitados:
            self.nvisitados.remove((self.x,self.y))
        self.visitados[(self.x, self.y)] = st[0:4]
        visitados = self.visitados.keys() #NOTE: tentativa de melhorar o desempenho, gerando a lista apenas uma vez
        if st[0] == False:
            if ((self.x-1, self.y) not in visitados) and ((self.x-1, self.y) not in self.nvisitados):
                self.nvisitados.append((self.x-1, self.y))          
        if st[1] == False:
            if ((self.x, self.y+1) not in visitados) and ((self.x, self.y+1) not in self.nvisitados):
                self.nvisitados.append((self.x, self.y + 1))            
        if st[2] == False:
            if ((self.x+1, self.y) not in visitados) and ((self.x+1, self.y) not in self.nvisitados):
                self.nvisitados.append((self.x + 1, self.y))            
        if st[3] == False:
            if ((self.x, self.y-1) not in visitados) and ((self.x, self.y-1) not in self.nvisitados):
                self.nvisitados.append((self.x, self.y - 1))
        if st[4] == True:
            self.sujeiras.add((self.x, self.y))
        if (st[5] == True) and  not ((self.x, self.y) in self.lixeiras):
            self.lixeiras.append((self.x, self.y))
        if (st[6] == True) and  not ((self.x, self.y) in self.recargas):
            self.recargas.append((self.x, self.y))
        
        #print 'Status da memória'
        #print self.visitados.keys()
        #print self.nvisitados
            
    
    #TODO: a checagem de colisão no ambiente NÃO funciona para colisão com paredes
    def escolherDirecao(self, paredes):
        #print 'escolher direção'
        direcoes = []
        for i, parede in enumerate(paredes):
            if not parede:
                direcoes.append(i)
                
        if len(direcoes) == 0:
            return 'parar'
                    
        if len(self.nvisitados) == 0 and len(self.sujeiras) == 0:
            return 'parar'
        
        nvisitados = []
        visitados = self.visitados.keys()
        for direcao in direcoes:
            if direcao == 0:
                if ((self.x-1, self.y) not in visitados):   #TODO: buscas a visitados podem ser substituídas por buscas a nvisitados? 
                    nvisitados.append((0, (-1, 0)))
            elif direcao == 1:
                if ((self.x, self.y+1) not in visitados):
                    nvisitados.append((1, (0, 1)))
            elif direcao == 2:
                if ((self.x+1, self.y) not in visitados):
                    nvisitados.append((2, (1, 0)))
            else:
                if ((self.x, self.y-1) not in visitados):
                    nvisitados.append((3, (0, -1)))
        if len(nvisitados) == 0:
            if len(self.nvisitados) == 0:
                return self.tracarPlanoSujeira()
            else:
                return self.tracarPlanoExploracao()
        #print paredes, nvisitados
        choiced = choice(nvisitados)
        self.px, self.py = choiced[1]
        self.energia -= 1
        self.recuperarMovimento = choiced[0]
        return 'mover %s' % self.recuperarMovimento
                    
    
    def tracarPlanoRecarga(self,st):
        #print 'Plano Recarga', st
        #self.info()
        if len(self.recargas) == 0:
            return self.escolherDirecao(st[:4])         
        self.plano = self.PLANO_RECARREGAR
        self.nrecargas = int((self.ENERGIAMAX - self.energia)/10)
        
        if st[6] == True: #o agente já está em um ponto de recarga
            self.movimentar = []
            self.nrecargas -= 1
            return 'recarregar'
            
        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1000 for i in range(sizey)] for i in range(sizex)]
        
        for x, y in self.visitados.keys():
            matriz[x-minx][y-miny] = 1000   
        
        for x,y in self.recargas:
            matriz[x - minx][y - miny] = -1
        caminho = self.caminhoMaisCurto(matriz, (self.x, self.y),minx, maxx,miny, maxy)
        self.movimentar = self.caminhoParaMovimentos(caminho)
        self.recuperarMovimento = self.movimentar.pop(0)
        self.energia -= 1
        self.px, self.py = self.DELTA_POS[self.recuperarMovimento]
        return "mover %s" % self.recuperarMovimento
                
    def tracarPlanoDeposito(self,st):
        #print 'Plano Deposito', st
        #self.info()
        if len(self.lixeiras) == 0:
            return self.escolherDirecao(st[:4])
        self.plano = self.PLANO_DEPOSITAR
    
        if st[5] == True: #o agente já está em um ponto de recarga
            self.movimentar = []
            self.plano = None
            return 'depositar'
        
        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1000 for i in range(sizey)] for i in range(sizex)]
        
        for x, y in self.visitados.keys():
            matriz[x-minx][y-miny] = 1000               
        
        #matriz.reverse()               
        for x,y in self.lixeiras:
            #matriz[maxx - x][y - miny] = -1
            matriz[x - minx][y - miny] = -1     
        caminho = self.caminhoMaisCurto(matriz, (self.x, self.y),minx, maxx,miny, maxy)
        #print 'caminho: ', caminho
        self.movimentar = self.caminhoParaMovimentos(caminho)
        self.recuperarMovimento = self.movimentar.pop(0)
        self.energia -= 1
        self.px, self.py = self.DELTA_POS[self.recuperarMovimento]          
        return "mover %s" % self.recuperarMovimento
    
    def tracarPlanoSujeira(self):
        #print 'Plano Sujeira', st
        #self.info()
        self.plano = self.PLANO_SUJEIRA
        
        """
        if st[4] == True: #o agente já está em um ponto de sujeira
            self.movimentar = []
            self.nrecargas -= 1
            return 'limpar'"""
            
        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1000 for i in range(sizey)] for i in range(sizex)]
        
        for x, y in self.visitados.keys():
            matriz[x-minx][y-miny] = 1000   
        
        for x,y in self.sujeiras:
            matriz[x - minx][y - miny] = -1
        caminho = self.caminhoMaisCurto(matriz, (self.x, self.y),minx, maxx,miny, maxy)
        self.movimentar = self.caminhoParaMovimentos(caminho)
        self.recuperarMovimento = self.movimentar.pop(0)
        self.energia -= 1
        self.px, self.py = self.DELTA_POS[self.recuperarMovimento]
        return "mover %s" % self.recuperarMovimento     
                
    def tracarPlanoExploracao(self):
        #print 'Plano Exploracao'
        #self.info()
        self.plano = self.PLANO_EXPLORAR
        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1 for i in range(sizey)] for i in range(sizex)]
        
        for x, y in self.visitados.keys():
            matriz[x-minx][y-miny] = 1000
        caminho = self.caminhoMaisCurto(matriz, (self.x, self.y),minx, maxx,miny, maxy)
        self.movimentar = self.caminhoParaMovimentos(caminho)
        self.energia -= 1
        self.recuperarMovimento = self.movimentar.pop(0)
        self.px, self.py = self.DELTA_POS[self.recuperarMovimento]
        return "mover %s" % self.recuperarMovimento
    
    #encontrar as coordenadas do mapa mental do agente
    def calcularDimensoes(self):
        visitados = self.visitados.keys()
        if len(self.nvisitados) != 0:
            maxx = max(max(visitados)[0], max(self.nvisitados)[0])
            minx = min(min(visitados)[0], min(self.nvisitados)[0])
            maxy = max(max(visitados, key=lambda k:k[1])[1],max(self.nvisitados, key=lambda k:k[1])[1])
            miny = min(min(visitados, key=lambda k:k[1])[1],min(self.nvisitados, key=lambda k:k[1])[1])             
        else:
            maxx = max(visitados)[0]
            minx = min(visitados)[0]
            maxy = max(visitados, key=lambda k:k[1])[1]
            miny = min(visitados, key=lambda k:k[1])[1]             
    
    
        return minx, maxx, miny, maxy
    
    def caminhoMaisCurto(self, matriz, atual, minx, maxx, miny, maxy):
        fila = deque()
        caminho = []
        fila.append(atual)
        px, py = atual
        matriz[px-minx][py-miny] =  0
        peso = 0
        while len(fila) > 0:            
            px, py = fila.popleft()
            if matriz[px - minx][py - miny] ==  -1:
                return (px,py) #TODO: se entrar aqui (é possível?) vai dar bug!!!!!!
            peso = matriz[px - minx][py - miny]
            direcoes = self.estadosParaDirecoes((px, py), self.visitados[(px, py)])
            for direcao in direcoes:
                opx, opy = direcao
                if matriz[opx - minx][opy - miny] > peso + 1:   #encontrou um caminho melhor (ou o primeiro caminho) até aquela posição.
                    matriz[opx - minx][opy - miny] = peso + 1
                    fila.append(direcao)
                elif matriz[opx - minx][opy - miny] == -1: #encontrou uma posição que ainda não foi visitada.
                    caminho.append((opx, opy))
                    while peso >= 0:
                        #if ((maxx - opx - 1 >= 0) and (matriz[maxx - opx - 1][opy - miny] == peso)):
                        #Sul
                        if ((opx - minx + 1 <= maxx - minx) and (matriz[opx - minx + 1][opy - miny] == peso)):
                            caminho.append((opx + 1, opy))
                            opx += 1
                            peso -= 1
                            continue
                        #Oeste
                        if ((opy - miny - 1 >= 0) and (matriz[opx - minx][opy - 1 - miny] == peso)):
                            caminho.append((opx, opy - 1))
                            opy -= 1
                            peso -= 1
                            continue            
                        #if (maxx - opx + 1 <= maxx - minx) and (matriz[maxx - opx + 1][opy - miny] == peso):
                        #Norte
                        if (opx - minx - 1 >= 0) and (matriz[opx - minx - 1][opy - miny] == peso):
                            caminho.append((opx - 1, opy))
                            peso -= 1
                            opx -= 1
                            continue
                        if (opy - miny + 1 <= maxy - miny) and (matriz[opx - minx][opy + 1 - miny] == peso):
                            caminho.append((opx, opy + 1))
                            peso -= 1
                            opy += 1
                            continue            
                    return caminho[::-1] #caminho do início pro fim.
        print 'nao encontrou caminho!'
        print self.info()
    
    #Método auxiliar que realiza a conversão de estados(paredes) para direções
    def estadosParaDirecoes(self, pos, st):
        ret = []
        x,y = pos
        if st[0] == False:
            ret.append((x-1,y))
        if st[1] == False:
            ret.append((x,y+1))         
        if st[2] == False:
            ret.append((x+1,y))
        if st[3] == False:
            ret.append((x,y-1))
        return ret
    
    #Método que transforma uma rota em uma série de movimentos. 
    def caminhoParaMovimentos (self, caminho):
        movimentos = []
        orix, oriy = caminho[0]
        for i in range(1,len(caminho)):
            desx, desy = caminho[i]
            if orix != desx:
                if orix > desx:
                    movimentos.append(0)
                else:
                    movimentos.append(2)
            else:
                if oriy > desy:
                    movimentos.append(3)
                else:
                    movimentos.append(1)
            orix, oriy = desx, desy
        return movimentos
    
                    
    def limpar(self):
        #O agente executa a ação de limpar em sua posição atual.
        #print 'limpei'
        self.sujeiras.discard((self.x, self.y))
        self.reservatorio += 1
    
    def carregar(self):
        #print 'carreguei'
        self.energia += 10
        
    def depositar(self):
        #print 'depositei'
        self.energia -= 1
        self.reservatorio = 0
                
    def parar(self):
        #O agente permanece parado e apenas informa esse fato ao observador.
        #print 'parei'
        self.info()
        while True:
            pass
                
    def mover(self):
        #movimento realizado com sucesso
        #print 'movi'
        self.x += self.px
        self.y += self.py
        
    def colidir(self):
        print 'colidi'          
        self.energia -= 1
        if self.plano != None:
            self.movimentar.insert(0,self.recuperarMovimento)
            
    def nop(self):
        pass
        #print 'nop'
            
    def info(self):
        print '*'*10
        print 'posicao', (self.x, self.y)
        print self.energia, self.reservatorio, self.plano
        print 'visitados', self.visitados.keys()
        print 'nvisitados', self.nvisitados
        print 'lixeiras', self.lixeiras
        print 'recargas', self.recargas
        print 'sujeiras', self.sujeiras 
        print '*'*10

        
if __name__ == '__main__':
    #agente = AspiradorIII(agid, configEnd, configComp)
    agente = AspiradorIII(1, *sys.argv[1:])
    agente.start()
