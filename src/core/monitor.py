#-*-coding:utf-8-*-
from multiprocessing import Process
import zmq


class Monitor(Process):
    def __init__(self):
        super(Monitor, self).__init__()

    def run(self):
        raise NotImplementedError
