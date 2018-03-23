import sys
from itertools import islice
from math import sqrt

from zephyrus.agent import Agent
from zephyrus.message import Message


class ZDTAgent(Agent):
    def mainloop(self):
        msg = Message.from_string(self.socket_receive.recv_string())
        action = self.perceive(msg.content)
        self.socket_send.send_string(str(action))

    def act(self, perceived):
        f1 = perceived[0]
        g = 1 + 9 * sum(islice(perceived, 1, None)) / (len(perceived) - 1)
        zdt = 1 - sqrt(f1 / g)
        return Message("agent", "RESULT", zdt)

    def perceive(self, perceived_data):
        return super().perceive(perceived_data)


if __name__ == '__main__':
    ZDTAgent(1, *sys.argv[1:]).start()