import operator
import sys

from abc import ABC, abstractmethod

from zephyrus.strategy.utils import INFINITY, SolutionComparison, SolutionType


class Solution(ABC):
    def __init__(self, solution_type: SolutionType):
        self.chromossome = None
        self.objectives = None
        self.type = solution_type
        self.dominated_indices = []  # S set from article
        self.n_dominated = 0
        self.distance = 0.0  # used on crowding-distance
        self.fitness = None

    def compare(self, other_solution):
        comp_operator = operator.le if SolutionType.MIN else operator.ge
        res = sum(map(comp_operator, self.objectives, other_solution.objectives))
        if res == 0:
            return SolutionComparison.IS_DOMINATED
        elif res == len(self.objectives):
            return SolutionComparison.DOMINATES
        return SolutionComparison.NEITHER

    def __str__(self):
        return "Solution: type {}, objectives: {}, fitness: {}".format(
            self.type, self.objectives, self.fitness)

    @abstractmethod
    def clone(self):
        pass


class Nsga2(ABC):
    def __init__(self, population_size, max_iterations):
        self.crossover_rate = 0.0
        self.mutation_rate = 0.0
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.main_log = None
        self.population_log = None

    #retorna uma lista de fronts
    def fast_non_dominated_sort(self, population):
        fronts = []
        current_front = []
        for individual in population:
            individual.n_dominated = 0
            individual.dominated_indices = []
        for index_i, individual in enumerate(population):
            for index_o, other_individual in enumerate(population):
                if index_i == index_o:
                    continue
                comp = individual.compare(other_individual)
                if comp == SolutionComparison.DOMINATES:
                    individual.dominated_indices.append(index_o)
                elif comp == SolutionComparison.IS_DOMINATED:
                    individual.n_dominated += 1
            if individual.n_dominated == 0:
                individual.fitness = 1
                current_front.append(individual)

        fronts.append(current_front)
        i = 0
        while len(fronts[i]) > 0:
            fronteAnterior = fronts[i]
            fronteNovo = []
            for individual in fronteAnterior:
                for indice in individual.dominated_indices:
                    q = population[indice] #tentativa de reduzir o acesso a índices de listas
                    q.n_dominated -= 1
                    if q.n_dominated == 0:
                        q.fitness = i + 2
                        fronteNovo.append(q)
            i += 1
            fronts.append(fronteNovo)
        return fronts  #NOTE: retorna um fronte vazio também?

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

    @abstractmethod
    def generate_initial_population(self):
        pass

    @abstractmethod
    def generate_population(self):
        pass

    def store_population(self, pid, population):
        l = '*' * 40
        with open(self.population_log, 'a') as log:
            log.write("Interation {}\n".format(pid))
            log.write("{}\n".format(l))
            for individual in population:
                log.write(individual.draw())
                for objective in individual.objectives:
                    log.write(str(objective) + ' ')
                log.write('\n')

    #TODO: mudar o nome para unir populações?
    def gerarConjunto(self, pop1, pop2):
        extra = filter(lambda p:p.cloned==False, pop2)
        pop1.extend(extra)
        return pop1

    def main_loop(self):
        p = self.generate_initial_population()
        self.store_population(0, p)
        q = []
        i = 0
        while i < self.max_iterations:
            log = open(self.main_log, "a")
            log.write("\nGeração %s\n" % (i+1))
            log.close()
            print('\r{} of {}'.format(i + 1, self.max_iterations), end='')
            #r = list(set(p + q))
            r = self.gerarConjunto(p, q)
            frontes = self.fast_non_dominated_sort(r)
            p = []
            for fronte in frontes:
                self.crowdingDistanceAssignment(fronte)
                p.extend(fronte)
                if len(p) >= self.population_size:
                    break
            p = sorted(p, key = lambda el: el.distance, reverse = True)
            p = p[:self.population_size]
            q = self.generate_population(p, self.population_size)
            i += 1
            self.store_population(i, p)
        return p
