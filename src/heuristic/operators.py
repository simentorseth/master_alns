from copy import copy
import random
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import (
    is_feasible,
    cost,
    get_to_and_from_costs,
    get_station_assignment,
    initialise_model,
)


def swap(elements, index1, index2):
    # TODO: Should this modify inplace instead?
    elements_copy = elements[:]  # shallow copy
    temp1, temp2 = elements_copy[index1], elements_copy[index2]
    elements_copy[index1], elements_copy[index2] = temp2, temp1
    return elements_copy


# oops, should've googled. python already implemented this in stdlib...
def shuffle(solution: Solution, problem: Problem) -> Solution:
    # TODO: Should this modify inplace instead?
    # If not, should it delete the "old" solution from memory?
    routes = solution.routes
    stations = solution.stations

    # shuffle nodes
    amount = random.randint(1, len(problem.map["Turbines"]) // 2)

    shuffled_routes = routes[:]
    for _ in range(amount):
        index1, index2 = random.sample(range(0, len(routes) - 1), 2)
        shuffled_routes = swap(shuffled_routes, index1, index2)

    # shuffle stations
    amount = random.randint(1, len(stations) // 2)

    shuffled_stations = stations[:]
    for _ in range(amount):
        index1, index2 = random.sample(range(0, len(stations) - 1), 2)
        shuffled_stations = swap(shuffled_stations, index1, index2)

    new_solution = Solution()
    new_solution.routes = shuffled_routes
    new_solution.stations = shuffled_stations
    return new_solution


def optimal_stations(solution: Solution, problem: Problem) -> Solution:
    to_and_from_costs = get_to_and_from_costs(solution, problem)
    fixed_costs = [
        problem._station_cost for _ in range(len(problem.map["Substations"]))
    ]

    model = initialise_model(to_and_from_costs, fixed_costs)
    model.optimize()
    assignment = get_station_assignment(
        model, len(to_and_from_costs), len(fixed_costs), problem
    )
    new_solution = copy(solution)
    new_solution.stations = assignment
    return new_solution
