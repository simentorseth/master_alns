from copy import copy
from random import shuffle, choice, random
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import (
    get_to_and_from_costs,
    get_station_assignment,
    initialise_model,
    findmin,
    feasible_inserts,
    insertion_costs,
    cost_of_removal,
)


def swap(elements, index1, index2):
    # TODO: Should this modify inplace instead?
    elements_copy = elements[:]  # shallow copy
    temp1, temp2 = elements_copy[index1], elements_copy[index2]
    elements_copy[index1], elements_copy[index2] = temp2, temp1
    return elements_copy


def shaw_selection(values, options, exclude, p, reverse=False):
    # Exclude specified indices from options
    excl = set(exclude)
    opts = [opt for opt in options if opt not in excl]

    # Exclude specified indices from values similarly
    vals = values[:]
    for index in sorted(exclude, reverse=True):
        if index - 1 < len(vals):  # adjust index for zero-based indexing
            del vals[index - 1]

    # Generate a biased random index
    r = random() ** p
    idx = int(r * len(vals))  # truncating automatically by converting to int

    # Sorting vals to get the node index
    sorted_indices = sorted(range(len(vals)), key=lambda x: vals[x], reverse=reverse)

    # Adjust for cases where idx might be out of bounds (e.g., when r is very small)
    idx = min(idx, len(sorted_indices) - 1)

    # Get the position in the original options list
    node_index = sorted_indices[idx]
    node = opts[node_index]

    return node


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


def rand_remov_greed_insrt_operator(
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


def greed_rand_remov_greed_insrt_operator(
    solution: Solution, num_to_remove: int, problem: Problem
) -> Solution:
    removal_costs = [0.0 for _ in range(problem.num_turbines)]
    tours = []
    current_route = []
    current_station_index = -1
    for node in solution.routes:
        if node == 0:
            current_station_index += 1
            if current_route:
                tours.append(current_route)
                for node in current_route:
                    removal_cost = cost_of_removal(
                        node,
                        current_route,
                        solution.stations[current_station_index],
                        solution.stations,
                        problem,
                    )
                    removal_costs[node - 1] = removal_cost

                current_route = []
        else:
            current_route.append(node)

    cost_reduction = 0
    to_remove = []
    for _ in range(num_to_remove):
        node = shaw_selection(
            removal_costs, problem.turbines, to_remove, p=10, reverse=True
        )
        to_remove.append(node)
        cost_reduction += removal_costs[node - 1]

        # actually remove it here
    for node in to_remove:
        node_idx = solution.routes.index(node)
        remove_tour_idx = solution.routes[: node_idx + 1].count(0)
        remove_tour = tours[remove_tour_idx]
        remove_tour.remove(node)

    shuffle(to_remove)

    for node in to_remove:
        tour = None
        min_cost = float("inf")
        insert = None
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
        if tour is None and insert is None:
            new_tour = [node]
            tours.append(new_tour)
            solution.stations.append(choice(problem.map["Substations"]))
            continue
        tours[tour].insert(insert, node)

    new_solution = Solution()
    new_solution.stations = copy(solution.stations)

    for i in range(len(tours)):
        if len(tours[i]) == 0:
            new_solution.stations.pop(i)
        else:
            tours[i].append(0)

    new_solution.routes = [node for tour in tours if tour for node in tour]

    return new_solution


def sim_rand_remov_greed_insrt_operator(
    solution: Solution, num_to_remove: int, problem: Problem
) -> Solution:
    assert num_to_remove >= 2

    # removal_costs = [0.0 for _ in range(problem.num_turbines)]
    tours = []
    current_route = []
    for node in solution.routes:
        if node == 0:
            if current_route:
                tours.append(current_route)
                current_route = []
        else:
            current_route.append(node)

    to_remove = [choice(problem.turbines)]
    for _ in range(num_to_remove - 1):
        comparison = choice(to_remove)
        node = shaw_selection(
            problem.similarity[comparison - 1][:], problem.turbines, to_remove, p=10
        )
        to_remove.append(node)
        # cost_reduction += removal_costs[node - 1]

        # actually remove it here
    for node in to_remove:
        node_idx = solution.routes.index(node)
        remove_tour_idx = solution.routes[: node_idx + 1].count(0)
        remove_tour = tours[remove_tour_idx]
        remove_tour.remove(node)

    shuffle(to_remove)

    for node in to_remove:
        tour = None
        min_cost = float("inf")
        insert = None
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
        if tour is None and insert is None:
            new_tour = [node]
            tours.append(new_tour)
            solution.stations.append(choice(problem.map["Substations"]))
            continue
        tours[tour].insert(insert, node)

    new_solution = Solution()
    new_solution.stations = copy(solution.stations)

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
