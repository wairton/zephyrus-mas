import json
import logging

from zephyrus.tester import Tester


class ZDTTester(Tester):
    def get_strategy_config(self):
        return {
            'niter': 100,
            'length': 10
        }

    def get_mediator_config(self):
        return {
            'agent_1': self.participants.address('agent_1'),
            'environment': self.participants.address('environment')
        }

    def report_result(self, msg):
        logging.info("Report: {}".format(str(msg)))

    def evaluate(self, data):
        result = None
        for item in data:
            parsed_item = json.loads(item)
            if parsed_item['type'] != 'RESULT':
                continue
            result = parsed_item['content']
            break
        return result


if __name__ == '__main__':
    import sys
    ZDTTester(*sys.argv[1:]).start()
