import unittest
from io import StringIO


from components import Components


class TestComponents(unittest.TestCase):
    def setUp(self):
        self.config_file = StringIO('["AG", "WALLN", "WALLE", "WALLS", "WALLW", "BIN", "TRASH", "RECHARGE"]')

    def test_load(self):
        components = Components('components.json')
        import pdb; pdb.set_trace()


if __name__ == '__main__':
    unittest.main()
