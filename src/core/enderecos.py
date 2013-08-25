#-*-coding:utf-8-*-
import sys

class Enderecos(object):
    def __init__(self, arqEnderecos):
        linhas = open(arqEnderecos).readlines()
        self.enderecos = {}
        for l in linhas:
            lsplit = l.split()
            if len(lsplit) == 3: #FIXME: isso foi posto aqui para tentar mitigar (na verdade, esconder) um bug
                participante, nome, endereco = l.split()
                self.enderecos[participante] = nome, endereco

    def participantes(self):
        """Uma lista de ..."""
        return self.enderecos.keys()

    def participante(self, participante):
        """Retorna a tupla (nome, endereco) de participante"""
        found = self.enderecos.get(participante)
        return found[0] if not found == None else None

    def nomes(self):
        """Retorna os nomes de todos os participantes."""
        return [(a, self.enderecos[a][0]) for a in self.enderecos.keys()]

    def nome(self, nomeBuscado):
        for participante, (nome, endereco) in self.enderecos.iteritems():
            if nome == nomeBuscado:
                return participante, endereco
        return None

    def endereco(self, participante):
        try:
            endereco = self.enderecos.get(participante)[1]
        except:
            return None
        return endereco

    def get(self, participante):
        return self.enderecos.get(participante)

    def getNome(self, nome):
        found = filter(lambda k:k[0] == nome, self.enderecos.values())
        return found[0] if len(found) != 0 else None
