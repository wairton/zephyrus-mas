import logging

from zephyrus.environment import Environment
from zephyrus.message import Message


class ZDTEnvironment(Environment):
    def mainloop(self):
        msg = Message(
            'environment', receiver='agent', message_type='PERCEIVED', content=self.places)
        self.socket_send.send_string(str(msg))
        logging.debug('Environment: received {}'.format(self.socket_receive.recv_string()))
        logging.debug('Environment: agent, please stop')
        self.socket_send.send_string(
            str(Message('environment', message_type='STOP', receiver='agent')))
        logging.debug("Environment: monitor, I'm stopping now")
        self.socket_send.send_string(
            str(Message('environment', message_type='STOP', receiver='mediator')))

    def configure(self, content):
        self.places = content

if __name__ == '__main__':
    import os
    import sys
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith('/') else os.path.join(basedir, s) for s in sys.argv[1:]]
    ZDTEnvironment(*args).start()
