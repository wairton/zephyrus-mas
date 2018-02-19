import sys

from script import Script
from zephyrus.components import ComponentManager, ComponentSet


def create_default_scenario(resolution):
    enum = ComponentManager.get_component_enum('componentes.js')
    scenario = []
    scenario.append((enum.WALLN + enum.WALLW).value)
    scenario.extend(enum.WALLN.value for _ in range(resolution - 2))
    scenario.append((enum.WALLN + enum.WALLE).value)
    for _ in range(resolution - 2):
        scenario.append(enum.WALLW.value)
        scenario.extend([0] * (resolution - 2))
        scenario.append(enum.WALLE.value)
    scenario.append((enum.WALLS + enum.WALLW).value)
    scenario.extend(enum.WALLS.value for _ in range(resolution - 2))
    scenario.append((enum.WALLS + enum.WALLE).value)
    return ' '.join(map(str, scenario))


def make_activity():
    parameters = {}
    parameters["main_log"] = raw_input('log principal (str): ')
    parameters["population_log"] = raw_input('log população (str): ')
    parameters["final_popularion_log"] = raw_input('log população final (str): ')

    parameters["n_generations"] = int(raw_input('quantas gerações (int): '))
    parameters["population_size"] = int(raw_input('tamanho da população (int): '))
    parameters["crossover_rate"] = float(raw_input('taxa de crossover (float): '))
    parameters["mutation_rate"] = float(raw_input('taxa de mutação (float): '))

    parameters["n_trash"] = int(raw_input('quantidade de sujeira (int): '))
    parameters["n_bin"] = int(raw_input('pontos de depósito (int): '))
    parameters["n_recharge"] = int(raw_input('pontos de recarga (int): '))
    parameters["resolution"] = int(raw_input('resolução (int): '))
    parameters["standard_scenario"] = create_default_scenario(parameters["resolucao"])
    return parameters


# simulation.json
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'uso: criarRoteiro.py nomeRoteiro nActivities'
        sys.exit(1)
    r = Roteiro(sys.argv[1])
    for i in range(int(sys.argv[2])):
        r.add(make_activity())
    r.save()
    print 'roteiro criado: '
    r.listItems()
