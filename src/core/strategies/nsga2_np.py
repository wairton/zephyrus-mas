# -*- coding: utf-8 -*-


class Nsga2(object):
    def __init__(self, npop, maxite):
        self.npop = npop
        self.maxite = maxite
        self.mainlog = None
        self.poplog = None

    def fastNondominatedSort(self, population):
        """
        returns a list of fronts
        """
        fronts = []
        currentFront = []
        for individual in population:
            individual.ndominam = 0
            individual.dominadas = []
        for indexI, individual in enumerate(population):
            for indexO, outroIndividuo in enumerate(population):
                if indexI == indexO:
                    continue
                comp = individual.comparar(outroIndividuo)
                if comp == COMP_DOMINA:
                    individual.dominadas.append(indexO)
                elif comp == COMP_DOMINADA:
                    individual.ndominam += 1
            if individual.ndominam == 0:
                individual.fitness = 1
                currentFront.append(individual)

        fronts.append(currentFront)
        i = 0
        while len(fronts[i]) > 0:
            previousFront = fronts[i]
            newFront = []
            for individual in previousFront:
                for index in individual.dominadas:
                    q = population[index] #tentativa de reduzir o acesso a índices de listas
                    q.ndominam -= 1
                    if q.ndominam == 0:
                        q.fitness = i + 2
                        newFront.append(q)
            i += 1
            fronts.append(newFront)
        return fronts  #NOTE: retorna um fronte vazio também?

    def crowdingDistanceAssignment(self, pontos):
        """
        #TODO: modificar nomenclatura desse método.
        """
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
        log = open(self.poplog,'a')
        log.write(str(pid) + '\n')
        for individuo in populacao:
            for objetivo in individuo.objetivos:
                log.write(str(objetivo)+' ')
            log.write('\n')
        log.close()

    def gerarConjunto(self, pop1, pop2):
        """
        #TODO: mudar o nome para unir populações?
        """
        extra = filter(lambda p: not p.cloned, pop2)
        return pop1+extra


    def mainLoop(self):
        p = self.gerarPopulacaoInicial()
        self.gravarPopulacao(0, p)
        q = []
        i = 0
        while i < self.maxite:
            log = open(self.mainlog, "a")
            log.write("\nGeração %s\n" % (i+1))
            log.close()
            #print "Geração %s" % (i+1),
            print >> sys.stderr, '.',
            #r = list(set(p + q))
            r = self.gerarConjunto(p, q)
            frontes = self.fastNondominatedSort(r)
            p = []
            for fronte in frontes:
                self.crowdingDistanceAssignment(fronte)
                p.extend(fronte)
                if len(p) >= self.npop:
                    break
            p = sorted(p, key=lambda el: el.distancia, reverse=True)
            p = p[:self.npop]
            q = self.gerarPopulacao(p, self.npop)
            i += 1
            self.gravarPopulacao(i, p)
        return p



class Solution(object):
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
