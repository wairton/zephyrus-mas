import json

import pytest
import zmq

from zephyrus.addresses import Participants
from zephyrus.agent import Agent
from zephyrus.message import Message
from zephyrus.tester import TesterMessenger as ZTesterMessenger


@pytest.fixture
def DummyAgent():
    class Dummy(Agent):
        def act(self, perceived):
            return Message('agent', message_type='RESULT', content=perceived[::-1])

        def perceive(self, perceived_data):
            return super().perceive(perceived_data)

        def configure(self, config_data):
            pass

        def mainloop(self):
            msg = Message.from_string(self.socket_receive.recv_string())
            action = self.perceive(msg.content)
            self.socket_send.send_string(str(action))
    return Dummy


@pytest.fixture
def address_config_file(tmpdir_factory):
    path = tmpdir_factory.mktemp('config').join('addresses.json')
    data = {
      "simulation": "tcp://127.0.0.1:7000",
      "strategy": "tcp://127.0.0.1:5000",
      "tester": "tcp://127.0.0.1:6600",
      "tester_par": "tcp://127.0.0.1:6601",
      "tester_est": "tcp://127.0.0.1:6605",
      "mediator": "tcp://127.0.0.1:6500",
      "environment": "tcp://127.0.0.1:6000",
      "agent": "tcp://127.0.0.1:6001"
    }
    json.dump(data, open(str(path), 'w'))
    return path


def test_agent_hello(DummyAgent, address_config_file):
    ag = DummyAgent(1, str(address_config_file))
    ag.start()
    messenger = ZTesterMessenger('tester')
    participants = Participants(str(address_config_file))
    ctx = zmq.Context()
    ssend = ctx.socket(zmq.PUSH)
    ssend.connect(participants.address('agent'))
    srecv = ctx.socket(zmq.PULL)
    srecv.bind(participants.address('mediator'))
    ssend.send_string(str(messenger.build_start_message()))
    content = list(range(10))
    ssend.send_string(json.dumps({'sender': 'oi', 'receiver': '', 'type': 'bumba', 'content': content}))
    msg = Message.from_json(srecv.recv_json())
    assert msg.sender == 'agent'
    assert msg.type == 'RESULT'
    assert msg.content == content[::-1]
    ssend.send_string(str(messenger.build_stop_message()))
    ag.join()
