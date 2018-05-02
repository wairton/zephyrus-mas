import sys
import json

from zephyrus.exceptions import ImproperlyConfigured


class Participants:
    def __init__(self, filename):
        try:
            self._addresses = json.load(open(filename))
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            raise ImproperlyConfigured(e)
        self._aliases = {v: k for k, v in self._addresses.items()}

    def alias(self, address):
        return self._aliases[address]

    @property
    def aliases(self):
        return list(self._addresses.keys())

    def address(self, alias):
        return self._addresses[alias]

    def __str__(self):
        return '<Participants>: {}'.format(str(self._addresses))


if __name__ == '__main__':
    Participants(sys.argv[1])
