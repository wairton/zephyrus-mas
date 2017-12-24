#! /usr/bin/python
#-*-coding:utf-8-*-
import sys
from multiprocessing import Process
import random

import zmq

class Dummy(Process):
    def __init__(self, endSelf, endEstra):
        super(Dummy, self).__init__()
        self.endereco = endSelf
        self.estrategia = endEstra
        
    def aval(self):
        print 'em aval'
        while True:
            msg = self.receive.recv()
            print 'recebi', msg
            msg = "%s %s" % (random.random()*100, random.random()*100)
            print 'enviei', msg
            self.send.send(msg)
        
    def run(self):
        contexto = zmq.Context()
        self.send = contexto.socket(zmq.PUSH)
        self.send.bind(self.endereco)
        self.receive = contexto.socket(zmq.PULL)
        self.receive.connect(self.estrategia)
        self.send.send('vai!') 
        self.aval()

if __name__ == '__main__':
    d = Dummy('tcp://127.0.0.1:6600', 'tcp://127.0.0.1:5000')
    d.start()
