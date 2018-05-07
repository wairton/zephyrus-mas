import zmq

from zephyrus.environment import Environment
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
                if len(self.posAgentes) == 0:
                    msg = "%s %s %s" % (self.id, agid, reply)
                    # print 'ambiente enviou %s' % (msg), time.time()
                    self.socket_send.send(msg)
                    msg = "%s %s %s" % (self.id, -1, "# ## ")
                    self.socket_send.send(msg)
                    self.reiniciarMemoria()
                    break
                # TODO: como o ambiente para?
            else:
                logging.error("Environmnent: received an invalid message '{}'".format(msg))
            logging.debug('Environment: answered {}'.format(reply))
            self.socket_send.send_string(str(reply))

    def load_from_file(self, filename):
        with open(filename) as conf_file:
            for line in conf_file:
                self.places.append([int(i) for i in line.strip().split()])
        self.nlines, self.ncols = len(self.places), len(self.places[0])

    def load_from_array(self, array):
        self.places = []
        # NOTE: esse comando deveria ser aqui?
        self.agent_positions = {}
        array = array.split()
        self.nlines = nlines = int(array[0])
        self.ncols = ncols = int(array[1])
        for i in range(nlines):
            start, end = 2 + ncols * i, 2 + ncols * (i + 1)
            self.places.append([int(i) for i in array[start:end]])

    def reconstruir(self, novaEstrutura, resolution):
        # turns a list into a matrix of resolution X resolution
        nlinhas = ncolunas = resolution
        for i in range(nlinhas):
            de, ate = ncolunas * i, ncolunas * (i + 1)
            self.places.append(novaEstrutura[de:ate])
        self.nlinhas, self.ncolunas = nlinhas, ncolunas

    def add_agent(self, agid, x, y):
        if 0 > x or len(self.places) <= x or 0 > y or len(self.places[0]) <= y:
            msg = "Environment: Trying to add an agent at an invalid position ({})".format((x, y))
            logging.error(msg)
            raise ZephyrusException(msg)
        loggin.debug("Environment: Added {} at ({})".format(agid, (x, y)))
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
        x, y = self.posAgentes[iden]
        if self.components.TRASH in self.places[x][y]:
            self.places[x][y] -= self.components.TRASH
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_perceive_action(self, agid):
        x, y = self.posAgentes[iden]
        return self.confirm_message(agid, self.places[x][y])

    def handle_recharge_action(self, agid):
        x, y = self.posAgentes[agid]
        if self.components.RECHARGE in self.places[x][y]:
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_deposit_action(self, agid):
        x, y = self.posAgentes[agid]
        if self.components.BIN in self.places[x][y]:
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_stop_action(self, agid):
        del self.posAgentes[agid]
        return self.confirm_message(agid)

    def confirm_message(agid, content=None):
        return self.messenger.build_confirm_message(receiver=agid, content=content)

    def reject_message(agid, content=None):
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
                ret.append(char)
            ret.append('\n')
        ret.append('\n')
        return ''.join(ret)

    def draw_to_file(self, filename, mode):
        with open(filename, mode) as log:
            log.write(self.draw())
