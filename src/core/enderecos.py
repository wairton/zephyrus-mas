#-*-coding:utf-8-*-
import sys
import json


class Enderecos(object):
    def __init__(self, config_file):
        self.addresses = json.load(open(config_file))
        # TODO validate file

    def participantes(self):
        """Uma lista de ..."""
        return self.addresses.keys()

    def participante(self, participante):
        """Retorna a tupla (nome, endereco) de participante"""
        found = self.addresses.get(participante)
        return found[0] if not found == None else None

    def nomes(self):
        """Retorna os nomes de todos os participantes."""
        return [(a, self.addresses[a][0]) for a in self.addresses.keys()]

    def nome(self, nomeBuscado):
        for participante, (nome, endereco) in self.addresses.iteritems():
            if nome == nomeBuscado:
                return participante, endereco
        return None

    def endereco(self, participante):
        try:
            endereco = self.addresses.get(participante)[1]
        except:
            return None
        return endereco

    def get(self, participante):
        return self.addresses.get(participante)

    def getNome(self, nome):
        found = filter(lambda k:k[0] == nome, self.addresses.values())
        return found[0] if len(found) != 0 else None


if __name__ == '__main__':
    Enderecos(sys.argv[1])
