import json


class Message:
    def __init__(self, sender, receiver=None, message_type=None, content=None):
        self.message = {
            'sender': sender,
            'receiver': receiver,
            'type': message_type,
            'content': content
        }

    def __str__(self):
        return json.dumps(self.message)

    def __repr__(self):
        return "Message: %s" % self

    @classmethod
    def from_json(self, json_dict):
        # TODO: missing attributes parsing
        return Message(json_dict['sender'], json_dict.get('receiver'), json_dict.get('type'), json_dict['content'])

    @classmethod
    def from_string(self, json_str):
        return Message.from_json(json.loads(json_str))

    @property
    def sender(self):
        return self.message['sender']

    @property
    def receiver(self):
        return self.message['receiver']

    @property
    def type(self):
        return self.message['type']

    @property
    def content(self):
        return self.message['content']


class MessengerMeta(type):
    def __new__(cls, clsname, supercls, attr_dict):
        clsobj = super().__new__(cls, clsname, supercls, attr_dict)
        if 'no_parameter_messages' not in attr_dict:
            raise AttributeError("no_parameter_messages attribute must be defined")
        for name, content in attr_dict['no_parameter_messages'].items():
            fullname, body = MessengerMeta.get_method(name, content)
            setattr(clsobj, fullname, body)
        return clsobj

    @staticmethod
    def get_method(name, msg_type):
        def method(self, receiver=None, content=None):
            receiver = receiver or self.default_receiver
            return Message(self.sender, receiver, message_type=msg_type, content=content)
        return 'build_{}_message'.format(name), method


class Messenger(metaclass=MessengerMeta):
    no_parameter_messages = {}

    def __init__(self, sender: str, default_receiver: str = None):
        self.sender = sender
        self.default_receiver = default_receiver
