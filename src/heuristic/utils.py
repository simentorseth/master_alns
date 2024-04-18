from heuristic.problem import Problem
import logging


def is_feasible(routes: list, stations: list, problem: Problem):
    separators = [i for i, x in enumerate(routes + [0]) if x == 0]
    idx = 0  # start index for current route

    num_tours = len(separators)
    used_time_windows = {w: [] for w in range(int(problem.num_time_windows))}

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
                        if len(used_time_windows[window_index]) == problem.num_vessels:
                            continue
                        else:
                            used_time_windows[window_index].append(i)
                            # feasible = True
                            break  # TODO: Check if this break is correct
                    else:
                        # logging.error(
                        #     f"Time window {window_index} violated for tour {i}. Route duration: {route_duration} hrs, Time window: {time_window}"
                        # )
                        feasible = False
                        break
    return feasible


def cost():
    raise NotImplementedError
