from heuristic.problem import Problem
from heuristic.solution import Solution
import logging
import gurobipy as gp
from random import randint


def is_feasible(solution: Solution, problem: Problem):
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
    window = problem.time_window_assignments[0]
    num_vessels = len(window)
    num_stations = len(set(stations))

    total_cost = 0

    # fixed costs
    total_cost += (
        num_vessels * problem.vessel_cost + num_stations * problem.station_cost
    )

    # sailing costs
    separators = [i for i, x in enumerate(routes + [0]) if x == 0]
    idx = 0  # start index for current route

    for i in range(len(separators)):
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


def initialise_model(to_and_from_costs: list[list[float]], fixed_costs: list[int]):
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
    assignment_matrix = [
        [int(x_values[i * num_destinations + j]) for j in range(num_destinations)]
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
    unvisited = problem.map["Turbines"].copy()
    routes = []
    while len(unvisited) > 0:
        tour_length = randint(1, len(unvisited))
        tour = []
        for _ in range(tour_length):
            turbine = unvisited.pop(randint(0, len(unvisited) - 1))
            tour.append(turbine)
        routes += tour + [0]
    num_tours = len([i for i, x in enumerate(routes) if x == 0])
    stations = [
        problem.map["Substations"][randint(0, len(problem.map["Substations"]) - 1)]
        for _ in range(num_tours)
    ]
    try:
        if num_tours > problem.num_vessels * problem.num_time_windows:
            raise ValueError()
    except ValueError as e:
        print(f"Too many tours!")
        print(
            f"Num tours: {num_tours} > Num vessels: {problem.num_vessels} * Num time windows: {problem.num_time_windows}"
        )
        print(f"Route: {routes}")
        print(f"Stations: {stations}")
        return None
    solution = Solution()
    solution.routes = routes
    solution.stations = stations
    return solution
