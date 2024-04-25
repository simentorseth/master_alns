from heuristic.alns import Alns
from heuristic.operators import shuffle
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import is_feasible, cost
from heuristic.visualise import visualise
from pprint import pprint
from random import randint


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
    solution.routes = routes[:-1]
    solution.stations = stations
    return solution


def main():
    filename = "./src/instances/instance_testing.csv"
    problem = Problem(filename)

    solution = None
    while not solution:
        s = random_solution(problem)
        if s is not None:
            if is_feasible(s, problem):
                solution = s
                del s
    initial = solution
    alns = Alns(
        problem,
        [shuffle],
        initial,
    )
    # alns.search()
    # best, best_cost = alns.get_best()
    # print(best)
    # print(f"Cost of best solution: {best_cost}")

    best, best_cost, results, mean = alns.consecutive_run()
    print(f"Best solution:")
    print(f"Routes: {best.routes}")
    print(f"Stations: {best.stations}")
    print(f"Cost: {best_cost}")
    print("\n")
    print(f"Results:")
    print(results)
    print("\n")
    print(f"Stats:")
    print(f"Mean cost: {mean}")

    # num_solutions = 1000
    # count = 0
    # for _ in range(num_solutions):
    #     routes, stations = random_solution(problem)
    #     if routes and stations:
    #         problem.time_window_assignments = {
    #             w: [] for w in range(int(problem.num_time_windows))
    #         }
    #         if is_feasible(routes, stations, problem):
    #             print(routes)
    #             print(stations)
    #             pprint(problem.time_window_assignments)
    #             print(cost(stations, problem))
    #             print("\n")
    #             count += 1
    #             if num_solutions <= 10:
    #                 # visualise(routes, stations, problem)
    #                 ...
    # print(f"Feasible solutions: {count}/{num_solutions} | {count/num_solutions:.2%}%")

    # routes = [6, 5, 0, 9, 3, 0, 1, 4, 10, 0, 2, 7, 8]
    # stations = [12, 12, 12, 12]
    # print((routes, stations))
    # print(shuffle((routes, stations), problem))


if __name__ == "__main__":
    main()
