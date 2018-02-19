import json
import math
import random

from core.strategies.nsga2 import Nsga2, Solution
from core.strategies.utils import manhattan_distance


class VaccumCleanerSolution(Solution):
    def __init__(self, solution_type):
        super().__init__(solution_type)
        self.chromossome = []
        self.cloned = False

    def clone(self):
        clone = VaccumCleanerSolution(self.type)
        clone.chromossome = self.chromossome[:]
        clone.objectives = self.objectives[:]
        clone.type = self.type
        # clone.dominated = self.dominated[:]
        # clone.n_dominated = self.n_dominated
        clone.distance = self.distance
        clone.fitness = self.fitness
        clone.cloned = True
        return clone

    def draw(self, destino):
        resolution = int(math.sqrt(len(self.chromossome)))
        pos = ['_', '*', 'u', '$', '@']
        for i in range(resolution):
            for j in range(resolution):
                destino.write(pos[self.chromossome[i * resolution + j]] + ' ')
            destino.write('\n')
        destino.write('\n')

    def __str__(self):
        return repr(self.chromossome)

    def decode(self, componentes):
        decoded = []
        for gene in self.chromossome:
            value = 0
            if gene == 1:
                value = componentes.adicionar('LIXO', 0)
            elif gene == 2:
                value = componentes.adicionar('LIXEIRA', 0)
            elif gene == 3:
                value = componentes.adicionar('RECARGA', 0)
            elif gene == 4:
                value = componentes.adicionarVarios(['AG','AG03'], 0)
            else:
                pass #TODO: raise an exception here?
            decoded.append(value)
        return decoded

    def evaluate(self, resolution): #TODO: o parâmetro resolução é realmente necessário?
        pos = zip(self.chromossome, [(i,j) for i in range(resolution) for j in range(resolution)])
        sujeiras = filter(lambda k:k[0] == 1, pos)
        lixeiras = filter(lambda k:k[0] == 2, pos)
        recargas = filter(lambda k:k[0] == 3, pos)
        agents = filter(lambda k:k[0] == 4, pos)
        dlixeira = 0
        drecarga = 0
        for n, pos in sujeiras:
            aux = resolution ** 2 #valor maior que o máximo
            #NOTE: poderiam ser feitas com min(map())
            for n2, posl in lixeiras:
                atual = manhattan_distance(pos, posl)
                if atual < aux:
                    aux = atual
            dlixeira += aux
            aux = resolution ** 2  # valor maior que o máximo
            for n2, posl in recargas:
                atual = manhattan_distance(pos, posl)
                if atual < aux:
                    aux = atual
            drecarga += aux
        self.objectives = (dlixeira, drecarga)

    def reproduction(self, outro, crossover_prob, mutation_prob, resolution, nsujeira, nlixeira, ncarga, nagente):
        novoIndividuo = self.crossover(outro, crossover_prob, resolution, nsujeira, nlixeira, ncarga, nagente)
        ocorreuMutacao = novoIndividuo.mutation(mutation_prob)
        if ocorreuMutacao:
            novoIndividuo.objectives = None
            novoIndividuo.cloned = False
        return novoIndividuo

    def crossover(self, outro, crossover_prob, resolution, nsujeira, nlixeira, ncarga, nagente):
        if random.random() < crossover_prob:
            new_individual = VaccumCleanerSolution(SolutionType.MIN)
            crossover_point = resolution ** 2 / 2
            new_individual.chromossome.extend(self.chromossome[:crossover_point])
            positions = {}
            maximos = (resolution ** 2 - (nsujeira + nlixeira + ncarga + nagente), nsujeira, nlixeira, ncarga, nagente)
            for i in range(5):
                positions[i] = 0
            for gene in new_individual.chromossome:
                positions[gene] += 1
            for gene in outro.chromossome[crossover_point:]:
                if positions[gene] < maximos[gene]:
                    new_individual.chromossome.append(gene)
                    positions[gene] += 1
            for gene in outro.chromossome[:crossover_point]:
                if len(new_individual.chromossome) == resolution ** 2:
                    break
                if positions[gene] < maximos[gene]:
                    new_individual.chromossome.append(gene)
                    positions[gene] += 1
            return new_individual
        return self.clone()

    def mutation(self, mutation_prob):
        mutation_ocurred = False
        for i in range(len(self.chromossome)):
            if random.random() < mutation_prob:
                mutation_ocurred = True
                outro = random.sample(range(len(self.chromossome)), 1)
                #NOTE: e se outro == i?
                self.chromossome[i], self.chromossome[outro] = self.chromossome[outro], self.chromossome[i]
        return mutation_ocurred


class VaccumCleanerNsga2(Nsga2):
    def __init__(self, npop, max_iterations):
        super().__init__(npop, max_iterations)
        self.nagentes = 0
        self.resolution = 0
        self.nsujeira = 0
        self.nlixeira = 0
        self.ncarga = 0
        self._evaluator = None

        self.componentes = Componentes('componentes.js')
        configuracao = json.load(open('configuracao.js'))
        self.mainlog = configuracao['mainlog']
        self.poplog = configuracao['poplog']

    @property
    def evaluator(self):
        return self._evaluator

    @evaluator.setter
    def evaluator(self, val):
        self._evaluator = val

    @staticmethod
    def draw(population, destino):
        arquivo = open(destino, 'w')
        for individual in population:
                individual.draw(arquivo)
        arquivo.close()

    def configurar(self, **args):
        for k in args.keys():
            valor = args[k]
            if k == 'agentes':
                self.nagentes = valor
            elif k == 'resolucao':
                self.resolution = valor
            elif k == 'sujeira':
                self.nsujeira = valor
            elif k == 'lixeira':
                self.nlixeira = valor
            elif k == 'carga':
                self.ncarga = valor
            elif k == 'crossover':
                self.crossover_prob = valor
            elif k == 'mutacao':
                self.mutation = valor
            else:
                print 'opção "%s" inválida' % (k)

    def generate_individual(self, resolution, nsujeira, nlixeira, ncarga, nagentes):
        chromossome = []
        chromossome.extend(1 for l in range(nsujeira))
        chromossome.extend(2 for l in range(nlixeira))
        chromossome.extend(3 for r in range(ncarga))
        chromossome.extend(4 for r in range(nagentes))
        nvazio = resolution ** 2 - len(chromossome)
        chromossome.extend(0 for i in range(nvazio))
        random.shuffle(chromossome)
        individual = VaccumCleanerSolution(SolutionType.MIN)
        individual.chromossome = chromossome
        individual.objectives = self.evaluator(individual.decode(self.componentes))
        return individual

    def salvar(self, destino):
        destino = open(destino,'w')

    def generate_initial_population(self, log=True):
        population = []
        for _ in range(self.npop):
            population.append(self.generate_individual(self.resolution, self.nsujeira, self.nlixeira, self.ncarga, self.nagentes))
        if log:
            VaccumCleanerNsga2.draw(population, 'inicial.txt')
        return population

    def generate_population(self, current_population, size):
        selected = [self.binary_tournament(current_population) for _ in range(size)]
        new_population = []
        for i in range(size - 1, -1, -1):
            #NOTE: refatore-me!!!!
            new_population.append(selected[i].reproduction(selected[i - 1], self.crossover_prob, self.mutation_prob, self.resolution, self.nsujeira, self.nlixeira, self.ncarga, self.nagentes))
        for individual in new_population:
            if individual.objectives == None:
                individual.objectives = self.evaluator(individual.decode(self.componentes))
        return new_population

    def binary_tournament(self, pop):
        a, b = random.sample(range(len(pop)), 2)
        # TODO: should exists another rule for tiebreak?
        return pop[a] if pop[a].fitness >= pop[b].fitness else pop[b]
