import pytest

from zephyrus.components import ComponentEnum


@pytest.fixture
def basic_enum():
    return ComponentEnum(['a', 'b', 'c'])


def test_component_enum(basic_enum):
    assert (basic_enum.A + basic_enum.B).value == 3

