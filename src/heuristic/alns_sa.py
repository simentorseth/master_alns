from copy import copy
from heuristic.problem import Problem
from heuristic.operators import escape
from heuristic.solution import Solution
from heuristic.utils import (
    cost,
    is_feasible,
    initialise_model,
    update_model,
    get_to_and_from_costs,
    get_station_assignment,
)
from itertools import accumulate
from statistics import mean
from random import random, randint
import time
import math


class AlnsSA:
    def __init__(
        self,
        problem: Problem,
        operators: list[callable],
        initial: Solution,
        *,
        max_iterations: int = 10000,
        max_no_improv: int = 1000,
    ) -> None:
        self.problem = problem
        self.model, self.x, self.y = initialise_model(
            problem.num_turbines, problem.num_stations
        )
        self.operators = operators
        self.initial = initial
        self.max_iterations = max_iterations
        self.max_no_improv = max_no_improv
        self._it_since_best = 0
        self._current: Solution = None
        self._best: Solution = None
        self._best_cost = 0
        self._current_cost = 0
        self._weights = [0.5 for _ in range(len(self.operators))]
        self._probability = []
        self._r = 0.5  # predifined value to balance earlier weights
        # TODO: Change this to depend on the problem size instead
        self._q_max = int(0.9 * len(problem.map["Turbines"]))
        self._alpha = (0.033) ** (1 / self.max_iterations)
        self._scores = [0 for _ in range(len(self.operators))]
        self.update_probability()

        # Simulated Annealing Stuff
        self._initial_temperature = 0
        self._temperature = 0
        self._final_temperature = 0.1

        # Stats
        self._operator_usage: list[list[int]] = []
        self._accepted_solutions: dict[int, float] = {}
        self._last_update: int = 0
        self._num_feasible: int = 0
        self._best_costs: dict[int, float] = {}

    def single_run(self) -> tuple[Solution, int]:
        self.search()
        return self.get_best()

    def consecutive_run(self) -> tuple[Solution, int, list[float], float]:
        all_time_best_cost = 0
        all_time_best = None
        best_costs_results = []
        all_convergence_values = []
        operator_usages = []
        acceptance_rates = []
        runtimes = []

        for i in range(10):
            start_time = time.perf_counter()
            self.search()
            current_best, current_best_cost = self.get_best()
            end_time = time.perf_counter()
            duration = end_time - start_time
            runtimes.append(duration)
            best_costs_results.append(current_best_cost)
            all_convergence_values.append(self._best_costs)
            operator_usages.append(self._operator_usage)
            acceptance_rates.append(self._accepted_solutions)
            if i == 0 or current_best_cost < all_time_best_cost:
                all_time_best = current_best
                all_time_best_cost = current_best_cost
            # reset stuff
            self._best_costs = {}
            self._operator_usage = []
            self._accepted_solutions = {}
            self._weights = [0.5 for _ in range(len(self.operators))]
            self._probability = []
            self.update_probability()
            self._scores = [0 for _ in range(len(self.operators))]
            self._last_update: int = 0
            self._num_feasible: int = 0

        return (
            all_time_best,
            all_time_best_cost,
            best_costs_results,
            all_convergence_values,
            operator_usages,
            acceptance_rates,
            runtimes,
        )

    def search(self) -> None:
        self._current = copy(self.initial)
        self._best = copy(self.initial)
        self._current_cost = cost(self._current, self.problem)
        self._best_cost = self._current_cost
        self._best_costs[0] = self._best_cost
        num_used_operators = [0 for _ in range(len(self.operators))]
        explored = {self._current: self._current_cost}
        delta_w = [0 for _ in range(100)]

        for w in range(100):
            operator = self.select_operator()
            if operator == 0:
                q = randint(2, self._q_max)
            else:
                q = randint(1, self._q_max)  # number of turbines to remove
            candidate = self.operators[operator](self._current, q, self.problem)
            candidate = self.get_optimal_stations(candidate, self.problem)
            num_used_operators[operator] += 1
            if is_feasible(candidate, self.problem):
                candidate_cost = cost(candidate, self.problem)
                delta_e = candidate_cost - self._current_cost
                if delta_e < 0:
                    self._current = candidate
                    self._current_cost = candidate_cost
                    if self._current_cost < self._best_cost:
                        self._best = self._current
                        self._best_cost = self._current_cost
                else:
                    if random() < 0.8:
                        self._current = candidate
                        self._current_cost = candidate_cost

                    delta_w[w] = delta_e

        avg_delta = mean(delta_w)
        self._initial_temperature = -avg_delta / -0.223
        self._temperature = self._initial_temperature
        self._alpha = (self._final_temperature / self._initial_temperature) ** (
            1 / 9900
        )

        for i in range(self.max_iterations - 100):
            self._it_since_best += 1
            if self._it_since_best > self.max_no_improv:
                q_escape = max(5, self._q_max)
                self._current = escape(self._current, q_escape, self.problem)
                self._it_since_best = 0

            operator = self.select_operator()

            if operator == 0:
                q = randint(2, self._q_max)
            else:
                q = randint(1, self._q_max)  # number of turbines to remove
            candidate = self.operators[operator](self._current, q, self.problem)
            if candidate.routes.count(0) != len(candidate.stations):
                raise ValueError
            # not sure if this needs to happen here
            # optimal station assignment does not take feasibility into account
            candidate = self.get_optimal_stations(candidate, self.problem)
            num_used_operators[operator] += 1

            if is_feasible(candidate, self.problem):
                self._num_feasible += 1

                candidate_cost = cost(candidate, self.problem)
                delta_e = candidate_cost - self._current_cost

                is_explored = candidate in explored
                if not is_explored:
                    explored[candidate] = candidate_cost

                if delta_e < 0:
                    self._current = candidate
                    self._current_cost = candidate_cost
                    if candidate_cost < self._best_cost:
                        self._last_update = i
                        self._best = candidate
                        self._best_cost = candidate_cost
                        self._best_costs[i] = candidate_cost
                        self._last_update = i
                        self.update_scores(operator, candidate_cost, is_explored)
                else:
                    if random() < math.exp(-delta_e / self._temperature):
                        self._accepted_solutions[i] = candidate_cost
                        self._current = candidate
                        self._current_cost = candidate_cost
                        self.update_scores(operator, candidate_cost, is_explored)
            self._temperature *= self._alpha

            if i % 100 == 0:
                self._operator_usage.append(num_used_operators)
                self.update_weights(num_used_operators)
                self.update_probability()
                self.reset_scores()
                num_used_operators = [0 for _ in range(len(self.operators))]

    def update_scores(self, operator: int, cost: int, unexplored: bool) -> None:
        if cost < self._best_cost:
            self._scores[operator] += 4
            self._it_since_best = 0
        elif cost < self._current_cost:
            self._scores[operator] += 2
        elif unexplored:
            self._scores[operator] += 0.5

    def reset_scores(self) -> None:
        self._scores = [0 for _ in range(len(self.operators))]

    def update_weights(self, num_used_operators: int) -> None:
        ratios = [0 for _ in range(len(self.operators))]
        for i in range(len(self.operators)):
            if num_used_operators[i] == 0:
                ratios[i] = 0
            ratios[i] = self._scores[i] / self._weights[i]

        self._weights = [
            (1 - self._r) * w + self._r * ratio
            for w, ratio in zip(self._weights, ratios)
        ]

    def update_probability(self) -> None:
        self._probability = list(
            accumulate([weight / sum(self._weights) for weight in self._weights])
        )

    # Remove?
    def update_best(self) -> None:
        raise NotImplementedError

    def select_operator(self) -> int | None:
        random_num = random()
        return next(
            (i for i, x in enumerate(self._probability) if x > random_num), None
        )

    def get_best(self) -> tuple[Solution, int]:
        return self._best, self._best_cost

    def get_optimal_stations(self, solution: Solution, problem: Problem):
        to_and_from_costs = get_to_and_from_costs(solution, problem)

        self.model = update_model(
            self.model, self.x, self.y, to_and_from_costs, problem.fixed_costs
        )
        assignment = get_station_assignment(
            self.model, len(to_and_from_costs), problem.num_stations, problem
        )

        new_solution = copy(solution)
        new_solution.stations = assignment
        return new_solution
