import json
import logging
import math
import random
from itertools import islice

from zephyrus.components import ComponentManager, ComponentEnum
from zephyrus.message import Message
from zephyrus.strategy import Strategy
from zephyrus.strategy.nsga2 import Nsga2, Solution
from zephyrus.strategy.utils import manhattan_distance



class Gene(Enum):
    TRASH = 1
    BIN = 2
    RECHARGE = 3
    AG = 4


class VacuumSolution(Solution):
    def __init__(self, solution_type, resolution):
        super().__init__(solution_type)
        self.chromossome = []
        self.cloned = False
        self.resolution = resolution

    def clone(self):
        clone = VacuumSolution(self.type, self.resolution)
        clone.chromossome = self.chromossome[:]
        clone.objectives = self.objectives[:]
        clone.type = self.type
        # clone.dominated = self.dominated[:]
        # clone.n_dominated = self.n_dominated
        clone.distance = self.distance
        clone.fitness = self.fitness
        clone.cloned = True
        return clone

    def draw(self):
        result = []
        pos = ['_', '*', 'u', '$', '@']
        resolution = self.resolution
        for i in range(resolution):
            for j in range(resolution):
                result.append(pos[self.chromossome[i * resolution + j]] + ' ')
            result.append('\n')
        result.append('\n')
        return ''.join(result)

    def __str__(self):
        return repr(self.chromossome)

    def decode(self, components):
        decoded = []
        for gene in self.chromossome:
            value = 0
            if gene == Gene.TRASH:
                value = components.TRASH.value
            elif gene == Gene.BIN:
                value = components.BIN.value
            elif gene == Gene.RECHARGE:
                value = components.RECHARGE.value
            elif gene == Gene.AG:
                value = components.AG.value
            else:
                raise ZephyrusException("Decode error: unknown value {}".format(gene))
            decoded.append(value)
        return decoded

    def evaluate(self):
        resolution = self.resolution
        gene_pos = zip(self.chromossome, [(i,j) for i in range(resolution) for j in range(resolution)])
        trash_items = filter(lambda k:k[0] == Gene.TRASH, gene_pos)
        bin_items = filter(lambda k:k[0] == Gene.BIN, gene_pos)
        recharge_items = filter(lambda k:k[0] == Gene.RECHARGE, gene_pos)
        bin_distance = 0
        recharge_distance = 0
        for gene, trash_pos in trash_items:
            min_distance = resolution ** 2
            #TODO: this could be done with some min(map()) magic
            for gene2, bin_pos in bin_items:
                distance = manhattan_distance(trash_pos, bin_pos)
                if distance < min_distance:
                    min_distance = distance
            bin_distance += min_distance
            #
            min_distance = resolution ** 2  # valor maior que o máximo
            for gene2, recharge_pos in recharge_items:
                distance = manhattan_distance(trash_pos, recharge_pos)
                if distance < min_distance:
                    min_distance = distance
            recharge_distance += min_distance
        self.objectives = (bin_distance, recharge_distance)

    def reproduction(self, other, crossover_prob, mutation_prob, n_trash, n_bin, n_recharge, n_ag):
        new_individual = self.crossover(other, crossover_prob, n_trash, n_bin, n_recharge, n_ag)
        has_mutate = new_individual.mutation(mutation_prob)
        if has_mutate:
            new_individual.objectives = None
            new_individual.cloned = False
        return new_individual

    def crossover(self, other, crossover_prob, n_trash, n_bin, n_recharge, n_ag):
        if random.random() < crossover_prob:
            new_individual = VacuumSolution(SolutionType.MIN, self.resolution)
            length = len(self.chromossome)
            crossover_point = length // 2
            new_individual.chromossome.extend(self.chromossome[:crossover_point])
            totals = (length - (n_trash + n_bin + n_recharge + n_ag), n_trash, n_bin, n_recharge, n_ag)
            positions = {i: 0 for i in range(5)}
            for gene in new_individual.chromossome:
                positions[gene] += 1
            for gene in islice(other.chromossome, crossover_point, None):
                if positions[gene] < totals[gene]:
                    new_individual.chromossome.append(gene)
                    positions[gene] += 1
            for gene in islice(other.chromossome, crossover_point):
                if len(new_individual.chromossome) == length:
                    break
                if positions[gene] < totals[gene]:
                    new_individual.chromossome.append(gene)
                    positions[gene] += 1
            return new_individual
        return self.clone()

    def mutation(self, mutation_prob):
        mutation_ocurred = False
        for i in range(len(self.chromossome)):
            if random.random() < mutation_prob:
                mutation_ocurred = True
                other = random.sample(range(len(self.chromossome)), 1)
                # TODO: what if other == i?
                self.chromossome[i], self.chromossome[other] = self.chromossome[other], self.chromossome[i]
        return mutation_ocurred


class VaccumCleanerNsga2(Nsga2):
    def __init__(self, npop, max_iterations, component_config):
        super().__init__(npop, max_iterations)
        self.n_ag = 0
        self.resolution = 0
        self.n_trash = 0
        self.n_bin = 0
        self.n_recharge = 0
        self._evaluator = None

        self.components = ComponentManager.get_component_enum(component_config)
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
                self.n_ag = valor
            elif k == 'resolucao':
                self.resolution = valor
            elif k == 'sujeira':
                self.n_trash = valor
            elif k == 'lixeira':
                self.n_bin = valor
            elif k == 'carga':
                self.n_recharge = valor
            elif k == 'crossover':
                self.crossover_prob = valor
            elif k == 'mutacao':
                self.mutation = valor
            else:
                print 'opção "%s" inválida' % (k)

    def generate_individual(self, resolution, n_trash, n_bin, n_recharge, n_ag):
        chromossome = []
        chromossome.extend(1 for l in range(n_trash))
        chromossome.extend(2 for l in range(n_bin))
        chromossome.extend(3 for r in range(n_recharge))
        chromossome.extend(4 for r in range(n_ag))
        nvazio = resolution ** 2 - len(chromossome)
        chromossome.extend(0 for i in range(nvazio))
        random.shuffle(chromossome)
        individual = VacuumSolution(SolutionType.MIN, self.resolution)
        individual.chromossome = chromossome
        individual.objectives = self.evaluator(individual.decode(self.components))
        return individual

    def salvar(self, destino):
        destino = open(destino,'w')

    def generate_initial_population(self, log=True):
        population = []
        for _ in range(self.npop):
            population.append(self.generate_individual(self.resolution, self.n_trash, self.n_bin, self.n_recharge, self.n_ag))
        if log:
            VaccumCleanerNsga2.draw(population, 'inicial.txt')
        return population

    def generate_population(self, current_population, size):
        selected = [self.binary_tournament(current_population) for _ in range(size)]
        new_population = []
        for i in range(size - 1, -1, -1):
            #NOTE: refatore-me!!!!
            new_population.append(selected[i].reproduction(selected[i - 1], self.crossover_prob, self.mutation_prob, self.n_trash, self.n_bin, self.n_recharge, self.n_ag))
        for individual in new_population:
            if individual.objectives == None:
                individual.objectives = self.evaluator(individual.decode(self.components))
        return new_population

    def binary_tournament(self, pop):
        a, b = random.sample(range(len(pop)), 2)
        # TODO: should exists another rule for tiebreak?
        return pop[a] if pop[a].fitness >= pop[b].fitness else pop[b]


class VacuumStrategy(Strategy):
    def configure(self, content):
        self.niter = content['niter']
        self.length = content['length']
        self.nevaluators = content.get('nevaluators', 1)

    def mainloop(self):
        if self.nevaluators == 1:
            self.mainloop_single()
        else:
            self.mainloop_dist()

    def mainloop_single(self):
        # TODO expecting configuration here?
        best_solution = None
        best_value = None
        for i in range(self.niter):
            logging.info("Strategy: progress {}/{}".format(i + 1, self.niter))
            solution = [random.random() for _ in range(self.length)]
            msg = self.messenger.build_evaluate_message(content=solution)
            self.socket_send.send_string(str(msg))
            ans = Message.from_string(self.socket_receive.recv_string())
            logging.debug('Received {}'.format(str(ans)))
            if ans.type == 'RESULT':
                if best_value is None or best_value > ans.content:
                    best_value = ans.content
                    best_solution = solution
            elif ans.type == 'STOP':
                logging.info('Strategy: stopping.')
                break
        logging.debug('Strategy: best found {}'.format(best_value))
        logging.debug('Strategy: best solution {}'.format(best_solution))
        self.socket_send.send_string(str(self.messenger.build_stop_message()))
        msg = self.messenger.build_result_message(content={
            'value': best_value,
            'solution': best_solution
        })
        logging.debug('Strategy: sending result {}'.format(str(msg)))
        self.socket_send.send_string(str(msg))

    def mainloop_dist(self):
        # TODO expecting configuration here?
        best_solution = None
        best_value = None

        poller = zmq.Poller()
        poller.register(self.socket_receive)
        navailable = self.nevaluators
        nwaiting = 0
        tsent = 0
        trecv = 0
        while trecv < self.niter:
            while navailable > 0 and tsent < self.niter:
                logging.info("Strategy: progress {}/{}".format(i + 1, self.niter))
                solution = [random.random() for _ in range(self.length)]
                msg = self.messenger.build_evaluate_message(content=solution)
                self.socket_send.send_string(str(msg))
                navailable -= 1
                nwaiting += 1
            failed = False
            while not failed and nwaiting > 0:
                # TODO adjust timeout value
                result = poller.poll(25)
                if self.socket_receive in result:
                    answer = Message.from_string(self.socket_receive.recv_string())
                    logging.debug('Received {}'.format(str(answer)))
                    if answer.type == 'RESULT':
                        if best_value is None or best_value > answer.content:
                            best_value = answer.content
                            best_solution = solution
                        nwaiting -= 1
                        trecv += 1
                        navailable += 1
                    if answer.type == 'STOP':
                        logging.error('Strategy: stopping.')
                        # TODO fix this,
                else:
                    failed = True
        logging.debug('Strategy: best found {}'.format(best_value))
        logging.debug('Strategy: best solution {}'.format(best_solution))
        self.socket_send.send_string(str(self.messenger.build_stop_message()))
        msg = self.messenger.build_result_message(content={
            'value': best_value,
            'solution': best_solution
        })
        logging.debug('Strategy: sending result {}'.format(str(msg)))
        self.socket_send.send_string(str(msg))
        poller.unregister(self.socket_receive)


if __name__ == '__main__':
    import sys
    import os
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith("/") else os.path.join(basedir, s) for s in sys.argv[1:]]
    VacuumStrategy(*args).start()
