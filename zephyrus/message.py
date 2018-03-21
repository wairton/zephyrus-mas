import json


class Message:
    def __init__(self, sender, message_type, content=None):
        self.message = {
            'sender': sender,
            'type': message_type,
            'content': content
        }

    def __str__(self):
        return json.dumps(self.message)

    def __repr__(self):
        return "Message: %s" % self

    @property
    def sender(self):
        return self.message['sender']

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
    def get_method(name, content):
        def method(self):
            return Message(self.sender, content)
        return 'build_{}_message'.format(name), method


class Messenger(metaclass=MessengerMeta):
    no_parameter_messages = {}

    def __init__(self, sender: str):
        self.sender = sender
