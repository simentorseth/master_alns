from heuristic.utils import is_valid


def test_shuffle(test_problem):
    routes, stations, problem = test_problem
    from heuristic.operators import shuffle

    solution = (routes, stations)
    new = shuffle(solution, problem)
    assert is_valid(*new, problem)


def test_swap():
    from heuristic.operators import swap

    elements = [1, 2, 3, 4, 5]
    index1, index2 = 1, 3
    new = swap(elements, index1, index2)
    assert new == [1, 4, 3, 2, 5]
