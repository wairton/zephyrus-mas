from subprocess import Popen

if __name__ == '__main__':
    enderecos = 'confs/addresses.json'
    simulacao = 'confs/simulation.json'
    executar = 'confs/run.json'
    componentes = 'confs/componentes.conf'
    comando = "python testador.py %s %s %s %s" % (simulacao, executar, enderecos, componentes)
    Popen(comando.split())
