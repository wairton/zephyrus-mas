#-*-coding:utf-8-*-
#This work is under LGPL license, see the LICENSE.LGPL file for further details.

from subprocess import Popen

if __name__ == '__main__':
    enderecos = 'confs/enderecos.conf'
    simulacao = 'confs/simulacao.conf'
    executar = 'confs/executar.conf'
    componentes = 'confs/componentes.conf'
    comando = "python testador.py %s %s %s %s" % (simulacao, executar, enderecos, componentes)
    Popen(comando.split())