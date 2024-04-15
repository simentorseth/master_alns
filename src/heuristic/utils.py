import logging
from problem import Problem


def feasible(routes: list, stations: list, problem: Problem):
    separators = [i for i, x in enumerate(routes + [0]) if x == 0]
    idx = 0  # start index for current route

    num_tours = len(separators)
    used_time_windows = []

    for i in range(num_tours):
        # get the current route
        current_route = routes[idx : separators[i]]
        # adjust start index for next iteration
        idx = separators[i] + 1

        if len(current_route) > 0:
            # check if battery level is within limits
            current_charge = problem.charge_capacity
            charge_levels = [current_charge] * len(current_route)
            for j in range(len(current_route) - 1):
                charge_levels[j] = (
                    current_charge
                    - problem.distances[current_route[j], current_route[j + 1]]
                    * problem.consumption_rate
                )
                if charge_levels[i] < 0 or charge_levels[i] > problem.charge_capacity:
                    logging.error(f"Battery capacity exceeded for vessel {i}")
                    return False
                current_charge = charge_levels[i]

            if num_tours <= problem.num_vessels * problem.num_time_windows:
                # check if time windows are met
                current_time = 0
                arrival_times = [0] * len(current_route) + [0]
                for j in range(len(arrival_times)):
                    if j == 0:
                        arrival_times[j] = (
                            current_time
                            + problem.travel_times[stations[i], current_route[j]]
                        )
                        current_time = arrival_times[j]
                    elif j == len(current_route):
                        arrival_times[j] = (
                            current_time
                            + problem.travel_times[current_route[j - 1], stations[i]]
                        )
                    else:
                        arrival_times[j] = (
                            current_time
                            + problem.demands[current_route[j - 1]]
                            + problem.travel_times[
                                current_route[j - 1], current_route[j]
                            ]
                        )
                        current_time = arrival_times[j]

                route_duration = arrival_times[-1]
                for window_index, time_window in problem.time_windows.items():
                    if route_duration <= time_window[1] - time_window[0]:
                        used_time_windows.append(window_index)
                        # TODO: Remove the early return and update a boolean value instead
                        return True
                else:
                    logging.error(
                        f"Time window {window_index} violated for vessel {i}. Route duration: {route_duration}, Time window: {time_window}"
                    )
                    return False
    return True


def route_distance(route: list[int], problem: Problem):
    distance = 0
    for i in range(len(route) - 1):
        distance += problem.distances[route[i], route[i + 1]]
    return distance


def cost():
    raise NotImplementedError
