import random
from heuristic.problem import Problem
from heuristic.utils import is_feasible, cost


def swap(elements, index1, index2):
    elements_copy = elements[:]  # shallow copy
    temp1, temp2 = elements_copy[index1], elements_copy[index2]
    elements_copy[index1], elements_copy[index2] = temp2, temp1
    return elements_copy


def shuffle(
    solution: tuple[list[int], list[int]], problem: Problem
) -> tuple[list[int], list[int]]:
    routes, stations = solution
    amount = random.randint(1, len(problem.map["Turbines"]) // 2)
    print(f"Shuffling {amount} times")

    shuffled = routes[:]
    for _ in range(amount):
        index1, index2 = random.sample(range(1, len(routes) - 1), 2)
        shuffled = swap(shuffled, index1, index2)

    return shuffled, stations
