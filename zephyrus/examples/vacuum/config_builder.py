import sys

from zephyrus.components import ComponentManager
from zephyrus.script import ConfigSection, Parameter, AutoParameter, ConfigBuilder, DefaultSimulationSection


class LogSection(ConfigSection):
    parameters = [
        Parameter('main_log', 'Main log filename(str)', str),
        Parameter('population_log', 'Population log filename (str)', str),
        Parameter('final_population_log', 'Final population log (str)', str)
    ]


class StrategySection(ConfigSection):
    parameters = [
        Parameter('n_generations', 'Number of generations (int)', int),
        Parameter('population_size', 'Population size (int)', int),
        Parameter('crossover_rate', 'Crossover rate (float)', float),
        Parameter('muration_rate', 'Mutation rate (float)', float)
    ]


class StandardScenarioParameter(AutoParameter):
    def parser(self, parameters, _globals):
        resolution = parameters['resolution']
        enum = ComponentManager.get_component_enum(_globals['components_filename'])
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


class EnvironmentSection(ConfigSection):
    parameters = [
        Parameter('n_trash', 'Quantity of trash (int)', int),
        Parameter('n_bin', 'Quantity of trash bin (int)', int),
        Parameter('n_recharge', 'Quantity of recharge points (int)', int),
        Parameter('resolution', 'Enviroment resolution (n x n blocks) (int)', int),
        StandardScenarioParameter('standard_scenario')
    ]


class VaccumConfigBuilder(ConfigBuilder):
    sections = [
        LogSection('log'),
        EnvironmentSection('environment'),
        StrategySection('strategy'),
        DefaultSimulationSection('simulation')
    ]

    def __init__(self, components_filename):
        self.globals = {'components_filename': components_filename}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage config_builder.py component_config output_file")
        sys.exit(1)
    VaccumConfigBuilder(sys.argv[1]).generate_config_file(sys.argv[2])
