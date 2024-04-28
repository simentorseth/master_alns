from heuristic.alns import Alns
from heuristic.operators import optimal_stations, random_operator, escape
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import is_feasible, random_solution
from heuristic.visualise import visualise
from pprint import pprint
import random
from random import randint


def run_single(problem: Problem, solution: Solution) -> None:
    alns = Alns(
        problem,
        [random_operator],
        solution,
    )

    best, best_cost = alns.single_run()
    assert is_feasible(best, problem)
    print(f"Best solution:")
    print(f"Routes: {best.routes}")
    print(f"Stations: {best.stations}")
    print(f"Cost: {best_cost}")
    print("\n")

    ans = input("Do you want to visualise the best solution? (y/n): ").lower()
    if ans == "y":
        visualise(best, problem)
    else:
        print("Exiting program...")


def run_consecutive(problem: Problem, solution: Solution) -> None:
    alns = Alns(
        problem,
        [random_operator],
        solution,
    )

    best, best_cost, results, mean_results = alns.consecutive_run()
    assert is_feasible(best, problem)
    print(f"Best solution:")
    print(f"Routes: {best.routes}")
    print(f"Stations: {best.stations}")
    print(f"Cost: {best_cost}")
    print(f"Results: {results}")
    print(f"Mean results: {mean_results}")
    print("\n")

    ans = input("Do you want to visualise the best solution? (y/n): ").lower()
    if ans == "y":
        visualise(best, problem)
    else:
        print("Exiting program...")


def main():
    filename = "./src/instances/instance_testing.csv"
    problem = Problem(filename)
    random.seed(1337)

    # solution = None
    # while not solution:
    #     s = random_solution(problem)
    #     if s is not None:
    #         if is_feasible(s, problem):
    #             solution = s
    #             del s
    # initial = solution
    initial = Solution()
    initial.routes = [4, 8, 0, 2, 6, 3, 0, 9, 10, 5, 1, 0, 7, 0]
    initial.stations = [11, 13, 11, 14]

    # run_single(problem, initial)
    run_consecutive(problem, initial)


if __name__ == "__main__":
    main()
