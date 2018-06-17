from zephyrus.mediator import Mediator


class ZDTMediator(Mediator):
    def configure(self, content):
        self.participants = content
        self.connect_to_participants()


if __name__ == '__main__':
    import sys
    ZDTMediator(*sys.argv[1:]).start()
