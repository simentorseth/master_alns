from copy import copy
from random import random
from itertools import accumulate, dropwhile
from heuristic.problem import Problem
from heuristic.utils import cost, is_feasible


class Alns:
    def __init__(
        self,
        problem: Problem,
        operators: list[function],
        initial_solution: ...,
        max_iterations: int,
        max_no_improv: int,
    ) -> None:
        self.problem = problem
        self.operators = operators
        self.initial_solution = initial_solution
        self.max_iterations = max_iterations
        self.max_no_improv = max_no_improv
        self._current = None
        self._best = None
        self._best_cost = 0
        self._current_cost = 0
        self._weights = [0.5 for _ in range(len(self.operators))]
        self._probability = self.update_probability()
        self._r = 0.5  # predifined value to balance earlier weights
        self.scores = []

    def update_scores(self, operator: function, cost: int) -> None:
        raise NotImplementedError

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

    def update_best(self) -> None:
        raise NotImplementedError

    def search(self) -> None:
        self._current, self._best = copy(self.initial_solution)
        self._current_cost = cost(self._current)
        it_since_best = 0
        num_used_operators = [0 for _ in range(len(self.operators))]
        explored = {self._current: self._current_cost}

        for i in range(self.max_iterations):
            if it_since_best > self.max_no_improv:
                ...
                # TODO: Apply escape algorithm

            random_num = random()
            operator = next(
                i
                for i, _ in enumerate(
                    dropwhile(lambda x: x > random_num, self.operators)
                )
            )

            candidate = copy(initial)
            operator = self.select_operator()
            candidate = operator(candidate)
            if cost(candidate) < cost(self._best):
                initial = candidate
                it_since_best = 0
                self.update_best()
            else:
                it_since_best += 1

        if i % 100 == 0:
            self.update_weights(num_used_operators)
            self.update_probability()
            self.reset_scores()
            num_used_operators = [0 for _ in range(len(self.operators))]

    def reset_scores(self) -> None:
        self._scores = [0 for _ in range(len(self.operators))]

    def select_operator(self, weights: list[float]) -> function:
        raise NotImplementedError

    def get_best(self) -> ...:
        return self._best
