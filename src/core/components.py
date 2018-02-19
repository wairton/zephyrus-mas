import functools
import json
import re

from sys import exit


class ComponentException(Exception):
    pass


class Composable:
    def as_component_set(self):
        raise NotImplementedError


class Component(Composable):
    __slots__ = ['name', 'value']

    def __init__(self, name='', value=0):
        self.name = name
        self.value = value

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Component {}: {}>".format(self.name, self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __get__(self):
        return self.value

    def __add__(self, other) -> ComponentSet:
        return self.as_component_set() + other

    def as_component_set(self):
        return ComponentSet(self.value)


class ComponentEnum:
    _identifier_pattern = re.compile(r"^[A-Z][A-Z0-9_]*$")

    @classmethod
    def is_valid_name(cls, name):
        return cls._identifier_pattern.match(name) is not None

    def __init__(self, items):
        value = 1
        self.name_value = {}
        self.value_name = {}
        for item in items:
            if not ComponentEnum.is_valid_name(item.upper()):
                raise ComponentException("Invalid component name: {}".format(item))
            component = Component(item.upper(), value)
            setattr(self, component.name, component)
            self.name_value[component.name] = component.value
            self.value_name[component.value] = component.name
            value <<= 1

    def get_value_for(self, name):
        return self.name_value[name]

    def get_name_for(self, value):
        return self.value_name[value]


def cast_component_set(method):
    @functools.wraps(method)
    def wrapped(self, other: Composable):
        other = other.as_component_set()
        return method(self, other)
    return wrapped


class ComponentSet(Composable):
    def __init__(self, value=0):
        self.value = value

    @classmethod
    def from_component_list(cls, components):
        cs = ComponentSet()
        for component in components:
            cs += component
        return cs

    @cast_component_set
    def __add__(self, other):
        return ComponentSet(self.value | other.value)

    @cast_component_set
    def __eq__(self, other):
        return self.value == other.value

    @cast_component_set
    def __contains__(self, item):
        return (self & item) == item

    @cast_component_set
    def __iadd__(self, other):
        self.value |= other.value
        return self

    @cast_component_set
    def __sub__(self, other):
        return ComponentSet((self.value | other.value) ^ other.value)

    @cast_component_set
    def __isub__(self, other):
        return self - other

    @cast_component_set
    def __repr__(self):
        return "<ComponentSet value={}>".format(self.value)

    def __len__(self):
        # TODO: This takes time linear to the size of value :(
        v = self.value
        size = 0
        while v > 0:
            if v & 1:
                size += 1
            v >>= 1
        return size

    @cast_component_set
    def __and__(self, other):
        return ComponentSet(self.value & other.value)

    @cast_component_set
    def __or__(self, other):
        return self + other

    @cast_component_set
    def __xor__(self, other):
        return ComponentSet(self.value ^ other.value)

    def as_component_set(self):
        return self


class ComponentManager:
    def __init__(self, component_enum=enum):
        self.enum = enum

    @classmethod
    def from_filename(cls, filename):
        try:
            json_items = json.load(open(filename))
        except:
            raise ComponentException("Unable to load {}".format(config_filename))
        return cls.from_component_names(json_items)

    @classmethod
    def get_component_enum(cls, filename):
        return cls(filename).enum

    @classmethod
    def from_component_enum(cls, enum):
        return ComponentManager(enum)

    @classmethod
    def from_component_names(self, names):
        return ComponentManager(ComponentEnum(names))

    @classmethod
    def group_components(self, *components):
        return ComponentSet.from_component_list(components)

