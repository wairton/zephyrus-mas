from zephyrus.tester import Tester


class VaccumTester(Tester):
    def build_environment_config_message(self, strategy_data):
        content = {
            'initial': ,
            'scenario': strategy_data,
            'agents': [a for a in self.participants.aliases if a.startswith('agent')]
        }
        self.messenger.build_config_message(receiver='environment', content=content)

    def get_mediator_config(self):
        return {
            'agent': self.participants.address('agent'),
            'environment': self.participants.address('environment')
        }

    def report_result(self, msg):
        print("TODO")
        logging.info("Report: {}".format(str(msg)))

    def evaluate(self, data):
        print("TODO")
        result = None
        for item in data:
            parsed_item = json.loads(item)
            if parsed_item['type'] != 'RESULT':
                continue
        return result


if __name__ == '__main__':
    t = VacuumTester(*sys.argv[1:])
    t.start()
