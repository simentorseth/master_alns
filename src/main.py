from heuristic.utils import is_feasible
from heuristic.problem import Problem
from heuristic.visualise import visualise
from pprint import pprint
from random import randint


def random_solution(problem: Problem) -> tuple[list[int], list[int]]:
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
        problem.map["Substations"][randint(1, len(problem.map["Substations"]) - 1)]
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
        return [], []
    return routes[:-1], stations


def main():
    """
    Numbers are based on the technical specification
    given for the Rem Energy CSOV, found at
    https://www.remoffshore.no/fleet/rem-energy/
    """
    file = "./src/instances/instance_testing.csv"
    problem = Problem(
        file,
        # num_vessels=3,
        # charge_capacity=2 * 341,  # kWh
        # velocity=5,  # m/s (2.57 m/s <--> 5 knots
        # consumption_rate=0.016,  # kWh/m
        # vessel_cost=1000,
        # station_cost=1000,
        # num_time_windows=3,
    )
    # route = [1, 8, 2, 0, 3, 5, 9, 0, 7, 4, 6, 10]
    # stations = [11, 12, 11]

    # pprint(
    #     is_feasible(
    #         [1, 2, 3, 0, 4, 5, 6, 0, 7, 8, 9, 10],
    #         [11, 11, 11],
    #         problem,
    #     )
    # )
    num_solutions = 1000000
    count = 0
    for _ in range(num_solutions):
        routes, stations = random_solution(problem)
        if routes and stations:
            if is_feasible(routes, stations, problem):
                count += 1
                if num_solutions <= 10:
                    ...
                    # visualise(routes, stations, problem)
    print(f"Feasible solutions: {count}/{num_solutions} | {count/num_solutions:.2%}%")


if __name__ == "__main__":
    main()
