import logging

from zephyrus.components import ComponentSet
from zephyrus.environment import Environment
from zephyrus.exceptions import ZephyrusException
from zephyrus.message import Message, Messenger


class EnvironmentMessenger(Messenger):
    basic_messages = ['CONFIRM', 'REJECT']


class VaccumEnvironment(Environment):
    messenger_class = EnvironmentMessenger

    def reset_memory(self):
        self.places = []
        self.agent_positions = {}

    def mainloop(self):
        while True:
            msg = Message.from_string(self.socket_receive.recv_string())
            logging.debug('Environment: received {}'.format(msg))
            if msg.type == 'PERCEIVE':
                reply = self.handle_perceive_action(msg.sender)
            elif msg.type == 'MOVE':
                reply = self.handle_move_action(msg.sender, msg.content)
            elif msg.type == 'CLEAN':
                reply = self.handle_clean_action(msg.sender)
            elif msg.type == 'RECHARGE':
                reply = self.handle_recharge_action(msg.sender)
            elif msg.type == 'DEPOSIT':
                reply = self.handle_deposit_action(msg.sender)
            elif msg.type == 'STOP':
                reply = self.handle_stop_action(msg.sender)
                if len(self.agent_positions) == 0:
                    # TODO
                    break
                # TODO: como o ambiente para?
            else:
                logging.error("Environmnent: received an invalid message '{}'".format(msg))
            logging.debug('Environment: answered {}'.format(reply))
            self.socket_send.send_string(str(reply))

    def configure(self, content):
        self.places = []
        self.agent_positions = {}
        initial = content['initial']
        scenario = content['scenario']
        agents = content['agents']
        if len(agents) > 1:
            logging.error("Environment: More than one agent found, this feature isn't implemented yet!")
        nrows = len(initial)
        ncols = len(initial[0])
        for i in range(nrows):
            row = []
            for j in range(ncols):
                row.append(ComponentSet(initial[i][j]) + ComponentSet(scenario[i][j]))
                # FIXME: This DOESN'T work for multiple agents!!!
                if self.components.AG in row[-1]:
                    self.agent_positions[agents[0]] = (i, j)
            self.places.append(row)

    def add_agent(self, agid, x, y):
        if 0 > x or len(self.places) <= x or 0 > y or len(self.places[0]) <= y:
            msg = "Environment: Trying to add an agent at an invalid position ({})".format((x, y))
            logging.error(msg)
            raise ZephyrusException(msg)
        logging.debug("Environment: Added {} at ({})".format(agid, (x, y)))
        self.agent_positions[agid] = (x, y)
        self.places[x][y] += self.components.AG

    def handle_move_action(self, agid, direction):
        if agid not in self.agent_positions.keys():
            # TODO: exception and log
            raise ZephyrusException()
        x, y = self.agent_positions[agid]
        if direction == 0:
            if self.components.WALLN in self.places[x][y] or self.components.AG in self.places[x - 1][y]:
                return self.reject_message(agid)
            self.agent_positions[agid] = x - 1, y
            self.places[x - 1][y] += self.components.AG
        elif direction == 1:
            if self.components.WALLE in self.places[x][y] or self.components.AG in self.places[x][y + 1]:
                return self.reject_message(agid)
            self.agent_positions[agid] = x, y + 1
            self.places[x][y + 1] += self.components.AG
        elif direction == 2:
            if self.components.WALLS in self.places[x][y] or self.components.AG in self.places[x + 1][y]:
                return self.reject_message(agid)
            self.agent_positions[agid] = x + 1, y
            self.places[x + 1][y] += self.components.AG
        elif direction == 3:
            if self.components.WALLW in self.places[x][y] or self.components.AG in self.places[x][y - 1]:
                return self.reject_message(agid)
            self.agent_positions[agid] = x, y - 1
            self.places[x][y - 1] += self.components.AG
        self.places[x][y] -= self.components.AG
        return self.confirm_message(agid)

    def handle_clean_action(self, agid):
        x, y = self.agent_positions[agid]
        if self.components.TRASH in self.places[x][y]:
            self.places[x][y] -= self.components.TRASH
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_perceive_action(self, agid):
        x, y = self.agent_positions[agid]
        return self.confirm_message(agid, self.places[x][y])

    def handle_recharge_action(self, agid):
        x, y = self.agent_positions[agid]
        if self.components.RECHARGE in self.places[x][y]:
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_deposit_action(self, agid):
        x, y = self.agent_positions[agid]
        if self.components.BIN in self.places[x][y]:
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_stop_action(self, agid):
        del self.agent_positions[agid]
        return self.confirm_message(agid)

    def confirm_message(self, agid, content=None):
        return self.messenger.build_confirm_message(receiver=agid, content=content)

    def reject_message(self, agid, content=None):
        return self.messenger.build_reject_message(receiver=agid, content=content)

    def draw(self):
        ret = []
        for place_row in self.places:
            for place in place_row:
                if self.components.AG in place:
                    ret.append('a')
                else:
                    ret.append('_')
                #
                if self.components.BIN in place:
                    ret.append('u')
                elif self.components.TRASH in place:
                    ret.append('*')
                elif self.components.RECHARGE in place:
                    ret.append('$')
                else:
                    ret.append('_')
            ret.append('\n')
        ret.append('\n')
        return ''.join(ret)

    def draw_to_file(self, filename, mode):
        with open(filename, mode) as log:
            log.write(self.draw())
