import logging
import time
from queue import Queue, Empty
from threading import Thread, Event, Lock

import zmq

from zephyrus.components import ComponentSet
from zephyrus.message import Message
from zephyrus.strategy.objective import LazyObjectives


class Evaluator:
    def __init__(self, main_config, components, messenger, socket_send, socket_receive, nworkers):
        self.stop_flag = None
        self._evaluation_id = 0
        self.queue = Queue()
        self.main_config = main_config
        self.messenger = messenger
        self.socket_send = socket_send
        self.socket_receive = socket_receive
        self.components = components
        self.nworkers = nworkers

    @property
    def evaluation_id(self):
        self._evaluation_id += 1
        return self._evaluation_id

    def start_consumer(self):
        self.stop_flag = Event()
        self.buffer_lock = Lock()
        self.consumer = Consumer(self.socket_send, self.socket_receive, self.messenger, self.stop_flag, self.buffer_lock, self.queue, self.nworkers)
        self.consumer.start()
        return self.queue

    def stop_consumer(self):
        if self.stop_flag is None:
            raise RuntimeError("Consumer must be started first")
        self.stop_flag.set()
        return self.consumer.finish_notifier

    def add_task(self, task):
        self.queue.put(task)

    def clear_buffer(self):
        self.consumer.clear_buffer()

    def set_evaluation_notifier(self, evaluation_id):
        return self.consumer.set_evaluation_notifier(evaluation_id)

    def evaluate(self, individual):
        next_id = self.evaluation_id
        decoded = individual.decode(self.components)
        scenario = self.main_config['environment']['standard_scenario']
        content = {
            'id': next_id,
            'data': [(ComponentSet(d) + ComponentSet(s)).value for (d, s) in zip(decoded, scenario)]
        }
        msg = self.messenger.build_evaluate_message(content=content)
        self.add_task(msg)
        return LazyObjectives(next_id, self.consumer.callback, self.set_evaluation_notifier)


class Consumer(Thread):
    def __init__(self, socket_send, socket_receive, messenger, stop_flag, buffer_lock, queue, nworkers):
        super().__init__()
        self.socket_receive = socket_receive
        self.socket_send = socket_send
        self.messenger = messenger
        self.stop_flag = stop_flag
        self.queue = queue
        self.buffer = {}
        self.notifiers = {}
        self.buffer_lock = buffer_lock
        self.nworkers = nworkers
        self.finish_notifier = Event()

    def run(self):
        available = self.nworkers
        working = 0
        result_poller = zmq.Poller()
        result_poller.register(self.socket_receive, zmq.POLLIN)
        logging.debug('Consumer: running')
        waiting = 0

        while not self.stop_flag.is_set() or waiting > 0 or not self.queue.empty():
            action = False
            if available > 0:
                action = True
                try:
                    item = self.queue.get(timeout=.1)
                except Empty:
                    logging.debug('Consumer: queue is empty')
                else:
                    logging.debug('Consumer: send {}'.format(str(item)))
                    self.socket_send.send_string(str(item))
                    available -= 1
                    working += 1
                    waiting += 1
            if working > 0:
                action = True
                sck = dict(result_poller.poll(100))
                if self.socket_receive in sck and sck[self.socket_receive] == zmq.POLLIN:
                    ans = Message.from_string(self.socket_receive.recv_string())
                    logging.debug('Consumer: received this {}'.format(str(ans)))
                    waiting -= 1
                    with self.buffer_lock:
                        working -= 1
                        available += 1
                        eval_id = ans.content['id']
                        self.buffer[eval_id] = ans.content['data']
                        if eval_id in self.notifiers:
                            self.notifiers[eval_id].set()
            if not action:
                time.sleep(.1)
        self.finish_notifier.set()

    def clear_buffer(self):
        with self.buffer_lock:
            self.buffer.clear()
            self.notifiers.clear()

    def set_evaluation_notifier(self, evaluation_id):
        if evaluation_id in self.notifiers:
            raise Exception('Already has a notification for {}'.format(evaluation_id))
        with self.buffer_lock:
            self.notifiers[evaluation_id] = Event()
            # value already calculated
            if evaluation_id in self.buffer:
                self.notifiers[evaluation_id].set()
        return self.notifiers[evaluation_id]

    def callback(self, eval_id):
        data = None
        with self.buffer_lock:
            if eval_id in self.buffer:
                data = self.buffer[eval_id]
        return data
