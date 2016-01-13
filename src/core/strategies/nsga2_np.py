
class Nsga2(object):
    def __init__(self, npop, maxite):
        self.npop = npop
        self.maxite = maxite
        self.mainlog = None
        self.poplog = None


    #retorna uma lista de frontes
    def fastNondominatedSort(self, populacao):
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
        log = open(self.poplog,'a')
        log.write(str(pid) + '\n')
        for individuo in populacao:
            for objetivo in individuo.objetivos:
                log.write(str(objetivo)+' ')
            log.write('\n')
        log.close()

    #TODO: mudar o nome para unir populações?
    def gerarConjunto(self, pop1, pop2):
        extra = filter(lambda p:p.cloned==False, pop2)
        return pop1+extra


    def mainLoop(self):
        p = self.gerarPopulacaoInicial()
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
            i += 1
            self.gravarPopulacao(i, p)
        return p
