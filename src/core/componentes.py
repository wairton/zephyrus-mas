#-*- coding:utf-8-*-
from sys import exit

class Componentes(object):
    def __init__(self, configuracao):
        """
        configuracao -> Nome do Arquivo de configuração
        """
        self.items = {}             #NOTE: seria bom criar get e set? itens está escrito em inglês
        #NOTE: valores não é um bom nome...
        self.valores = {} #utilizado na busca de um nome a partir de um valor.
        try:
            linhas = open(configuracao, 'r').readlines()
        except:
            print "Erro durante a abertura do arquivo de configuração dos componentes."
            exit()

        cod = 1
        for linha in linhas:
            if linha[-1] == '\n': linha = linha[:-1]
            linha = linha.split(',')
            if len(linha) > 2:
                self.items[linha[0]] = cod, linha[1], linha[2]
                self.valores[cod] = linha[0]
            else:
                #TODO: tratar erro
                pass
            cod <<= 1

    def adicionar(self, item, valor):
        return self.items[item][0] | valor

    def adicionarVarios(self, itens, valor):
        if len(itens) == 1:
            return self.adicionar(itens[0], valor)
        else:
            return self.adicionar(itens[0], self.adicionarVarios(itens[1:], valor))

    def remover(self, item, valor):
        return self.items[item][0] ^ valor

    def checar(self, item, valor):
        #sei que não precisa de != 0
        return (self.items[item][0] & valor) != 0

    @staticmethod
    def juntar(v1, v2):
        return v1 | v2

    @staticmethod
    def separar(v1, v2):
        return v1 ^ v2

