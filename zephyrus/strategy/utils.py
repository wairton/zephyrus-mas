from enum import Enum


class SolutionType(Enum):
    MIN = -1
    MAX = 1


class SolutionComparison(Enum):
    DOMINATES = 1
    IS_DOMINATED = -1
    NEITHER = 0


INFINITY = float('inf')


def manhattan_distance(p1, p2):
    return sum(abs(i1 - i2) for i1, i2 in zip(p1, p2))
