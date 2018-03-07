import pytest

from zephyrus.components import ComponentEnum, ComponentException, ComponentSet


@pytest.fixture
def basic_enum():
    return ComponentEnum(['a', 'b', 'c'])


@pytest.fixture
def all_items(basic_enum):
    return basic_enum.A + basic_enum.B + basic_enum.C


def test_component_add(basic_enum):
    cs = (basic_enum.A + basic_enum.B)
    assert cs.value == 3
    assert isinstance(cs, ComponentSet)


def test_component_eq(basic_enum):
    assert basic_enum.A == basic_enum.A
    assert basic_enum.A != basic_enum.B


def test_component_lt(basic_enum):
    assert basic_enum.A < basic_enum.B
    assert basic_enum.C > basic_enum.B


def test_component_enum_iadd(basic_enum):
    enum = basic_enum.A
    enum += basic_enum.C
    assert basic_enum.C in enum


def test_component_enum_is_valid_name():
    assert not ComponentEnum.is_valid_name('a')
    assert not ComponentEnum.is_valid_name('1A')
    assert not ComponentEnum.is_valid_name('A-')
    assert not ComponentEnum.is_valid_name('')
    assert ComponentEnum.is_valid_name('A')
    assert ComponentEnum.is_valid_name('AB2A')
    assert ComponentEnum.is_valid_name('AB_A2')


def test_component_enum_sub(basic_enum):
    enum = basic_enum.A + basic_enum.B
    enum -= basic_enum.A
    assert basic_enum.A not in enum
    assert basic_enum.B in enum


def test_component_enum_init():
    # valid names follow the pattern ^[A-Z][A-Z0-9_]*$
    items = ['a', '1']
    with pytest.raises(ComponentException):
        ComponentEnum(items)

    items = ['a', 'b!']
    with pytest.raises(ComponentException):
        ComponentEnum(items)

    assert ComponentEnum(['a', 'b']).__dict__ == ComponentEnum(['A', 'B']).__dict__
    assert ComponentEnum(['b', 'a']).__dict__ != ComponentEnum(['a', 'b']).__dict__


def test_component_set_contains(basic_enum, all_items):
    assert basic_enum.C in all_items


def test_component_enum_get_value_for(basic_enum):
    assert basic_enum.get_value_for('b') == 2
    with pytest.raises(KeyError):
        basic_enum.get_value_for('e')


def test_component_enum_get_name_for(basic_enum):
    assert basic_enum.get_name_for(4) == 'C'
    with pytest.raises(KeyError):
        basic_enum.get_name_for(3)
