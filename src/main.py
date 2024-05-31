from heuristic.alns import Alns
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.initial import create_initial_solution
from heuristic.operators import (
    rand_remov_greed_insrt_operator,
    greed_rand_remov_greed_insrt_operator,
    sim_rand_remov_greed_insrt_operator,
)
from heuristic.utils import (
    is_feasible,
    cost,
    save_run,
    save_solution,
)

import gurobipy as gp

from statistics import mean
import time
import random
import argparse
import os


def run_once(solution: Solution, operators: list[callable], problem: Problem, env) -> None:
    alns = Alns(problem, operators, solution, env)
    start_time = time.perf_counter()
    best_solution, best_cost = alns.run()
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Last update: {alns._iter_improve}")

    try:
        assert is_feasible(best_solution, problem)
        assert cost(best_solution, problem) == best_cost

        print(f"Best solution:")
        print(best_solution)
        print(f"Cost: {best_cost}")
        print(f"Runtime: {duration:.2f}s")
        print("\n")
    except AssertionError:
        print(f"{problem._filename} is infeasible!!!")
        if cost(best_solution, problem) != best_cost:
            print("Cost mismatch!!!")
            print("Cost: ", best_cost)
            print("Calculated cost: ", cost(best_solution, problem))
            print(best_solution)


def run_ten(solution: Solution, operators: list[callable], problem: Problem, env):
    all_time_best_solution = None
    all_time_best_cost = float("inf")
    costs = []
    runtimes = []

    for i in range(10):
        alns = Alns(problem, operators, solution, env)
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


def main(args):
     # If testing, set the seed
    seed = 1337
    random.seed(seed)

    filename = args.file

    operators = [
        sim_rand_remov_greed_insrt_operator,
        greed_rand_remov_greed_insrt_operator,
        rand_remov_greed_insrt_operator,
    ]

    problem = Problem(filename)
    initial = create_initial_solution(problem)
    assert is_feasible(initial, problem)
    print("Cost of initial solution:")
    print(f"{round(cost(initial, problem), 2)}")

    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()

        match args.num_runs:
            case 1:
                print(f"Running {os.path.basename(filename)} for 1 run")
                run_once(initial, operators, problem, env)
            case 10:
                print(f"Running {os.path.basename(filename)} for 10 runs")
                _, all_time_best_cost, costs, runtimes = run_ten(
                initial, operators, problem, env
                )
                print("All time best objective value:")
                print(round(all_time_best_cost, 2))
                print("Average objective value:")
                print(round(mean(costs), 2))
                print("Average runtime:")
                print(round(mean(runtimes), 2))
                print("\n")






if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("num_runs", type=int, help="Number of runs to perform")
    parser.add_argument("file", type=str, help="Instance file to solve.")
    args = parser.parse_args()
    main(args)