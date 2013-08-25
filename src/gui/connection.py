#-*-coding:utf-8-*-
import os
import zmq
from subprocess import Popen, PIPE

def getIp():
    comando = Popen("ifconfig", stdout=PIPE)
    stdout = comando.communicate()[0]
    return stdout.split()[9]

