class Alns:
    def __init__(
        self, problem, operators, initial_solution, max_iterations, max_no_improv
    ):
        self.problem = problem
        self.operators = operators
        self.initial_solution = initial_solution
        self.max_iterations = max_iterations
        self.max_no_improv = max_no_improv
        self.best = None

    def update_weights(self):
        raise NotImplementedError

    def update_best(self):
        raise NotImplementedError

    def search(self):
        raise NotImplementedError

    def get_best(self):
        return self.best
