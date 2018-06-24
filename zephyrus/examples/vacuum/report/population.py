import re
from collections import defaultdict
import matplotlib.pyplot as plt


def load_population_log(filename):
    pattern = re.compile('^\d.+')
    iterations = defaultdict(list)
    with open(filename) as log:
        iteration = -1
        for line in log:
            if line.startswith('**'):
                iteration += 1
            if pattern.match(line):
               iterations[iteration].append(tuple(float(l) for l in line.split()))
    return iterations


def pli(iterations, steps, alpha=1.0):
    for step in steps:
        x, y = zip(*iterations[step])
        plt.scatter(x, y, label="{} Iterações".format(step), marker='.', alpha=alpha)
    plt.legend()
    plt.grid(True)
    plt.axis([15, 80, -2, 40])
    plt.xlabel('Objetivo 1')
    plt.ylabel('Objetivo 2')


def side_by_side3(iterations, alpha=.75):
    attrs = {
        # 'dpi': 200,
        # 'figsize': (8, 5)
    }
    plt.figure(1, **attrs)
    plt.subplot(321)
    pli(populations, [0, 100], alpha)
    plt.subplot(322)
    pli(populations, [100, 200], alpha)
    plt.subplot(323)
    pli(populations, [200, 300], alpha)
    plt.subplot(324)
    pli(populations, [300, 400], alpha)
    plt.subplot(325)
    pli(populations, [0, 400], alpha)
    plt.show()

if __name__ == '__main__':
    import sys
    populations = load_population_log(sys.argv[1])
    side_by_side3(populations)
