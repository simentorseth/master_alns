from copy import copy
from heuristic.problem import Problem
from heuristic.solution import Solution
from heuristic.utils import cost, is_feasible
from itertools import accumulate
from statistics import mean
from random import random  # , shuffle


class Alns:
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
        self._q_max = max(5, len(self.problem.map["Turbines"]) // 5)
        self._alpha = (0.033) ** (1 / self.max_iterations)
        self._scores = [0 for _ in range(len(self.operators))]
        self.update_probability()

    def single_run(self) -> tuple[Solution, int]:
        self.search()
        return self.get_best()

    def consecutive_run(self) -> ...:
        best_cost = 0
        best = None
        results = []

        for i in range(10):
            self.search()
            current, current_cost = self.get_best()
            results.append(current_cost)
            if i == 0 or current_cost < best_cost:
                best = current
                best_cost = current_cost

        return best, best_cost, results, mean(results)

    def search(self) -> None:
        self._current = copy(self.initial)
        self._best = copy(self.initial)
        self._current_cost = cost(self._current, self.problem)
        self._best_cost = self._current_cost

        num_used_operators = [0 for _ in range(len(self.operators))]
        explored = {self._current: self._current_cost}

        for i in range(self.max_iterations):
            self._it_since_best += 1  # Should this be here?
            if self._it_since_best > self.max_no_improv:
                num_to_remove = max(
                    5, len(self.problem.map["Turbines"])
                )  # no idea what to put here
                print(f"Escaping with {num_to_remove} turbines")
                # self._current, cost_difference = self.escape(
                #     self._current, num_to_remove, self.problem
                # )
                # self._current_cost += cost_difference
                self._it_since_best = 0

            random_num = random()
            operator = self.select_operator(random_num)
            if len(self.operators) == 1:
                operator = 0
            candidate = self.operators[operator](self._current, self.problem)
            num_used_operators[operator] += 1

            if is_feasible(candidate, self.problem):
                candidate_cost = cost(candidate, self.problem)
                is_explored = candidate in explored
                if not is_explored:
                    explored[candidate] = candidate_cost

                if candidate_cost < self._best_cost:
                    self.update_scores(operator, candidate_cost, is_explored)

                acceptance = (0.3 * self._alpha**i) + 1  # some number
                if (
                    candidate_cost < acceptance * self._best_cost
                    or candidate_cost < self._current_cost
                ):
                    self._current = candidate
                    self._current_cost = candidate_cost
                    if candidate_cost < self._best_cost:
                        self._best = candidate
                        self._best_cost = candidate_cost

            if i % 100 == 0:
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
        self._probability = accumulate(
            [weight / sum(self._weights) for weight in self._weights]
        )

    # Remove?
    def update_best(self) -> None:
        raise NotImplementedError

    def select_operator(self, random_num: float) -> int | None:
        return next(
            (i for i, x in enumerate(self._probability) if x > random_num), None
        )

    def get_best(self) -> tuple[Solution, int]:
        return self._best, self._best_cost

    def escape(self, solution: Solution) -> Solution:
        # TODO: Implement this. Not sure what, but it should
        # move things around significantly. Can I have a dummy vessel?
        # What would that even mean in this context?
        raise NotImplementedError
        routes = solution.routes

        tours = []
        separators = [i for i, x in enumerate(routes) if x == 0]
        start_idx = 0

        num_tours = len(separators)
        for i in range(num_tours):
            # get the current route
            current_route = routes[start_idx : separators[i]]
            shuffled = shuffle(current_route)
            tours.append(current_route)
            # adjust start index for next iteration
            start_idx = separators[i] + 1

        stations = solution.stations
        shuffle(stations)

        new_solution = Solution()
        new_solution.routes = [
            t for i, tour in enumerate(tours) for t in (tour if i == 0 else [0] + tour)
        ]
        new_solution.stations = stations
