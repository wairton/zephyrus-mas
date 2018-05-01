import random
import logging

from zephyrus.message import Message
from zephyrus.strategy import Strategy


class ZDTStrategy(Strategy):
    def configure(self, content):
        self.niter = content['niter']
        self.length = content['length']
        self.nevaluators = content.get('nevaluators', 1)

    def mainloop(self):
        if self.nevaluators == 1:
            self.mainloop_single()
        else:
            self.mainloop_dist()

    def mainloop_single(self):
        # TODO expecting configuration here?
        best_solution = None
        best_value = None
        for i in range(self.niter):
            logging.info("Strategy: progress {}/{}".format(i + 1, self.niter))
            solution = [random.random() for _ in range(self.length)]
            msg = self.messenger.build_evaluate_message(content=solution)
            self.socket_send.send_string(str(msg))
            ans = Message.from_string(self.socket_receive.recv_string())
            logging.debug('Received {}'.format(str(ans)))
            if ans.type == 'RESULT':
                if best_value is None or best_value > ans.content:
                    best_value = ans.content
                    best_solution = solution
            elif ans.type == 'STOP':
                logging.info('Strategy: stopping.')
                break
        logging.debug('Strategy: best found {}'.format(best_value))
        logging.debug('Strategy: best solution {}'.format(best_solution))
        self.socket_send.send_string(str(self.messenger.build_stop_message()))
        msg = self.messenger.build_result_message(content={
            'value': best_value,
            'solution': best_solution
        })
        logging.debug('Strategy: sending result {}'.format(str(msg)))
        self.socket_send.send_string(str(msg))

    def mainloop_dist(self):
        # TODO expecting configuration here?
        best_solution = None
        best_value = None

        poller = zmq.Poller()
        poller.register(self.socket_receive)
        navailable = self.nevaluators
        nwaiting = 0
        tsent = 0
        trecv = 0
        while trecv < self.niter:
            while navailable > 0 and tsent < self.niter:
                logging.info("Strategy: progress {}/{}".format(i + 1, self.niter))
                solution = [random.random() for _ in range(self.length)]
                msg = self.messenger.build_evaluate_message(content=solution)
                self.socket_send.send_string(str(msg))
                navailable -= 1
                nwaiting += 1
            failed = False
            while not failed and nwaiting > 0:
                # TODO adjust timeout value
                result = poller.poll(25)
                if self.socket_receive in result:
                    answer = Message.from_string(self.socket_receive.recv_string())
                    logging.debug('Received {}'.format(str(answer)))
                    if answer.type == 'RESULT':
                        if best_value is None or best_value > answer.content:
                            best_value = answer.content
                            best_solution = solution
                        nwaiting -= 1
                        trecv += 1
                        navailable += 1
                    if answer.type == 'STOP':
                        logging.error('Strategy: stopping.')
                        # TODO fix this,
                else:
                    failed = True
        logging.debug('Strategy: best found {}'.format(best_value))
        logging.debug('Strategy: best solution {}'.format(best_solution))
        self.socket_send.send_string(str(self.messenger.build_stop_message()))
        msg = self.messenger.build_result_message(content={
            'value': best_value,
            'solution': best_solution
        })
        logging.debug('Strategy: sending result {}'.format(str(msg)))
        self.socket_send.send_string(str(msg))
        poller.unregister(self.socket_receive)


if __name__ == '__main__':
    import sys
    import os
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith("/") else os.path.join(basedir, s) for s in sys.argv[1:]]
    ZDTStrategy(*args).start()
