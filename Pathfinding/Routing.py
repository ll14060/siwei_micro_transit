# This is the routing module, it is a collection of functions
from gurobipy import *
import copy
import Parameter as para

# Suppose we compute the path lookup table before hand, a hash table
# Link_tt = {(1,3):[5,[1, 2, 3]]}
# Link_tt = {(O,D):[Total time, [Path]]}
Link_tt = {} # This is a dummy Link_tt, is not used

# The below functions are all for routing time/distance calculation
# The functions will calculate Cij for matching based on shortest path and check eligibility
# The input includes matched person and vehicle objects


# This function is to get estimated travel time for vehicle with zero task registered
# It will return a travel time based on Link_tt (either SHP or BiPath
def VehZeroTaskTimePreMatch(Person, Vehicle, Link_tt, currentTime):
    # Vehicle origin is not current location, but the closest node moving toward
    origin = Vehicle.nextNode
    # Pickup point is the person's pickup point
    pickup = Person.pickLoc
    # Drop Off point is the person's dropoff point
    dropoff = Person.dropLoc
    # Get the travel time, time is the first item of the hash table
    if Vehicle.status == 'I':
        TimetoPick = currentTime + Link_tt[(origin, pickup)][0]
    elif Vehicle.status == 'R':
        TimetoPick = Vehicle.timeNextNode + Link_tt[(origin, pickup)][0]

    # Need to check the time window of pickup passenger
    if TimetoPick > Person.pickTimeLatest:
        TimetoPick = float('Inf')

    TimetoDrop = TimetoPick + Link_tt[(pickup, dropoff)][0]
    TotalTaskDuration = TimetoDrop - currentTime
    # Task path should start with next node (after reaching current location)
    # Remember current location must be the last node in trajectory list
    taskPath = Link_tt[(origin, pickup)][1] + Link_tt[(pickup, dropoff)][1][1:]
    tasksequence = [(Person, 'P'), (Person, 'D')]
    taskTime = [(Person, 'P', TimetoPick), (Person, 'D', TimetoDrop)]

    # Need to construct time dependent taskPath = [(Node, time)]
    # If the vehicle is idle, no next node
    # This condition was used before: Vehicle.timeNextNode is None or Vehicle.timeNextNode < currentTime
    if Vehicle.status == 'I':
        timeArriveNextNode = currentTime
    elif Vehicle.status == 'R':
        timeArriveNextNode = Vehicle.timeNextNode

    taskPathwithTime = [(Vehicle.nextNode, timeArriveNextNode)]
    for i in range(1, len(taskPath)):
        node_to_arrive = taskPath[i]
        time_to_arrive = taskPathwithTime[i-1][1] + Link_tt[(taskPathwithTime[i-1][0],node_to_arrive)][0]
        taskPathwithTime.append((node_to_arrive, time_to_arrive))
    debug = 0
    # If the vehicle is idle and about to relocate, use time to pick instead of total duration
    if Vehicle.status == 'I':
        TotalTaskDuration = TimetoPick - currentTime

    return TotalTaskDuration, taskPathwithTime, tasksequence, taskTime


#####################################################################################################
# Two sub functions used in "VehOnePersonMatch"
# The following function identifies segment as a pickup or a drop, then returns the node/location
# Input is task = (Person, 'FLAG')
def identifySegFlag(task):
    if task[1] == 'P':
        node = task[0].pickLoc
    elif task[1] == 'D':
        node = task[0].dropLoc

    return node


# This function is to estimate travel time for vehicle with one task registered
# We first define a function to check time window eligibility for two tasks
def checkTimeWindowTwo(TimeP1, TimeD1, TimeP2, TimeD2, TotalTime, Person1, Person2):
    # Logic check of four time points
    check = (TimeP1 < Person1.pickTimeLatest) * (TimeD1 < Person1.dropTimeLatest) * (TimeP2 < Person2.pickTimeLatest) * (TimeD2 < Person2.dropTimeLatest)
    # If check = 0 means at least one time window is violated
    if check == 0:
        # Then set the total time to be a large number
        TotalTime = float('inf')

    return TotalTime


# We have two cases: 1. enroute to pickup, 2. enroute to drop off
# We calculate the marginal cost of inserting the new customer to current route
def VehOnePersonPreMatch(Person2, Vehicle, currentTime, Link_tt):

    origin = Vehicle.nextNode
    # Calculating the current path time cost for future detour time cost calculation
    currentPathTimeCost = Vehicle.path[-1][1] - currentTime

    # 1. Vehicle has a pick up task, dropoff list should be empty
    if Vehicle.futureTasks[0][1] == 'P':
        # Name Person1, who is the person in toPick
        Person1 = Vehicle.futureTasks[0][0]

        # Get the travel time/Distance for all possible segments
        # Origin could link to P1 and P2
        DistOrP1 = Link_tt[origin,Person1.pickLoc][0]
        DistOrP2 = Link_tt[origin, Person2.pickLoc][0]
        # P1 could lead to D1,P2 or D2
        DistP1D1 = Link_tt[Person1.pickLoc,Person1.dropLoc][0]
        DistP1P2 = Link_tt[Person1.pickLoc,Person2.pickLoc][0]
        DistP1D2 = Link_tt[Person1.pickLoc,Person2.dropLoc][0]
        # P2 could lead to D2, P1, or D1
        DistP2D2 = Link_tt[Person2.pickLoc,Person2.dropLoc][0]
        DistP2P1 = Link_tt[Person2.pickLoc,Person1.pickLoc][0]
        DistP2D1 = Link_tt[Person2.pickLoc,Person1.dropLoc][0]
        # D1 could lead to P2 or D2
        DistD1P2 = Link_tt[Person1.dropLoc,Person2.pickLoc][0]
        DistD1D2 = Link_tt[Person1.dropLoc,Person2.dropLoc][0]
        # D2 could lead to P1 or D1
        DistD2P1 = Link_tt[Person2.dropLoc,Person1.pickLoc][0]
        DistD2D1 = Link_tt[Person2.dropLoc,Person1.dropLoc][0]

        # Construct two hash table to store total travel time and sequence:
        TravelTime = {}
        Sequence = {}
        TaskTime = {}

        # Option 1: Origin-Pick1-Drop1-Pick2-Drop2
        # TotalDistOP1 = DistOrP1 + DistP1D1 + DistD1P2 + DistP2D2
        TimetoP1 = Vehicle.timeNextNode + DistOrP1
        TimetoD1 = TimetoP1 + DistP1D1
        TimetoP2 = TimetoD1 + DistD1P2
        TimetoD2 = TimetoP2 + DistP2D2
        TotalDistOP1 = TimetoD2 - Vehicle.timeNextNode
        # Check time window eligibility
        TotalDistOP1 = checkTimeWindowTwo(TimetoP1, TimetoD1, TimetoP2, TimetoD2, TotalDistOP1, Person1, Person2)
        TravelTime.update({"Option1": TotalDistOP1})
        Sequence.update({'Option1': [(Person1, 'P'), (Person1, 'D'), (Person2, 'P'), (Person2, 'D')]})
        TaskTime.update({'Option1': [(Person1, 'P', TimetoP1), (Person1, 'D',TimetoD1), (Person2, 'P',TimetoP2), (Person2, 'D', TimetoD2)]})

        # Option 2: Origin-Pick2-Drop2-Pick1-Drop1
        # TotalDistOP2 = DistOrP2 + DistP2D2 + DistD2P1 + DistP1D1
        TimetoP2 = Vehicle.timeNextNode + DistOrP2
        TimetoD2 = TimetoP2 + DistP2D2
        TimetoP1 = TimetoD2 + DistD2P1
        TimetoD1 = TimetoP1 + DistP1D1
        TotalDistOP2 = TimetoD1 - Vehicle.timeNextNode
        # Check time window eligibility
        TotalDistOP2 = checkTimeWindowTwo(TimetoP1, TimetoD1, TimetoP2, TimetoD2, TotalDistOP2, Person1, Person2)
        TravelTime.update({"Option2": TotalDistOP2})
        Sequence.update({'Option2': [(Person2, 'P'), (Person2, 'D'), (Person1, 'P'), (Person1, 'D')]})
        TaskTime.update({'Option2': [(Person2, 'P',TimetoP2), (Person2, 'D',TimetoD2), (Person1, 'P',TimetoP1), (Person1, 'D',TimetoD1)]})

        # Option 3: Origin-Pick1-Pick2-Drop1-Drop2
        # TotalDistOP3 = DistOrP1 + DistP1P2 + DistP2D1 + DistD1D2
        TimetoP1 = Vehicle.timeNextNode + DistOrP1
        TimetoP2 = TimetoP1 + DistP1P2
        TimetoD1 = TimetoP2 + DistP2D1
        TimetoD2 = TimetoD1 + DistD1D2
        TotalDistOP3 = TimetoD2 - Vehicle.timeNextNode
        # Check capacity constraint
        if Person2.size + Person1.size > Vehicle.cap:
            # If it more than capacity, return a very large number
            TotalDistOP3 = float('inf')
        else:
            # Check time window eligibility
            TotalDistOP3 = checkTimeWindowTwo(TimetoP1,TimetoD1, TimetoP2, TimetoD2, TotalDistOP3, Person1, Person2)
        TravelTime.update({"Option3": TotalDistOP3})
        Sequence.update({'Option3': [(Person1, 'P'), (Person2, 'P'), (Person1, 'D'), (Person2, 'D')]})
        TaskTime.update({'Option3': [(Person1, 'P',TimetoP1), (Person2, 'P',TimetoP2), (Person1, 'D',TimetoD1), (Person2, 'D',TimetoD2)]})

        # Option 4: Origin-Pick1-Pick2-Drop2-Drop1
        # TotalDistOP4 = DistOrP1 + DistP1P2 + DistP2D2 + DistD2D1
        TimetoP1 = Vehicle.timeNextNode + DistOrP1
        TimetoP2 = TimetoP1 + DistP1P2
        TimetoD2 = TimetoP2 + DistP2D2
        TimetoD1 = TimetoD2 + DistD2D1
        TotalDistOP4 = TimetoD1 - Vehicle.timeNextNode
        # Check capacity constraint
        if Person2.size + Person1.size > Vehicle.cap:
            # If it more than capacity, return a very large number
            TotalDistOP4 = float('inf')
        else:
            # Check time window eligibility
            TotalDistOP4 = checkTimeWindowTwo(TimetoP1,TimetoD1, TimetoP2, TimetoD2, TotalDistOP4, Person1, Person2)
        TravelTime.update({"Option4": TotalDistOP4})
        Sequence.update({'Option4': [(Person1, 'P'), (Person2, 'P'), (Person2, 'D'), (Person1, 'D')]})
        TaskTime.update({'Option4': [(Person1, 'P', TimetoP1), (Person2, 'P', TimetoP2), (Person2, 'D', TimetoD2), (Person1, 'D', TimetoD1)]})

        # Option 5: Origin-Pick2-Pick1-Drop1-Drop2
        # TotalDistOP5 = DistOrP2 + DistP2P1 + DistP1D1 + DistD1D2
        TimetoP2 = Vehicle.timeNextNode + DistOrP2
        TimetoP1 = TimetoP2 + DistP2P1
        TimetoD1 = TimetoP1 + DistP1D1
        TimetoD2 = TimetoD1 + DistD1D2
        TotalDistOP5 = TimetoD2 - Vehicle.timeNextNode
        if Person2.size + Person1.size > Vehicle.cap:
            # If it more than capacity, return a very large number
            TotalDistOP5 = float('inf')
        else:
            # Check time window eligibility
            TotalDistOP5 = checkTimeWindowTwo(TimetoP1,TimetoD1, TimetoP2, TimetoD2, TotalDistOP5, Person1, Person2)
        TravelTime.update({"Option5": TotalDistOP5})
        Sequence.update({'Option5': [(Person2, 'P'), (Person1, 'P'), (Person1, 'D'), (Person2, 'D')]})
        TaskTime.update({'Option5': [(Person2, 'P', TimetoP2), (Person1, 'P', TimetoP1), (Person1, 'D', TimetoD1), (Person2, 'D', TimetoD2)]})

        # Option 6: Origin-Pick2-Pick1-Drop2-Drop1
        # TotalDistOP6 = DistOrP2 + DistP2P1 + DistP1D2 + DistD2D1
        TimetoP2 = Vehicle.timeNextNode + DistOrP2
        TimetoP1 = TimetoP2 + DistP2P1
        TimetoD2 = TimetoP1 + DistP1D2
        TimetoD1 = TimetoD2 + DistD2D1
        TotalDistOP6 = TimetoD1 - Vehicle.timeNextNode
        if Person2.size + Person1.size > Vehicle.cap:
            # If it more than capacity, return a very large number
            TotalDistOP6 = float('inf')
        else:
            # Check time window eligibility
            TotalDistOP6 = checkTimeWindowTwo(TimetoP1, TimetoD1, TimetoP2, TimetoD2, TotalDistOP6, Person1, Person2)
        TravelTime.update({"Option6": TotalDistOP6})
        Sequence.update({'Option6': [(Person2, 'P'), (Person1, 'P'), (Person2, 'D'), (Person1, 'D')]})
        TaskTime.update({'Option6': [(Person2, 'P', TimetoP2), (Person1, 'P',TimetoP1), (Person2, 'D',TimetoD2), (Person1, 'D',TimetoD1)]})

        # Now find the smallest value of 6 options
        minimumTime = min(TravelTime.values())
        # Calculate the minimum detour time
        minDetourTime = minimumTime - currentPathTimeCost

        # Find minimum travel time key
        minimumKey = list(TravelTime.keys())[list(TravelTime.values()).index(minimumTime)]

        # Find the task sequence
        taskSquence = Sequence[minimumKey]
        taskTime = TaskTime[minimumKey]

        # Based on the sequence to get path
        # Segment 1 is current loc to first node
        node1 = identifySegFlag(taskSquence[0])
        seg1 = Link_tt[(Vehicle.nextNode, node1)][1]
        # Seg 2
        node2 = identifySegFlag(taskSquence[1])
        seg2 = Link_tt[(node1, node2)][1][1:]
        # Seg 3
        node3 = identifySegFlag(taskSquence[2])
        seg3 = Link_tt[(node2, node3)][1][1:]
        # Seg 4
        node4 = identifySegFlag(taskSquence[3])
        seg4 = Link_tt[(node3, node4)][1][1:]
        taskPath = seg1 + seg2 + seg3 + seg4

        # Need to construct time dependent taskPath = [(Node, time)]
        taskPathwithTime = [(Vehicle.nextNode, Vehicle.timeNextNode)]
        for i in range(1, len(taskPath)):
            node_to_arrive = taskPath[i]
            time_to_arrive = taskPathwithTime[i-1][1] + Link_tt[(taskPathwithTime[i-1][0],node_to_arrive)][0]
            taskPathwithTime.append((node_to_arrive, time_to_arrive))

        return minDetourTime, taskPathwithTime, taskSquence, taskTime

    # 2. The vehicle has a dropoff task, pickup list should be empty
    elif Vehicle.futureTasks[0][1] == 'D':
        # Name Person1, who is the person in toDrop
        Person1 = Vehicle.futureTasks[0][0]

        # Get the travel time/Distance for all possible segments
        # Orgin could lead to D1 and P2
        DistOrP2 = Link_tt[origin, Person2.pickLoc][0]
        DistOrD1 = Link_tt[origin, Person1.dropLoc][0]
        # P2 could lead to D2, or D1
        DistP2D2 = Link_tt[Person2.pickLoc,Person2.dropLoc][0]
        DistP2D1 = Link_tt[Person2.pickLoc,Person1.dropLoc][0]
        # D1 could lead to P2 or D2
        DistD1P2 = Link_tt[Person1.dropLoc,Person2.pickLoc][0]
        DistD1D2 = Link_tt[Person1.dropLoc,Person2.dropLoc][0]
        # D2 could lead to D1
        DistD2D1 = Link_tt[Person2.dropLoc,Person1.dropLoc][0]

        # In order to use the same function "checkTimeWindowTwo" we create a fake TimetoP1, a very small number
        TimetoP1 = 0.1

        # Construct two hash table to store total travel time and sequence:
        TravelTime = {}
        Sequence = {}
        TaskTime = {}

        # Option 1: Origin-Drop1-Pick2-Drop2
        TimetoD1 = Vehicle.timeNextNode + DistOrD1
        TimetoP2 = TimetoD1 + DistD1P2
        TimetoD2 = TimetoP2 + DistP2D2
        TotalDistOP1 = TimetoD2 - Vehicle.timeNextNode
        # Check time window eligibility
        TotalDistOP1 = checkTimeWindowTwo(TimetoP1, TimetoD1, TimetoP2, TimetoD2, TotalDistOP1, Person1, Person2)
        TravelTime.update({"Option1": TotalDistOP1})
        Sequence.update({'Option1': [(Person1, 'D'), (Person2, 'P'), (Person2, 'D')]})
        TaskTime.update({'Option1': [(Person1, 'D', TimetoD1), (Person2, 'P', TimetoP2), (Person2, 'D', TimetoD2)]})

        # Option 2: Origin-Pick2-Drop1-Drop2
        # TotalDistOP5 = DistOrP2 + DistP2P1 + DistP1D1 + DistD1D2
        TimetoP2 = Vehicle.timeNextNode + DistOrP2
        TimetoD1 = TimetoP2 + DistP2D1
        TimetoD2 = TimetoD1 + DistD1D2
        TotalDistOP2 = TimetoD2 - Vehicle.timeNextNode
        if Person2.size + Person1.size > Vehicle.cap:
            # If it more than capacity, return a very large number
            TotalDistOP2 = float('inf')
        else:
            # Check time window eligibility
            TotalDistOP2 = checkTimeWindowTwo(TimetoP1,TimetoD1, TimetoP2, TimetoD2, TotalDistOP2, Person1, Person2)
        TravelTime.update({"Option2": TotalDistOP2})
        Sequence.update({'Option2': [(Person2, 'P'), (Person1, 'D'), (Person2, 'D')]})
        TaskTime.update({'Option2': [(Person2, 'P',TimetoP2), (Person1, 'D',TimetoD1), (Person2, 'D',TimetoD2)]})

        # Option 3: Origin-Pick2-Drop2-Drop1
        # TotalDistOP6 = DistOrP2 + DistP2P1 + DistP1D2 + DistD2D1
        TimetoP2 = Vehicle.timeNextNode + DistOrP2
        TimetoD2 = TimetoP2 + DistP2D2
        TimetoD1 = TimetoD2 + DistD2D1
        TotalDistOP3 = TimetoD1 - Vehicle.timeNextNode
        if Person2.size + Person1.size > Vehicle.cap:
            # If it more than capacity, return a very large number
            TotalDistOP3 = float('inf')
        else:
            # Check time window eligibility
            TotalDistOP3 = checkTimeWindowTwo(TimetoP1, TimetoD1, TimetoP2, TimetoD2, TotalDistOP3, Person1, Person2)
        TravelTime.update({"Option3": TotalDistOP3})
        Sequence.update({'Option3': [(Person2, 'P'), (Person2, 'D'), (Person1, 'D')]})
        TaskTime.update({'Option3': [(Person2, 'P',TimetoP2), (Person2, 'D',TimetoD2), (Person1, 'D',TimetoD1)]})

        # Now find the smallest value of 3 options
        minimumTime = min(TravelTime.values())
        # Calculate the minimum detour time
        minDetourTime = minimumTime - currentPathTimeCost

        # Find minimum travel time key
        minimumKey = list(TravelTime.keys())[list(TravelTime.values()).index(minimumTime)]

        # Find the task sequence
        taskSquence = Sequence[minimumKey]
        taskTime = TaskTime[minimumKey]

        # Based on the sequence to get path
        # Segment 1 is current loc to first node
        node1 = identifySegFlag(taskSquence[0])
        seg1 = Link_tt[(Vehicle.nextNode, node1)][1]
        # Seg 2
        node2 = identifySegFlag(taskSquence[1])
        seg2 = Link_tt[(node1, node2)][1][1:]
        # Seg 3
        node3 = identifySegFlag(taskSquence[2])
        seg3 = Link_tt[(node2, node3)][1][1:]

        taskPath = seg1 + seg2 + seg3

        # Need to construct time dependent taskPath = [(Node, time)]
        taskPathwithTime = [(Vehicle.nextNode, Vehicle.timeNextNode)]
        for i in range(1, len(taskPath)):
            node_to_arrive = taskPath[i]
            time_to_arrive = taskPathwithTime[i-1][1] + Link_tt[(taskPathwithTime[i-1][0],node_to_arrive)][0]
            taskPathwithTime.append((node_to_arrive, time_to_arrive))
        return minDetourTime, taskPathwithTime, taskSquence, taskTime


#####################################################################################################
# This function is called single vehicle capacitated VRP with TW and pickup/delivery
# links is a Gurobi tuple-list, which are all (i, j) representation of links, use for Xij DVs
# linkCost is a hash table which contains link travel time (must be time, not distance)
# timeVars are a list of t[i] DVs, timeWindow is a hash table for LAT of each Node
# loadVars are a list of occupancy at node i, occ[i], loadTask is a hash table for load at each node, drop with '-'
# pickdropPair is a list of tuples, which represents a task request both pickup and dropoff (not yet picked)
# nodeList includes all nodes, hub is current location, end is a dummy location for OVRP
# Vehicle is an vehicle object
def scvrptwpd(links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, currentime, Vehicle):

    # # Identify hub and end from nodeList
    # hub = nodeList[0]
    # end = nodeList[-1]

    # Call Gurobi
    m = Model('TwoDrops')

    dummy=0
    # Setup decision vars, which is the number of links xij, together with objective
    x = m.addVars(links, vtype = GRB.BINARY, obj=linkCost, name ="link")
    t = m.addVars(timeVars, vtype = GRB.CONTINUOUS, name = 'time')
    n = m.addVars(loadVars, vtype = GRB.CONTINUOUS, name = 'occu')

    # Update Model
    m.update()
    # Mute output
    m.setParam('OutputFlag', 0)

    # Add routing constraints
    # Leading constraint
    for i in nodeList:
        if i != 'end':
            m.addConstr(sum(x[i,j] for i , j in links.select(i, '*')) == 1)

    # Receiving constr
    for j in nodeList:
        if j != 'hub':
            m.addConstr(sum(x[i,j] for i , j in links.select('*', j)) == 1)

    # Flow balance
    for j in nodeList:
        if j not in ['hub', 'end']:
            m.addConstr(sum(x[i,j] for i, j in links.select('*', j)) == sum(x[i,j] for i, j in links.select(j , '*')))

    # Time window constraint
    for i in timeVars:
        if i != 'hub':
            m.addConstr(t[i] <= timeWindow[i])

    # Sequence Time window, 100 is the big M ####
    m.addConstr(t['hub'] == currentime)
    for i, j in links:
        if j != 'end':
            # Need to add a condition where the two task happen at different nodes
            if linkCost[(i,j)] != 0:
                m.addConstr(t[i] + linkCost[(i,j)] <= t[j] + (1 - x[i,j])*100)
            # If two tasks happen at the same node, the time lag set to be two time steps
            elif linkCost[(i,j)] == 0:
                m.addConstr(t[i] + 0.1 <= t[j] + (1 - x[i,j])*1000)


    # for p/d pair, p must ahead d
    for i, j  in pickdropPair:
        m.addConstr(t[i] + 1 <= t[j])

    # Capacity constraints
    for i in loadVars:
        m.addConstr(n[i] <= Vehicle.cap)

    # Load Dynamics:
    m.addConstr(n['hub'] == Vehicle.occu)
    for i, j in links:
        # except the end node, M = 100 ####
        if j != 'end':
            m.addConstr(n[i] + loadTask[i] <= n[j] + (1 - x[i,j])*100)

    # END of adding vars, constraints

    m.optimize()

    # Construct a Dict to store sequence, {NodeID : Time at the Node}
    sequenDict = {}

    if m.status == GRB.Status.OPTIMAL:
        objValue = m.objVal
        # print('The final solution is:')
        # For timeVars, find the arrival time at each location
        for loc in timeVars:
            sequenDict.update({loc: t[loc].x})

        # for i,j in links:
        #     if(x[i,j].x > 0):
        #         print(i, j, x[i,j].x)
    else: # return a very large cost
        objValue = float('inf')

    return objValue, sequenDict


#####################################################################################################
# The following functions are all used for "two assigned tasks + one new request" cases
#####################################################################################################
# This function generates input for Gurobi is 2 drops + 1 new request
def genVarsTwoDrop(Vehicle, Person3, Linktt):

    Person1 = Vehicle.futureTasks[0][0]
    Person2 = Vehicle.futureTasks[1][0]

    # Setup Nodes and Links
    # Node set contains hub, two existing drop nodes and a pair of new p/d nodes
    hub = Vehicle.nextNode
    drop1 = Person1.dropLoc
    drop2 = Person2.dropLoc
    pick3 = Person3.pickLoc
    drop3 = Person3.dropLoc

    # Creat a pick/drop pair
    pickdropPair = [('P3', 'D3')]

    # end is a dummy node with a very large id
    end = '999999999'

    # In order to avoid duplicated nodes appear in VRP/PDP Gurobi, we need to do a node lookup table
    nodelookup = {'hub':hub, 'D1':drop1, 'D2':drop2, 'P3':pick3, 'D3':drop3, 'end':end}
    nodeList = list(nodelookup.keys())

    # Linkcost set will be in hash table
    # Initiate the hash table with drop nodes to end as zeros, since we are not returning to hub
    linkCost = {('D3', 'end'):0, ('D1', 'end'):0, ('D2', 'end'):0}

    # Add all other links
    # Hub could lead to D1, D2, P3
    receiveList = ['P3', 'D1', 'D2']
    for i in receiveList:
        linkCost.update({('hub', i):Linktt[(hub, nodelookup[i])][0]})

    # pick3 could lead to all other nodes exclude hub and end
    leadNodes = ['P3']
    receiveList = ['D1', 'D2', 'P3', 'D3']
    for i in leadNodes:
        for j in receiveList:
            if i != j:
                linkCost.update({(i, j):Linktt[(nodelookup[i], nodelookup[j])][0]})

    # drop1 could lead to pick3, drop3, drop2
    receiveList = ['D2', 'P3', 'D3']
    for j in receiveList:
        linkCost.update({('D1', j):Linktt[(drop1, nodelookup[j])][0]})

    # drop2 could lead to drop1, pick3 and drop3
    receiveList = ['D1', 'P3', 'D3']
    for j in receiveList:
        linkCost.update({('D2', j):Linktt[(drop2, nodelookup[j])][0]})

    # drop3 could lead to drop1, drop2
    receiveList = ['D1', 'D2']
    for j in receiveList:
        linkCost.update({('D3', j):Linktt[(drop3, nodelookup[j])][0]})

    # Links are in tuple list
    links = tuplelist()
    # Link names are linkcost keys
    linkList = list(linkCost.keys())
    # Append them to the tuplelist
    for i in linkList:
        links.append(i)

    # Also need to creat a time window constraints and vars
    timeWindow = {'D1':Person1.dropTimeLatest, 'D2':Person2.pickTimeLatest, 'D3':Person3.dropTimeLatest}
    timeWindow.update({'P3':Person3.pickTimeLatest})
    timeVars = list(timeWindow.keys())
    timeVars.append('hub')

    # Also need to fit capacity
    loadTask = {'hub':0, 'D1':-Person1.size, 'D2':-Person2.size, 'P3':Person3.size, 'D3':-Person3.size}
    loadVars = list(loadTask.keys())

    return links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, nodelookup


#####################################################################################################
# This function generates input for gurobi is 1 drop + 1 pick + 1 new request
def genVarsOnePOneD(Vehicle, Person3, Linktt):

    # Identify Person 1 and Person 2, the one need to be dropped is P1
    Person1 = Vehicle.futureTasks[0][0]
    Person2 = Vehicle.futureTasks[1][0]
    if Person1 == Person2: # Equal means Pick1 and then Drop1
        Person1 = Vehicle.futureTasks[2][0]
    elif Person1 != Person2 and Vehicle.futureTasks[0][1] == 'P':
        Person1 = Vehicle.futureTasks[1][0]
        Person2 = Vehicle.futureTasks[0][0]

    # Create a lookup table for persons
    # This lookup table need to be expanded when the problem size got expanded
    PersonLookup = {'1':Person1, '2':Person2, '3':Person3}

    # Setup Nodes and Links
    # Node set containts hub, two existing drop nodes and a pair of new p/d nodes
    hub = Vehicle.nextNode
    drop1 = Person1.dropLoc
    pick2 = Person2.pickLoc
    drop2 = Person2.dropLoc
    pick3 = Person3.pickLoc
    drop3 = Person3.dropLoc

    # Creat a pick/drop pair
    pickdropPair = [('P2', 'D2'), ('P3', 'D3')]

    # end is a dummy node with a very large id
    end = '999999999'
    nodeList = [hub, drop1, pick2, drop2, pick3, drop3, end]

    # In order to avoid duplicated nodes appear in VRP/PDP Gurobi, we need to do a node lookup table
    nodelookup = {'hub':hub, 'D1':drop1, 'P2':pick2, 'D2':drop2, 'P3':pick3, 'D3':drop3, 'end':end}
    nodeList = list(nodelookup.keys())

    # Linkcost set will be in hash table
    # Initiate the hash table with drop nodes to end as zeros, since we are not returning to hub
    linkCost = {('D3', 'end'):0, ('D1', 'end'):0, ('D2', 'end'):0}

    # Add all other links
    # Hub could lead to all pick nodes and Drop 1
    receiveList = ['D1', 'P2', 'P3']
    for i in receiveList:
        linkCost.update({('hub', i):Linktt[(hub, nodelookup[i])][0]})

    # pick2/ pick3 could lead to all other nodes exclude hub and end
    leadNodes = ['P2', 'P3']
    receiveList = ['D1', 'P2', 'D2', 'P3', 'D3']
    for i in leadNodes:
        for j in receiveList:
            if i != j:
                linkCost.update({(i, j):Linktt[(nodelookup[i], nodelookup[j])][0]})

    # drop1 could lead to pick3, drop3, drop2, pick2
    receiveList = ['P2', 'D2', 'P3', 'D3']
    for j in receiveList:
        linkCost.update({('D1', j):Linktt[(drop1, nodelookup[j])][0]})

    # drop2 could lead to drop1, pick3 and drop3
    receiveList = ['D1', 'P3', 'D3']
    for j in receiveList:
        linkCost.update({('D2', j):Linktt[(drop2, nodelookup[j])][0]})

    # drop3 could lead to drop1, drop2, pick2
    receiveList = ['D1', 'P2', 'D2']
    for j in receiveList:
        linkCost.update({('D3', j):Linktt[(drop3, nodelookup[j])][0]})


    # Links are in tuple list
    links = tuplelist()
    # Link names are linkcost keys
    linkList = list(linkCost.keys())
    # Append them to the tuplelist
    for i in linkList:
        links.append(i)

    # Also need to creat a time window constratints and vars
    #     endtime = max(Person1.dropTimeLatest, Person2.dropTimeLatest, Person3.dropTimeLatest)
    timeWindow = {'D1':Person1.dropTimeLatest, 'P2':Person2.pickTimeLatest, 'D2':Person2.dropTimeLatest}
    timeWindow.update({'P3':Person3.pickTimeLatest, 'D3':Person3.dropTimeLatest})
    timeVars = list(timeWindow.keys())
    timeVars.append('hub')

    # Also need to fit capacity
    loadTask = {'hub':0, 'D1':-Person1.size, 'P2':Person2.size, 'D2':-Person2.size, 'P3':Person3.size, 'D3':-Person3.size}
    loadVars = list(loadTask.keys())

    return links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, nodelookup, PersonLookup


#####################################################################################################
# This function generates input for Gurobi is 2 picks + 1 new request
def genVarsTwoPick(Vehicle, Person3, Linktt):

    # Identify Person 1 and Person 2
    Person1 = Vehicle.futureTasks[0][0]
    Person2 = Vehicle.futureTasks[1][0]
    if Person1 == Person2: # Equal means Pick1 and then Drop1
        Person2 = Vehicle.futureTasks[2][0]

    # Setup Nodes and Links
    # Node set containts hub, two existing drop nodes and a pair of new p/d nodes
    hub = Vehicle.nextNode
    pick1 = Person1.pickLoc
    drop1 = Person1.dropLoc
    pick2 = Person2.pickLoc
    drop2 = Person2.dropLoc
    pick3 = Person3.pickLoc
    drop3 = Person3.dropLoc

    # Creat a pick/drop pair
    pickdropPair = [('P1', 'D1'), ('P2', 'D2'), ('P3', 'D3')]

    # end is a dummy node with a very large id
    end = '999999999'

    # In order to avoid duplicated nodes appear in VRP/PDP Gurobi, we need to do a node lookup table
    nodelookup = {'hub':hub, 'P1':pick1, 'D1':drop1, 'P2':pick2, 'D2':drop2, 'P3':pick3, 'D3':drop3, 'end':end}
    nodeList = list(nodelookup.keys())


    # Linkcost set will be in hash table
    # Initiate the hash table with drop nodes to end as zeros, since we are not returning to hub
    linkCost = {('D3', 'end'):0, ('D1', 'end'):0, ('D2', 'end'):0}

    # Add all other links
    # Hub could lead to all pick nodes
    receiveList = ['P1', 'P2', 'P3']
    for i in receiveList:
        linkCost.update({('hub', i):Linktt[(hub, nodelookup[i])][0]})

    # pick1/pick2/ pick3 could lead to all other nodes exclude hub and end
    leadNodes = ['P1', 'P2', 'P3']
    receiveList = ['P1','D1', 'P2', 'D2', 'P3', 'D3']
    for i in leadNodes:
        for j in receiveList:
            if i != j:
                linkCost.update({(i, j):Linktt[(nodelookup[i], nodelookup[j])][0]})

    # drop1 could lead to pick3, drop3, drop2, pick2
    receiveList = ['P2', 'D2', 'P3', 'D3']
    for j in receiveList:
        linkCost.update({('D1', j):Linktt[(drop1, nodelookup[j])][0]})

    # drop2 could lead to pick1, drop1, pick3 and drop3
    receiveList = ['P1','D1', 'P3', 'D3']
    for j in receiveList:
        linkCost.update({('D2', j):Linktt[(drop2, nodelookup[j])][0]})

    # drop3 could lead to pick1, drop1, drop2, pick2
    receiveList = ['P1','D1', 'P2', 'D2']
    for j in receiveList:
        linkCost.update({('D3', j):Linktt[(drop3, nodelookup[j])][0]})

    # Links are in tuple list
    links = tuplelist()
    # Link names are linkcost keys
    linkList = list(linkCost.keys())
    # Append them to the tuplelist
    for i in linkList:
        links.append(i)

    # Also need to creat a time window constratints and vars
    #     endtime = max(Person1.dropTimeLatest, Person2.dropTimeLatest, Person3.dropTimeLatest)
    timeWindow = {'D1':Person1.dropTimeLatest, 'P2':Person2.pickTimeLatest, 'D2':Person2.dropTimeLatest}
    timeWindow.update({'P1':Person1.pickTimeLatest, 'P3':Person3.pickTimeLatest, 'D3':Person3.dropTimeLatest})
    timeVars = list(timeWindow.keys())
    timeVars.append('hub')

    # Also need to fit capacity
    loadTask = {'hub':0, 'P1':Person1.size, 'D1':-Person1.size, 'P2':Person2.size, 'D2':-Person2.size, 'P3':Person3.size, 'D3':-Person3.size}
    loadVars = list(loadTask.keys())

    return links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, nodelookup


#####################################################################################################
# This function calculates total time/distance when a vehicle has 2 tasks ahead
# There are around 50 cases in total, I will do a VRP for each vehicle, Complexity =
def VehTwoPersonPreMatch(Person3, Vehicle, currentTime, Link_tt):

    # Calculating the current path time cost for future detour time cost calculation
    currentPathTimeCost = Vehicle.path[-1][1] - currentTime

    # In total 3 cases, 2 picks, 1 pick 1 drop, 2 drops
    # 1. Two drop cases
    if len(Vehicle.futureTasks) == 2:
        Person1 = Vehicle.futureTasks[0][0]
        Person2 = Vehicle.futureTasks[1][0]
        links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, nodeLookup= genVarsTwoDrop(Vehicle, Person3, Link_tt)
        objValue, sequenDict = scvrptwpd(links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, currentTime, Vehicle)
        # First sort the dictionary based on values
        sorted_task_nodes = [k for k, v in sorted(sequenDict.items(), key=lambda item: item[1],reverse=False)]
        # Decide task sequence
        taskSequence = []
        taskTime = []

        # Due to my stupid data structure I need to create a lookup table here for references "P1" to Person1
        # This lookup table need to be expanded when the problem size got expanded
        PersonLookup = {'1':Person1, '2':Person2, '3':Person3}
        # Inititate the location and time now to fine the task completion time for each task
        locNow = nodeLookup['hub']
        timeNow = Vehicle.timeNextNode
        for i in sorted_task_nodes:
            if i != 'hub':
                status = i[0]
                personTarget = PersonLookup[i[1:]]
                taskSequence.append((personTarget,status))

                # Create taskTime [(PersonObj, 'P'/'D', Time), (PersonObj,...)]
                timeSeg = Link_tt[(locNow, nodeLookup[i])][0]
                timeArrive = timeNow + timeSeg
                taskTime.append((personTarget, status, timeArrive))
                locNow = nodeLookup[i]
                timeNow = timeArrive

    # 3. Two picks, means futuretask length is 4
    elif len(Vehicle.futureTasks) == 4:

        # identify person 1 and person 2
        Person1 = Vehicle.futureTasks[0][0]
        Person2 = Vehicle.futureTasks[1][0]
        if Person1 == Person2: # Equal means Pick1 and then Drop1
            Person2 = Vehicle.futureTasks[2][0]

        links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, nodeLookup= genVarsTwoPick(Vehicle, Person3, Link_tt)
        objValue, sequenDict = scvrptwpd(links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, currentTime, Vehicle)


        # First sort the dictionary based on values
        sorted_task_nodes = [k for k, v in sorted(sequenDict.items(), key=lambda item: item[1],reverse=False)]
        # Decide task sequence
        taskSequence = []
        taskTime = []

        # Loop around both sorted nodes to get task sequence
        # Due to my stupid data structure I need to create a lookup table here for references "P1" to Person1
        # This lookup table need to be expanded when the problem size got expanded
        PersonLookup = {'1':Person1, '2':Person2, '3':Person3}
        # Inititate the location and time now to fine the task completion time for each task
        locNow = nodeLookup['hub']
        timeNow = Vehicle.timeNextNode
        for i in sorted_task_nodes:
            if i != 'hub':
                status = i[0]
                personTarget = PersonLookup[i[1:]]
                taskSequence.append((personTarget,status))

                # Create taskTime [(PersonObj, 'P'/'D', Time), (PersonObj,...)]
                timeSeg = Link_tt[(locNow, nodeLookup[i])][0]
                timeArrive = timeNow + timeSeg
                taskTime.append((personTarget, status, timeArrive))
                locNow = nodeLookup[i]
                timeNow = timeArrive

    # 2. One pick and One drop
    else:
        # Need to identify person 1 and person 2, it is done in the genVarsOnepOneD

        links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, nodeLookup, PersonLookup= genVarsOnePOneD(Vehicle, Person3, Link_tt)
        objValue, sequenDict = scvrptwpd(links, linkCost, timeVars, timeWindow, loadVars, loadTask, pickdropPair, nodeList, currentTime, Vehicle)
        # First sort the dictionary based on values
        sorted_task_nodes = [k for k, v in sorted(sequenDict.items(), key=lambda item: item[1],reverse=False)]

        # Decide task sequence
        taskSequence = []
        taskTime = []
        # Loop around both sorted nodes to get task sequence
        # Due to my stupid data structure I need to create a lookup table here for references "P1" to Person1
        # in this step since, Person 1 and 2 are not equivalent, need to identify, the work is done in genVarsOnePOneD

        # Inititate the location and time now to fine the task completion time for each task
        locNow = nodeLookup['hub']
        timeNow = Vehicle.timeNextNode
        for i in sorted_task_nodes:
            if i != 'hub':
                status = i[0]
                personTarget = PersonLookup[i[1:]]
                taskSequence.append((personTarget,status))

                # Create taskTime [(PersonObj, 'P'/'D', Time), (PersonObj,...)]
                timeSeg = Link_tt[(locNow, nodeLookup[i])][0]
                timeArrive = timeNow + timeSeg
                taskTime.append((personTarget, status, timeArrive))
                locNow = nodeLookup[i]
                timeNow = timeArrive
    # If no optimal solution found then return empty (or infinite objective)
    if math.isinf(objValue):
        return objValue,[],[],[]
    # Find the path based on sequenceDict
    ############## May need to modify####
    dummy=0
    # Construct a taskPath List to store path, initiate with the first segment
    taskPath=copy.deepcopy(Link_tt[(nodeLookup[sorted_task_nodes[0]], nodeLookup[sorted_task_nodes[1]])][1])

    # For every item, find the segment between item[i] and item [i+1]
    for i in range(1, len(sorted_task_nodes)-1):
        taskPath.extend(Link_tt[(nodeLookup[sorted_task_nodes[i]], nodeLookup[sorted_task_nodes[i+1]])][1][1:])

    # Need to construct time dependent taskPath = [(Node, time)]
    taskPathwithTime = [(Vehicle.nextNode, Vehicle.timeNextNode)]
    for i in range(1, len(taskPath)):
        node_to_arrive = taskPath[i]
        time_to_arrive = taskPathwithTime[i-1][1] + Link_tt[(taskPathwithTime[i-1][0], node_to_arrive)][0]
        taskPathwithTime.append((node_to_arrive, time_to_arrive))

    # Returen the marginal cost (detour cost) of adding the new customer
    return objValue-currentPathTimeCost, taskPathwithTime, taskSequence, taskTime

