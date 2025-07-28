# Simulation Module
import Person
import copy
import Vehicle
import Parameter as para
import Routing as rt
import Matching as mtch
import OD_Demand
if para.network_name == 'Anaheim':
    from read_network import SPSkims as od_tt,road_network
    from anaheim_demand_weights import lookup_demand_weights
    from anaheim_demand_weights import find_nearby_demand_node,find_time_period_24_hour
    no_of_nodes = len(road_network.nodes())
else:
    from link_cost_cal import od_tt
    from demand_weights import lookup_demand_weights
    no_of_nodes = 24
import Path_Finding as pf
from Path_Finding import  road_network

import time
import networkx as nx
import inputs as ip
# from inputs import VehicleList,PersonList,PersonU,PersonRequest,VehAvbl,PersonPicked,PersonServed,PersonReject,VehPick,                                                                                             VehEmpty,VehDrop
from Output_Metrics import output_metrics



start = time.time()
# # Initialize the supply and demand
# VehicleList = OD_Demand.VehicleList
# PersonList = OD_Demand.PersonList
# # Reduce number of vehicles for now
# VehicleList=VehicleList[0:para.Fleet_size]
# # A Place to store future demand information

futureRequest = []

# # Set up a series of lists to store vehicles and persons and they will change dynamically
#
# # A list of all Persons objects with status as 'U'
# PersonU = [p for p in PersonList if p.requesttime < para.SimTime]
# # A list of persons that requested a vehicle but not matched yet
# PersonRequest = []
# # A list of persons who are matched but not yet picked
# PersonMatch = []
# # A list of persons who are picked but not dropped
# PersonPicked = []
# # A list of persons who are served
# PersonServed = []
# # A list of persons who are not served, i.e., Time exceeds maxpickuptime
# PersonReject=[]
# # A list of vehicles which are idle (no match), includes both "I" and "R"
# VehEmpty = [veh for veh in VehicleList]
# # A list of vehicles which are enroute to pick up
# VehPick = []
# # A list of vehicles which are enroute to drop off
# VehDrop = []
# # An additional list for eligible vehicles for pickup at each time step
# VehAvbl = []


def main_sim(start, endtime, matchflag, bi_cri_flag):

    # Initiate Time, time in minutes, set them in Parameter
    t = start - para.TimeStep

    # Simulation Starts

    while t < endtime + para.maxPickUpWaitTime:

        t = round(t+para.TimeStep, 1)
        print(" Time step (min) ",t)

        with open(para.output_timestep_log, 'a') as op_file:
            print("",file=op_file)
            print("******Time Step*****" + str(round(t,1)) + " minutes ",file=op_file)
            print("",file=op_file)

        # Clean up VehAvbl
        ip.VehAvbl.clear()

        # Find all passengers who made a request during the past 6 secs (status = 'U' and request_time < t)
        for p in ip.PersonU:
            # Check whether a request already happened
            if round(p.requesttime,1) <= t:
                # Update Person attributes
                p.status = 'R'
                ip.PersonRequest.append(p)
                ip.PersonU.remove(p)

        # Find the persons which cannot be served because pick time beyond max time
        for p in ip.PersonRequest:
            # Current time is beyond the max pick time
            if p.pickTimeLatest < t:
                p.status = 'RE'
                ip.PersonReject.append(p)
                ip.PersonRequest.remove(p)
        # End of Finding request persons

        # Updating vehicles, order Empty(R>I)-->Drop-->Pick
        # 1. Update vehicles who are empty
        # No need to track idletime/stationary time or cumulative time after main simulation period
        if matchflag:
            for v in ip.VehEmpty:
                # 1.1 If a vehicle is relocating
                if v.status == 'R':
                    v.updateVehAfterTime(t)

                # 1.2 If a vehicle is idle
                if v.status == 'I':
                    v.updateVehIdle(t)
                    if v.status == 'R':
                        # Need a relocate location function

                        relocateLoc = find_nearby_demand_node(v.currentLoc, t)
                        v.reloc = relocateLoc
                        # if the node is current node, reset the idle timer, let the vehicle wait for another 5 mins
                        if v.currentLoc == relocateLoc:
                            v.idlTimeCum += v.idlTimeOneCum
                            v.idlTimeStart = t
                            v.idlTimeOneCum = 0
                            v.status = 'I'
                            v.reloc = None
                        else:
                            if bi_cri_flag:
                                if para.SimTime == 180:
                                    timeperiod = int(t/30)
                                elif para.SimTime == 1440:
                                    timeperiod = find_time_period_24_hour(t)
                                reward = lookup_demand_weights(v.currentLoc, relocateLoc,timeperiod)
                                timeArriveNextNode = t
                                biPath, biPathTimeCost = pf.weightedSHP(od_tt, no_of_nodes, v.currentLoc, relocateLoc,reward,1,1,timeArriveNextNode,para.bi_criterion_policy)
                                v.path = biPath
                                v.timeNextLoc = biPathTimeCost + timeArriveNextNode
                                v.timeNextLoc = round(v.timeNextLoc,1)
                                v.nextNode = v.path[1][0]
                                v.timeNextNode = v.path[1][1]
                            else:
                                newPath = od_tt[v.currentLoc, relocateLoc][1]
                                # Need to construct time dependent taskPath = [(Node, time)]
                                timeaArriveCurrentNode = t
                                taskPathwithTime = [(v.currentLoc, timeaArriveCurrentNode)]
                                for i in range(1, len(newPath)):
                                    node_to_arrive = newPath[i]
                                    time_to_arrive = taskPathwithTime[i-1][1] + od_tt[(taskPathwithTime[i-1][0],node_to_arrive)][0]
                                    taskPathwithTime.append((node_to_arrive, time_to_arrive))
                                # Update next node and next location (location and time)
                                v.nextNode = taskPathwithTime[1][0]
                                v.nextLoc = taskPathwithTime[-1][0]
                                v.timeNextNode = taskPathwithTime[1][1]
                                v.timeNextLoc = taskPathwithTime[-1][1]
                                v.path = taskPathwithTime


        # 2. Update vehicle who is to drop off
        len_drop_list = len(ip.VehDrop)
        drop_task_veh_list = []
        for v in ip.VehDrop:





            # Check whether a drop off happened
            if round(v.timeNextLoc,1) <= t: # Yes
                drop_task_veh_list.append(v)
                # Update vehicle attributes
                v.updateVehAfterDrop(t)

                # # Update Person attributes, the person just dropped is the last of served person of the vehicle
                # # Shifting this call to updateVehAfterDrop function
                # PersonTemp = v.personServed[-1]
                # PersonTemp.updatePersonAfterDrop(v)
                # # Remove the person from picked list
                # PersonPicked.remove(PersonTemp)
                # PersonServed.append(PersonTemp)

                ###################################################################
                # initialize bi-criteria condition usage flag
                bi_cri_use = False
                # If the vehicle has only one task as to to drop off, consider bi-path
                if para.bi_criterion_flag and bi_cri_flag:
                    # Check bi-criteria conditions:
                    if para.bi_criteria_condi == '1':
                        # Check whether conditions fulfilled:
                        if len(v.futureTasks) == 1 and v.futureTasks[0][1] == 'D' and v.nextNode != v.nextLoc:
                            # It is the condition to use bi-criteria path
                            bi_cri_use = True
                    elif para.bi_criteria_condi == '2':
                        # Check whether conditions fulfilled:
                        if 2 >= len(v.futureTasks) >= 1 and v.futureTasks[0][1] == 'D' and v.nextNode != v.nextLoc:
                            bi_cri_use = True
                    elif para.bi_criteria_condi == '3':
                        debug = 0
                        if 2 >= len(v.futureTasks) >= 1 and v.nextNode != v.nextLoc:
                            bi_cri_use = True
                ###################################################################
                # the flg is true means consider bi-path
                if bi_cri_use:
                    if para.SimTime == 180:
                        timeperiod = int(t / 30)
                    elif para.SimTime == 1440:
                        timeperiod = find_time_period_24_hour(t)
                    reward = lookup_demand_weights(v.currentLoc,v.nextLoc,timeperiod)
                    timeArriveNextNode = v.timeNextNode
                    # Function calls for bi criterion path finding
                    # If Policy is 2a or 2b call biobjective formulation
                    if para.bi_criterion_policy[0]=='2':
                        biPath, biPathTimeCost = pf.weightedSHP(od_tt, no_of_nodes, v.nextNode, v.nextLoc,reward,1,1,timeArriveNextNode,para.bi_criterion_policy)
                        debug = 0
                    # If Policy is 1a or 1b call doubly constrained uniobjective formulation
                    elif para.bi_criterion_policy[0]=='1':
                        biPath,biPathTimeCost = pf.constrained_demand_SHP(od_tt, no_of_nodes, v.nextNode, v.nextLoc, reward,para.min_demand_factor,para.max_detour_factor,timeArriveNextNode,method=para.bi_criterion_policy)
                    with open(para.output_timestep_log,'a') as op_file:
                        print("Vehicle ",v.id, " is on Bi-criterion path ",file=op_file)
                        print("Bi path ",biPath,file=op_file)
                        print("BipathTimecost ",file=op_file)


                        # Check time window


                    if len(v.futureTasks) == 1:
                        # If time window constraint is violated then reject new path
                        if biPathTimeCost + timeArriveNextNode > v.personIn[0].dropTimeLatest:
                            continue
                        else: # Change the vehicle Path
                            v.path = biPath
                            v.timeNextLoc = biPathTimeCost + timeArriveNextNode
                            v.timeNextLoc = round(v.timeNextLoc,1)
                            # Update person attributes based on new path
                            for (p,flag) in v.futureTasks:
                                for (nodetemp,timetemp) in v.path:
                                    if flag == 'D' and p.dropLoc == nodetemp:
                                        p.dropTime = timetemp
                                    elif flag == 'P' and p.pickLoc == nodetemp:
                                        p.pickTime = timetemp
                            dummy = 0
                            with open(para.output_timestep_log,'a') as op_file:
                                print("Vehicle ",v.id, " is on Bi-criterion path ",file=op_file)
                                print("Bi path ",biPath,file=op_file)
                                print("BipathTimecost ", biPathTimeCost, file=op_file)
                                print('NextLocTime', v.timeNextLoc, file=op_file)
                    # Insert here
                    elif len(v.futureTasks) == 2:
                        dummy = 0
                        timeLastLoc = v.path[-1][1]
                        biTimeArriveTime1 = biPathTimeCost + timeArriveNextNode
                        timeDiff = biTimeArriveTime1 - v.timeNextLoc
                        biTimeArriveTime2 = timeDiff + timeLastLoc
                        # Case 1. Two dropoff tasks
                        if v.futureTasks[0][1] == 'D':
                            if biTimeArriveTime1 < v.personIn[0].dropTimeLatest and biTimeArriveTime2 < v.personIn[1].dropTimeLatest:
                                if v.personIn[0].dropLoc == v.personIn[1].dropLoc:  # Same Location for the two
                                    biPath.append(biPath[-1])
                                    v.path = biPath
                                    v.timeNextLoc = biPathTimeCost + timeArriveNextNode
                                    v.timeNextLoc = round(v.timeNextLoc, 1)
                                    # Update person attributes based on new path
                                    v.futureTasks[0][0].dropTime = round(biTimeArriveTime1,1)
                                    v.futureTasks[1][0].dropTime = round(biTimeArriveTime2,1)
                                    dummy = 0
                                    with open(para.output_timestep_log, 'a') as op_file:
                                        print("Vehicle ", v.id, " is on Bi-criterion path ", file=op_file)
                                        print("Bi path ", biPath, file=op_file)
                                        print("BipathTimecost ", biPathTimeCost, file=op_file)
                                        print('NextLocTime', v.timeNextLoc, file=op_file)
                                else:  # Two different task locations
                                    # find the path after the first task
                                    for i in range(len(v.path)):
                                        if v.path[i][0] == v.futureTasks[0][0].dropLoc:
                                            pathOriginal = v.path[(i + 1):]
                                            break
                                    pathNew = []
                                    for (nodetemp, timetemp) in pathOriginal:
                                        pathNew.append((nodetemp, timetemp + timeDiff))
                                    v.path = biPath + pathNew
                                    v.timeNextLoc = biPathTimeCost + timeArriveNextNode
                                    v.timeNextLoc = round(v.timeNextLoc, 1)
                                    v.futureTasks[0][0].dropTime = round(biTimeArriveTime1,1)
                                    v.futureTasks[1][0].dropTime = round(biTimeArriveTime2,1)
                        # Case 2. One person, pick then drop
                        elif v.futureTasks[0][1] == 'P':
                            if biTimeArriveTime1 < v.futureTasks[0][0].pickTimeLatest and biTimeArriveTime2 < \
                                    v.futureTasks[1][0].dropTimeLatest:
                                # find the path after the first task
                                for i in range(len(v.path)):
                                    if v.path[i][0] == v.futureTasks[0][0].pickLoc:
                                        pathOriginal = v.path[(i + 1):]
                                        break
                                pathNew = []
                                for (nodetemp, timetemp) in pathOriginal:
                                    pathNew.append((nodetemp, timetemp + timeDiff))
                                v.path = biPath + pathNew
                                v.timeNextLoc = biPathTimeCost + timeArriveNextNode
                                v.timeNextLoc = round(v.timeNextLoc, 1)
                                v.futureTasks[0][0].pickTime = round(biTimeArriveTime1,1)
                                v.futureTasks[1][0].dropTime = round(biTimeArriveTime2,1)
                                with open(para.output_timestep_log, 'a') as op_file:
                                    print("Vehicle ", v.id, " is on Bi-criterion path ", file=op_file)
                                    print("Bi path ", biPath, file=op_file)
                                    print("BipathTimecost ", biPathTimeCost, file=op_file)
                                    print('NextLocTime', v.timeNextLoc, file=op_file)
                    # End of insert

                # # Move vehicle obj to correct list/set, no need to change if status is still "D"
                # if v.status == 'I':
                #     ip.VehEmpty.append(v)
                #     ip.VehDrop.remove(v)
                # elif v.status == 'P':
                #     ip.VehPick.append(v)
                #     ip.VehDrop.remove(v)

                # This part is the judgement for which vehicles are eligible for new matching
                # May need extra work to show clear policies of vehicle usage
                # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
                # if len(v.toDrop) < 3:
                if v not in ip.VehAvbl:
                    ip.VehAvbl.append(v)
            else: # No, no drop off happened

                v.updateVehAfterTime(t)
                # This part is the judgement for which vehicles are eligible for new matching
                # May need extra work to show clear policies of vehicle usage
                # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
                # if len(v.toDrop) < 3:
                if v not in ip.VehAvbl:
                    ip.VehAvbl.append(v)
        # Now move vehicles that dropped off a passenger to the appropriate lists
        for v in drop_task_veh_list:
            # Move vehicle obj to correct list/set, no need to change if status is still "D"
            if v.status == 'I':
                ip.VehEmpty.append(v)
                ip.VehDrop.remove(v)
            elif v.status == 'P':
                ip.VehPick.append(v)
                ip.VehDrop.remove(v)

        # 3. Update vehicles who are to pickup
        pick_task_veh_list = []
        for v in ip.VehPick:
            pickPerson = v.futureTasks[0][0]
            # Check if a pickup already happened
            if round(pickPerson.pickTime,1) <= t: # Yes
                pick_task_veh_list.append(v)
                # Update Person attributes
                # Debug, move this call to updateVehAfterPick()
                # pickPerson.status = 'P'
                # ip.PersonPicked.append(pickPerson)
                # ip.PersonMatch.remove(pickPerson)
                # Update Vehicle attributes
                debug = 1
                v.updateVehAfterPick(t)

                ###################################################################
                # initialize bi-criteria condition usage flag
                bi_cri_use = False
                # If the vehicle has only one task as to to drop off, consider bi-path
                if para.bi_criterion_flag and bi_cri_flag:
                    # Check bi-criteria conditions:
                    if para.bi_criteria_condi == '1':
                        # Check whether conditions fulfilled:
                        if len(v.futureTasks) == 1 and v.futureTasks[0][1] == 'D' and v.nextNode != v.nextLoc:
                            # It is the condition to use bi-criteria path
                            bi_cri_use = True
                    elif para.bi_criteria_condi == '2':
                        # Check whether conditions fulfilled:
                        if 2 >= len(v.futureTasks) >= 1 and v.futureTasks[0][1] == 'D' and v.nextNode != v.nextLoc:
                            bi_cri_use = True
                    elif para.bi_criteria_condi == '3':
                        if 2 >= len(v.futureTasks) >= 1 and v.nextNode != v.nextLoc:
                            bi_cri_use = True

                # If the vehicle has only one task as to to drop off, consider bi-path
                if bi_cri_use:
                    timeperiod = int(t/30)
                    reward = lookup_demand_weights(v.currentLoc,v.nextLoc,timeperiod)
                    timeArriveCurrentNode = v.trajectory[-1][1] + od_tt[(v.trajectory[-1][0],v.currentLoc)][0]
                    # Function calls for bi criterion path finding
                    # If Policy is 2a or 2b call biobjective formulation
                    if para.bi_criterion_policy[0] == '2':
                        biPath, biPathTimeCost = pf.weightedSHP(od_tt, no_of_nodes, v.currentLoc, v.nextLoc, reward, 1, 1,
                                                                timeArriveCurrentNode, para.bi_criterion_policy)
                        debug = 1
                    # If Policy is 1a or 1b call doubly constrained uniobjective formulation
                    elif para.bi_criterion_policy[0] == '1':
                        biPath, biPathTimeCost = pf.constrained_demand_SHP(od_tt, no_of_nodes, v.currentLoc, v.nextLoc, reward,
                                                                           para.min_demand_factor,
                                                                           para.max_detour_factor, timeArriveCurrentNode,
                                                                           method=para.bi_criterion_policy)



                        if len(v.futureTasks) == 1:
                            # Check time window
                            if biPathTimeCost + timeArriveCurrentNode > v.personIn[0].dropTimeLatest:
                                continue
                            else:# Change the vehicle Path
                                v.path = biPath
                                v.timeNextLoc = biPathTimeCost + timeArriveCurrentNode
                                v.timeNextLoc = round(v.timeNextLoc, 1)
                                # Update person attributes based on new path
                                v.futureTasks[0][0].dropTime = v.timeNextLoc
                            dummy = 0
                        elif len(v.futureTasks) == 2:
                            timeLastLoc = v.path[-1][1]
                            biTimeArriveTime1 = biPathTimeCost + timeArriveCurrentNode
                            timeDiff = biTimeArriveTime1 - v.timeNextLoc
                            biTimeArriveTime2 = timeDiff + timeLastLoc
                            # Only One case, two drop offs
                            if biTimeArriveTime1 < v.personIn[0].dropTimeLatest and biTimeArriveTime2 < v.personIn[
                                1].dropTimeLatest:
                                if v.personIn[0].dropLoc == v.personIn[1].dropLoc:  # Same Location for the two
                                    # Duplicate the last for the same task location
                                    biPath.append(biPath[-1])
                                    v.path = biPath
                                    v.timeNextLoc = biPathTimeCost + timeArriveCurrentNode
                                    v.timeNextLoc = round(v.timeNextLoc, 1)
                                    # Update person attributes based on new path
                                    v.futureTasks[0][0].dropTime = round(biTimeArriveTime1,1)
                                    v.futureTasks[1][0].dropTime = round(biTimeArriveTime2,1)
                                    dummy = 0
                                    with open(para.output_timestep_log, 'a') as op_file:
                                        print("Vehicle ", v.id, " is on Bi-criterion path ", file=op_file)
                                        print("Bi path ", biPath, file=op_file)
                                        print("BipathTimecost ", biPathTimeCost, file=op_file)
                                        print('NextLocTime', v.timeNextLoc, file=op_file)
                                else:  # Two different task locations
                                    # find the path after the first task
                                    for i in range(len(v.path)):
                                        if v.path[i][0] == v.futureTasks[0][0].dropLoc:
                                            pathOriginal = v.path[(i + 1):]
                                            break
                                    pathNew = []
                                    for (nodetemp, timetemp) in pathOriginal:
                                        pathNew.append((nodetemp, timetemp + timeDiff))
                                    v.path = biPath + pathNew
                                    v.timeNextLoc = biPathTimeCost + timeArriveCurrentNode
                                    v.timeNextLoc = round(v.timeNextLoc, 1)
                                    v.futureTasks[0][0].dropTime = round(biTimeArriveTime1,1)
                                    v.futureTasks[1][0].dropTime = round(biTimeArriveTime2,1)
                                    with open(para.output_timestep_log, 'a') as op_file:
                                        print("Vehicle ", v.id, " is on Bi-criterion path ", file=op_file)
                                        print("Bi path ", biPath, file=op_file)
                                        print("BipathTimecost ", biPathTimeCost, file=op_file)
                                        print('NextLocTime', v.timeNextLoc, file=op_file)
                # Update person share trip information
                if v.occu >= 2:
                    Person.updatePersonTripShare(v)
                # # Move the vehicle to correct set
                # if v.status =='D':
                #     ip.VehDrop.append(v)
                #     ip.VehPick.remove(v)

                # This part is the judgement for which vehicles are eligible for new matching
                # May need extra work to show clear policies of vehicle usage
                # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
                # if len(v.toDrop) < 3:
                if v not in ip.VehAvbl:
                    ip.VehAvbl.append(v)

            # No pickup happened
            else:
                v.updateVehAfterTime(t)
                # This part is the judgement for which vehicles are eligible for new matching
                # May need extra work to show clear policies of vehicle usage
                # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
                # if len(v.toDrop) < 3:
                if v not in ip.VehAvbl:
                    ip.VehAvbl.append(v)

        # End of Updating Vehicles
        # Move vehicles that picked passengers in this time steps to the correct lists
        for v in pick_task_veh_list:
            # Move the vehicle to correct set
            if v.status == 'D':
                ip.VehDrop.append(v)
                ip.VehPick.remove(v)

        if matchflag:
            # Available vehicles for new matching will be VehAvbl and VehEmpty
            ip.VehAvbl = ip.VehAvbl + ip.VehEmpty


            # Matching Part

            with open(para.output_timestep_log,"a") as op_file:
                print ("-- Before Call to Match()  perreq=",len(ip.PersonRequest)," vehavbl=",len(ip.VehAvbl),file=op_file)
            dummy=0
            if len(ip.PersonRequest) == 0:
                continue
            # Match results from matching module
            print ("No of Requests ",len(ip.PersonRequest))
            matchResults = mtch.matchPaxtoVeh(ip.PersonRequest, ip.VehAvbl, t)
            print("No of Assignments ", len(matchResults))
            # End of Matching Part

            # Find the route for Vehicle Person objects

            # Now we need to update person/vehicle objects attributes
            for costObject in matchResults:

                # Ensure precision
                costObject.taskTime = [(p,status,round(time,1)) for p,status,time in costObject.taskTime]
                costObject.taskPath = [(node,round(time,1)) for node,time in costObject.taskPath]
                vehTemp = costObject.vehicle
                perTemp = costObject.person
                ip.PersonMatch.append(perTemp)
                ###### Check ##########
                ip.PersonRequest.remove(perTemp)
                tasktotalcost = costObject.cost
                tasktotalpath = costObject.taskPath

                # Update vehicle status
                # print ("-- In update veh status, vehicle",costObject.vehicle.id," has future tasks  ",len(costObject.vehicle.futureTasks))
                vehTemp.status = costObject.taskSequence[0][1]
                # Update IdleTime Flg, before adding new tasks if no future task, the vehicle switch from idle to none
                if len(vehTemp.futureTasks) == 0:
                    vehTemp.idlTimeOneCum = t - vehTemp.idlTimeStart
                    vehTemp.idlTimeCum += vehTemp.idlTimeOneCum
                    vehTemp.idlTimeOneCum = 0
                if vehTemp.status == 'P' and vehTemp not in ip.VehPick:
                    ip.VehPick.append(vehTemp)
                    if vehTemp in ip.VehEmpty:
                        ip.VehEmpty.remove(vehTemp)
                    if vehTemp in ip.VehDrop:
                        ip.VehDrop.remove(vehTemp)
                elif vehTemp.status == 'D' and vehTemp not in ip.VehDrop:
                    ip.VehDrop.append(vehTemp)
                    if vehTemp in ip.VehEmpty:
                        ip.VehEmpty.remove(vehTemp)
                    if vehTemp in ip.VehPick:
                        ip.VehPick.remove(vehTemp)

                # Update future tasks
                # Oct 15, the problem is here, you cannot let v.futureTasks = costObjectve.tasksequence,
                vehTemp.futureTasks = costObject.taskSequence
                vehTemp.path = tasktotalpath



                # Now update all persons related to the vehicle
                Person.updatePersonAfterMatch(costObject)


                # Need to update next node the vehicle is moving toward
                vehTemp.nextNode = vehTemp.path[0][0]
                vehTemp.timeNextNode = vehTemp.path[0][1]
                # Update nextLoc and time
                if vehTemp.futureTasks[0][1] == 'D':
                    vehTemp.nextLoc = vehTemp.futureTasks[0][0].dropLoc
                    # Find the time arrive at next node from path
                    vehTemp.timeNextLoc = vehTemp.futureTasks[0][0].dropTime
                    # for (node, time) in tasktotalpath:
                    #     if vehTemp.nextLoc == node:
                    #         vehTemp.timeNextLoc = time
                elif vehTemp.futureTasks[0][1] == 'P':
                    vehTemp.nextLoc = vehTemp.futureTasks[0][0].pickLoc
                    vehTemp.timeNextLoc = vehTemp.futureTasks[0][0].pickTime
                    # for (node, time) in tasktotalpath:
                    #     if vehTemp.nextLoc == node:
                    #         vehTemp.timeNextLoc = time

        with open(para.output_timestep_log, "a") as op_file:
            print('No of person request remaining after call to matching module', len(ip.PersonRequest),file=op_file)
        for v in ip.VehicleList:
            with open(para.output_timestep_log, "a") as op_file:
                print ("Veh-",v.id," # future tasks: ", len(v.futureTasks), file=op_file)
                future_tasks=[(task[0].person_id,task[0].pickLoc,"to",task[0].dropLoc,task[1]) for task in v.futureTasks]
                print (future_tasks,file=op_file)
                print("vehicle path", v.path,file=op_file)
                print("currentLoc", v.currentLoc, file=op_file)
                print("nextLoc", v.nextLoc, file=op_file)



        # Direction Part: Give pickup and dropoff sequence to vehicles
        # Output:
        op_file.close()

        # increment time step

    return


# All Function calls for running simulation and post simulation output metric calculation
def run_simulation():
    # Function call to update parameters from parameters json file
    para.update_parameters()
    # Initalize Requests and Vehicle Fleet
    ip.init_demand_supply()

    # function call for normal simulation period

    main_sim(para.InitialTime, para.SimTime, matchflag=True, bi_cri_flag=True)

    print("**After simulation time period**")
    # Need to loop through PersonMatched and PersonPicked to find the maximum drop time
    SimTime2 = 0
    for p in ip.PersonMatch+ip.PersonPicked:
        if p.dropTime > SimTime2:
            SimTime2 = p.dropTime + 0.1

    # Need to loop through all vehicles in
    print(SimTime2)

    # Need to loop through all vehicles
    for v in ip.VehEmpty:
        if v.idlTimeStart < para.SimTime:
            v.idlTimeOneCum = para.SimTime - v.idlTimeStart
            v.emptyTimeOneCum = para.SimTime - v.emptyTimeStart
            v.idlTimeCum += v.idlTimeOneCum
            v.emptyTimeCum += v.emptyTimeOneCum
            v.idlTimeStart = para.SimTime
            v.emptyTimeStart = para.SimTime
    # End of calculating empty and idle time


    main_sim(para.SimTime+para.maxPickUpWaitTime, SimTime2, matchflag=False, bi_cri_flag=False)


    print('This is the end of simulation...')

    # Function calls for output metrics

    output_metrics()



