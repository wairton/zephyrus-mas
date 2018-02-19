import unittest


class TestSolution(unittest.TestCase):
    def test_a_dominates_b(self):
        sol_a = Solution(SolutionType.MIN)
        sol_a.objetivos = [1.0, 2.0, 3.0]
        sol_b = Solution(SolutionType.MIN)
        sol_b.objetivos = [3.0, 2.0, 1.0]

        self.assertEqual(sol_a.compare(sol_b), COMP_DOMINADA)

    def test_a_is_dominated_by_b(self):
        pass

    def test_a_and_b_non_dominated(self):
        pass

