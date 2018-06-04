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
        return Message(json_dict['sender'], json_dict.get('receiver'), json_dict.get('type'), json_dict.get('content'))

    @classmethod
    def from_string(self, json_str):
        return Message.from_json(json.loads(json_str))

    @property
    def sender(self):
        return self.message['sender']

    @sender.setter
    def sender(self, value):
        self.message['sender'] = value

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
        if 'basic_messages' not in attr_dict:
            raise AttributeError("basic_messages attribute must be defined")
        for name in attr_dict['basic_messages']:
            fullname, body = MessengerMeta.get_method(name)
            setattr(clsobj, fullname, body)
        return clsobj

    @staticmethod
    def get_method(name):
        def method(self, receiver=None, content=None):
            receiver = receiver or self.default_receiver
            return Message(self.sender, receiver, message_type=name.upper(), content=content)
        return 'build_{}_message'.format(name.lower()), method


class Messenger(metaclass=MessengerMeta):
    basic_messages = []

    def __init__(self, sender: str, default_receiver: str = None):
        self.sender = sender
        self.default_receiver = default_receiver

    def build_message(self, receiver, message_type, content):
        return Message(self.sender, receiver, message_type=message_type.upper(), content=content)
