from copy import copy
from random import shuffle, choice
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import (
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
    fixed_costs = [problem._station_cost for _ in range(len(problem.stations))]

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
    separators = [i for i, x in enumerate(routes) if x == 0]
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

    turbines = problem.turbines.copy()
    to_remove = []
    for _ in range(num_remove):
        node = choice(turbines)
        to_remove.append(node)
        turbines.remove(node)

    for node in to_remove:
        node_idx = routes.index(node)
        remove_tour_idx = routes[: node_idx + 1].count(0)
        remove_tour = tours[remove_tour_idx]
        remove_tour.remove(node)

    shuffle(to_remove)
    return to_remove, tours


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
                costs: list[float] = insertion_costs(
                    current_tour, solution.stations[i], node, insert_indices, problem
                )
                curr_min_cost, idx = findmin(costs)
                if curr_min_cost < min_cost:
                    min_cost = curr_min_cost
                    tour = i
                    insert = insert_indices[idx]
            else:
                new_tour = [node]
                tours.append(new_tour)
                continue
        tours[tour].insert(insert, node)

    # this is old, does not work
    for i in range(len(tours)):
        if i == len(tours) - 1:
            continue
        else:
            tours[i].append(0)

    new_solution = Solution()
    new_solution.routes = [node for tour in tours for node in tour]
    new_solution.stations = copy(solution.stations)
    return new_solution


def random_greedy_operator(
    solution: Solution, num_remove: int, problem: Problem
) -> Solution:
    routes = solution.routes.copy()
    stations = solution.stations.copy()

    # indices of the tour separators
    separators = [i for i, x in enumerate(routes) if x == 0]
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
        remove_tour_idx = routes[: node_idx + 1].count(0)
        remove_tour = tours[remove_tour_idx]
        remove_tour.remove(node)

    shuffle(to_remove)

    for node in to_remove:
        tour = None
        min_cost = float("inf")
        insert = None
        for i, current_tour in enumerate(tours):
            insert_indices = feasible_inserts(current_tour, stations[i], node, problem)
            if len(insert_indices) > 0:
                costs = insertion_costs(
                    current_tour, stations[i], node, insert_indices, problem
                )
                curr_min_cost, idx = findmin(costs)
                if curr_min_cost < min_cost:
                    min_cost = curr_min_cost
                    tour = i
                    insert = insert_indices[idx]
        if tour is None and insert is None:
            new_tour = [node]
            tours.append(new_tour)
            stations.append(choice(problem.map["Substations"]))
            continue
        tours[tour].insert(insert, node)

    new_solution = Solution()
    new_solution.stations = copy(stations)

    for i in range(len(tours)):
        if len(tours[i]) == 0:
            new_solution.stations.pop(i)
        else:
            tours[i].append(0)

    new_solution.routes = [node for tour in tours if tour for node in tour]

    return new_solution


def escape(solution: Solution, num_remove: int, problem: Problem) -> Solution:
    removed, tours = random_removal(solution, num_remove, problem)
    for node in removed:
        inserted = False
        for i, current_tour in enumerate(tours):
            insert_indices = feasible_inserts(
                current_tour, solution.stations[i], node, problem
            )
            if len(insert_indices) > 0:
                current_tour.insert(choice(insert_indices), node)
                inserted = True
                break
        if not inserted:
            # raise Exception("No feasible insertions found")
            new_tour = [node]
            tours.append(new_tour)
            solution.stations.append(choice(problem.stations))

    new_solution = Solution()
    new_solution.stations = copy(solution.stations)

    for i in range(len(tours)):
        if len(tours[i]) == 0:
            new_solution.stations.pop(i)
        else:
            tours[i].append(0)

    new_solution.routes = [node for tour in tours if tour for node in tour]

    return new_solution
