from zephyrus.mediator import Mediator


class ZDTMediator(Mediator):
    pass


if __name__ == '__main__':
    import sys
    ZDTMediator(*sys.argv[1:]).start()
