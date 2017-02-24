import math
import random


class Crossover(object):
    def __init__(self, probability):
        self.probability = probability

    def execute(self, *solutions):
        # TODO: validate solutions, 2, with len of at least 3
        parent1, parent2 = solutions
        offspring1 = parent1[:]
        offspring2 = parent2[:]
        if random.random() <= self.probability:
            return self.foo(offspring1, offspring2)
        return offspring1, offspring2

    def foo(self, offspring1, offspring2):
        raise NotImplementedError


class OnePointCrossover(Crossover):
    def __init__(self, probability):
        super().__init__(probability)

    def foo(self, offspring1, offspring2):
        index = random.randint(1, len(offspring1) - 2)
        slice1, slice2 = offspring1[index:], offspring2[index:]
        offspring1[index:] = slice2
        offspring2[index:] = slice1
        return offspring1, offspring2


class KPointCrossover(Crossover):
    def __init__(self, probability, k):
        super().__init__(probability)
        self.k = k

    def _partitions(self, n, size):
        # TODO: size must be >= n
        parts = []
        while n > 1:
            current = random.randint(1, size - n + 1)
            parts.append(current)
            n -= 1
            size -= current
        parts.append(size)
        random.shuffle(parts)
        slices = []
        index = 0
        for part in parts:
            slices.append((index, index + part))
            index += part
        return slices

    def foo(self, offspring1, offspring2):
        slices = self._partitions(self.k + 1, len(offspring1))
        for i, current_slice in enumerate(slices):
            if i % 2 == 1:
                start, end = current_slice
                slice1 = offspring1[start:end]
                slice2 = offspring2[start:end]
                offspring2[start:end] = slice1
                offspring1[start:end] = slice2
        return offspring1, offspring2


class UniformCrossover(Crossover):
    def __init__(self,  probability, point_probability=0.5):
        super().__init__(probability)
        self.point_probability = point_probability

    def foo(self, offspring1, offspring2):
        for i in range(len(offspring1)):
            if random.random() <= self.point_probability:
                offspring1[i], offspring2[i] = offspring2[i], offspring1[i]
        return offspring1, offspring2


class SBXCrossover(Crossover):
    def __init__(self, probability, distribution_index):
        self.probability = probability
        self.distribution_index = distribution_index

    def execute(solutions):
        parent1, parent2 = solutions
        offspring1 = parent1[:]
        offspring2 = parent2[:]
        if random() <= self.probability:
            for i in range(len(offspring)):
                pass
        return offspring1, offspring2

def get_unbounder_beta_bar():
    pass

def get_bounded_beta_bar(x1, x2, x_lower, x_upper, di):
    beta = 1 + (2 / (x2 - x1)) * min((x1 - x_lower), (x_upper - x2))
    alpha = 2 - pow(beta, -(di + 1))
    u = random.random()
    if u <= 1 / alpha:
        return pow(alpha * u, 1 / (di + 1))
    return pow(1 / (2 - alpha * u), 1 / (di + 1))

def unbounded_crossover(x1, x2,  di):
    beta = 1 + (2 / (x2 - x1)) * min((x1 - x_lower), (x_upper - x2))
    alpha = 2 - pow(beta, -(di + 1))
    u = random.random()
    if u <= .5:
        beta_bar = pow(alpha * u, 1 / (di + 1))
    else:
        beta_bar = pow(1 / (2 - alpha * u), 1 / (di + 1))

    y1 = .5 * ((x1 + x2) - beta_bar * abs(x2 - x1))
    y2 = .5 * ((x1 + x2) + beta_bar * abs(x2 - x1))
    return y1, y2


def bounded_crossover(x1, x2, x_lower, x_upper, di):
    beta = 1 + (2 / (x2 - x1)) * min((x1 - x_lower), (x_upper - x2))
    alpha = 2 - pow(beta, -(di + 1))
    u = random.random()
    if u <= 1 / alpha:
        beta_bar = pow(alpha * u, 1 / (di + 1))
    else:
        beta_bar = pow(1 / (2 - alpha * u), 1 / (di + 1))

    y1 = 0.5 * ((x1 + x2) - beta_bar * abs(x2 - x1))
    y2 = 0.5 * ((x1 + x2) + beta_bar * abs(x2 - x1))
    return y1, y2



if __name__ == '__main__':
    solution1 = [1,2,3,4,5]
    solution2 = [5,6,7,8,9]
    crossover = OnePointCrossover(1)
    print(crossover.execute(solution1, solution2))
    crossover = UniformCrossover(1)
    print(crossover.execute(solution1, solution2))
    crossover = KPointCrossover(1, 3)
    print(crossover.execute(solution1, solution2))
    print(bounded_crossover(2, 2.4, 1, 4, 1))
    print(bounded_crossover(2, 2.4, 1, 4, 2))
    print(bounded_crossover(2, 2.4, 1, 4, 10))
    print(bounded_crossover(2, 2.4, 1, 4, 100))

