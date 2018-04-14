import logging
import sys
from itertools import islice
from math import sqrt

from zephyrus.agent import Agent
from zephyrus.message import Message


class ZDTAgent(Agent):
    def mainloop(self):
        while True:
            msg = Message.from_string(self.socket_receive.recv_string())
            logging.debug("Agent: received {}".format(str(msg)))
            if msg.type == 'STOP':
                action = Message("agent", message_type="STOP", receiver="mediator")
                self.socket_send.send_string(str(action))
                break
            else:
                action = self.perceive(msg.content)
                self.socket_send.send_string(str(action))

    def act(self, perceived):
        f1 = perceived[0]
        g = 1 + 9 * sum(islice(perceived, 1, None)) / (len(perceived) - 1)
        zdt = 1 - sqrt(f1 / g)
        return Message("agent", message_type="RESULT", receiver="environment", content=zdt)

    def perceive(self, perceived_data):
        return super().perceive(perceived_data)

    def configure(self, config_data):
        pass


if __name__ == '__main__':
    import sys
    import os
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith("/") else os.path.join(basedir, s) for s in sys.argv[1:]]
    ZDTAgent(1, *args).start()
