#! /usr/bin/python
#-*-coding:utf-8-*-
#This work is under LGPL license, see the LICENSE.LGPL file for further details.

import math
import time
import sys
import json
from os.path import abspath
from random import shuffle, sample, random
from exceptions import Exception
from multiprocessing import Process

import zmq

from core.componentes import Componentes
from core.enderecos import Enderecos


MIN = -1
MAX = 1

INFINITO = 1e1000
INFINITO_NEG = -1e1000


COMP_DOMINA = 1
COMP_DOMINADA = -1
COMP_NONE = 0


class Solucao(object):
    def __init__(self, tipo):
        self.cromossomo = None
        self.objetivos = None
        self.tipo = tipo #maximizar ou minimizar
        self.dominadas = [] #conjunto S do artigo
        self.ndominam = 0 #ni
        self.distancia = 0.0 #para crowding-distance
        self.fitness = None


    def comparar(self, outraSolucao):
        res = None
        if self.tipo == MIN:
            res = map(lambda a,b: a <= b, self.objetivos, outraSolucao.objetivos)
        else:
            res = map(lambda a,b: a >= b, self.objetivos, outraSolucao.objetivos)
        false, true = False in res, True in res #NOTE: o nome dessas variáveis torna o código confuso
        if false and true:
            return 0 #nem domina nem é dominada
        elif true:
            return 1 #domina
        else:
            return -1 #é dominada
        #a opção not false e not true não pode ser teoricamente atingida

    def __str__(self):
        return repr(self.valores)


class SolucaoAspirador(Solucao):
    def __init__(self, tipo):
        super(SolucaoAspirador, self).__init__(tipo)
        self.cromossomo = []
        self.cloned = False

    def clone(self):
        clone = SolucaoAspirador(self.tipo)
        clone.cromossomo = self.cromossomo[:]
        clone.objetivos = self.objetivos[:]
        clone.tipo = self.tipo
        clone.distancia = self.distancia
        clone.fitness = self.fitness
        clone.cloned = True
        return clone

    def draw(self, destino):
        resolucao = int(math.sqrt(len(self.cromossomo)))
        pos = ['_','*', 'u','$','@']
        for i in range(resolucao):
            for j in range(resolucao):
                destino.write(pos[self.cromossomo[i*resolucao+j]] + ' ')
            destino.write("\n")
        destino.write("\n")

    def __str__(self):
        return repr(self.cromossomo)


    def distanciaM(self, ta, tb):
        return abs(ta[0] - tb[0]) + abs(ta[1] - tb[1])

    def decodificar(self, componentes):
        decodificado = [0 for i in self.cromossomo]
        for i in xrange(len(decodificado)):
            gene = self.cromossomo[i]
            if gene == 1:
                decodificado[i] = componentes.adicionar('LIXO',0)
            elif gene == 2:
                decodificado[i] = componentes.adicionar('LIXEIRA',0)
            elif gene == 3:
                decodificado[i] = componentes.adicionar('RECARGA',0)
            elif gene == 4:
                decodificado[i] = componentes.adicionarVarios(['AG','AG03'],0)
            else:
                pass #TODO:exceção?

        return decodificado

    def avaliar(self, resolucao): #TODO: o parâmetro resolução é realmente necessário?
        pos = zip(self.cromossomo, [(i,j) for i in range(resolucao) for j in range(resolucao)])
        sujeiras = filter(lambda k:k[0] == 1, pos)
        lixeiras = filter(lambda k:k[0] == 2, pos)
        recargas = filter(lambda k:k[0] == 3, pos)
        agentes = filter(lambda k:k[0] == 4, pos)
        dlixeira = 0
        drecarga = 0
        for n, pos in sujeiras:
            aux = resolucao**2 #valor maior que o máximo
            #NOTE: poderiam ser feitas com min(map())
            for n2, posl in lixeiras:
                atual = self.distanciaM(pos,posl)
                if atual < aux:
                    aux = atual
            dlixeira += aux
            aux = resolucao**2 #valor maior que o máximo
            for n2, posl in recargas:
                atual = self.distanciaM(pos,posl)
                if atual < aux:
                    aux = atual
            drecarga += aux
        self.objetivos = (dlixeira, drecarga)

    def reproduzir(self, outro, crossoverProb, mutacaoProb, resolucao, nsujeira, nlixeira, ncarga, nagente):
        novoIndividuo = self.crossover(outro, crossoverProb, resolucao, nsujeira, nlixeira, ncarga, nagente)
        ocorreuMutacao = novoIndividuo.mutacao(mutacaoProb)
        if ocorreuMutacao:
            novoIndividuo.objetivos = None
            novoIndividuo.cloned = False
        return novoIndividuo

    def crossover(self, outro, crossoverProb, resolucao, nsujeira, nlixeira, ncarga, nagente):
        if random() < crossoverProb:
            novoIndividuo = SolucaoAspirador(MIN)
            pontoCrossover = resolucao**2/2
            novoIndividuo.cromossomo.extend(self.cromossomo[:pontoCrossover])
            posicoes = {}
            maximos = (resolucao**2 - (nsujeira + nlixeira + ncarga + nagente), nsujeira, nlixeira, ncarga, nagente)
            for i in range(5):
                posicoes[i] = 0
            for gene in novoIndividuo.cromossomo:
                posicoes[gene] += 1
            for gene in outro.cromossomo[pontoCrossover:]:
                if posicoes[gene] < maximos[gene]:
                    novoIndividuo.cromossomo.append(gene)
                    posicoes[gene] += 1
            for gene in outro.cromossomo[:pontoCrossover]:
                if len(novoIndividuo.cromossomo) == resolucao**2:
                    break
                if posicoes[gene] < maximos[gene]:
                    novoIndividuo.cromossomo.append(gene)
                    posicoes[gene] += 1
            return novoIndividuo
        else:
            return self.clone()

    def mutacao(self, mutacaoProb):
        ocorreuMutacao = False
        for i in xrange(len(self.cromossomo)):
            if random() < mutacaoProb:
                ocorreuMutacao = True
                outro = sample(xrange(len(self.cromossomo)), 1)
                #NOTE: e se outro == i?
                self.cromossomo[i], self.cromossomo[outro] = self.cromossomo[outro], self.cromossomo[i]
        return ocorreuMutacao


class Nsga2Exception(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Nsga2(Process):
    def __init__(self, configEst, configEnd, configCom):
        super(Nsga2, self).__init__()
        self.crossoverProb = 0.0
        self.mutacaoProb = 0.0
        self.componentes = Componentes(configCom)
        self.configuracoes = json.load(open(configEst))
        self.enderecos = Enderecos(configEnd)
        self.enderecos.participantes()
        #TODO: guardar o log
        self.npop = 0
        self.maxite = 0

    def run(self):
        raise NotImplementedError

    def fastNondominatedSort(self, populacao):
        """
        returns a list of fronts.
        """
        frontes = []
        fronteAtual = []
        for individuo in populacao:
            individuo.ndominam = 0
            individuo.dominadas = []
        for indiceI, individuo in enumerate(populacao):
            for indiceO, outroIndividuo in enumerate(populacao):
                if indiceI == indiceO:
                    continue
                comp = individuo.comparar(outroIndividuo)
                if comp == COMP_DOMINA:
                    individuo.dominadas.append(indiceO)
                elif comp == COMP_DOMINADA:
                    individuo.ndominam += 1
            if individuo.ndominam == 0:
                individuo.fitness = 1
                fronteAtual.append(individuo)

        frontes.append(fronteAtual)
        i = 0
        while len(frontes[i]) > 0:
            fronteAnterior = frontes[i]
            fronteNovo = []
            for individuo in fronteAnterior:
                for indice in individuo.dominadas:
                    q = populacao[indice] #tentativa de reduzir o acesso a índices de listas
                    q.ndominam -= 1
                    if q.ndominam == 0:
                        q.fitness = i + 2
                        fronteNovo.append(q)
            i += 1
            frontes.append(fronteNovo)
        return frontes  #NOTE: retorna um fronte vazio também?

    def configurar(self, **args):
        for k, valor in args.iteritems():
            if k == 'npopulacao':
                self.npop = valor
            elif k == 'ngeracoes':
                self.maxite = valor
            elif k == 'crossover':
                self.crossoverProb = valor
            elif k == 'mutacao':
                self.mutacao = valor

    #TODO: modificar nomenclatura desse método.
    def crowdingDistanceAssignment(self, pontos):
        for i in pontos:
            i.distancia = 0.0
        nobjetivos = len(pontos[0].objetivos)
        l = len(pontos)
        for m in range(nobjetivos):
            pontos = sorted(pontos, key=lambda ponto: ponto.objetivos[m])
            pontos[0].distancia, pontos[-1].distancia = INFINITO, INFINITO
            i = 1
            while (i < l-1):
                pontos[i].distancia += (pontos[i+1].objetivos[m] - pontos[i-1].objetivos[m])
                i += 1

    def gerarPopulacaoInicial(self):
        raise NotImplementedError

    def gerarPopulacao(self):
        raise NotImplementedError

    def gravarPopulacao(self, pid, populacao):
        log = open('populacao.txt','a')
        log.write(str(pid) + '\n')
        for individuo in populacao:
            for objetivo in individuo.objetivos:
                log.write(str(objetivo)+' ')
            log.write('\n')
        log.close()

    #TODO: mudar o nome para unir populações?
    def gerarConjunto(self, pop1, pop2):
        extra = filter(lambda p:p.cloned==False, pop2)
        for e in extra:
            for p in pop1:
                if e.cromossomo == p.cromossomo:
                    break
            else:
                pop1.append(e)
        return pop1


    def mainLoop(self):
        print "mainloop()"
        msg = self.socketReceive.recv() #aguarda mensagem de inicialização
        p = self.gerarPopulacaoInicial()
        self.gravarPopulacao(0, p)
        q = []
        i = 0
        while i < self.maxite:
            print >> sys.stderr, i,
            #log = open(self.mainlog,"a")
            #log.write("\nGeração %s\n" % (i+1))
            #log.close()
            #print "Geração %s" % (i+1),
            #r = list(set(p + q))
            r = self.gerarConjunto(p, q)
            frontes = self.fastNondominatedSort(r)
            p = []
            for fronte in frontes:
                self.crowdingDistanceAssignment(fronte)
                p.extend(fronte)
                if len(p) >= self.npop:
                    break
            p = sorted(p, key = lambda el: el.distancia, reverse = True)
            p = p[:self.npop]
            q = self.gerarPopulacao(p, self.npop)
            if i % 50 == 0:
                Nsga2Aspirador.draw(p, 'pop_%s.txt' % i)
            i += 1
            self.gravarPopulacao(i, p)
        return p



class Nsga2Aspirador(Nsga2):
    def __init__(self, configEst, configEnd, configCom):
        super(Nsga2Aspirador, self).__init__(configEst, configEnd, configCom)
        self.nagentes = 0
        self.resolucao = 0
        self.nsujeira = 0
        self.nlixeira = 0
        self.ncarga = 0

        self.configurar(**self.configuracoes)

    def avaliar(self, cenario):
        self.socketSend.send(' '.join(map(str, cenario)))
        resposta = self.socketReceive.recv()
        return tuple(map(float, resposta.split()))

    @staticmethod
    def draw(populacao, destino):
        arquivo = open(destino, 'w')
        for individuo in populacao:
            individuo.draw(arquivo)
        arquivo.close()

    def run(self):
        contexto = zmq.Context()
        self.socketSend = contexto.socket(zmq.PUSH)
        self.socketSend.connect(self.enderecos.endereco('testador'))
        self.socketReceive = contexto.socket(zmq.PULL)
        self.socketReceive.bind(self.enderecos.endereco('estrategia'))
        popFinal = self.mainLoop()
        Nsga2Aspirador.draw(popFinal, 'pop_final.txt')
        
        self.socketSend.send("###")

    def configurar(self, **args):
        super(Nsga2Aspirador, self).configurar(**args)
        for k, valor in args.iteritems():
            if k == 'agentes':
                self.nagentes = valor
            elif k == 'resolucao':
                self.resolucao = valor
            elif k == 'sujeira':
                self.nsujeira = valor
            elif k == 'lixeira':
                self.nlixeira = valor
            elif k == 'carga':
                self.ncarga = valor
            else:
                pass

    def gerarIndividuo(self, resolucao, nsujeira, nlixeira, ncarga, nagentes):
        cromossomo = []
        cromossomo.extend((1 for l in xrange(nsujeira)))
        cromossomo.extend((2 for l in xrange(nlixeira)))
        cromossomo.extend((3 for r in xrange(ncarga)))
        cromossomo.extend((4 for r in xrange(nagentes)))
        nvazio = resolucao**2 - len(cromossomo)
        cromossomo.extend((0 for i in xrange(nvazio)))
        shuffle(cromossomo)
        individuo = SolucaoAspirador(MIN)
        individuo.cromossomo = cromossomo
        individuo.objetivos = self.avaliar(individuo.decodificar(self.componentes))
        return individuo

    def salvar(self, destino):
        destino = open(destino,'w')


    def gerarPopulacaoInicial(self):
        print 'gerarPopulação inicial'
        populacao = []
        for i in range(self.npop):
            populacao.append(self.gerarIndividuo(self.resolucao, self.nsujeira, self.nlixeira, self.ncarga, self.nagentes))

        Nsga2Aspirador.draw(populacao, 'pop_inicial.txt')
        return populacao

    def gerarPopulacao(self, populacaoAtual, tamanho):
        selecionados = []
        for i in xrange(tamanho):
            selecionados.append(self.torneioBinario(populacaoAtual))
        novaPopulacao = []
        for i in range(tamanho-1, -1,-1):
            #XXX
            novaPopulacao.append(selecionados[i].reproduzir(selecionados[i-1],
                                                        self.crossoverProb, self.mutacaoProb, self.resolucao,
                                                        self.nsujeira, self.nlixeira, self.ncarga, self.nagentes))
        for individuo in novaPopulacao:
            if individuo.objetivos == None:
                individuo.objetivos = self.avaliar(individuo.decodificar(self.componentes))
        return novaPopulacao

    def torneioBinario(self, pop):
        a, b = sample(xrange(len(pop)),2)
        if pop[a].fitness >= pop[b].fitness: #TODO: deveria haver outra regra para desempate?
            return pop[a]
        else:
            return pop[b]

if __name__ == '__main__':
    estrategia = Nsga2Aspirador(*sys.argv[1:])
    estrategia.start()
