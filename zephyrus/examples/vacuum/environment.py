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
                acao = self.handle_perceive_action(msg.sender)
            elif msg.type == 'MOVE':
                acao = self(msg.sender, msg.content)
            elif msg.type == 'CLEAN':
                acao = self.handle_clean_action(msg.sender)
            elif msg.type == 'RECHARGE':
                acao = self.rhandle_recharge_action(msg.sender)
            elif msg.type == 'DEPOSIT':
                acao = self.handle_deposit_action(msg.sender)
            elif msg.type == 'STOP':
                acao = self.handle_stop_action(msg.sender)
                if len(self.posAgentes) == 0:
                    msg = "%s %s %s" % (self.id, agid, acao)
                    # print 'ambiente enviou %s' % (msg), time.time()
                    self.socket_send.send(msg)
                    msg = "%s %s %s" % (self.id, -1, "# ## ")
                    self.socket_send.send(msg)
                    self.reiniciarMemoria()
                    break
                # TODO: como o ambiente para?
            else:
                logging.error("Environmnent: received an invalid message '{}'".format(msg))
            msg = "%s %s %s" % (self.id, agid, acao)
            # print 'ambiente enviou %s' % (msg), time.time()
            self.socket_send.send(msg)

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
            self.estrutura.append(novaEstrutura[de:ate])
        self.nlinhas, self.ncolunas = nlinhas, ncolunas

    def adicionarAgente(self, idAgente, x, y):
        # TODO: checar se a posicao do agente é válida
        # print 'AMBIENTE: adicionado agente %s em %s %s' % (idAgente, x, y)
        # print self.estrutura
        self.posAgentes[idAgente] = (x, y)
        self.estrutura[x][y] = self.componentes.adicionarVarios(['AG03', 'AG'], self.estrutura[x][y])

    def handle_move_action(self, iden, direcao):
        if direcao < 0 or direcao > 3:
            # TODO: notificar passagem de valor inválido.
            pass
        else:
            # não considera o caso em que o agente sai dos limites...
            x, y = None, None
            if iden in self.posAgentes.keys():
                x, y = self.posAgentes[iden]
            # print 'em', x, y
            if direcao == 0:
                # print 'para cima'
                if self.componentes.checar('PAREDEN', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x - 1][y]):
                    return "colidiu"
                self.posAgentes[iden] = x - 1, y
                self.estrutura[x - 1][y] = self.componentes.adicionar('AG', self.estrutura[x - 1][y])
            elif direcao == 1:
                # print 'para direita'
                if self.componentes.checar('PAREDEL', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x][y + 1]):
                    return "colidiu"
                self.posAgentes[iden] = x, y + 1
                self.estrutura[x][y + 1] = self.componentes.adicionar('AG', self.estrutura[x][y + 1])
            elif direcao == 2:
                # print 'para baixo'
                if self.componentes.checar('PAREDES', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x + 1][y]):
                    return "colidiu"
                self.posAgentes[iden] = x + 1, y
                self.estrutura[x + 1][y] = self.componentes.adicionar('AG', self.estrutura[x + 1][y])
            elif direcao == 3:
                # print 'para esquerda'
                if self.componentes.checar('PAREDEO', self.estrutura[x][y]) or self.componentes.checar('AG', self.estrutura[x][y - 1]):
                    return "colidiu"
                self.posAgentes[iden] = x, y - 1
                self.estrutura[x][y - 1] = self.componentes.adicionar('AG', self.estrutura[x][y - 1])

            self.estrutura[x][y] = self.componentes.remover('AG', self.estrutura[x][y])
            return "moveu"

    def handle_clean_action(self, agid):
        x, y = self.posAgentes[iden]
        if self.componentes.checar('LIXO', self.estrutura[x][y]):
            self.estrutura[x][y] = self.componentes.remover('LIXO', self.estrutura[x][y])
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_perceive_action(self, agid):
        x, y = self.posAgentes[iden]
        return self.confirm_message(agid, self.estrutura[x][y])

    def handle_recharge_action(self, agid):
        x, y = self.posAgentes[agid]
        if self.componentes.checar('RECARGA', self.estrutura[x][y]):
            return self.confirm_message(agid)
        return self.reject_message(agid)

    def handle_deposit_action(self, agid):
        x, y = self.posAgentes[agid]
        if self.componentes.checar('LIXEIRA', self.estrutura[x][y]):
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
        for linha in self.estrutura:
            for item in linha:
                info = filter(lambda k: self.componentes.checar(k, item), ['LIXEIRA', 'LIXO', 'RECARGA', 'AG'])
                if 'AG' in info:
                    ret.append('a')
                else:
                    ret.append('_')
                if 'LIXEIRA' in info:
                    ret.append('u')
                elif 'LIXO' in info:
                    ret.append('*')
                elif 'RECARGA' in info:
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
