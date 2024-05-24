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
from math import floor, exp
from random import random, randint
from statistics import mean


class Alns:
    def __init__(self, problem: Problem, operators: list[callable], initial: Solution, env,
        *,
        max_iterations = 10000,
        max_iter_no_improve = 10000,
        iter_escape = 1000,
    ) -> None:
        # Initialisation
        self._problem = problem
        self._model, self.x, self.y = initialise_model(problem.num_turbines, problem.num_stations, env)
        for j in self.y.keys():
            self.y[j].obj = problem.fixed_costs[j]

        # Parameters
        self._max_iterations = max_iterations
        self._max_iter_no_improve = max_iter_no_improve
        self._warm_iter = 100
        self._iter_escape = iter_escape
        self._operators = operators
        self._initial = initial
        self._iter_improve = 0
        self._weights = [0.5 for _ in range(len(self._operators))]
        self._probabilities = []
        self._smooth_factor = 0.5  # predifined value to balance earlier weights
        self._q_max = floor(0.6 * self._problem.num_turbines)  # TODO: Test this
        
        self._scores = [0 for _ in range(len(self._operators))]
        self.update_probability()

        # Simulated Annealing Variables
        self._initial_temperature = 0.0
        self._temperature = 0.0
        self._final_temperature = 0.1
        self._alpha = 0

        # Variables
        self._current = None
        self._best = None
        self._current_cost = 0
        self._best_cost = 0

        # Statistics
        self._operator_usage: list[list[int]] = []
        self._accepted_solutions: dict[int, float] = {}
        self._num_feasible: int = 0
        self._best_costs: dict[int, float] = {}

    def run(self) -> tuple[Solution, float]:
        self.search()
        return self.get_best()

    def search(self) -> None:
        self._current = copy(self._initial)
        self._best = copy(self._initial)
        self._current_cost = cost(self._current, self._problem)
        self._best_cost = self._current_cost
        self._best_costs[0] = self._best_cost
        num_used_operators = [0 for _ in range(len(self._operators))]
        explored = {self._current: self._current_cost}
        delta_w = [0 for _ in range(100)]

        # warm up
        for w in range(self._warm_iter):
            operator = self.select_operator()
            if operator == 0:
                q = randint(2, self._q_max)
            else:
                q = randint(1, self._q_max)
            
            candidate = self._operators[operator](self._current, q, self._problem)
            candidate = self.get_optimal_stations(candidate, self._problem)
            num_used_operators[operator] += 1

            if is_feasible(candidate, self._problem):
                candidate_cost = cost(candidate, self._problem)
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
        
        self._initial_temperature = mean(delta_w) / 0.223
        self._temperature = self._initial_temperature
        self._alpha = (self._final_temperature / self._initial_temperature) ** (1 / (self._max_iterations - self._warm_iter))

        for i in range(self._max_iterations - self._warm_iter):
            if i - self._iter_improve >= self._max_iter_no_improve:
                break
            
            if i % self._iter_escape == 0 and i != 0:
                q_escape = max(5, self._q_max)
                self._current = escape(self._current, q_escape, self._problem)

            operator = self.select_operator()

            if operator == 0:
                q = randint(2, self._q_max)
            else:
                q = randint(1, self._q_max)  # number of turbines to remove
            
            candidate = self._operators[operator](self._current, q, self._problem)
            
            if candidate.routes.count(0) != len(candidate.stations):
                raise ValueError(f"Iteration: {i}, Operator: {self._operators[operator]}, Candidate: {candidate}")
            
            candidate = self.get_optimal_stations(candidate, self._problem)
            if 0 in candidate.stations:
                raise ValueError(f"Iteration: {i}, Operator: {self._operators[operator]}, Candidate: {candidate}")
            
            if candidate.routes.count(0) != len(candidate.stations):
                raise ValueError(f"Iteration: {i}, Operator: {self._operators[operator]}, Candidate: {candidate}")
            
            num_used_operators[operator] += 1
            
            if is_feasible(candidate, self._problem):
                self._num_feasible += 1
                
                candidate_cost = cost(candidate, self._problem)
                delta_e = candidate_cost - self._current_cost

                is_explored = candidate in explored
                if not is_explored:
                    explored[candidate] = candidate_cost

                if delta_e < 0:
                    self._current = candidate
                    self._current_cost = candidate_cost
                    if candidate_cost < self._best_cost:
                        self._iter_improve = i
                        self._best = candidate
                        self._best_cost = candidate_cost
                        self.update_scores(operator, candidate_cost, is_explored)
                        # Update stats
                        self._best_costs[i] = self._best_cost
                else:
                    if random() < exp(-delta_e / self._temperature):
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
                num_used_operators = [0 for _ in range(len(self._operators))]

    def update_scores(self, operator: int, cost: int, unexplored: bool) -> None:
        if cost < self._best_cost:
            self._scores[operator] += 4
            self._iter_improve = 0
        elif cost < self._current_cost:
            self._scores[operator] += 2
        elif unexplored:
            self._scores[operator] += 0.5

    def update_weights(self, num_used_operators: int) -> None:
        ratios = [0 for _ in range(len(self._operators))]
        for i in range(len(self._operators)):
            if num_used_operators[i] == 0:
                ratios[i] = 0
            ratios[i] = self._scores[i] / self._weights[i]

        self._weights = [
            (1 - self._smooth_factor) * w + self._smooth_factor * ratio
            for w, ratio in zip(self._weights, ratios)
        ]
    
    def update_probability(self) -> None:
        self._probabilities = list(
            accumulate([weight / sum(self._weights) for weight in self._weights])
        )
    
    def reset_scores(self) -> None:
        self._scores = [0 for _ in range(len(self._operators))]

    def select_operator(self) -> int | None:
        random_num = random()
        return next(
            (i for i, x in enumerate(self._probabilities) if x > random_num), None
        )

    def get_best(self) -> tuple[Solution, int]:
        return self._best, self._best_cost

    def get_optimal_stations(self, solution: Solution, problem: Problem):
        to_and_from_costs = get_to_and_from_costs(solution, problem)
        assert len(to_and_from_costs) == len(solution.stations)
        self._model = update_model(
            self._model, self.x, self.y, to_and_from_costs, problem.fixed_costs
        )
        assignment = get_station_assignment(
            self._model, len(to_and_from_costs), problem.num_stations, problem
        )

        new_solution = copy(solution)
        new_solution.stations = assignment
        return new_solution

    def get_statistics(self) -> dict[str, any]:
        stats = {}
        stats["operator_usage"] = self._operator_usage
        stats["accepted_solutions"] = self._accepted_solutions
        stats["num_feasible"] = self._num_feasible
        stats["best_costs"] = self._best_costs
        stats["last_update"] = self._iter_improve

        return stats
    
    def get_parameters(self) -> dict[str, any]:
        return {
            "max_iterations": self._max_iterations,
            "max_iter_no_improve": self._max_iter_no_improve,
            "iter_escape": self._iter_escape,
            "weights": self._weights,
            "probabilities": self._probabilities,
            "smooth_factor": self._smooth_factor,
            "q_max": self._q_max,
            "alpha": self._alpha,
        }