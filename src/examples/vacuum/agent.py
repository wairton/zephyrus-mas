#!/usr/bin/python
#This work is under LGPL license, see the LICENSE.LGPL file for further details.

import enum
import logging
import sys
import time
from collections import deque
from multiprocessing import Process
from random import choice

import zmq

from core.components import ComponentManager, ComponentSet
from core.address import Participants
from core.exceptions import ZephyrusException
from core.message import Message


class AgentMessenger:
    def __init__(self, sender: str):
        self.sender = sender

    def build_clean_message(self):
        return Message(self.sender, "CLEAN")

    def build_recharge_message(self):
        return Message(self.sender, "RECHARGE")

    def build_move_message(self, destination):
        return Message(self.sender, "MOVE %s" % destination)

    def build_stop_messsage(self):
        return Message(self.sender, "STOP")


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


class AgentAction:
    def __init__(self, content):
        self.content = content


class VacuumAgent(Process):
    def __init__(self, ag_id, address_config, component_config):
        super(VacuumAgent, self).__init__()
        self.id = ag_id
        # communication
        self.messenger = AgentMessenger("agent <{}>".format(ag_id))
        participants = Participants(address_config)
        self.address = participants.address('agent')
        self.monitor_address = participants.address('monitor')
        self.socket_receive = None
        self.socket_send = None
        # internal state
        self.components = c = ComponentManager(component_config).enum
        self.WALLS = c.WALLN + c.WALLE + c.WALLS + c.WALLE
        self.DELTA_POS = ((-1, 0), (0, 1), (1, 0), (0, -1))
        self.MAX_ENERGY = 80.0
        self.RECHARGE_THRESHOLD = 0.25
        self.DEPOSIT_CAPACITY = 4
        self.reset_memory()

    def reset_memory(self):
        self.visited = set()
        self.wall_map = {}
        self.non_visited = set()
        self.trash_bins = []
        self.recharge_points = []
        self.trash_points = set()
        self.movements = []

        self.x, self.y = 0, 0
        self.px, self.py = 0, 0
        self.perceived_data = None
        self.send = True #True se agente deve enviar mensagem, False caso esteja esperando resposta
        self.is_acting = True #False para enviar ação de perceive
        self.energy = self.MAX_ENERGY
        self.deposit = 0
        self.plan = Plan.NONE
        self.nrecharge_points = 0 #usada durante a execução do plano de recarga
        self.movement_recover = 0 #armazena um movemento tentado para recuperá-lo em caso de falha.

    def perceive(self, perceived_data):
        return self.act(ComponentSet(perceived_data))

    def run(self):
        logging.debug('Agente rodando!!!')
        context = zmq.Context()
        self.socket_receive = context.socket(zmq.PULL)
        self.socket_receive.bind(self.address)
        self.socket_send = context.socket(zmq.PUSH)
        self.socket_send.connect(self.monitor_address)
        self.ready()

    def ready(self):
        logging.info("Agent %s is ready." % (self.id))
        while True:
            msg = self.socket_receive.recv()
            if msg == "@@@":
                self.mainloop()
            elif msg == "###":
                logging.info("Agente %s recebeu mensagem de finalização de atividades." % (self.id))
                break
            else:
                logging.warning("Agente %s recebeu mensagem inválida." % (self.id))

    def mainloop(self):
        self.reset_memory()
        self.send = True
        self.is_acting = False
        while True:
            if self.send:
                if self.is_acting == False:
                    self.socket_send.send("%s %s perceive" % (self.id, 0))
                    self.send = False
                else:
                    acao = self.perceive(self.perceived_data)
                    msg = "%s %s " % (self.id, 0)
                    #TODO: tratar o caso PARAR
                    self.socket_send.send(msg + acao)
                    self.send = False
            else:
                if self.is_acting == False:
                    msg = self.socket_receive.recv()
                    self.send = True
                    self.is_acting = True
                    self.perceived_data = int(msg.split()[2])
                else:
                    msg = self.socket_receive.recv() #apenas um feedback (ack)
                    retorno = msg.split()[-1]
                    if retorno == 'moveu':
                        self.mover()
                    elif retorno == 'limpou':
                        self.limpar()
                    elif retorno == 'recarregou':
                        self.carregar()
                    elif retorno == 'depositou':
                        self.depositar()
                    elif retorno == 'colidiu':
                        self.colidir()
                    elif retorno == 'parou':
                        break
                    elif retorno == 'nop':
                        self.nop()
                    else:
                        pass
                    self.send = True
                    self.is_acting = False


    def act(self, perceived: ComponentSet):
        self.memorize(perceived)
        if self.energy <= 0:
            return 'parar'
        if self.plan != Plan.NONE:
            if self.plan == Plan.EXPLORE:
                if len(self.movements) == 0:
                    raise ZephyrusException('Unable to follow EXPLORE Plan: No movements left')
                self.movement_recover = self.movements.pop(0)
                self.px, self.py = self.DELTA_POS[self.movement_recover]
                if len(self.movements) == 0:
                    self.plan = Plan.NONE
                return self.messenger.build_move_message(self.movement_recover)
            elif self.plan == Plan.DEPOSIT:
                if len(self.movements) > 0:
                    self.movement_recover = self.movements.pop(0)
                    self.px, self.py = self.DELTA_POS[self.movement_recover]
                    self.energy -= 1
                    return "mover %s" % self.movement_recover
                else:
                    self.plan = Plan.NONE
                    return "depositar"
            elif self.plan == Plan.RECHARGE:
                if len(self.movements) > 0:
                    self.movement_recover = self.movements.pop(0)
                    self.px, self.py = self.DELTA_POS[self.movement_recover]
                    self.energy -= 1
                    return "mover %s" % self.movement_recover
                else:
                    self.nrecharge_points -= 1
                    if self.nrecharge_points == 0:
                        self.plan = Plan.NONE
                    return "recarregar"
            elif self.plan == Plan.CLEAN:
                if len(self.movements) > 0:
                    self.movement_recover = self.movements.pop(0)
                    self.px, self.py = self.DELTA_POS[self.movement_recover]
                    self.energy -= 1
                    return "mover %s" % self.movement_recover
                else:
                    self.plan = Plan.NONE
                    return "limpar"
            else:
                raise ZephyrusException("plano desconhecido")
        elif (self.energy / self.MAX_ENERGY) < self.RECHARGE_THRESHOLD:
            return self.tracarPlanoRecarga(perceived)
        elif self.deposit == self.DEPOSIT_CAPACITY:
            return self.tracarPlanoDeposito(perceived)
        elif self.components.TRASH in perceived:
            self.energy -= 3 #consome energia independente de limpar ou não de verdade
            return  'limpar'
        else:
            return self.escolherDirecao(self.get_perceived_wall_info(perceived))

    def get_perceived_wall_info(self, perceived: ComponentSet) -> ComponentSet:
        return self.WALLS & perceived

    def memorize(self, perceived: ComponentSet):
        if (self.x, self.y) in self.non_visited:
            self.non_visited.remove((self.x,self.y))
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
        if self.components.BIN in perceived and not ((self.x, self.y) in self.trash_bins):
            self.trash_bins.append((self.x, self.y))
        if self.components.RECHARGE in perceived and not ((self.x, self.y) in self.recharge_points):
            self.recharge_points.append((self.x, self.y))

    #TODO: a checagem de colisão no ambiente NÃO funciona para colisão com paredes
    def escolherDirecao(self, paredes: ComponentSet):
        available_directions = []
        for i, parede in enumerate(paredes):
            if not parede:
                available_directions.append(i)

        if len(available_directions) == 0:
            return 'parar'

        if len(self.non_visited) == 0 and len(self.trash_points) == 0:
            return 'parar'

        nvisitados = []
        for direcao in direcoes:
            if direcao == 0:
                if ((self.x - 1, self.y) not in self.visited):
                    nvisitados.append((0, (-1, 0)))
            elif direcao == 1:
                if ((self.x, self.y+1) not in self.visited):
                    nvisitados.append((1, (0, 1)))
            elif direcao == 2:
                if ((self.x+1, self.y) not in self.visited):
                    nvisitados.append((2, (1, 0)))
            else:
                if ((self.x, self.y-1) not in self.visited):
                    nvisitados.append((3, (0, -1)))
        if len(nvisitados) == 0:
            if len(self.non_visited) == 0:
                return self.tracarPlanoSujeira()
            else:
                return self.tracarPlanoExploracao()
        chosen = choice(nvisitados)
        self.energy -= 1
        self.px, self.py = chosen[1]
        self.movement_recover = chosen[0]
        return 'mover %s' % self.movement_recover

    def tracarPlanoRecarga(self,st):
        if len(self.recharge_points) == 0:
            return self.escolherDirecao(st[:4])
        self.plan = Plan.RECHARGE
        self.nrecharge_points = int((self.MAX_ENERGY - self.energy)/10)

        if st[6] == True: #o agente já está em um ponto de recarga
            self.movements = []
            self.nrecharge_points -= 1
            return 'recarregar'

        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1000 for i in range(sizey)] for i in range(sizex)]

        for x, y in self.visited:
            matriz[x-minx][y-miny] = 1000

        for x,y in self.recharge_points:
            matriz[x - minx][y - miny] = -1
        caminho = self.shortest_path(matriz, (self.x, self.y),minx, maxx,miny, maxy)
        self.movements = self.caminhoParaMovimentos(caminho)
        self.movement_recover = self.movements.pop(0)
        self.energy -= 1
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return "mover %s" % self.movement_recover

    def tracarPlanoDeposito(self,st):
        if len(self.trash_bins) == 0:
            return self.escolherDirecao(st[:4])
        self.plan = Plan.DEPOSIT

        if st[5] == True: #o agente já está em um ponto de recarga
            self.movements = []
            self.plan = None
            return 'depositar'

        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1000 for i in range(sizey)] for i in range(sizex)]

        for x, y in self.visited:
            matriz[x-minx][y-miny] = 1000

        for x,y in self.trash_bins:
            matriz[x - minx][y - miny] = -1
        caminho = self.shortest_path(matriz, (self.x, self.y),minx, maxx, miny, maxy)
        self.movements = self.caminhoParaMovimentos(caminho)
        self.movement_recover = self.movements.pop(0)
        self.energy -= 1
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return "mover %s" % self.movement_recover

    def tracarPlanoSujeira(self):
        self.plan = Plan.CLEAN

        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1000 for i in range(sizey)] for i in range(sizex)]

        for x, y in self.visited:
            matriz[x-minx][y-miny] = 1000

        for x,y in self.trash_points:
            matriz[x - minx][y - miny] = -1
        caminho = self.shortest_path(matriz, (self.x, self.y),minx, maxx,miny, maxy)
        self.movements = self.caminhoParaMovimentos(caminho)
        self.movement_recover = self.movements.pop(0)
        self.energy -= 1
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return "mover %s" % self.movement_recover

    def tracarPlanoExploracao(self):
        self.plan = Plan.EXPLORE
        minx, maxx, miny, maxy = self.calcularDimensoes()
        sizex = maxx - minx + 1
        sizey = maxy - miny + 1
        matriz = [[-1 for i in range(sizey)] for i in range(sizex)]

        for x, y in self.visited:
            matriz[x-minx][y-miny] = 1000
        caminho = self.shortest_path(matriz, (self.x, self.y),minx, maxx,miny, maxy)
        self.movements = self.caminhoParaMovimentos(caminho)
        self.energy -= 1
        self.movement_recover = self.movements.pop(0)
        self.px, self.py = self.DELTA_POS[self.movement_recover]
        return "mover %s" % self.movement_recover

    def calcularDimensoes(self):
        visitados = self.visited
        if len(self.non_visited) != 0:
            maxx = max(max(visitados)[0], max(self.non_visited)[0])
            minx = min(min(visitados)[0], min(self.non_visited)[0])
            maxy = max(max(visitados, key=lambda k:k[1])[1], max(self.non_visited, key=lambda k:k[1])[1])
            miny = min(min(visitados, key=lambda k:k[1])[1], min(self.non_visited, key=lambda k:k[1])[1])
        else:
            maxx = max(visitados)[0]
            minx = min(visitados)[0]
            maxy = max(visitados, key=lambda k:k[1])[1]
            miny = min(visitados, key=lambda k:k[1])[1]

        return minx, maxx, miny, maxy

    def shortest_path(self, matriz, atual, minx, maxx, miny, maxy):
        queue = deque()
        caminho = []
        queue.append(atual)
        px, py = atual
        matriz[px-minx][py-miny] =  0
        peso = 0
        while len(queue) > 0:
            px, py = queue.popleft()
            weight = matriz[px - minx][py - miny]
            assert weight != -1
            direcoes = self._wall_components_to_directions((px, py), self.wall_map[(px, py)])
            for direcao in direcoes:
                opx, opy = direcao
                if matriz[opx - minx][opy - miny] > weight + 1:   #encontrou um caminho melhor (ou o primeiro caminho) até aquela posição.
                    matriz[opx - minx][opy - miny] = weight + 1
                    queue.append(direcao)
                elif matriz[opx - minx][opy - miny] == -1: #encontrou uma posição que ainda não foi visitada.
                    caminho.append((opx, opy))
                    while weight >= 0:
                        #Sul
                        if ((opx - minx + 1 <= maxx - minx) and (matriz[opx - minx + 1][opy - miny] == weight)):
                            caminho.append((opx + 1, opy))
                            opx += 1
                            weight -= 1
                            continue
                        #Oeste
                        if ((opy - miny - 1 >= 0) and (matriz[opx - minx][opy - 1 - miny] == weight)):
                            caminho.append((opx, opy - 1))
                            opy -= 1
                            weight -= 1
                            continue
                        #Norte
                        if (opx - minx - 1 >= 0) and (matriz[opx - minx - 1][opy - miny] == weight):
                            caminho.append((opx - 1, opy))
                            weight -= 1
                            opx -= 1
                            continue
                        if (opy - miny + 1 <= maxy - miny) and (matriz[opx - minx][opy + 1 - miny] == weight):
                            caminho.append((opx, opy + 1))
                            weight -= 1
                            opy += 1
                            continue
                    return caminho[::-1]
        logging.error(self.info())
        raise ZephyrusException("Unable to find path")

    #Método auxiliar que realiza a conversão de estados(paredes) para direções
    def _wall_components_to_directions(self, position, st: ComponentSet):
        directions = []
        x, y = position
        if self.components.WALLN not in st:
            ret.append((x - 1, y))
        if self.components.WALLE not in st:
            ret.append((x, y + 1))
        if self.components.WALLS not in st:
            ret.append((x + 1, y))
        if self.components.WALLW not in st:
            ret.append((x, y - 1))
        return directions

    def caminhoParaMovimentos (self, caminho):
        movementos = []
        orix, oriy = caminho[0]
        for i in range(1,len(caminho)):
            desx, desy = caminho[i]
            if orix != desx:
                if orix > desx:
                    movementos.append(0)
                else:
                    movementos.append(2)
            else:
                if oriy > desy:
                    movementos.append(3)
                else:
                    movementos.append(1)
            orix, oriy = desx, desy
        return movementos

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
