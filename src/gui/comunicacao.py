#-*-coding:utf-8-*-
import zmq
from subprocess import Popen, PIPE

def getIp():
    comando = Popen("ifconfig", stdout=PIPE)
    stdout = comando.communicate()[0]
    return stdout.split()[9]

if __name__ == '__main__':
    endereco = raw_input("Endereço do servidor: ")
    porta = raw_input("Qual a porta: ")
    contexto = zmq.Context()
    socketEnvio = contexto.socket(zmq.PUSH)
    socketResposta = contexto.socket(zmq.PULL)
    socketResposta.bind("tcp://" + getIp() + ":5000")
    print "Tentando conexão com {}:{}".format(endereco, porta)
    socketEnvio.connect("tcp://" + endereco + ":" + porta)
    print "Conexão estabelecida, enviando mensagem "
    socketEnvio.send("olá sou o " + getIp())
    print "Aguardando resposta"
    recebi = socketResposta.recv()
    print recebi
