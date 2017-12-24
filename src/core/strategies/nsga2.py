import json
import math
import operator
import sys
import time

from enum import Enum
from random import shuffle, sample, random

from componentes import Componentes


class SolutionType(Enum):
    MIN = -1
    MAX = 1


class SolutionComp(Enum):
    DOMINATES = 1
    IS_DOMINATED = -1
    NEITHER = 0


INFINITY = 1e1000


class Solution(object):
    def __init__(self, type):
        self.chromossome = None
        self.objectives = None
        self.type = type #maximizar ou minimizar
        self.dominadas = [] #conjunto S do artigo
        self.ndominam = 0 #ni
        self.distance = 0.0 #para crowding-distance
        self.fitness = None

    def compare(self, other_solution):
        comp_operator = operator.le if SolutionType.MIN else operator.ge
        res = sum(map(comp_operator, self.objectives, other_solution.objectives))
        if res == 0:
            return SolutionComp.IS_DOMINATED
        elif res == len(self.objectives):
            return SolutionComp.DOMINATES
        return SolutionComp.NEITHER

    def __str__(self):
        return repr(self.valores)


class SolutionAspirador(Solution):
    def __init__(self, type):
        super(SolutionAspirador, self).__init__(type)
        self.chromossome = []
        self.cloned = False

    def clone(self):
        clone = SolutionAspirador(self.type)
        clone.chromossome = self.chromossome[:]
        clone.objectives = self.objectives[:]
        clone.type = self.type
        #clone.dominadas = self.dominadas[:]
        #clone.ndominam = self.ndominam
        clone.distance = self.distance
        clone.fitness = self.fitness
        clone.cloned = True
        return clone

    def draw(self, destino):
        resolucao = int(math.sqrt(len(self.chromossome)))
        pos = ['_','*', 'u','$','@']
        for i in range(resolucao):
                for j in range(resolucao):
                        destino.write(pos[self.chromossome[i*resolucao+j]] + ' ')
                destino.write("\n")
        destino.write("\n")

    def __str__(self):
        return repr(self.chromossome)


    def distanciaM(self, ta, tb):
        return abs(ta[0] - tb[0]) + abs(ta[1] - tb[1])

    def decodificar(self, componentes):
        decodificado = [0 for i in self.chromossome]
        for i in xrange(len(decodificado)):
            gene = self.chromossome[i]
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
        pos = zip(self.chromossome, [(i,j) for i in range(resolucao) for j in range(resolucao)])
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
        self.objectives = (dlixeira, drecarga)

    def reproduzir(self, outro, crossoverProb, mutacaoProb, resolucao, nsujeira, nlixeira, ncarga, nagente):
        novoIndividuo = self.crossover(outro, crossoverProb, resolucao, nsujeira, nlixeira, ncarga, nagente)
        #print novoIndividuo
        ocorreuMutacao = novoIndividuo.mutacao(mutacaoProb)
        if ocorreuMutacao:
                novoIndividuo.objectives = None
                novoIndividuo.cloned = False
        return novoIndividuo

    def crossover(self, outro, crossoverProb, resolucao, nsujeira, nlixeira, ncarga, nagente):
        if random() < crossoverProb:
            novoIndividuo = SolutionAspirador(MIN)
            pontoCrossover = resolucao**2/2
            novoIndividuo.chromossome.extend(self.chromossome[:pontoCrossover])
            posicoes = {}
            maximos = (resolucao**2 - (nsujeira + nlixeira + ncarga + nagente), nsujeira, nlixeira, ncarga, nagente)
            for i in range(5):
                    posicoes[i] = 0
            for gene in novoIndividuo.chromossome:
                    posicoes[gene] += 1
            for gene in outro.chromossome[pontoCrossover:]:
                    if posicoes[gene] < maximos[gene]:
                            novoIndividuo.chromossome.append(gene)
                            posicoes[gene] += 1
            for gene in outro.chromossome[:pontoCrossover]:
                    if len(novoIndividuo.chromossome) == resolucao**2:
                            break
                    if posicoes[gene] < maximos[gene]:
                            novoIndividuo.chromossome.append(gene)
                            posicoes[gene] += 1
            return novoIndividuo
        else:
            return self.clone()

    def mutacao(self, mutacaoProb):
        ocorreuMutacao = False
        for i in xrange(len(self.chromossome)):
            if random() < mutacaoProb:
                ocorreuMutacao = True
                outro = sample(xrange(len(self.chromossome)), 1)
                #NOTE: e se outro == i?
                self.chromossome[i], self.chromossome[outro] = self.chromossome[outro], self.chromossome[i]
        return ocorreuMutacao


class Nsga2(object):
    def __init__(self, npop, maxite):
        self.npop = npop
        self.maxite = maxite
        self.mainlog = None
        self.poplog = None


    #retorna uma lista de frontes
    def fast_non_dominated_sort(self, populacao):
        frontes = []
        fronteAtual = []
        for individuo in populacao:
            individuo.ndominam = 0
            individuo.dominadas = []
        for indiceI, individuo in enumerate(populacao):
            for indiceO, outroIndividuo in enumerate(populacao):
                if indiceI == indiceO:
                        continue
                comp = individuo.compare(outroIndividuo)
                if comp == SolutionComp.DOMINATES:
                        individuo.dominadas.append(indiceO)
                elif comp == SolutionComp.IS_DOMINATED:
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

    #TODO: modificar nomenclatura desse método.
    def crowdingDistanceAssignment(self, pontos):
        for i in pontos:
            i.distance = 0.0
        nobjectives = len(pontos[0].objectives)
        l = len(pontos)
        for m in range(nobjectives):
            pontos = sorted(pontos, key=lambda ponto: ponto.objectives[m])
            pontos[0].distance, pontos[-1].distance = INFINITY, INFINITY
            i = 1
            while (i < l-1):
                pontos[i].distance += (pontos[i+1].objectives[m] - pontos[i-1].objectives[m])
                i += 1

    def gerar_populacao_inicial(self):
        raise NotImplementedError

    def gerarPopulacao(self):
        raise NotImplementedError

    def gravarPopulacao(self, pid, populacao):
        log = open(self.poplog,'a')
        log.write(str(pid) + '\n')
        for individuo in populacao:
            for objetivo in individuo.objectives:
                log.write(str(objetivo)+' ')
            log.write('\n')
        log.close()

    #TODO: mudar o nome para unir populações?
    def gerarConjunto(self, pop1, pop2):
        extra = filter(lambda p:p.cloned==False, pop2)
        return pop1+extra


    def main_loop(self):
        p = self.gerar_populacao_inicial()
        self.gravarPopulacao(0, p)
        q = []
        i = 0
        while i < self.maxite:
            log = open(self.mainlog,"a")
            log.write("\nGeração %s\n" % (i+1))
            log.close()
            #print "Geração %s" % (i+1),
            print >> sys.stderr, '.',
            #r = list(set(p + q))
            r = self.gerarConjunto(p, q)
            frontes = self.fast_non_dominated_sort(r)
            p = []
            for fronte in frontes:
                self.crowdingDistanceAssignment(fronte)
                p.extend(fronte)
                if len(p) >= self.npop:
                    break
            p = sorted(p, key = lambda el: el.distance, reverse = True)
            p = p[:self.npop]
            q = self.gerarPopulacao(p, self.npop)
            i += 1
            self.gravarPopulacao(i, p)
        return p



class Nsga2Aspirador(Nsga2):
    def __init__(self, npop, maxite):
        super(Nsga2Aspirador, self).__init__(npop, maxite)
        self.crossoverProb = 0.0
        self.mutacaoProb = 0.0
        self.nagentes = 0
        self.resolucao = 0
        self.nsujeira = 0
        self.nlixeira = 0
        self.ncarga = 0
        self._avaliador = None

        self.componentes = Componentes('componentes.js')
        configuracao = json.load(open('configuracao.js'))
        self.mainlog = configuracao['mainlog']
        self.poplog = configuracao['poplog']

    @property
    def avaliador(self):
        return self._avaliador

    @avaliador.setter
    def avaliador(self, val):
        self._avaliador = val

    @staticmethod
    def draw(populacao, destino):
        arquivo = open(destino, 'w')
        for individuo in populacao:
                individuo.draw(arquivo)
        arquivo.close()

    def configurar(self, **args):
        for k in args.keys():
            valor = args[k]
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
            elif k == 'crossover':
                self.crossoverProb = valor
            elif k == 'mutacao':
                self.mutacao = valor
            else:
                print 'opção "%s" inválida' % (k)

    def gerarIndividuo(self, resolucao, nsujeira, nlixeira, ncarga, nagentes):
        chromossome = []
        chromossome.extend([1 for l in xrange(nsujeira)])
        chromossome.extend([2 for l in xrange(nlixeira)])
        chromossome.extend([3 for r in xrange(ncarga)])
        chromossome.extend([4 for r in xrange(nagentes)])
        nvazio = resolucao**2 - len(chromossome)
        chromossome.extend([0 for i in xrange(nvazio)])
        shuffle(chromossome)
        individuo = SolutionAspirador(MIN)
        individuo.chromossome = chromossome
        #individuo.avaliar(resolucao)
        individuo.objectives = self.avaliador(individuo.decodificar(self.componentes))
        return individuo

    def salvar(self, destino):
        destino = open(destino,'w')

    def gerar_populacao_inicial(self):
        populacao = []
        for i in range(self.npop):
            populacao.append(self.gerarIndividuo(self.resolucao, self.nsujeira, self.nlixeira, self.ncarga, self.nagentes))

        Nsga2Aspirador.draw(populacao, 'inicial.txt')
        return populacao

    def gerarPopulacao(self, populacaoAtual, tamanho):
        """print 'Hora de gerar uma nova população!'
        print 'Populacao atual'
        for i in populacaoAtual:
                print i"""
        selecionados = []
        for i in xrange(tamanho):
            selecionados.append(self.torneioBinario(populacaoAtual))
        #print 'Eis os selecionados:'
        #for i in selecionados:
        #       print i
        novaPopulacao = []
        for i in range(tamanho-1, -1,-1):
            #NOTE: refatore-me!!!!
            novaPopulacao.append(selecionados[i].reproduzir(selecionados[i-1], self.crossoverProb, self.mutacaoProb, self.resolucao, self.nsujeira, self.nlixeira, self.ncarga, self.nagentes))
        for individuo in novaPopulacao:
            if individuo.objectives == None:
                individuo.objectives = self.avaliador(individuo.decodificar(self.componentes))
        return novaPopulacao

    def torneioBinario(self, pop):
        a, b = sample(xrange(len(pop)),2)
        if pop[a].fitness >= pop[b].fitness: #deveria haver outra regra para desempate?
            return pop[a]
        else:
            return pop[b]
