from zephyrus.mediator import Mediator


class VacuumMediator(Mediator):
    def configure(self, content):
        self.participants = content
        self.connect_to_participants()


if __name__ == '__main__':
    import sys
    import os
    basedir = os.path.dirname(__file__)
    config_path = sys.argv[-1]
    args = []
    if not config_path.startswith('/'):
        config_path = os.path.join(basedir, config_path)
    args.append(config_path)
    if len(sys.argv) > 2:
        args.append(sys.argv[1])
    VacuumMediator(*args).start()
