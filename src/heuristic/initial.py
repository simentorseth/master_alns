from heuristic.problem import Problem
from heuristic.solution import Solution


def create_initial_solution(problem: Problem) -> Solution:
    cluster_assignment = {k: None for k in problem.turbines}

    for turbine in problem.turbines:
        min_distance = float("inf")
        assigned_station = None
        for station in problem.stations:
            distance = problem.distances[turbine, station]
            if distance < min_distance:
                min_distance = distance
                assigned_station = station
        cluster_assignment[turbine] = assigned_station

    clustering = {k: [] for k in problem.stations}
    for turbine, assignment in cluster_assignment.items():
        clustering[assignment].append(turbine)
    
    routes = []
    stations = []
    for cluster_center, cluster in clustering.items():
        unassigned = set(cluster)

        tour = [cluster_center]
        duration = 0
        charge_level = problem.charge_capacity

        while unassigned:
            for turbine in cluster:
                if turbine in unassigned:
                    distance = problem.distances[tour[-1], turbine]
                    travel_time = problem.travel_times[tour[-1], turbine]
                    demand = problem.demands[tour[-1]]
                    consumed_charge = distance * problem.consumption_rate

                    duration += travel_time + demand
                    charge_level -= consumed_charge

                    if duration <= 8 and charge_level >= 0 and charge_level <= problem.charge_capacity:
                        distance = problem.distances[turbine, tour[0]]
                        travel_time = problem.travel_times[turbine, tour[0]]
                        demand = problem.demands[turbine]
                        consumed_charge = distance * problem.consumption_rate

                        final_duration = duration + travel_time + demand
                        final_charge_level = charge_level - consumed_charge
                        if final_duration <= 8 and final_charge_level >= 0 and final_charge_level <= problem.charge_capacity: 
                            tour.append(turbine)
                            unassigned.remove(turbine)

            if len(tour) > 1:
                tour.pop(0)  # remove station node
                tour.append(0)  # add padding
                routes.extend(tour)
                stations.append(cluster_center)

                # reset for a new tour
                tour = [cluster_center]
                duration = 0
                charge_level = problem.charge_capacity

    assert routes.count(0) == len(stations)
    
    solution = Solution()
    solution.routes = routes
    solution.stations = stations

    return solution
