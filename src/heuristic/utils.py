from heuristic.problem import Problem
from heuristic.solution import Solution
import logging
import gurobipy as gp
from random import randint, shuffle, choices 
import os
import csv

from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
import numpy as np


def is_feasible(solution: Solution, problem: Problem):
    routes = solution.routes
    stations = solution.stations

    start_index = 0
    tour_index = 0
    for i in range(len(routes)):
        if routes[i] == 0:  # Separator found, indicating the end of a tour
            current_tour = routes[start_index:i]
            if start_index < i:
                # Check if the charge level and route duration is within limits
                charge = problem.charge_capacity
                duration = 0
                for j in range(len(current_tour) + 1):
                    if j == 0:
                        # From station to first node
                        distance = problem.distances[
                            stations[tour_index], current_tour[j]
                        ]
                        travel_time = problem.travel_times[
                            stations[tour_index], current_tour[j]
                        ]
                        demand = 0.0
                    elif j == len(current_tour):
                        # From last node to station
                        distance = problem.distances[
                            stations[tour_index], current_tour[j - 1]
                        ]
                        travel_time = problem.travel_times[
                            stations[tour_index], current_tour[j - 1]
                        ]
                        demand = problem.demands[current_tour[j - 1]]
                    else:
                        # From node to node
                        distance = problem.distances[
                            current_tour[j - 1], current_tour[j]
                        ]
                        travel_time = problem.travel_times[
                            current_tour[j - 1], current_tour[j]
                        ]
                        demand = problem.demands[current_tour[j - 1]]
                    charge -= distance * problem.consumption_rate
                    duration += travel_time + demand
                    if charge < 0 or charge > problem.charge_capacity:
                        return False
                    if duration > 8.0:
                        return False

            # Update for next tour
            start_index = i + 1
            tour_index += 1

    if tour_index > problem.num_vessels * problem.num_time_windows:
        return False
    if tour_index != len(stations):
        return False
    return True


@DeprecationWarning
def feasible(solution: Solution, problem: Problem):
    routes = solution.routes
    stations = solution.stations
    separators = [i for i, x in enumerate(routes) if x == 0]
    idx = 0  # start index for current route

    num_tours = len(separators)
    # used_time_windows = {w: [] for w in range(int(problem.num_time_windows))}

    feasible = True

    for i in range(num_tours):
        # get the current route
        current_route = routes[idx : separators[i]]
        # adjust start index for next iteration
        idx = separators[i] + 1

        if len(current_route) > 0:
            # check if battery level is within limits
            current_charge = problem.charge_capacity
            charge_levels = [0] * len(current_route) + [0]
            for j in range(len(charge_levels)):
                # TODO: Add route duration violation check early?
                if j == 0:
                    charge_levels[j] = round(
                        (
                            current_charge
                            - problem.distances[stations[i], current_route[j]]
                            * problem.consumption_rate
                        ),
                        2,
                    )
                elif j == len(current_route):
                    charge_levels[j] = round(
                        (
                            current_charge
                            - problem.distances[current_route[j - 1], stations[i]]
                            * problem.consumption_rate
                        ),
                        2,
                    )
                else:
                    charge_levels[j] = round(
                        (
                            current_charge
                            - problem.distances[current_route[j - 1], current_route[j]]
                            * problem.consumption_rate
                        ),
                        2,
                    )
                if charge_levels[j] < 0 or charge_levels[j] > problem.charge_capacity:
                    logging.error(
                        f"Battery capacity exceeded for vessel {i + 1}. Battery level: {charge_levels[j]} kWh"
                    )
                    feasible = False
                    break
                current_charge = charge_levels[j]

            if num_tours <= problem.num_vessels * problem.num_time_windows:
                # check if time windows are met
                current_time = 0
                # TODO: Add route duration violation check early?
                arrival_times = [0] * len(current_route) + [0]
                for j in range(len(arrival_times)):
                    if j == 0:
                        arrival_times[j] = round(
                            (
                                current_time
                                + problem.travel_times[stations[i], current_route[j]]
                            ),
                            3,
                        )
                        current_time = arrival_times[j]
                    elif j == len(current_route):
                        arrival_times[j] = round(
                            (
                                current_time
                                + problem.travel_times[
                                    current_route[j - 1], stations[i]
                                ]
                            ),
                            3,
                        )
                    else:
                        arrival_times[j] = round(
                            (
                                current_time
                                + problem.demands[current_route[j - 1]]
                                + problem.travel_times[
                                    current_route[j - 1], current_route[j]
                                ]
                            ),
                            3,
                        )
                        current_time = arrival_times[j]

                route_duration = arrival_times[-1]
                for window_index, time_window in problem.time_windows.items():
                    if route_duration <= time_window[1] - time_window[0]:
                        # skip if all vessels are already assigned to this time window
                        if (
                            len(problem.time_window_assignments[window_index])
                            == problem.num_vessels
                        ):
                            continue
                        else:
                            problem.assign_time_window(window_index, i)
                            # used_time_windows[window_index].append(i)
                            # feasible = True
                            break  # TODO: Check if this break is correct
                    else:
                        # logging.error(
                        #     f"Time window {window_index} violated for tour {i}. Route duration: {route_duration} hrs, Time window: {time_window}"
                        # )
                        feasible = False
                        break
    return feasible


def cost(solution: Solution, problem: Problem):
    # this should work as intended
    routes = solution.routes
    stations = solution.stations
    window = {w: [] for w in range(int(problem.num_time_windows))}

    total_cost = 0

    # sailing costs
    separators = [i for i, x in enumerate(routes) if x == 0]
    idx = 0  # start index for current route

    current_window = 0
    for i in range(len(separators)):
        # assign tour to window
        if len(window[current_window]) >= problem.num_vessels:
            current_window += 1
        window[current_window].append(i)
        # get the current route
        current_route = routes[idx : separators[i]]
        # adjust start index for next iteration
        idx = separators[i] + 1
        # check if current route is empty
        if len(current_route) > 0:
            # add the sailing costs for the current route
            for j in range(len(current_route) - 1):
                total_cost += problem.sailing_costs[
                    current_route[j], current_route[j + 1]
                ]
            # add the sailing costs to and from the station
            total_cost += problem.sailing_costs[stations[i], current_route[0]]
            total_cost += problem.sailing_costs[current_route[-1], stations[i]]

    # fixed costs
    num_used_vessels = len(window[0])
    num_stations = len(set(stations))

    total_cost += (
        num_used_vessels * problem.vessel_cost + num_stations * problem.station_cost
    )

    return total_cost


def is_valid(solution: Solution, problem: Problem):
    routes = solution.routes
    stations = solution.stations
    # check if the solution is empty
    if len(routes) == 0 or len(stations) == 0:
        return False
    # check if all nodes are visited
    visited_nodes = []
    for node in routes:
        if node == 0:
            continue
        if node not in visited_nodes:
            visited_nodes.append(node)
        else:
            return False  # we have a duplicate node

    if len(visited_nodes) != len(problem.map["Turbines"]):
        return False
    # check if the amount of tours and stations match
    num_tours = len([i for i, x in enumerate(routes + [0]) if x == 0])
    if num_tours != len(stations):
        return False
    # otherwise
    return True


def get_to_and_from_costs(solution: Solution, problem: Problem):
    to_and_from_costs = []

    current_route = []
    for node in solution.routes:
        if node == 0:
            if current_route:
                start, end = current_route[0], current_route[-1]
                costs = []
                for station in problem.stations:
                    cost = problem.to_and_from_costs[start][end][station]
                    costs.append(cost)
                current_route = []
                to_and_from_costs.append(costs)
        else:
            current_route.append(node)
    return to_and_from_costs


@DeprecationWarning
def get_to_and_from_costs_old(solution: Solution, problem: Problem):
    routes = solution.routes

    # indices for the separators
    separators = [i for i, x in enumerate(routes + [0]) if x == 0]
    # start index for current route
    idx = 0

    table = []
    num_tours = len(separators)
    for i in range(num_tours):
        # get the current route
        current_route = routes[idx : separators[i]]
        # adjust start index for next iteration
        idx = separators[i] + 1
        if len(current_route) > 0:
            to_and_from_costs = []
            start, end = current_route[0], current_route[-1]
            for station in problem.map["Substations"]:
                to_and_from_costs.append(
                    round(
                        problem.sailing_costs[start, station]
                        + problem.sailing_costs[end, station],
                        1,
                    )
                )
            table.append(to_and_from_costs)
    return table


def initialise_model_old(to_and_from_costs: list[list[float]], fixed_costs: list[int]):
    m = gp.Model("Optimal Station Assignment")
    x = m.addVars(
        [
            (i, j)
            for i in range(len(to_and_from_costs))
            for j in range(len(fixed_costs))
        ],
        vtype=gp.GRB.BINARY,
        name="x",
    )
    y = m.addVars(
        [j for j in range(len(fixed_costs))],
        vtype=gp.GRB.BINARY,
        name="y",
    )
    m.setObjective(
        gp.quicksum(
            to_and_from_costs[i][j] * x[i, j]
            for i in range(len(to_and_from_costs))
            for j in range(len(fixed_costs))
        )
        + gp.quicksum(fixed_costs[j] * y[j] for j in range(len(fixed_costs))),
        gp.GRB.MINIMIZE,
    )
    m.addConstrs(
        gp.quicksum(x[i, j] for j in range(len(fixed_costs))) == 1
        for i in range(len(to_and_from_costs))
    )
    m.addConstrs(
        gp.quicksum(x[i, j] for i in range(len(to_and_from_costs)))
        <= y[j] * len(to_and_from_costs)
        for j in range(len(fixed_costs))
    )
    return m, x, y


def initialise_model(num_tours: int, num_stations: int, env):
    m = gp.Model("Optimal Station Assignment", env)
    x = m.addVars(
        [(i, j) for i in range(num_tours) for j in range(num_stations)],
        vtype=gp.GRB.BINARY,
        name="x",
    )
    y = m.addVars(
        [j for j in range(num_stations)],
        vtype=gp.GRB.BINARY,
        name="y",
    )
    # Initially set placeholder objective with zeros which will be updated per iteration
    m.setObjective(
        gp.quicksum(0 * x[i, j] for i in range(num_tours) for j in range(num_stations))
        + gp.quicksum(0 * y[j] for j in range(num_stations)),
        gp.GRB.MINIMIZE,
    )
    m.addConstrs(
        gp.quicksum(x[i, j] for j in range(num_stations)) == 1 for i in range(num_tours)
    )
    m.addConstrs(
        gp.quicksum(x[i, j] for i in range(num_tours)) <= y[j] * num_tours
        for j in range(num_stations)
    )

    return m, x, y


def update_model(
    m: gp.Model,
    x: gp.Var,
    y: gp.Var,
    to_and_from_costs: list[list[float]],
    fixed_costs: list[int],
):
    # Reset model to clear previous solution
    m.reset()
    for i, j in x.keys():
        if i < len(to_and_from_costs):
            x[i, j].obj = to_and_from_costs[i][j]
        else:
            x[i, j].obj = 0
    # Update objective function coefficients
    # for i, j in x.keys():
    #     x[i, j].obj = to_and_from_costs[i][j]
    # for j in y.keys():
    #     y[j].obj = fixed_costs[j]

    # Optimize the model with the new parameters
    m.optimize()

    return m


def get_station_assignment(
    model: gp.Model,
    num_sources: int,
    num_destinations: int,
    problem: Problem,
):
    # Retrieve the x[i, j] values from the model after optimization
    x_values = model.getAttr("X", model.getVars())

    # Create a 2D matrix to store the values of x[i, j]
    # assignment_matrix = [
    #     [int(x_values[i * num_destinations + j]) for j in range(num_destinations)]
    #     for i in range(num_sources)
    # ]
    assignment_matrix = [
        [1 if x_values[i * num_destinations + j] > 0.5 else 0 for j in range(num_destinations)]
        for i in range(num_sources)
    ]
    # Get the assignment of stations to each tour
    assignment = [0 for _ in range(num_sources)]
    for tour_idx in range(len(assignment_matrix)):
        for i, value in enumerate(assignment_matrix[tour_idx]):
            if value == 1:
                assignment[tour_idx] = problem.map["Substations"][i]
                break

    return assignment


def findmin(itr: list[int]) -> tuple[float, int]:
    if not itr:  # Check if the iterable is empty
        return None

    min_value: int = itr[0]
    min_index: int = 0

    for index, value in enumerate(itr):
        if value < min_value:
            min_value = value
            min_index = index

    return min_value, min_index


def insertion_costs(
    tour: list[int],
    station: int,
    node: int,
    insert_indices: list[int],
    problem: Problem,
) -> list[float]:
    costs = []
    if len(tour) == 0:
        # TODO: Unsure about this right here, double the work optimal station operator???
        cost = problem.sailing_costs[station, node]
        cost += problem.sailing_costs[node, station]
        costs.append(cost)
        return costs
    if len(tour) == 1:
        cost = problem.sailing_costs[node, tour[0]]
        costs.append(cost)
        return costs
    for i in insert_indices:
        cost = 0
        if i == 0:
            cost += problem.sailing_costs[node, tour[0]]
        elif i == len(tour):
            cost += problem.sailing_costs[tour[-1], node]
        else:
            cost += problem.sailing_costs[tour[i - 1], node]
            cost += problem.sailing_costs[node, tour[i]]
        costs.append(cost)
    return costs


@DeprecationWarning
def charge_levels_are_feasible(tour: list[int], station: int, problem: Problem) -> bool:
    current_charge = problem.charge_capacity
    charge_levels = [0] * len(tour) + [0]
    for j in range(len(charge_levels)):
        if j == 0:
            charge_levels[j] = round(
                (
                    current_charge
                    - problem.distances[station, tour[j]] * problem.consumption_rate
                ),
                2,
            )
        elif j == len(tour):
            charge_levels[j] = round(
                (
                    current_charge
                    - problem.distances[tour[j - 1], station] * problem.consumption_rate
                ),
                2,
            )
        else:
            charge_levels[j] = round(
                (
                    current_charge
                    - problem.distances[tour[j - 1], tour[j]] * problem.consumption_rate
                ),
                2,
            )
        if charge_levels[j] < 0 or charge_levels[j] > problem.charge_capacity:
            return False
        current_charge = charge_levels[j]
    return True


def feasible_tour(tour: list[int], station: int, problem: Problem) -> bool:
    complete_tour = [station] + tour + [station]
    charge = problem.charge_capacity
    duration = 0
    for i in range(len(complete_tour) - 1):
        charge -= (
            problem.distances[complete_tour[i], complete_tour[i + 1]]
            * problem.consumption_rate
        )
        duration += (
            problem.travel_times[complete_tour[i], complete_tour[i + 1]]
            + problem.demands[complete_tour[i]]
        )
        if charge < 0 or charge > problem.charge_capacity:
            return False  # no feasible insertions
        if (
            duration > 8.0  # should it be >= or strictly > ?
        ):  # hard coded time window length, should be changed to problem specific:
            return False  # no feasible insertionscharge = problem.charge_capacity
    return True


def feasible_inserts(
    tour: list[int], station: int, node: int, problem: Problem
) -> list[int]:
    complete_tour = [station] + tour + [station]
    charge = problem.charge_capacity
    duration = 0
    for i in range(len(complete_tour) - 1):
        charge -= (
            problem.distances[complete_tour[i], complete_tour[i + 1]]
            * problem.consumption_rate
        )
        duration += (
            problem.travel_times[complete_tour[i], complete_tour[i + 1]]
            + problem.demands[complete_tour[i]]
        )
        if charge < 0 or charge > problem.charge_capacity:
            return []  # no feasible insertions
        if (
            duration >= 8.0  # should it be >= or strictly > ?
        ):  # hard coded time window length, should be changed to problem specific:
            return []  # no feasible insertions

    insert_indices = []
    for i in range(1, len(complete_tour)):
        insert_charge = 0
        insert_duration = 0
        insert_charge += (
            problem.distances[complete_tour[i - 1], node] * problem.consumption_rate
        )
        insert_charge += (
            problem.distances[node, complete_tour[i]] * problem.consumption_rate
        )
        insert_duration += problem.travel_times[complete_tour[i - 1], node]
        insert_duration += (
            problem.travel_times[node, complete_tour[i]] + problem.demands[node]
        )
        if (
            charge - insert_charge > 0
            or charge - insert_charge < problem.charge_capacity
        ):
            if duration + insert_duration <= 8.0:
                insert_indices.append(i - 1)
    return insert_indices


def random_solution(problem: Problem) -> Solution:
    # max_tours = problem.num_vessels * problem.num_time_windows
    max_tours = problem.num_turbines
    nodes = problem.turbines.copy()
    depots = problem.stations.copy()

    solution = None

    while True:
        num_tours = randint(1, max_tours)
        approx_size = len(nodes) // num_tours
        remainder = len(nodes) % num_tours

        shuffle(nodes)
        tours = []
        start_index = 0

        for i in range(num_tours):
            if i < remainder:
                end_index = start_index + approx_size + 1
            else:
                end_index = start_index + approx_size
            tours.append(nodes[start_index:end_index])
            start_index = end_index

    
        stations = choices(depots, k=num_tours)
        routes = []
        for tour in tours:
            tour.append(0)
            routes.extend(tour)

        temporary = Solution()
        temporary.routes = routes
        temporary.stations = stations
        if is_feasible(temporary, problem):
            solution = temporary
            break

    return solution


def cost_of_removal(
    node: int, tour: list[int], station: int, stations: list[int], problem: Problem
) -> float:
    removal_cost = 0

    if len(tour) == 0:
        raise Exception("Empty tour when calculating removal cost!")

    if len(tour) == 1:
        removal_cost += problem.to_and_from_costs[node][node][station]
        if stations.count(station) == 1:
            removal_cost += problem.station_cost
        return removal_cost

    where_in_tour = tour.index(node)

    # if the node to remove is at the start of the tour
    if where_in_tour == 0:
        # only the forward sailing cost contributes
        removal_cost += problem.sailing_costs[node, tour[where_in_tour + 1]]
    # if the node to remove is at the end of the tour
    elif where_in_tour == len(tour) - 1:
        # only the backward sailing cost contributes
        removal_cost += problem.sailing_costs[tour[where_in_tour - 1], node]
    # otherwise
    else:
        # the forward sailing cost contributes
        removal_cost += problem.sailing_costs[node, tour[where_in_tour + 1]]
        # and the backward sailing cost contributes
        removal_cost += problem.sailing_costs[tour[where_in_tour - 1], node]

    return removal_cost


def initial_solution(problem: Problem) -> Solution:
    # First: Clustering with the stations as centroids

    cluster_assignment = [-1 for _ in range(problem.num_turbines)]

    for i, node in enumerate(problem.turbines):
        min_distance = float("inf")
        assigned_station = -1
        for j, station_idx in enumerate(problem.stations):
            distance = problem.distances[node, station_idx]
            if distance < min_distance:
                min_distance = distance
                assigned_station = j
        cluster_assignment[i] = assigned_station

    clustering = [[] for _ in range(problem.num_stations)]
    for i, assignment in enumerate(cluster_assignment):
        clustering[assignment].append(i + 1)

    # Second: Clarke & Wright savings algorithm

    solution = Solution()

    for station_idx, cluster in enumerate(clustering):
        station = problem.stations[station_idx]
        # Initialize active routes set with all initial individual routes
        active_routes = set(tuple([node]) for node in cluster)
        # Route map to keep track of which route each node currently belongs to
        routes = {node: [node] for node in cluster}
        # Keep track of merged routes
        merged_routes = set()
        # Calculate savings
        savings = {}
        for node1 in cluster:
            for node2 in cluster:
                if node1 != node2:
                    ordered_pair = tuple(sorted((node1, node2)))
                    if ordered_pair not in savings:
                        saving = (
                            problem.distances[station, node1]
                            + problem.distances[station, node2]
                            - problem.distances[node1, node2]
                        )
                        savings[(node1, node2)] = saving
        # Sort savings in descending order
        sorted_savings = dict(sorted(savings.items(), key=lambda x: x[1], reverse=True))
        for (i, j), saving in sorted_savings.items():
            # Retrieve current routes for i and j
            route_i = tuple(routes[i])
            route_j = tuple(routes[j])

            # Check if either route has been merged or if they are the same route
            if (
                route_i in merged_routes
                or route_j in merged_routes
                or route_i == route_j
            ):
                continue
            # Check if i is the last element of its route and j is the first element of its route
            if routes[i][-1] == i and routes[j][0] == j:
                # Merge routes
                new_route = routes[i] + routes[j]
                new_route_tuple = tuple(new_route)
                # Check if route is feasible
                if feasible_tour(new_route, station, problem):
                    # Update the route mapping to the new merged route for all involved nodes
                    for node in routes[i] + routes[j]:
                        routes[node] = new_route

                    # Update active routes and merged routes tracking
                    active_routes.discard(route_i)
                    active_routes.discard(route_j)
                    active_routes.add(new_route_tuple)
                    merged_routes.add(route_i)
                    merged_routes.add(route_j)
        # Extend the initial solution
        for tour in active_routes:
            padded_tour = list(tour) + [0]
            solution.routes.extend(padded_tour)
            solution.stations.append(station)

    return solution


def save_solution(
    path: str,
    objective_value: float,
    avg_objective_value: float,
    avg_runtime: float,
    solution: Solution,
    initial: Solution,
    problem: Problem,
):
    with open(path, "w") as f:
        f.write(f"{os.path.basename(problem._filename)[:-4]}\n")
        f.write(f"Objective value: {objective_value:.2f}\n")
        f.write(f"Avg. Objective value: {avg_objective_value:.2f}\n")
        f.write(f"Avg. Runtime: {avg_runtime:.2f} s\n")
        f.write(f"Tours:\n")
        f.write(f"{solution.routes}\n")
        f.write(f"Stations:\n")
        f.write(f"{solution.stations}\n")
        f.write(f"Initial solution:\n")
        f.write(f"Routes: {initial.routes}\n")
        f.write(f"Stations: {initial.stations}\n")


def save_run(
    path: str,
    objective_value: float,
    avg_objective_value: float,
    avg_runtime: float,
    problem: Problem,
    num_stations: int=0,
):
    with open(path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        if num_stations == 0:
            writer.writerow(
                [problem._filename, objective_value, avg_objective_value, avg_runtime]
            )
        else:
            writer.writerow(
                [problem._filename, num_stations, objective_value, avg_objective_value, avg_runtime]
            )
        # writer.writerow(
        #     [problem._filename, objective_value, avg_objective_value, avg_runtime]
        # )