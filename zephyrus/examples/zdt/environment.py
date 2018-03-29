import logging

from zephyrus.environment import Environment
from zephyrus.message import Message


class ZDTEnvironment(Environment):
    def mainloop(self):
        logging.debug("mainloop {}".format(self.places))
        # self.socket_send.send("environment", "REQUEST", self.places)
        # msg = self.socket_receive.recv()

    def configure(self, content):
        self.places = content

if __name__ == '__main__':
    import sys
    import os
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith("/") else os.path.join(basedir, s) for s in sys.argv[1:]]
    ZDTEnvironment(*args).start()
