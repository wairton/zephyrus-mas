from zephyrus.mediator import Mediator


class ZDTMediator(Mediator):
    pass


if __name__ == '__main__':
    import sys
    import os
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith("/") else os.path.join(basedir, s) for s in sys.argv[1:]]

    ZDTMediator(*args).start()
