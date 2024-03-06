from pdp_utils import *
from pdp_utils import load_problem
import time
import random
import numpy as np
import math

def checkFeasibility(solution, prob):
    feasiblity, c = feasibility_check(solution, prob)
    return feasiblity

def checkVehicleFeasibility(vehicle, solution, prob):
    feasibility, c = feasible_vehicle(vehicle, prob, solution)
    return feasibility

def calculateObjective(solution, prob):
    return cost_function(solution, prob)

def createStartSolution(prob):
    start_solution = [0 for _ in range(prob['n_vehicles'])]

    for i in range(1, prob['n_calls']+1):
        start_solution.append(i)
        start_solution.append(i)

    return start_solution

def findHighestTravelCost(vehicle, possible_calls, prob, zeroIndex, solution):
    Cargo = prob['Cargo']
    tempidx = zeroIndex[vehicle] + 1 if vehicle != 0 else 0
    currentVPlan = solution[tempidx:zeroIndex[vehicle]]
    currentVPlan = currentVPlan - 1

    if len(currentVPlan) > 0:
        sortRout = np.sort(currentVPlan, kind='mergesort')
        I = np.argsort(currentVPlan, kind='mergesort')
        Indx = np.argsort(I, kind='mergesort')

        PortIndex = Cargo[sortRout, 1].astype(int)
        PortIndex[::2] = Cargo[sortRout[::2], 0]
        PortIndex = PortIndex[Indx] - 1

        Diag = prob['TravelCost'][vehicle, PortIndex[:-1], PortIndex[1:]]

        call = currentVPlan[Diag.argmax()]

        if call in possible_calls:
            costly_call = call
        else:
            costly_call = random.choice(possible_calls)

    else:
        costly_call = random.choice(possible_calls)

    return costly_call

def rouletteWheelSelection(P1, P2, P3):
    rand = random.random()
    sum = P1+P2+P3
    if rand < (P1/sum):
        operator = OP1
        oper = 0
    elif rand < ((P1+P2)/sum):
        operator = OP2
        oper = 1
    elif rand < ((P1+P2+P3)/sum):
        operator = OP3
        oper = 2
    else:
        raise Exception('The probabilities are too small.')

    return operator, oper


def OP1(solution, prob, pre_calls):
    """
    This operator removes a random number of random calls between 1-3, and places them back in the best possible position.
    """
    new_solution = solution.copy()
    solution_ex = np.array(new_solution)
    solution_ex = np.append(solution_ex, [0])
    zeroIndex = np.array(np.where(np.array(solution_ex) == 0)[0], dtype=int)
    possible_calls = [n for n in range(1, prob['n_calls']+1)]
    
    n_calls = random.randint(1, 3)
    calls = [[] for _ in range(n_calls)]

    for i in range(n_calls):
        calls[i] = random.choice(possible_calls)
        possible_calls.remove(calls[i])
    
    random.shuffle(calls)

    pre_calls = []
    for call in calls:
        pre_calls.append(call)
        new_solution.remove(call)
        new_solution.remove(call)
        
        compatible_vehicles = []

        for vehicle in range(prob['n_vehicles']):
            if (prob['VesselCargo'][vehicle][call-1] == 1):
                compatible_vehicles.append(vehicle)

        best_solution = solution.copy()
        best_objective = calculateObjective(solution, prob)
        found = False

        for vehicle in compatible_vehicles:
            solution_ex = np.array(new_solution)
            solution_ex = np.append(solution_ex, [0])
            zeroIndex = np.array(np.where(np.array(solution_ex) == 0)[0], dtype=int)

            vehicle_indexes = []
            start_index = zeroIndex[vehicle-1]+1 if vehicle != 0 else 0
            for i in range(start_index, zeroIndex[vehicle]+1):
                vehicle_indexes.append(i)
            
            if len(vehicle_indexes) <= 1:
                current_solution = new_solution.copy()
                current_solution.insert(start_index, call)
                current_solution.insert(start_index, call)
                if checkVehicleFeasibility(vehicle, current_solution, prob):
                    current_objective = calculateObjective(current_solution, prob)
                    if (current_objective <= best_objective):
                        best_solution = current_solution
                        best_objective = current_objective
                        found = True

            else:
                availible_p = findAvailibleCapacity(new_solution, prob, vehicle, vehicle_indexes, call)
                for p in availible_p:
                    this_solution = new_solution.copy()
                    this_solution.insert(p, call)
                    availible_q = findPossibleQ(availible_p, p)
                    for q in availible_q:
                        q_sol = this_solution.copy()
                        q_sol.insert(q, call)
                        if checkVehicleFeasibility(vehicle, q_sol, prob):
                            this_objective = calculateObjective(q_sol, prob)
                            if (this_objective <= best_objective):
                                best_solution = q_sol
                                best_objective = this_objective
                                found = True

        if found:     
            new_solution = best_solution
        else:
            new_solution.append(call)
            new_solution.append(call)
    
    return new_solution, pre_calls

def OP2(solution, prob, pre_calls):
    """
    This operator sometimes focuses on only removing from dummy and removes a random number between 1-3 of random calls, 
    and places them back in random order in a compatible vehicle in a compatible position. If there are not that many 
    elements in dummy it chooses a random call from the whole set.
    """
    new_solution = solution.copy()
    dummy = []
    solution_ex = np.array(new_solution)
    solution_ex = np.append(solution_ex, [0])
    zeroIndex = np.array(np.where(np.array(solution_ex) == 0)[0], dtype=int)
    possible_calls = [n for n in range(1, prob['n_calls']+1)]


    for pre_call in pre_calls:
        possible_calls.remove(pre_call)

    for index, value in enumerate(new_solution):
        if index > zeroIndex[-2]:
            if value not in pre_calls:
                dummy.append(value)
    
    n_calls = random.randint(1, 3)
    calls = [[] for _ in range(n_calls)]
    pre_calls = []
    
    if len(dummy) > prob['n_calls']/3:
        best_call = None
        worst_cost = 0
        for dummy_call in dummy:
            dummy_cost = prob['Cargo'][dummy_call-1][3]
            if dummy_cost > worst_cost:
                worst_cost = dummy_cost
                best_call = dummy_call

        calls[0] = best_call
        dummy.remove(best_call)
        dummy.remove(best_call)
        pre_calls.append(best_call)
        possible_calls.remove(best_call)

        for i in range(1, n_calls):
            if len(dummy) > 0:
                calls[i] = random.choice(dummy)
                dummy.remove(calls[i])
                dummy.remove(calls[i])
                pre_calls.append(calls[i])
                possible_calls.remove(calls[i])
            else:
                calls[i] = random.choice(possible_calls)
                possible_calls.remove(calls[i])
                pre_calls.append(calls[i])
        
    else:
        rand = random.random()
        if rand < 0.01:
            Cargo = prob['Cargo']
            TravelCost = prob['TravelCost']
            FirstTravelCost = prob['FirstTravelCost']
            vehicle_costs = [[] for _ in range(prob['n_vehicles'])]
            Solution = np.append(new_solution, [0])
            tempidx = 0

            for i in range(prob['n_vehicles']):
                currentVPlan = Solution[tempidx:zeroIndex[i]]
                currentVPlan = currentVPlan - 1
                NoDoubleCallOnVehicle = len(currentVPlan)
                tempidx = zeroIndex[i] + 1

                if NoDoubleCallOnVehicle > 0:
                    sortRout = np.sort(currentVPlan, kind='mergesort')
                    I = np.argsort(currentVPlan, kind='mergesort')
                    Indx = np.argsort(I, kind='mergesort')

                    PortIndex = Cargo[sortRout, 1].astype(int)
                    PortIndex[::2] = Cargo[sortRout[::2], 0]
                    PortIndex = PortIndex[Indx] - 1

                    Diag = TravelCost[i, PortIndex[:-1], PortIndex[1:]]

                    FirstVisitCost = FirstTravelCost[i, int(Cargo[currentVPlan[0], 0] - 1)]

                    vehicle_costs[i] = np.sum(np.hstack((FirstVisitCost, Diag.flatten()))) + (np.sum(prob['PortCost'][i, currentVPlan]) / 2)
                else:
                    vehicle_costs[i] = 0
            
            
            max_vehicle = vehicle_costs.index(max(vehicle_costs))

            vehicle_calls = []
            start_index = zeroIndex[max_vehicle-1]+1 if max_vehicle != 0 else 0
            for i in range(start_index, zeroIndex[max_vehicle]):
                vehicle_calls.append(new_solution[i])
            
            new_solution = [i for i in new_solution if i not in vehicle_calls]

            new_solution.extend(vehicle_calls)
            
        for i in range(n_calls):
            calls[i] = random.choice(possible_calls)
            possible_calls.remove(calls[i])
            pre_calls.append(calls[i])
        
        random.shuffle(calls)

    for call in calls:        
        compatible_vehicles = []
        new_solution.remove(call)
        new_solution.remove(call)

        for vehicle in range(prob['n_vehicles']):
            if (prob['VesselCargo'][vehicle][call-1] == 1):
                compatible_vehicles.append(vehicle)

        while True:
            if len(compatible_vehicles) > 1:
                vehicle = random.choice(compatible_vehicles)
            elif len(compatible_vehicles) == 1:
                vehicle = compatible_vehicles[0]
            else:
                new_solution.append(call)
                new_solution.append(call)
                break
                
            compatible_vehicles.remove(vehicle)

            solution_ex = np.array(new_solution)
            solution_ex = np.append(solution_ex, [0])
            zeroIndex = np.array(np.where(np.array(solution_ex) == 0)[0], dtype=int)

            vehicle_indexes = []
            start_index = zeroIndex[vehicle-1]+1 if vehicle != 0 else 0
            for i in range(start_index, zeroIndex[vehicle]+1):
                vehicle_indexes.append(i)
            
            if len(vehicle_indexes) <= 1:
                current_solution = new_solution.copy()
                current_solution.insert(start_index, call)
                current_solution.insert(start_index, call)
                if checkVehicleFeasibility(vehicle, current_solution, prob):
                    new_solution = current_solution
                    break
                
            else:
                found = False
                availible_p = findAvailibleCapacity(new_solution, prob, vehicle, vehicle_indexes, call)
                for p in availible_p:
                    this_solution = new_solution.copy()
                    this_solution.insert(p, call)
                    availible_q = findPossibleQ(availible_p, p)
                    for q in availible_q:
                        q_sol = this_solution.copy()
                        q_sol.insert(q, call)
                        if checkVehicleFeasibility(vehicle, q_sol, prob):
                            new_solution = q_sol
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

    return new_solution, pre_calls

def OP3(solution, prob, pre_calls):
    """
    This operator chooses a random vehicle and removes the most costly call in the vehicle. A random number between 1-3 is chosen. If the number
    of calls is more than 1 the rest of the call is chosen at random. Then the call(s) are reinserted into the first feasible position in a 
    random vehicle
    """
    new_solution = solution.copy()
    dummy = []
    solution_ex = np.array(new_solution)
    solution_ex = np.append(solution_ex, [0])
    zeroIndex = np.array(np.where(np.array(solution_ex) == 0)[0], dtype=int)
    possible_calls = [n for n in range(1, prob['n_calls']+1)]
    n_vehicles = prob['n_vehicles']

    for pre_call in pre_calls:
        possible_calls.remove(pre_call)

    for index, value in enumerate(new_solution):
        if index > zeroIndex[-2]:
            if value not in pre_calls:
                dummy.append(value)
    
    n_calls = random.randint(1, 3)
    calls = [[] for _ in range(n_calls)]
    pre_calls = []

    removal_vehicle = random.choice(range(n_vehicles))

    vehicle_indexes = []
    start_index = zeroIndex[removal_vehicle-1]+1 if removal_vehicle != 0 else 0
    for i in range(start_index, zeroIndex[removal_vehicle]+1):
        vehicle_indexes.append(i)
    
    if len(vehicle_indexes) <= 1:
        costly_call = random.choice(possible_calls)
    else:
        costly_call = findHighestTravelCost(removal_vehicle, possible_calls, prob, zeroIndex, solution_ex)

    calls[0] = costly_call
    possible_calls.remove(costly_call)
    pre_calls.append(costly_call)

    for j in range(1, n_calls):
        calls[j] = random.choice(possible_calls)
        possible_calls.remove(calls[j])
        pre_calls.append(calls[j])

    for call in calls:        
        compatible_vehicles = []
        new_solution.remove(call)
        new_solution.remove(call)

        for vehicle in range(n_vehicles):
            if (prob['VesselCargo'][vehicle][call-1] == 1):
                compatible_vehicles.append(vehicle)

        while True:
            if len(compatible_vehicles) > 1:
                vehicle = random.choice(compatible_vehicles)
            elif len(compatible_vehicles) == 1:
                vehicle = compatible_vehicles[0]
            else:
                new_solution.append(call)
                new_solution.append(call)
                break
                
            compatible_vehicles.remove(vehicle)

            solution_ex = np.array(new_solution)
            solution_ex = np.append(solution_ex, [0])
            zeroIndex = np.array(np.where(np.array(solution_ex) == 0)[0], dtype=int)

            vehicle_indexes = []
            start_index = zeroIndex[vehicle-1]+1 if vehicle != 0 else 0
            for i in range(start_index, zeroIndex[vehicle]+1):
                vehicle_indexes.append(i)
            
            if len(vehicle_indexes) <= 1:
                current_solution = new_solution.copy()
                current_solution.insert(start_index, call)
                current_solution.insert(start_index, call)
                if checkVehicleFeasibility(vehicle, current_solution, prob):
                    new_solution = current_solution
                    break
                
            else:
                found = False
                availible_p = findAvailibleCapacity(new_solution, prob, vehicle, vehicle_indexes, call)
                for p in availible_p:
                    this_solution = new_solution.copy()
                    this_solution.insert(p, call)
                    availible_q = findPossibleQ(availible_p, p)
                    for q in availible_q:
                        q_sol = this_solution.copy()
                        q_sol.insert(q, call)
                        if checkVehicleFeasibility(vehicle, q_sol, prob):
                            new_solution = q_sol
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

    return new_solution, pre_calls

def OP4(solution, prob):
    """
    This operator removes a number of call dependent on the total number for calls into dummy
    """
    new_solution = solution.copy()
    n_calls = prob['n_calls']
    possible_calls = [n for n in range(1, n_calls+1)]
    n_remove = math.ceil(n_calls/7)

    for i in range(n_remove):
        call = random.choice(possible_calls)
        possible_calls.remove(call)

        new_solution.remove(call)
        new_solution.remove(call)
        new_solution.append(call)
        new_solution.append(call)
    
    return new_solution

def escape(solution, prob):
    current_solution = solution.copy()
    current_solution = OP4(current_solution, prob)
    return current_solution

def generalAdaptiveMetaheuristics(prob, S_0):
    incumbent = S_0.copy()
    best_solution = S_0.copy()
    i_best = 0
    deltaW = []
    pre_calls = []
    points = [0, 0, 0]
    operator_used = [0, 0, 0]
    P1 = 1/3
    P2 = 1/3
    P3 = 1/3
    r = 0.6

    incumbent_objective = calculateObjective(incumbent, prob)
    best_objective = incumbent_objective

    for w in range(100):
        i_best += 1

        operator, oper = rouletteWheelSelection(P1, P2, P3)
        operator_used[oper] += 1
        current_solution, pre_calls = operator(incumbent, prob, pre_calls)
        current_objective = calculateObjective(current_solution, prob)

        deltaE = current_objective - incumbent_objective

        if checkFeasibility(current_solution, prob):
            if deltaE <= 0:
                incumbent = current_solution
                incumbent_objective = current_objective
                points[oper] += 2
                if incumbent_objective < best_objective:
                    best_solution = incumbent
                    best_objective = incumbent_objective
                    points[oper] += 2
                    i_best = 0
            else:
                rand = random.random()
                if rand < 0.8:
                    incumbent = current_solution
                    incumbent_objective = current_objective
                deltaW.append(deltaE)

    if operator_used[0] > 0:
        P1 = P1*(1-r) + r*(points[0]/operator_used[0])
    else:
        P1 = P1*(1-r)
    if operator_used[1] > 0:
        P2 = P2*(1-r) + r*(points[1]/operator_used[1])
    else:
        P2 = P2*(1-r)
    if operator_used[2] > 0:
        P3 = P3*(1-r) + r*(points[2]/operator_used[2])
    else:
        P3 = P3*(1-r)
    count = 0
    points = [0, 0, 0]
    operator_used = [0, 0, 0]

    deltaAvg = np.average(deltaW) if len(deltaW) > 0 else 100000
    T_0 = (-deltaAvg / np.log(0.8))
    #alpha = np.power(0.1/T_0, (1/9900))
    alpha = 0.9995
    T = T_0
    count = 0

    for i in range(9900):
        i_best += 1
        count += 1
        if i_best > 300:
            incumbent = escape(incumbent, prob)
            incumbent_objective = calculateObjective(incumbent, prob)
            i_best = 0

        operator, oper = rouletteWheelSelection(P1, P2, P3)
        operator_used[oper] += 1
        current_solution, pre_calls = operator(incumbent, prob, pre_calls)
        current_objective = calculateObjective(current_solution, prob)

        deltaE = current_objective - incumbent_objective

        if checkFeasibility(current_solution, prob):
            if deltaE <= 0:
                incumbent = current_solution
                incumbent_objective = current_objective
                points[oper] += 2
                
                if incumbent_objective < best_objective:
                    best_solution = incumbent
                    best_objective = incumbent_objective
                    points[oper] += 2
                    i_best = 0
            else:
                rand = random.random()
                p = np.exp(-deltaE/T)
                if rand < p:
                    incumbent = current_solution
                    incumbent_objective = current_objective
        
        if count >= 100:
            if operator_used[0] > 0:
                P1 = P1*(1-r) + r*(points[0]/operator_used[0])
            else:
                P1 = P1*(1-r)
            if operator_used[1] > 0:
                P2 = P2*(1-r) + r*(points[1]/operator_used[1])
            else:
                P2 = P2*(1-r)
            if operator_used[2] > 0:
                P3 = P3*(1-r) + r*(points[2]/operator_used[2])
            else:
                P3 = P3*(1-r)
            count = 0
            points = [0, 0, 0]
            operator_used = [0, 0, 0]

        T = alpha * T

    return best_solution


def run10searches(S_0, prob):
    runningTimes = []
    best_solution = S_0
    objectives = []
    best_objective = calculateObjective(best_solution, prob)

    for i in range(10):
        tic = time.perf_counter()
        current_solution = generalAdaptiveMetaheuristics(prob, S_0)
        toc = time.perf_counter()

        running_time = (toc-tic)
        runningTimes.append(running_time)
        current_objective = calculateObjective(current_solution, prob)
        objectives.append(current_objective)

        if current_objective < best_objective:
            best_solution = current_solution
            best_objective = current_objective
    
    print('all objectives:', objectives)
    average_objective = np.average(objectives)
    average_runningTime = np.average(runningTimes)


    improvement = 100 * (calculateObjective(S_0, prob) - calculateObjective(best_solution, prob)) / calculateObjective(S_0, prob)

    print()
    print(' average objective |  best objective | improvement | running time')
    print('-------------------|-----------------|-------------|-------------')
    print('     %.1f     |    %.1f    |    %.2f    |    %.2f' %(average_objective, calculateObjective(best_solution, prob), improvement, average_runningTime))
    print()

    print('The best solution is: ', best_solution)

def runSearch(S_0, prob):

    tic = time.perf_counter()
    current_solution = generalAdaptiveMetaheuristics(prob, S_0)
    toc = time.perf_counter()

    running_time = (toc-tic)
    
    objective = calculateObjective(current_solution, prob)
    S_0_objective = calculateObjective(S_0, prob)

    improvement = 100 * (S_0_objective - objective) / S_0_objective

    print()
    print('   objective     | improvement | running time')
    print('-----------------|-------------|-------------')
    print('    %.1f   |    %.2f    |    %.2f' %(objective, improvement, running_time))
    print()

    print('The best solution is: ', current_solution)

def runAllOnce():
    print('------------Final Submission------------')

    tic = time.perf_counter()
    print()
    print('------------Vehicle 7 Call 3------------')
    prob1 = load_problem('./Call_7_Vehicle_3.txt')
    S_1 = createStartSolution(prob1)
    runSearch(S_1, prob1)

    print()
    print('------------Vehicle 18 Call 5------------')
    prob2 = load_problem('./Call_18_Vehicle_5.txt')
    S_2 = createStartSolution(prob2)
    runSearch(S_2, prob2)

    print()
    print('------------Vehicle 35 Call 7------------')
    prob3 = load_problem('./Call_35_Vehicle_7.txt')
    S_3 = createStartSolution(prob3)
    runSearch(S_3, prob3)

    print()
    print('------------Vehicle 80 Call 20------------')
    prob4 = load_problem('./Call_80_Vehicle_20.txt')
    S_4 = createStartSolution(prob4)
    runSearch(S_4, prob4)

    print()
    print('------------Vehicle 130 Call 40------------')
    prob5 = load_problem('./Call_130_Vehicle_40.txt')
    S_5 = createStartSolution(prob5)
    runSearch(S_5, prob5)
    toc = time.perf_counter()

    print('total runtime in minutes: %.1f' %((toc-tic)/60))


#prob = load_problem('/Users/tereseespeland/Documents/EnergiUiB/8. Semester/INF273/Assignments/Problems/Call_7_Vehicle_3.txt')
#S_0 = createStartSolution(prob)
#run10searches(S_0, prob)

runAllOnce()
