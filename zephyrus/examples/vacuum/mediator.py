from zephyrus.mediator import Mediator


class VacuumMediator(Mediator):
    def configure(self, content):
        self.participants = content
        self.connect_to_participants()


if __name__ == '__main__':
    import sys
    VacuumMediator(*sys.argv[1:]).start()
