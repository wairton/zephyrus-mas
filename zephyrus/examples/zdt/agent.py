import logging
import sys
from itertools import islice
from math import sqrt

from zephyrus.agent import Agent
from zephyrus.message import Message


class ZDTAgent(Agent):
    def mainloop(self):
        start_message = Message(self.alias, message_type="START", receiver="mediator")
        self.socket_send.send_string(str(start_message))
        #
        perceive_message = Message(self.alias, message_type="PERCEIVE", receiver="environment")
        self.socket_send.send_string(str(perceive_message))
        msg = Message.from_string(self.socket_receive.recv_string())
        action = self.perceive(msg.content)
        self.socket_send.send_string(str(action))
        #
        stop_message = Message(self.alias, message_type="STOP", receiver="mediator")
        self.socket_send.send_string(str(stop_message))

    def act(self, perceived):
        f1 = perceived[0]
        g = 1 + 9 * sum(islice(perceived, 1, None)) / (len(perceived) - 1)
        zdt = 1 - sqrt(f1 / g)
        return Message(self.alias, message_type="RESULT", receiver="environment", content=zdt)

    def perceive(self, perceived_data):
        return super().perceive(perceived_data)

    def configure(self, config_data):
        pass


if __name__ == '__main__':
    import sys
    ZDTAgent(1, *sys.argv[1:]).start()
