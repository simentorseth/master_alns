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
import time
from statistics import mean
import os


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


def main():
    # If testing, set the seed
    random.seed(1337)

    # Define the operators
    operators = [
        sim_rand_remov_greed_insrt_operator,
        greed_rand_remov_greed_insrt_operator,
        rand_remov_greed_insrt_operator,
    ]

    instances_path = (
        "/Users/simentorseth/developer/thesis/lrptw_instances/small_instances/"
    )
    save_path = (
        "/Users/simentorseth/developer/thesis/alns_solutions/small_instances/"
    )
    results_path = "/Users/simentorseth/developer/thesis/alns_solutions/small_instances/results.csv"

    for num_turbines in [5, 10, 15]:
        path = instances_path + str(num_turbines)
        for file in sorted(os.listdir(path)):
            print("Running instance: ", file)
            filename = path + "/" + file
            problem = Problem(filename)
            initial = random_solution(problem)
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
   
    

if __name__ == "__main__":
    main()
