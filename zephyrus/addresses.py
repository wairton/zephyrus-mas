import sys
import json

from zephyrus.exceptions import ImproperlyConfigured


class Participants:
    def __init__(self, filename):
        try:
            self.addresses = json.load(open(filename))
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            raise ImproperlyConfigured(e)
        self.aliases = {v: k for k, v in self.addresses.items()}

    def alias(self, address):
        return self.aliases[address]

    def address(self, alias):
        return self.addresses[alias]

    def __str__(self):
        return '<Participants>: {}'.format(str(self.addresses))


if __name__ == '__main__':
    Participants(sys.argv[1])
