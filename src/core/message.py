import json


class Message:
    def __init__(self, sender, content):
        self.message = {
            'sender': sender,
            'content': content
        }

    def __str__(self):
        return json.dumps(self.message)

    def __repr__(self):
        return "Message: %s" % self
