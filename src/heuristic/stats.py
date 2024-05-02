import matplotlib.pyplot as plt
import numpy as np


def plot_runtime_vs_problem_size(runtimes, problem_sizes):
    plt.figure(figsize=(10, 7))
    for i in range(len(problem_sizes)):
        plt.plot(problem_sizes, runtimes)
    plt.title("")
    plt.xlabel("no. Nodes * no. Charging units")
    plt.ylabel("Running Time (Seconds)")
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_operator_usage(freq: list[int], operators: list[callable]):
    freq = np.array(freq)

    iterations = generate_iteration_labels(len(freq), segment_size=100)

    plt.figure(figsize=(10, 7))
    for i in range(len(operators)):
        plt.plot(iterations, freq[:, i], label=operators[i].__name__)
    plt.xticks(iterations[::10] + [iterations[-1]])
    plt.title("Operator Usage Frequency Each 100 Iterations")
    plt.xlabel("Iteration Segments")
    plt.ylabel("Frequency of Usage")
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_acceptance_rate(accepted_costs: dict[int, float], max_iterations: int):

    # Generate a list of acceptance status: 1 if accepted in that iteration, 0 otherwise
    acceptance_status = [
        1 if i in accepted_costs else 0 for i in range(1, max_iterations + 1)
    ]

    # Calculate cumulative sum of accepted solutions to get the number of accepts up to each iteration
    cumulative_accepts = [
        sum(acceptance_status[: i + 1]) for i in range(max_iterations)
    ]

    # Calculate acceptance rate as the ratio of cumulative accepts to the number of iterations
    acceptance_rate = [cumulative_accepts[i] / (i + 1) for i in range(max_iterations)]

    # Plotting the acceptance rate
    plt.figure(figsize=(10, 6))
    plt.plot(
        range(1, max_iterations + 1),
        acceptance_rate,
        label="Acceptance Rate",
        color="blue",
    )
    plt.title("Acceptance Rate over Iterations")
    plt.xlabel("Iteration")
    plt.ylabel("Acceptance Rate")
    plt.grid(True)
    plt.legend()
    plt.show()


def plot_convergence(best_costs: dict[int, float], max_iterations: int):
    continuous_data = []
    last_best_value = float("inf")

    for i in range(max_iterations + 1):
        if i in best_costs:
            last_best_value = best_costs[i]
        continuous_data.append(last_best_value)

    plt.figure(figsize=(10, 6))
    plt.plot(
        range(1, len(continuous_data) + 1), continuous_data, linestyle="-", color="b"
    )
    plt.title("Convergence Curve of ALNS")
    plt.xlabel("Iteration")
    plt.ylabel("Best Objective Function Value")
    plt.grid(True)
    plt.show()


def plot_average_convergence(convergence_data, max_iterations):
    filled_data = []
    for run_data in convergence_data:
        if not run_data:
            continue
        sorted_iterations = sorted(run_data.items())
        last_value = sorted_iterations[0][1]
        filled_run = {}
        for i in range(max_iterations + 1):
            if i in run_data:
                last_value = run_data[i]
            filled_run[i] = last_value
        filled_data.append(filled_run)

    average_data = []
    for i in range(max_iterations + 1):
        sum_values = sum(run_data[i] for run_data in filled_data)
        average_data.append(sum_values / len(filled_data))

    plt.figure(figsize=(10, 6))
    plt.plot(range(len(average_data)), average_data, linestyle="-", color="b")
    plt.title("Average Convergence Curve Over 10 Runs")
    plt.xlabel("Iteration")
    plt.ylabel("Average Best Objective Value")
    plt.grid(True)
    plt.show()


def plot_average_operator_usage(all_operator_usage, operators):
    stacked = np.stack(all_operator_usage, axis=0)
    average_usage = np.mean(stacked, axis=0)

    iterations = generate_iteration_labels(len(average_usage), segment_size=100)
    num_operators = average_usage.shape[1]

    # Plotting the operator usage
    plt.figure(figsize=(10, 6))
    for op_index in range(num_operators):
        plt.plot(
            iterations,
            average_usage[:, op_index],
            linestyle="-",
            label=f"{operators[op_index].__name__}",
        )

    plt.title("Average Operator Usage Over 10 Runs")
    plt.xticks(iterations[::10] + [iterations[-1]])
    plt.xlabel("Iteration")
    plt.ylabel("Average Usage (%)")
    plt.legend()
    plt.grid(True)
    plt.show()


# this does not work...
@DeprecationWarning
def plot_average_acceptance_rate(runs):
    max_length = max(max(run.keys()) if run else 0 for run in runs)
    # Initialize a list to hold processed data
    processed_data = []

    # Process each run
    for run in runs:
        run_data = [0] * (
            max_length + 1
        )  # Initialize all iterations as 0 (not accepted)
        for iteration in run:
            run_data[iteration] = 1  # Mark iterations where an acceptance occurred
        processed_data.append(run_data)
    # Convert list of lists to a NumPy array for efficient computation
    data_array = np.array(processed_data)
    # Calculate average acceptance rate at each iteration
    acceptance_rates = np.mean(data_array, axis=0)

    plt.figure(figsize=(10, 6))
    plt.plot(acceptance_rates, linestyle="-", color="b")
    plt.title("Average Acceptance Rate Over 10 Runs")
    plt.xlabel("Iteration")
    plt.ylabel("Acceptance Rate")
    plt.grid(True)
    plt.show()


def generate_iteration_labels(data_length, segment_size=100):
    """Generate labels for iteration blocks given the total number of data points and block size."""
    labels = []
    for i in range(0, data_length):
        start = i * segment_size + 1
        end = (i + 1) * segment_size
        labels.append(f"{start}-\n{end}")
    return labels
