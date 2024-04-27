from copy import copy
from random import shuffle, choice
from pprint import pprint
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import (
    is_feasible,
    cost,
    get_to_and_from_costs,
    get_station_assignment,
    initialise_model,
    findmin,
    feasible_inserts,
    insertion_costs,
)


def swap(elements, index1, index2):
    # TODO: Should this modify inplace instead?
    elements_copy = elements[:]  # shallow copy
    temp1, temp2 = elements_copy[index1], elements_copy[index2]
    elements_copy[index1], elements_copy[index2] = temp2, temp1
    return elements_copy


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


def random_removal(solution: Solution, num_remove: int, problem: Problem) -> list[int]:
    routes = solution.routes

    # indices of the tour separators
    separators = [i for i, x in enumerate(routes + [0]) if x == 0]
    # start index for current route
    idx = 0

    tours = []
    num_tours = len(separators)

    for i in range(num_tours):
        # get the current route
        current_route = routes[idx : separators[i]]  # the slice makes a shallow copy
        # add the current route to the list of tours
        tours.append(current_route)
        # adjust start index for next iteration
        idx = separators[i] + 1

    turbines = problem.map["Turbines"].copy()
    to_remove = []
    for _ in range(num_remove):
        node = choice(turbines)
        to_remove.append(node)
        turbines.remove(node)

    for node in to_remove:
        node_idx = routes.index(node)
        remove_tour_idx = sum(1 for x in routes[: node_idx + 1] if x == 0) + 1
        remove_tour = tours[remove_tour_idx - 1]
        remove_tour.remove(node)

    shuffle(to_remove)
    return to_remove, tours, solution


def greedy_insertion(
    solution: Solution, to_remove: list[int], tours: list[list[int]], problem: Problem
) -> Solution:
    for node in to_remove:
        tour = 0
        min_cost = float("inf")
        insert = 0
        for i, current_tour in enumerate(tours):
            insert_indices = feasible_inserts(
                current_tour, solution.stations[i], node, problem
            )
            if len(insert_indices) > 0:
                costs = insertion_costs(
                    current_tour, solution.stations[i], node, insert_indices, problem
                )
                curr_min_cost, idx = findmin(costs)
                if curr_min_cost < min_cost:
                    min_cost = curr_min_cost
                    tour = i
                    insert = insert_indices[idx]
        tours[tour].insert(insert, node)

    for i in range(len(tours)):
        if i == len(tours) - 1:
            continue
        else:
            tours[i].append(0)

    new_solution = Solution()
    new_solution.routes = [node for tour in tours for node in tour]
    new_solution.stations = copy(solution.stations)
    return new_solution


# def shuffle(solution: Solution, problem: Problem) -> Solution:
#     # TODO: Should this modify inplace instead?
#     # If not, should it delete the "old" solution from memory?
#     routes = solution.routes
#     stations = solution.stations

#     # shuffle nodes
#     amount = random.randint(1, len(problem.map["Turbines"]) // 2)

#     shuffled_routes = routes[:]
#     for _ in range(amount):
#         index1, index2 = random.sample(range(0, len(routes) - 1), 2)
#         shuffled_routes = swap(shuffled_routes, index1, index2)

#     # shuffle stations
#     amount = random.randint(1, len(stations) // 2)

#     shuffled_stations = stations[:]
#     for _ in range(amount):
#         index1, index2 = random.sample(range(0, len(stations) - 1), 2)
#         shuffled_stations = swap(shuffled_stations, index1, index2)

#     new_solution = Solution()
#     new_solution.routes = shuffled_routes
#     new_solution.stations = shuffled_stations
#     return new_solution
