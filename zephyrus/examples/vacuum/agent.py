import enum
import logging
import sys
import time
from collections import deque
from itertools import islice
from random import choice

from zephyrus.agent import Agent
from zephyrus.components import ComponentSet
from zephyrus.exceptions import ZephyrusException
from zephyrus.message import Message, Messenger


class AgentMessenger(Messenger):
    basic_messages = ['perceive', 'clean', 'recharge', 'stop', 'move', 'deposit']


class Plan(enum.Enum):
    NONE = 0
    CLEAN = 1
    DEPOSIT = 2
    EXPLORE = 3
    RECHARGE = 4


class Movement(enum.Enum):
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4


class VacuumAgent(Agent):
    messenger_class = AgentMessenger

    def __init__(self, ag_id, address_config, component_config):
        super().__init__(ag_id, address_config, component_config)
        self.id = ag_id
        # communication
        # internal state
        self.WALLS = c.WALLN + c.WALLE + c.WALLS + c.WALLE
        self.DELTA_POS = ((-1, 0), (0, 1), (1, 0), (0, -1))
        self.MAX_ENERGY = 80.0
        self.RECHARGE_THRESHOLD = 0.25
        self.DEPOSIT_CAPACITY = 4
        self.reset_memory()
        # TODO should this be moved to base class?
        self.messenger.default_receiver = "environment"

    def reset_memory(self):
        self.visited = set()
        self.wall_map = {}
        self.non_visited = set()
        self.trash_bins = set()
        self.recharge_points = set()
        self.trash_points = set()
        self.movements = []

        self.x, self.y = 0, 0
        self.px, self.py = 0, 0
        self.energy = self.MAX_ENERGY
        self.deposit = 0
        self.plan = Plan.NONE
        # used during recharge plan
        self.nrecharge_points = 0
        # recover movement in case of failure
        self.movement_recover = 0

    def perceive(self, perceived_data):
        return self.act(ComponentSet(perceived_data))

    def mainloop(self):
        self.reset_memory()
        while True:
            self.socket_send.send_string(str(self.messenger.build_perceive_action()))
            action = self.perceive(self.perceived_data)
            # TODO: handle stop!
            self.socket_send.send_string(str(action))
            feedback = Message.from_string(self.socket_receive.recv_string())
            if feedback.type == 'CONFIRM':
                if action.type == 'MOVE':
                    self.mover()
                elif action.type == 'CLEAN':
                    self.limpar()
                elif action.type == 'RECHARGE':
                    self.carregar()
                elif action.type == 'DEPOSIT':
                    self.depositar()
            elif feedback.type == 'REJECT' and action.type == 'MOVE':
                self.colidir()
            else:
                pass
                # TODO: log invalid message?

    def act(self, perceived: ComponentSet):
        self.memorize(perceived)
        if self.energy <= 0:
            return self.messenger.build_stop_message()
        if self.plan != Plan.NONE:
            if self.plan == Plan.EXPLORE:
                if len(self.movements) == 0:
                    raise ZephyrusException('Unable to follow EXPLORE Plan: No movements left')
                self.movement_recover = self.movements.pop(0)
                self.px, self.py = self.DELTA_POS[self.movement_recover]
                if len(self.movements) == 0:
                    self.plan = Plan.NONE
                return self.messenger.build_move_message(content=self.movement_recover)
            elif self.plan == Plan.DEPOSIT:
                if len(self.movements) > 0:
                    self.movement_recover = self.movements.pop(0)
                    self.px, self.py = self.DELTA_POS[self.movement_recover]
                    self.energy -= 1
                    return self.messenger.build_move_message(content=self.movement_recover)
                else:
                    self.plan = Plan.NONE
                    return self.messenger.build_deposit_message()
            elif self.plan == Plan.RECHARGE:
                if len(self.movements) > 0:
                    self.movement_recover = self.movements.pop(0)
                    self.px, self.py = self.DELTA_POS[self.movement_recover]
                    self.energy -= 1
                    return self.messenger.build_move_message(content=self.movement_recover)
                else:
                    self.nrecharge_points -= 1
                    if self.nrecharge_points == 0:
                        self.plan = Plan.NONE
                    return self.messenger.build_recharge_message()
            elif self.plan == Plan.CLEAN:
                if len(self.movements) > 0:
                    self.movement_recover = self.movements.pop(0)
                    self.px, self.py = self.DELTA_POS[self.movement_recover]
                    self.energy -= 1
                    return self.messenger.build_move_message(content=self.movement_recover)
                else:
                    self.plan = Plan.NONE
                    return self.messenger.build_clean_message()
            else:
                raise ZephyrusException("Unknown Plan")
        elif (self.energy / self.MAX_ENERGY) < self.RECHARGE_THRESHOLD:
            return self.devise_recharge_plan(perceived)
        elif self.deposit == self.DEPOSIT_CAPACITY:
            return self.devise_deposit_plan(perceived)
        elif self.components.TRASH in perceived:
            # consumes energy regardless
            self.energy -= 3
            return self.messenger.build_clean_message()
        return self.choose_direction(self.get_perceived_wall_info(perceived))


    def get_perceived_wall_info(self, perceived: ComponentSet) -> ComponentSet:
        return self.WALLS & perceived

    def memorize(self, perceived: ComponentSet):
        if (self.x, self.y) in self.non_visited:
            self.non_visited.remove((self.x, self.y))
        self.wall_map[(self.x, self.y)] = self.get_perceived_wall_info(perceived)
        if self.components.WALLN not in perceived:
            if ((self.x - 1, self.y) not in self.visited) and ((self.x - 1, self.y) not in self.non_visited):
                self.non_visited.add((self.x - 1, self.y))
        if self.components.WALLE not in perceived:
            if ((self.x, self.y + 1) not in self.visited) and ((self.x, self.y + 1) not in self.non_visited):
                self.non_visited.add((self.x, self.y + 1))
        if self.components.WALLS not in perceived:
            if ((self.x + 1, self.y) not in self.visited) and ((self.x + 1, self.y) not in self.non_visited):
                self.non_visited.add((self.x + 1, self.y))
        if self.components.WALLW not in perceived:
            if ((self.x, self.y - 1) not in self.visited) and ((self.x, self.y - 1) not in self.non_visited):
                self.non_visited.add((self.x, self.y - 1))
        if self.components.TRASH in perceived:
            self.trash_points.add((self.x, self.y))
        if self.components.BIN in perceived:
            self.trash_bins.add((self.x, self.y))
        if self.components.RECHARGE in perceived:
            self.recharge_points.add((self.x, self.y))

    def choose_direction(self, walls: ComponentSet):
        has_places_to_explore = len(self.non_visited) > 0 or len(self.trash_points) > 0
        if walls == self.WALLS or not has_places_to_explore:
            return self.messenger.build_stop_message()
        x, y = self.x, self.y
        non_visited = []
        if self.components.WALLN not in walls and (x - 1, y) not in self.visited:
            non_visited.append((Movement.UP, (-1, 0)))
        elif self.components.WALLE not in walls and (x, y + 1) not in self.visited:
            non_visited.append((Movement.RIGHT, (0, 1)))
        elif self.components.WALLS not in walls and (x + 1, y) not in self.visited:
            non_visited.append((Movement.DOWN, (1, 0)))
        elif self.components.WALLW not in walls and (x, y - 1) not in self.visited:
            non_visited.append((Movement.LEFT, (0, -1)))
        if len(non_visited) == 0:
            if len(self.non_visited) == 0:
                return self.devise_clean_plan()
            else:
                return self.devise_exploration_plan()
        chosen_movement, chosen_delta = choice(non_visited)
        # TODO I don't think thats the right place to decrease energy
        # maybe we should move this to after the action's confirmation
        self.energy -= 1
        self.px, self.py = chosen_delta
        self.movement_recover = chosen_movement
        # TODO: thanks to the mainloop refactor, we can now get rid of
        # movement_recover
        return self.messenger.build_move_message(content=self.movement_recover)

    def devise_recharge_plan(self, perceived: ComponentSet):
        if len(self.recharge_points) == 0:
            return self.choose_direction(self.get_perceived_wall_info(perceived))

        self.plan = Plan.RECHARGE
        self.nrecharge_points = int((self.MAX_ENERGY - self.energy) / 10)

        if self.components.RECHARGE in perceived:
            self.movements = []
            self.nrecharge_points -= 1
            return self.messenger.build_recharge_message()

        minx, maxx, miny, maxy = self.calculate_dimensions()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matrix = [[-1000 for i in range(sizey)] for i in range(sizex)]
        for x, y in self.visited:
            matrix[x - minx][y - miny] = 1000
        for x, y in self.recharge_points:
            matrix[x - minx][y - miny] = -1

        path = self.shortest_path(matrix, self.x, self.y, minx, maxx, miny, maxy)
        self.movements = self.path_to_movements(path)
        self.movement_recover = self.movements.pop(0)
        # TODO: this -1 shouldn't be here
        self.energy -= 1
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return self.messenger.build_move_message(content=self.movement_recover)

    def devise_deposit_plan(self, perceived: ComponentSet):
        if len(self.trash_bins) == 0:
            return self.choose_direction(self.get_perceived_wall_info(perceived))

        if self.components.DEPOSIT in perceived:
            self.movements = []
            self.plan = None
            return self.messenger.build_deposit_message()

        self.plan = Plan.DEPOSIT
        minx, maxx, miny, maxy = self.calculate_dimensions()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matrix = [[-1000 for i in range(sizey)] for i in range(sizex)]
        for x, y in self.visited:
            matrix[x - minx][y - miny] = 1000
        for x, y in self.trash_bins:
            matrix[x - minx][y - miny] = -1

        path = self.shortest_path(matrix, self.x, self.y, minx, maxx, miny, maxy)
        self.movements = self.path_to_movements(path)
        self.movement_recover = self.movements.pop(0)
        # energy -1 shouldn't be here
        self.energy -= 1
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return self.messenger.build_move_message(content=self.movement_recover)

    def devise_clean_plan(self):
        self.plan = Plan.CLEAN
        minx, maxx, miny, maxy = self.calculate_dimensions()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matrix = [[-1000 for i in range(sizey)] for i in range(sizex)]
        for x, y in self.visited:
            matrix[x-minx][y-miny] = 1000
        for x, y in self.trash_points:
            matrix[x - minx][y - miny] = -1

        path = self.shortest_path(matrix, self.x, self.y, minx, maxx, miny, maxy)
        self.movements = self.path_to_movements(path)
        self.movement_recover = self.movements.pop(0)
        # energy -1 shouldn't be here
        self.energy -= 1
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return self.messenger.build_move_message(content=self.movement_recover)

    def devise_exploration_plan(self):
        self.plan = Plan.EXPLORE
        minx, maxx, miny, maxy = self.calculate_dimensions()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matrix = [[-1 for i in range(sizey)] for i in range(sizex)]
        for x, y in self.visited:
            matrix[x-minx][y-miny] = 1000

        path = self.shortest_path(matrix, self.x, self.y, minx, maxx, miny, maxy)
        self.movements = self.path_to_movements(path)
        # energy -1 shouldn't be here
        self.energy -= 1
        self.movement_recover = self.movements.pop(0)
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return self.messenger.build_move_message(content=self.movement_recover)

    def calculate_dimensions(self):
        # TODO this code seems inneficient...
        visited = self.visited
        if len(self.non_visited) != 0:
            maxx = max(max(visited)[0], max(self.non_visited)[0])
            minx = min(min(visited)[0], min(self.non_visited)[0])
            maxy = max(max(visited, key=lambda k:k[1])[1], max(self.non_visited, key=lambda k:k[1])[1])
            miny = min(min(visited, key=lambda k:k[1])[1], min(self.non_visited, key=lambda k:k[1])[1])
        else:
            maxx = max(visited)[0]
            minx = min(visited)[0]
            maxy = max(visited, key=lambda k:k[1])[1]
            miny = min(visited, key=lambda k:k[1])[1]
        return minx, maxx, miny, maxy

    def shortest_path(self, matrix, px, py, minx, maxx, miny, maxy):
        queue = deque()
        path = []
        queue.append((px, py))
        matrix[px - minx][py - miny] =  0
        while len(queue) > 0:
            px, py = queue.popleft()
            weight = matrix[px - minx][py - miny]
            assert weight != -1
            directions = self._wall_components_to_directions((px, py), self.wall_map[(px, py)])
            for opx, opy in directions:
                tx = opx - minx
                ty = opy - miny
                if matrix[tx][ty] > weight + 1:
                    matrix[tx][ty] = weight + 1
                    queue.append((opx, opy))
                elif matrix[tx][ty] == -1:
                    path.append((opx, opy))
                    while weight >= 0:
                        if (tx + 1 <= maxx - minx) and matrix[tx + 1][ty] == weight: # Down
                            path.append((opx + 1, opy))
                            opx += 1
                            tx += 1
                        elif ty >= 1 and matrix[tx][ty - 1] == weight: # Left
                            path.append((opx, opy - 1))
                            opy -= 1
                            ty -= 1
                        elif tx >= 1 and matrix[tx - 1][ty] == weight: # Up
                            path.append((opx - 1, opy))
                            opx -= 1
                            tx -= 1
                        elif (ty + 1 <= maxy - miny) and matrix[tx][ty + 1] == weight: # Right
                            path.append((opx, opy + 1))
                            opy += 1
                            ty += 1
                        weight -= 1
                    return path[::-1]
        logging.error(self.info())
        raise ZephyrusException("Unable to find path")

    def _wall_components_to_directions(self, position, walls: ComponentSet):
        directions = []
        x, y = position
        if self.components.WALLN not in walls:
            directions.append((x - 1, y))
        if self.components.WALLE not in walls:
            directions.append((x, y + 1))
        if self.components.WALLS not in walls:
            directions.append((x + 1, y))
        if self.components.WALLW not in walls:
            directions.append((x, y - 1))
        return directions

    def path_to_movements(self, path):
        movements = []
        orix, oriy = path[0]
        for desx, desy in islice(path, 1, None):
            if orix != desx:
                if orix > desx:
                    movements.append(Movement.UP)
                else:
                    movements.append(Movement.DOWN)
            else:
                if oriy > desy:
                    movements.append(Movement.LEFT)
                else:
                    movements.append(Movement.RIGHT)
            orix, oriy = desx, desy
        return movements

    def limpar(self):
        #O agente executa a ação de limpar em sua posição atual.
        self.trash_points.discard((self.x, self.y))
        self.deposit += 1

    def carregar(self):
        self.energy += 10

    def depositar(self):
        self.energy -= 1
        self.deposit = 0

    def parar(self):
        #O agente permanece parado e apenas informa esse fato ao observador.
        self.info()
        while True:
            pass

    def mover(self):
        #movemento realizado com sucesso
        self.x += self.px
        self.y += self.py

    def colidir(self):
        logging.debug('colidi')
        self.energy -= 1
        if self.plan != None:
            self.movements.insert(0, self.movement_recover)

    def nop(self):
        pass

    def info(self):
        info = []
        separator = '*' * 10
        info.append(separator)
        info.append('Position: {} {}'.format(self.x, self.y))
        info.append('{} {} {}'.format(self.energy, self.deposit, self.plan))
        info.append('Visited: {}', self.visited)
        info.append('Non visited: {}'.format(self.non_visited))
        info.append('Trash bins: {}'.format(self.trash_bins))
        info.append('Recharge points: {}'.format(self.recharge_points))
        info.append('Trash_points: {}'.format(self.trash_points))
        info.append(separator)
        return '\n'.join(info)


if __name__ == '__main__':
    agente = VacuumAgent(1, *sys.argv[1:])
    agente.start()
