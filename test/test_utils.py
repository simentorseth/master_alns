from heuristic.solution import Solution
from heuristic.utils import is_feasible
from heuristic.problem import Problem


def test_feasible(test_problem):
    routes, stations, problem = test_problem
    window_assignment = {0: [0, 1, 2], 1: [3], 2: []}
    solution = Solution()
    solution.routes = routes
    solution.stations = stations
    assert is_feasible(solution, problem) == True
    assert problem.time_window_assignments == window_assignment
