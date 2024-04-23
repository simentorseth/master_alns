import pytest

from heuristic.problem import Problem


@pytest.fixture
def test_problem():
    filename = "./src/instances/instance_testing.csv"
    problem = Problem(filename)
    routes = [6, 5, 0, 9, 3, 0, 1, 4, 10, 0, 2, 7, 8]
    stations = [12, 12, 12, 12]
    # window_assignment = {0: [0, 1, 2], 1: [3], 2: []}
    # problem.time_window_assignments = window_assignment
    return routes, stations, problem
