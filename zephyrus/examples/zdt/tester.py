from zephyrus.tester import Tester


class ZDTTester(Tester):
    def get_strategy_config(self):
        return {
            'niter': 10,
            'length': 10
        }

    def get_mediator_config(self):
        return {
            'agent': self.participants.address('agent'),
            'environment': self.participants.address('environment')
        }


if __name__ == '__main__':
    import os
    import sys
    basedir = os.path.dirname(__file__)
    args = [s if s.startswith("/") else os.path.join(basedir, s) for s in sys.argv[1:]]
    ZDTTester(*args).start()
