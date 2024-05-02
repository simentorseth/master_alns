from heuristic.alns import Alns
from heuristic.operators import (
    rand_remov_greed_insrt_operator,
    greed_rand_remov_greed_insrt_operator,
    sim_rand_remov_greed_insrt_operator,
)
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import is_feasible, initial_solution, random_solution
from heuristic.visualise import visualise
import random
from heuristic.stats import (
    plot_operator_usage,
    plot_acceptance_rate,
    plot_convergence,
    plot_average_convergence,
    plot_average_operator_usage,
)
import time
from statistics import mean, median, variance


def run_single(
    solution: Solution, operators: list[callable], problem: Problem, *, statistics=False
) -> None:
    alns = Alns(problem, operators, solution)
    start_time = time.perf_counter()
    best, best_cost = alns.single_run()
    end_time = time.perf_counter()
    duration = end_time - start_time
    assert is_feasible(best, problem)
    print(f"Best solution:")
    print(f"Routes: {best.routes}")
    print(f"Stations: {best.stations}")
    print(f"Cost: {best_cost}")
    print(f"Runtime: {duration:.2f}s")
    print("\n")

    if statistics:
        plot_operator_usage(alns._operator_usage, operators)
        plot_acceptance_rate(alns._accepted_solutions, alns.max_iterations)
        plot_convergence(alns._best_costs, alns.max_iterations)
        print(f"Number of feasible solutions: {alns._num_feasible}")
        print(f"Last iteration where best cost was updated: {alns._last_update}")
    ans = input("Do you want to visualise the best solution? (y/n): ").lower()
    if ans == "y":
        visualise(best, problem)
    else:
        print("Exiting program...")


def run_consecutive(
    solution: Solution, operators: list[callable], problem: Problem, statistics=False
) -> None:
    alns = Alns(problem, operators, solution)
    (
        all_time_best,
        all_time_best_cost,
        best_costs,
        all_convergences,
        all_operator_usages,
        all_accepted_solutions,
        runtimes,
    ) = alns.consecutive_run()
    assert is_feasible(all_time_best, problem)
    print(f"Best solution:")
    print(f"Routes: {all_time_best.routes}")
    print(f"Stations: {all_time_best.stations}")
    print(f"Cost: {all_time_best_cost}")
    print(f"Average Runtime: {mean(runtimes):.2f}s")
    print("\n")

    if statistics:
        plot_average_convergence(all_convergences, alns.max_iterations)
        plot_average_operator_usage(all_operator_usages, operators)

        print(f"Mean best cost: {mean(best_costs)}")
        print(f"Median best cost: {median(sorted(best_costs))}")
        print(f"Best cost variance: {variance(best_costs)}")
    # ans = input("Do you want to visualise the best solution? (y/n): ").lower()
    # if ans == "y":
    #     visualise(best, problem)
    # else:
    #     print("Exiting program...")


def main():
    # filename = "./src/instances/instance_testing.csv"
    filename = "./src/instances/westermost_rough_testing.csv"
    problem = Problem(filename)
    random.seed(1)

    operators = [
        sim_rand_remov_greed_insrt_operator,
        greed_rand_remov_greed_insrt_operator,
        rand_remov_greed_insrt_operator,
    ]

    # initial = initial_solution(problem)
    initial = random_solution(problem)
    print(initial.routes.count(0))
    print(len(initial.stations))
    # run_single(initial, operators, problem, statistics=True)
    run_consecutive(initial, operators, problem, statistics=True)


if __name__ == "__main__":
    main()
