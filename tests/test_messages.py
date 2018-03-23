import json

import pytest

from zephyrus.message import Messenger, Message


def test_message():
    sender = 'tester'
    msg_type = 'type'
    content = 'message content'
    m = Message(sender, msg_type, content)
    assert m.sender == sender
    assert m.type == msg_type
    assert m.content == content
    expected_dict = {'sender': sender, 'type': msg_type, 'content': content}
    assert str(m) == json.dumps(expected_dict)


def test_no_parameter_methods_generation():
    class TMessenger(Messenger):
        no_parameter_messages = {
            'lob': 'law'
        }

    t = TMessenger('bob')
    assert hasattr(t, 'build_lob_message')
    lob_message = t.build_lob_message()
    assert lob_message.sender == 'bob'
    assert lob_message.type == 'law'
    assert lob_message.content is None