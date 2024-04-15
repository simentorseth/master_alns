from utils import feasible
from pprint import pprint
from problem import Problem


def main():
    """
    Numbers are based on the technical specification
    given for the Rem Energy CSOV, found at
    https://www.remoffshore.no/fleet/rem-energy/
    """
    file = "./src/heuristic/instances/aberdeen_wf.csv"
    problem = Problem(
        file,
        num_vessels=3,
        charge_capacity=2 * 341,  # kWh
        velocity=5,  # m/s (2.57 m/s <--> 5 knots
        consumption_rate=0.016,  # kWh/m
        vessel_cost=1000,
        station_cost=1000,
        num_time_windows=3,
    )

    routes = [1, 2, 0, 4, 5, 6, 0, 7, 8, 9, 10]
    stations = [11, 11, 11]

    pprint(feasible(routes, stations, problem))
    # pprint(problem.travel_times)


if __name__ == "__main__":
    main()
