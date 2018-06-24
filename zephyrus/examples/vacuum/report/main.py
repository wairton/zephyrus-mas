import sys
from statistics import mean, stdev


values = []
for line in open(sys.argv[1]).readlines():
    if line.startswith('total'):
        values.append(float(line.split()[-1]))

print("Number of generations: {}".format(len(values)))
print("Min time: {} s".format(min(values)))
print("Max time: {} s".format(max(values)))
print("Total time: {} s".format(sum(values)))
print("Mean time: {} s".format(mean(values)))
print("Std deviation: {}".format(stdev(values)))
