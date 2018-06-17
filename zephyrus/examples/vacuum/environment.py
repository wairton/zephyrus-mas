import logging

from zephyrus.components import ComponentSet
from zephyrus.environment import Environment
from zephyrus.exceptions import ZephyrusException
from zephyrus.message import Message, Messenger
from zephyrus.examples.vacuum.agent import Movement


class VaccumEnvironment(Environment):
    messenger_class = EnvironmentMessenger

    def reset_memory(self):
        self.places = []
        self.agent_positions = {}

    def mainloop(self):
        start_message = self.messenger.build_start_message(receiver='mediator')
        self.socket_send.send_string(str(start_message))
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
                    self.socket_send.send_string(str(reply))
                    stop_message = self.messenger.build_stop_message(receiver='mediator')
                    self.socket_send.send_string(str(stop_message))
                    break
            elif msg.type == 'CONFIG':
                # this handles the case where start arrives before config message
                self.configure(msg.content)
                continue
            else:
                logging.error("Environmnent: received an invalid message '{}'".format(msg))

            logging.debug('Environment: answered {}'.format(reply))
            self.socket_send.send_string(str(reply))

    def slice(self, bitch, resolution):
        result = []
        for i in range(resolution):
            result.append(bitch[i * resolution: (i + 1) * resolution])
        return result

    def configure(self, content):
        self.places = []
        self.agent_positions = {}
        resolution = content['resolution']
        initial = self.slice(content['initial'], resolution)
        scenario = self.slice(content['scenario']['data'], resolution)
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
        direction = Movement(direction)
        if agid not in self.agent_positions.keys():
            # TODO: exception and log
            raise ZephyrusException()
        x, y = self.agent_positions[agid]
        if direction == Movement.UP:
            if self.components.WALLN in self.places[x][y] or self.components.AG in self.places[x - 1][y]:
                return self.reject_message(agid)
            self.agent_positions[agid] = x - 1, y
            self.places[x - 1][y] += self.components.AG
        elif direction == Movement.RIGHT:
            if self.components.WALLE in self.places[x][y] or self.components.AG in self.places[x][y + 1]:
                return self.reject_message(agid)
            self.agent_positions[agid] = x, y + 1
            self.places[x][y + 1] += self.components.AG
        elif direction == Movement.DOWN:
            if self.components.WALLS in self.places[x][y] or self.components.AG in self.places[x + 1][y]:
                return self.reject_message(agid)
            self.agent_positions[agid] = x + 1, y
            self.places[x + 1][y] += self.components.AG
        elif direction == Movement.LEFT:
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
        return self.confirm_message(agid, self.places[x][y].value)

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


if __name__ == '__main__':
    import sys
    VaccumEnvironment(*sys.argv[1:]).start()
