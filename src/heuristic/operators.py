import random
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import is_feasible, cost


def swap(elements, index1, index2):
    # TODO: Should this modify inplace instead?
    elements_copy = elements[:]  # shallow copy
    temp1, temp2 = elements_copy[index1], elements_copy[index2]
    elements_copy[index1], elements_copy[index2] = temp2, temp1
    return elements_copy


def shuffle(solution: Solution, problem: Problem) -> Solution:
    # TODO: Should this modify inplace instead?
    # If not, should it delete the "old" solution from memory?
    routes = solution.routes
    stations = solution.stations
    amount = random.randint(1, len(problem.map["Turbines"]) // 2)

    shuffled = routes[:]
    for _ in range(amount):
        index1, index2 = random.sample(range(1, len(routes) - 1), 2)
        shuffled = swap(shuffled, index1, index2)

    new_solution = Solution()
    new_solution.routes = shuffled
    new_solution.stations = stations
    return new_solution
