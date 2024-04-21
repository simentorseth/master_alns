from heuristic.utils import is_feasible
from heuristic.problem import Problem


def test_feasible(test_problem):
    routes, stations, problem = test_problem
    window_assignment = {0: [0, 1, 2], 1: [3], 2: []}
    assert is_feasible(routes, stations, problem) == True
    assert problem.time_window_assignments == window_assignment
