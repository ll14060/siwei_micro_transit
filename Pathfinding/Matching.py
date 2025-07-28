import gurobipy as grp
import Parameter
import Person
import Vehicle
from Path_Finding import road_network
import networkx as nx
import Routing as rt
if Parameter.network_name == 'Anaheim':
    from read_network import SPSkims as od_tt
else:
    from link_cost_cal import od_tt
import time


# A Fake Linktt_table
Link_tt_short = od_tt

# # Test Network
#
# for o,d,data in road_network.edges(data=True):
#     print (o,d, ": cost_ij :",data['cost_ij']," , reward_ij: ",data['reward_ij'])
# print ("Number of nodes, ",road_network.number_of_nodes())
# print ("Number of edges, ",road_network.number_of_edges())


# Cost objects to pass to gurobi optimizer
class CostObject:

    # Input are person obj, veh obj,
    def __init__(self,per,veh,cost, taskPath, taskSequence, taskTime):
        self.person = per
        self.vehicle = veh
        self.cost = cost
        self.matched = False
        # Task path is a time dependent path = [(Node, time)]
        self.taskPath = taskPath
        self.taskSequence = taskSequence
        self.taskTime = taskTime

# End of CostObject class


# These are the matching algorithms
# Input list of requests in the time step, list of vehicles eligible for matching in the time step
# Current time step time
# Returns a list of CostObjects that have been matched
def matchPaxtoVeh(person,vehicle,current_time):

    # List of costobjects to be passed
    pax_veh_objects = []
    # Indices associated with person p
    p_indices={}
    # Indices associated with vehicle v
    v_indices={}

    # Time check point
    start = time.time()

    # For each request find vehicles that are eligible to cater to the request
    for p in person:
        # Debug
        if p.person_id == 675:
            print('Debug Now')
        # List of vehicles that are eligible to pickup person p
        veh_eligible=[]
        # Check if vehicle can pickup request from current location satisfying max pickup constraitn
        for v in vehicle:
            # Find shortest path time from vehicle's next node to person's pickup location
            # min_pickup_time= nx.shortest_path_length(road_network, v.nextNode,p.pickLoc,weight='cost_ij')
            min_pickup_time = od_tt[(v.nextNode,p.pickLoc)][0]
            # Add a condition to avoid None type for time next node
            if v.timeNextNode is None:
                v.timeNextNode = current_time
            if (min_pickup_time <= p.pickTimeLatest - v.timeNextNode):
                # If vehicle can pickup within latest pickup time
                # Add to eligible list for the person p
                veh_eligible.append(v)
                # Create p-v cost object for now
                # Needs further filtering later (k nearest) obj could be created later
                # Find the number of to pick and to drop passengers for each vehicle
                toPickcount, toDropcount=v.findToPickandDropCount()
                if len(v.futureTasks) == 0:
                    # link_tt_short is the node to node shortest travel time table
                    costpvTemp, taskPathTime, taskSequence, taskTime = rt.VehZeroTaskTimePreMatch(p,v, Link_tt_short, current_time)
                    dummy = 0
                elif toPickcount <=1 and toDropcount <=1:
                    costpvTemp, taskPathTime, taskSequence, taskTime = rt.VehOnePersonPreMatch(p, v, current_time, Link_tt_short)
                elif toPickcount <= 2 and toDropcount <= 2:
                    costpvTemp, taskPathTime, taskSequence, taskTime = rt.VehTwoPersonPreMatch(p, v, current_time, Link_tt_short)
                else:
                    continue
                # Create candidate match object if cost less than max pickup reward parameter
                if costpvTemp <= Parameter.maxPickupReward:
                    pax_veh_objects.append(CostObject(p,v,costpvTemp, taskPathTime, taskSequence, taskTime))
    with open(Parameter.output_timestep_log, 'a') as op_file:
        print('No. of PV combinations ', len(pax_veh_objects),file=op_file)
    # Check all P-V objects
    # for pv in pax_veh_objects:
    #     print ("Pax-",pv.person.person_id," Veh-",pv.vehicle.id," Cost-",pv.cost)

    # Time check point 1
    checkpoint1 = time.time()
    pairwiseroutingtime = checkpoint1 - start
    # print('Time to calculate Cij ', pairwiseroutingtime)
        ###  Do Later: Find k nearest vehicles and k random occupied vehicles

        # Update cost values

        # Do later for DARP costs
        # Function calls to update costs for DARP

    # Update indices of decision variables associated with each person and vehicle
    pv_counter=0
    for pv in pax_veh_objects:
        try:
            p_indices[pv.person.person_id].extend([pv_counter])

        except:
            p_indices[pv.person.person_id]=[pv_counter]

        try:
            v_indices[pv.vehicle.id].extend([pv_counter])
        except:
            v_indices[pv.vehicle.id]=[pv_counter]
        pv_counter=pv_counter + 1

    # Set up Matching Optimization Problem
    # -------------------------------------

    model = grp.Model("min_cost_matching")
    # Mute gurobi output
    model.setParam('OutputFlag', False)
    model.setParam(grp.GRB.param.Threads, 2)


    # Decision variable
    # z = [0 for k in pax_veh_objects]
    z=[0 for k in pax_veh_objects]

    for k in range(0,len(pax_veh_objects)):
        z[k] = model.addVar(vtype=grp.GRB.CONTINUOUS, obj=(pax_veh_objects[k].cost - Parameter.maxPickupReward), name=f'z[{k}]',lb=0,ub=1)
    # print (" No. of p-v objects ",len(pax_veh_objects))
    model.update()
    # Add constraints
    # At most one assignment for each passenger and vehicle
    for veh_index in v_indices.values():
        ############################# There was an error here "'int' object is not iterable"
        model.addConstr(grp.quicksum(z[k] for k in (veh_index)) <= 1)
    for pax_index in p_indices.values():
        model.addConstr(grp.quicksum(z[k] for k in (pax_index)) <= 1)
    model.update()
    # model_log = "model_timestep_" + str(current_time)
    # model_log = model_log + ".lp"
    # model.write(model_log)
    # Solve Optimization Problem
    model.optimize()

    # Retrieve Assignments
    # List of Matches (List of PV Cost Objects)
    pv_matched_objects=[]

    if model.status == grp.GRB.Status.OPTIMAL:
        solution = model.getAttr("X", model.getVars())
        for k in range(pv_counter):
            # P-V Cost object is chosen to be matched
            if solution[k] >= 0.99:
                pv_matched_objects.append(pax_veh_objects[k])
    # else:
    #     print('Infeasible')
    # Time to check matching
    checkpoint2 = time.time()
    matchingTime = checkpoint2 - checkpoint1
    # print('Mathcing Time ', matchingTime)
    # print ("Number of matches =",len(pv_matched_objects))
    # model_log="model_timestep_"+str(current_time)
    # model_log=model_log+".lp"
    # model.write(model_log)
    with open(Parameter.output_timestep_log,'a') as op_file:
        print ("No of matches ",len(pv_matched_objects),file=op_file)
    return pv_matched_objects

















