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
        return self.parser(input("{}: ".format(self.message.strip(": "))))


# TODO get a better name for this
class AutoParameter(abc.ABC):
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, parameters, **kwargs):
        return self.parser(parameters, **kwargs)

    @abc.abstractmethod
    def parser(self, parameters, **kwargs):
        pass


class ConfigSection:
    def __init__(self, name):
        self.name = name

    def get_dict(self, _globals):
        section = {}
        for parameter in self.parameters:
            section[parameter.name] = parameter(parameters=section, _globals=_globals)
        return section


class ConfigBuilder:
    def get_dict(self, nested=True):
        config = {}
        _globals = getattr(self, 'globals', {})
        for section in self.sections:
            if nested:
                config[section.name] = section.get_dict(_globals)
            else:
                config.update(self.get_dict(_globals))
        return config

    def generate_config_file(self, filename, nested=True):
        with open(filename, 'w') as output:
            json.dump(self.get_dict(nested), output, sort_keys=True, indent=2)
        print("config generated at {}".format(filename))
