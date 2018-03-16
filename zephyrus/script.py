import abc
import json


class Script(list):
    def __init__(self, filename=None, iterable=None):
        if iterable is not None:
            super().__init__(iterable)
        else:
            super().__init__()
        self.filename = filename

    def save(self, filename=None):
        if filename is not None:
            self.filename = filename
        save = open(self.filename, 'w')
        json.dump(self, save)
        save.close()

    def load(self, filename):
        self.clean()
        self.extend(json.load(open(filename)))

    def update(self, filename, index):
        d = json.load(open(filename))
        up = self[index]
        for key in up.keys():
            d[key] = up[key]
        json.dump(d, open(filename, 'w'))


class Parameter:
    def __init__(self, name, message, parser):
        self.name = name
        self.message = message
        self.parser = parser

    def __call__(self, *args, **kwargs):
        return self.parser(input(self.message))


# TODO get a better name for this
class AutoParameter(abc.ABC):
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, parameters, **kwargs):
        return self.parser(parameters)

    @abc.abstractmethod
    def parser(self, parameters):
        pass


class ConfigSection:
    @classmethod
    def get_dict(cls):
        section = {}
        for parameter in cls.parameters:
            section[parameter.name] = parameter(parameters=section)
        return section


class ConfigBuilder:
    def get_dict(self):
        config = {}
        for section in self.sections:
            config.update(section.get_dict())
        return config

    def generate_config_file(self, filename):
        with open(filename, 'w') as output:
            json.dump(output, self.get_dict())
