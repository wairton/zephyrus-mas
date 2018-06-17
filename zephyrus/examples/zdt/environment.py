import logging

from zephyrus.environment import Environment
from zephyrus.message import Message


class ZDTEnvironment(Environment):
    def mainloop(self):
        start_message = self.messenger.build_start_message(receiver='mediator')
        self.socket_send.send_string(str(start_message))

        while True:
            msg = Message.from_string(self.socket_receive.recv_string())
            logging.debug('Environment: received {}'.format(msg))
            if msg.type == 'PERCEIVE':
                reply = self.messenger.build_confirm_message(receiver=msg.sender, content=self.points)
                self.socket_send.send_string(str(reply))
            elif msg.type == 'RESULT':
                logging.debug("Environment: received result from {}".format(msg.sender))
                break
            elif msg.type == 'CONFIG':
                # this handles the case where start arrives before config message
                self.configure(msg.content)
            else:
                logging.error("Environmnent: received an invalid message '{}'".format(msg))
        logging.debug("Environment: monitor, I'm stopping now")
        stop_message = self.messenger.build_stop_message(receiver='mediator')
        self.socket_send.send_string(str(stop_message))

    def configure(self, content):
        self.points = content

if __name__ == '__main__':
    import os
    import sys
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith('/') else os.path.join(basedir, s) for s in sys.argv[1:]]
    ZDTEnvironment(*args).start()
