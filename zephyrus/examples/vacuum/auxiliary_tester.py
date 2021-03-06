import logging
import math

from zephyrus.message import Message
from zephyrus.auxiliary_tester import AuxiliaryTester


class VaccumAuxiliaryTester(AuxiliaryTester):
    def build_environment_config_message(self, strategy_data):
        content = {
            'initial': self.config['environment']['standard_scenario'],
            'resolution': self.config['environment']['resolution'],
            'scenario': strategy_data,
            'agents': [a for a in self.participants.aliases if a.startswith('agent')]
        }
        return self.messenger.build_config_message(receiver='environment', content=content)

    def get_mediator_config(self):
        return {
            'agent_1': self.participants.address('agent_1'),
            'environment': self.participants.address('environment')
        }

    def get_agent_config(self):
        return {}

    def report_result(self, msg):
        print("TODO report result")
        logging.info("Report: {}".format(str(msg)))

    def evaluate(self, data):
        # FIXME: does not work for multiple agents
        energy = min_energy = 80
        collected = steps = 0
        resolution = self.config['environment']['resolution']
        size = resolution * resolution
        n_trash = self.config['environment']['n_trash']
        for item in data:
            msg = Message.from_string(item)
            if not msg.sender.startswith('agent'):
                continue
            if msg.type == 'MOVE':
                steps += 1
                energy -= 1
            elif msg.type == 'CLEAN':
                collected += 1
                energy -= 3
            elif msg.type == 'RECHARGE':
                energy += 10
            elif msg.type == 'DEPOSIT':
                energy -= 1
            # update min_energy
            if energy < min_energy:
                min_energy = energy
        max_consumption = 80 - min_energy
        collect_rate = collected / n_trash
        # furthest place, back and forth plus plus energy to collect and to deposit
        min_consumption = (2 * math.sqrt(2) * resolution + 4)
        steps_rate = max(steps / size, 1.0)
        if steps_rate > 3.0:
            obj1 = 60 / steps_rate * collect_rate
        else:
            obj1 = (100 - 40 * (steps_rate - 1)) * collect_rate
        obj2 = 100.0 * collect_rate * math.log(1 + (80 - max_consumption) / (80 - min_consumption), 2)
        return obj1, obj2


if __name__ == '__main__':
    import sys
    VaccumAuxiliaryTester(*sys.argv[1:]).start()
