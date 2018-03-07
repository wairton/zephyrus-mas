import json
import random

import pytest

from zephyrus.addresses import Participants
from zephyrus.exceptions import ImproperlyConfigured


@pytest.fixture(scope='session')
def config_json():
    return {
      "simulation": "tcp://127.0.0.1:7000",
      "strategy": "tcp://127.0.0.1:5000",
      "tester": "tcp://127.0.0.1:6600",
      "tester_par": "tcp://127.0.0.1:6601",
      "tester_est": "tcp://127.0.0.1:6605",
      "monitor": "tcp://127.0.0.1:6500",
      "environment": "tcp://127.0.0.1:6000",
      "agent": "tcp://127.0.0.1:6001"
    }


@pytest.fixture(scope='session')
def address_configuration_file(tmpdir_factory, config_json):
    filename = tmpdir_factory.mktemp('conf').join('addresses.json')
    with open(str(filename), 'w') as output:
        json.dump(config_json, output)
    return filename


def test_participants_alias_and_address(address_configuration_file, config_json):
    participants = Participants(str(address_configuration_file))
    alias, address = random.choice(list(config_json.items()))
    assert participants.alias(address) == alias
    assert participants.address(alias) == address


def test_participants_invalid_alias_and_address(address_configuration_file, config_json):
    participants = Participants(str(address_configuration_file))
    alias, address = random.choice(list(config_json.items()))
    with pytest.raises(KeyError):
        participants.alias(address + address)
    with pytest.raises(KeyError):
        participants.address(alias + alias)


def test_participants_invalid_config_file(tmpdir):
    p = tmpdir.mkdir("foo").join("fakeconfig.json")
    p.write("[invalid gibberish]")
    with pytest.raises(ImproperlyConfigured):
        Participants(str(p))
