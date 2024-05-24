from heuristic.alns import Alns
from heuristic.alns_sa import AlnsSA
from heuristic.operators import (
    rand_remov_greed_insrt_operator,
    greed_rand_remov_greed_insrt_operator,
    sim_rand_remov_greed_insrt_operator,
)
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import (
    is_feasible,
    initial_solution,
    random_solution,
    cost,
    save_run,
    save_solution,
)
from heuristic.visualise import visualise
import random
from heuristic.stats import (
    plot_operator_usage,
    plot_acceptance_rate,
    plot_convergence,
    plot_average_convergence,
    plot_average_operator_usage,
)
from heuristic.initial import create_initial_solution
import time
from statistics import mean
import os
import argparse


def run_once(
    solution: Solution,
    operators: list[callable],
    problem: Problem,
    *,
    statistics: bool = False,
) -> None:
    alns = Alns(problem, operators, solution)
    start_time = time.perf_counter()
    best_solution, best_cost = alns.run()
    end_time = time.perf_counter()
    duration = end_time - start_time

    try:
        assert is_feasible(best_solution, problem)
        assert cost(best_solution, problem) == best_cost

        print(f"Best solution:")
        print(best_solution)
        print(f"Cost: {best_cost}")
        print(f"Runtime: {duration:.2f}s")
        print("\n")

        if statistics:
            stats = alns.get_statistics()
            parameters = alns.get_parameters()

            plot_operator_usage(stats["operator_usage"], operators)
            plot_acceptance_rate(stats["accepted_solutions"], parameters["max_iterations"])
            plot_convergence(stats["best_costs"], parameters["max_iterations"])
            print(f"Number of feasible solutions: {stats['num_feasible']}")
            print(f"Last iteration where best cost was updated: {stats['last_update']}")

            while True:
                ans = input(
                    "Do you want to visualise the best solution? (y/n): "
                ).lower()
                if ans == "y":
                    visualise(best_solution, problem)
                    break
                elif ans == "n":
                    print("Exiting program...")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

    except AssertionError:
        print(f"{problem._filename} is infeasible!!!")
        if cost(best_solution, problem) != best_cost:
            print("Cost mismatch!!!")
            print("Cost: ", best_cost)
            print("Calculated cost: ", cost(best_solution, problem))
            print(best_solution)


def run_ten(
    solution: Solution,
    operators: list[callable],
    problem: Problem,
    statistics: bool = False,
):
    all_time_best_solution = None
    all_time_best_cost = float("inf")
    costs = []
    runtimes = []

    for i in range(10):
        alns = Alns(problem, operators, solution)
        start_time = time.perf_counter()
        best_solution, best_cost = alns.run()
        end_time = time.perf_counter()
        duration = end_time - start_time

        try:       
            assert is_feasible(best_solution, problem)
            assert cost(best_solution, problem) == best_cost

            costs.append(best_cost)
            runtimes.append(duration)

            if best_cost < all_time_best_cost:
                all_time_best_cost = best_cost
                all_time_best_solution = best_solution
        except AssertionError:
            print(f"{problem._filename} is infeasible. Run {i + 1} failed.")
            if cost(best_solution, problem) != best_cost:
                print("Cost mismatch!!!")
                print("Cost: ", best_cost)
                print("Calculated cost: ", cost(best_solution, problem))
                print(best_solution)
        
    return all_time_best_solution, all_time_best_cost, costs, runtimes


def run_alns_sa_once(
    solution: Solution,
    operators: list[callable],
    problem: Problem,
    statistics: bool = False,
):
    alns_sa = AlnsSA(problem, operators, solution)
    start_time = time.perf_counter()
    best_solution, best_cost = alns_sa.single_run()
    end_time = time.perf_counter()
    duration = end_time - start_time

    try:
        assert is_feasible(best_solution, problem)
        assert cost(best_solution, problem) == best_cost

        print(f"Best solution:")
        print(best_solution)
        print(f"Cost: {best_cost}")
        print(f"Runtime: {duration:.2f}s")
        print("\n")

        if statistics:
            plot_operator_usage(alns_sa._operator_usage, operators)
            plot_acceptance_rate(alns_sa._accepted_solutions, alns_sa.max_iterations)
            plot_convergence(alns_sa._best_costs, alns_sa.max_iterations)
            print(f"Number of feasible solutions: {alns_sa._num_feasible}")
            print(f"Last iteration where best cost was updated: {alns_sa._last_update}")
            while True:
                ans = input(
                    "Do you want to visualise the best solution? (y/n): "
                ).lower()
                if ans == "y":
                    visualise(best_solution, problem)
                    break
                elif ans == "n":
                    print("Exiting program...")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

    except AssertionError:
        print(f"{problem._filename} is infeasible!!!")
        if cost(best_solution, problem) != best_cost:
            print("Cost mismatch!!!")
            print("Cost: ", best_cost)
            print("Calculated cost: ", cost(best_solution, problem))
            print(best_solution)


def small_main():
    # If testing, set the seed
    seed = 1337
    random.seed(seed)

    # Define the operators
    operators = [
        sim_rand_remov_greed_insrt_operator,
        greed_rand_remov_greed_insrt_operator,
        rand_remov_greed_insrt_operator,
    ]

    instances_path = (
        "/Users/simentorseth/Developer/thesis/lrptw_instances/test/small/"
    )
    save_path = (
        "/Users/simentorseth/Developer/thesis/alns_solutions/test/small/"
    )
    # results_path = "/Users/simentorseth/Developer/thesis/alns_solutions/small_instances/results.csv"
    results_path = "/Users/simentorseth/Developer/thesis/alns_solutions/test/small/results_2024-05-22.csv"

    for num_turbines in [5, 10, 15]:
        path = instances_path + str(num_turbines)
        for file in sorted(os.listdir(path)):
            print("Running instance: ", file)
            filename = path + "/" + file
            problem = Problem(filename)
            initial = create_initial_solution(problem)
            assert is_feasible(initial, problem)
            print("Cost of initial solution:")
            print(f"{cost(initial, problem)}")

            all_time_best_solution, all_time_best_cost, costs, runtimes = run_ten(
            initial, operators, problem
            )

            # print("All time best solution:")
            # print(all_time_best_solution)
            print("All time best objective value:")
            print(round(all_time_best_cost, 2))
            print("Average objective value:")
            print(round(mean(costs), 2))
            print("Average runtime:")
            print(round(mean(runtimes), 2))
            print("\n")

            save_run(
                results_path, all_time_best_cost, mean(costs), mean(runtimes), problem,
            )

            save_solution(
                save_path + str(num_turbines) + "/" + file[:-4] + ".txt", all_time_best_cost, mean(costs), mean(runtimes), all_time_best_solution, initial, problem)


def initial_test_main():
    path = "/Users/simentorseth/Developer/thesis/lrptw_instances/tuning_instances/"
    for file in sorted(os.listdir(path)):
        if file == ".DS_Store":
            continue
        problem = Problem(path + file)
        initial = create_initial_solution(problem)
        f, r = is_feasible(initial, problem)
        print(f"{os.path.basename(file)},{f},{r}")

def tuning_main():
    operators = [
        sim_rand_remov_greed_insrt_operator,
        greed_rand_remov_greed_insrt_operator,
        rand_remov_greed_insrt_operator,
    ]

    tuning_instances = "/Users/simentorseth/Developer/thesis/parameter_tuning_instances.txt"
    path = "/Users/simentorseth/Developer/thesis/lrptw_instances/"
    for file in os.listdir(path):
        print("Running instance: ", file)
        filename = file
        problem = Problem(filename)
        initial = create_initial_solution(problem)
        assert is_feasible(initial, problem)
        print("Cost of initial solution:")
        print(f"{cost(initial, problem)}")

        all_time_best_solution, all_time_best_cost, costs, runtimes = run_ten(
        initial, operators, problem
        )

        print("All time best objective value:")
        print(round(all_time_best_cost, 2))
        print("Average objective value:")
        print(round(mean(costs), 2))
        print("Average runtime:")
        print(round(mean(runtimes), 2))
        print("\n")

        save_path = ("/Users/simentorseth/Developer/thesis/alns_solutions/test/large/")
        results_path = "/Users/simentorseth/Developer/thesis/alns_solutions/test/large/results_2024-05-22.csv"

        save_run(
            results_path, all_time_best_cost, mean(costs), mean(runtimes), problem,
        )

        save_solution(
            save_path + file[:-4] + ".txt", all_time_best_cost, mean(costs), mean(runtimes), all_time_best_solution, initial, problem)


if __name__ == "__main__":
    initial_test_main()