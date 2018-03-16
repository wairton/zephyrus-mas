import abc
from multiprocessing import Process

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager


class Environment(abc.ABC, Process):
    def __init__(self, mid, participants_config, components_config):
        super().__init__()
        # TODO: give a better name
        self.places = []
        self.posAgentes = {}
        self.id = mid
        self.participants = Participants(participants_config)
        self.components = ComponentManager(components_config).enum

    @abc.abstractmethod
    def run(self):
        pass

    def load_from_file(self, filename):
        with open(filename) as conf_file:
            for line in conf_file:
                self.places.append([int(i) for i in line.strip().split()])
        self.nlines, self.ncols = len(self.places), len(self.places[0])

    def load_from_array(self, array):
        self.places = []
        # NOTE: esse comando deveria ser aqui?
        self.posAgentes = {}
        array = array.split()
        self.nlines = nlines = int(array[0])
        self.ncols = ncols = int(array[1])
        for i in range(nlines):
            start, end = 2 + ncols * i, 2 + ncols * (i + 1)
            self.places.append([int(i) for i in array[start:end]])

    def __str__(self):
        return 'Environ: ' + ' '.join(self.places[:])

    def add_agent(self, agent_id, line, col):
        if not 0 <= line < self.nlines or 0 <= col < self.ncols:
            raise ValueError("Invalid line or col provided")
        self.agent_pos[agent_id] = (line, col)
        return len(self.agent_pos)
