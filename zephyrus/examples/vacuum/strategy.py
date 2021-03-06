import enum
import json
import logging
import random
from itertools import islice

from zephyrus.components import ComponentSet
from zephyrus.exceptions import ZephyrusException
from zephyrus.message import Message
from zephyrus.strategy import Strategy, Objectives, Evaluator
from zephyrus.strategy.nsga2 import Nsga2, Solution
from zephyrus.strategy.utils import SolutionType


class Gene(enum.Enum):
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
        clone.objectives = self.objectives.copy()
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
            if gene == Gene.TRASH.value:
                value = components.TRASH.value
            elif gene == Gene.BIN.value:
                value = components.BIN.value
            elif gene == Gene.RECHARGE.value:
                value = components.RECHARGE.value
            elif gene == Gene.AG.value:
                value = components.AG.value
            elif gene != 0:
                raise ZephyrusException("Decode error: unknown value {}".format(gene))
            decoded.append(value)
        return decoded

    def reproduction(self, other, crossover_rate, mutation_rate, n_trash, n_bin, n_recharge, n_ag):
        new_individual = self.crossover(other, crossover_rate, n_trash, n_bin, n_recharge, n_ag)
        has_mutate = new_individual.mutation(mutation_rate)
        if has_mutate:
            new_individual.objectives = None
            new_individual.cloned = False
        return new_individual

    def crossover(self, other, crossover_rate, n_trash, n_bin, n_recharge, n_ag):
        if random.random() < crossover_rate:
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

    def mutation(self, mutation_rate):
        mutation_ocurred = False
        for i in range(len(self.chromossome)):
            if random.random() < mutation_rate:
                mutation_ocurred = True
                other = random.sample(range(len(self.chromossome)), 1)[0]
                # TODO: what if other == i?
                self.chromossome[i], self.chromossome[other] = self.chromossome[other], self.chromossome[i]
        return mutation_ocurred


class VaccumCleanerNsga2(Nsga2):
    def __init__(self):
        super().__init__(0, 0)
        self.n_ag = 0
        self.resolution = 0
        self.n_trash = 0
        self.n_bin = 0
        self.n_recharge = 0
        self._evaluator = None

    @property
    def evaluator(self):
        return self._evaluator

    @evaluator.setter
    def evaluator(self, val):
        self._evaluator = val

    @staticmethod
    def save_population_to_file(population, filename):
        with open(filename, 'w') as out:
            for individual in population:
                out.write(individual.draw())

    def configure(self, **kwargs):
        valid_options = set([
            'n_ag',
            'resolution',
            'n_trash',
            'n_bin',
            'n_recharge',
            'crossover_rate',
            'mutation_rate',
            'population_size',
            'max_iterations',
            'population_log',
            'main_log',
        ])
        for config, value in kwargs.items():
            if config not in valid_options:
                logging.warning('invalid config {}'.format('config'))
                continue
            setattr(self, config, value)

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
        individual.objectives = self.evaluator(individual)
        return individual

    def generate_initial_population(self, log=True):
        population = []
        for _ in range(self.population_size):
            population.append(self.generate_individual(self.resolution, self.n_trash, self.n_bin, self.n_recharge, self.n_ag))
        if log:
            # TODO: add initial config
            VaccumCleanerNsga2.save_population_to_file(population, 'inicial.log')
        return population

    def generate_population(self, current_population, size):
        selected = [self.binary_tournament(current_population) for _ in range(size)]
        new_population = []
        for i in range(size - 1, -1, -1):
            # NOTE: refatore-me!!!!
            new_population.append(selected[i].reproduction(selected[i - 1], self.crossover_rate, self.mutation_rate, self.n_trash, self.n_bin, self.n_recharge, self.n_ag))

        for individual in new_population:
            if individual.objectives is None:
                individual.objectives = self.evaluator(individual)
        return new_population

    def binary_tournament(self, pop):
        a, b = random.sample(range(len(pop)), 2)
        # TODO: should exists another rule for tiebreak?
        return pop[a] if pop[a].fitness >= pop[b].fitness else pop[b]


class VacuumStrategy(Strategy):
    def __init__(self, main_config, address_config, component_config):
        super().__init__(address_config, component_config)
        with open(main_config) as config:
            self.main_config = json.load(config)

    def build_nsga2_config(self):
        return {
            'n_ag': self.main_config['environment']['n_agent'],
            'resolution': self.main_config['environment']['resolution'],
            'n_trash': self.main_config['environment']['n_trash'],
            'n_bin': self.main_config['environment']['n_bin'],
            'n_recharge': self.main_config['environment']['n_recharge'],
            'crossover_rate': self.main_config['strategy']['crossover_rate'],
            'mutation_rate': self.main_config['strategy']['mutation_rate'],
            'population_size': self.main_config['strategy']['population_size'],
            'max_iterations': self.main_config['strategy']['n_generations'],
            'population_log': self.main_config['log']['population_log'],
            'main_log': self.main_config['log']['main_log']
        }

    def evaluator_callback(self, individual):
        #
        decoded = individual.decode(self.components)
        scenario = self.main_config['environment']['standard_scenario']
        content = {
            'id': None,
            'data': [(ComponentSet(d) + ComponentSet(s)).value for (d, s) in zip(decoded, scenario)]
        }
        msg = self.messenger.build_evaluate_message(content=content)
        self.socket_send.send_string(str(msg))
        ans = Message.from_string(self.socket_receive.recv_string())
        logging.debug('Received {}'.format(str(ans)))
        return Objectives(ans.content['data'])

    def configure(self, content):
        self.nevaluators = content.get('nevaluators', 1)

    def mainloop(self):
        nsga2 = VaccumCleanerNsga2()
        nsga2.configure(**self.build_nsga2_config())
        # FIXME: 1 does not necessarily means single...

        if self.main_config['simulation']['mode'] == 'CENTRALIZED':
            evaluator = None
            nsga2.evaluator = self.evaluator_callback
        else:
            evaluator = self.prepare_evaluator()
            nsga2.evaluator = evaluator.evaluate
        nsga2.main_loop()
        if evaluator is not None:
            notifier = evaluator.stop_consumer()
            notifier.wait()
        self.socket_send.send_string(str(self.messenger.build_stop_message()))
        msg = self.messenger.build_result_message(content={
            'value': 0,
            'solution': 0
        })
        logging.debug('Strategy: sending result {}'.format(str(msg)))
        self.socket_send.send_string(str(msg))

    def prepare_evaluator(self):
        config = {
            'socket_send': self.socket_send,
            'socket_receive': self.socket_receive,
            'messenger': self.messenger,
            'main_config': self.main_config,
            'components': self.components,
            'nworkers': self.nevaluators
        }
        evaluator = Evaluator(**config)
        evaluator.start_consumer()
        return evaluator


if __name__ == '__main__':
    import sys
    import os
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith("/") else os.path.join(basedir, s) for s in sys.argv[1:]]
    VacuumStrategy(*args).start()
