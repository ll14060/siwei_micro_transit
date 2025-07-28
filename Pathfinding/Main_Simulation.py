# Simulation Module
import Person
import copy
import Vehicle
import Parameter as para
import Routing as rt
import Matching as mtch
import OD_Demand
from link_cost_cal import od_tt
import Path_Finding as pf
from Path_Finding import  road_network
import demand_weights
import time
import networkx as nx


start = time.time()
# Initialize the supply and demand
VehicleList = OD_Demand.VehicleList
PersonList = OD_Demand.PersonList
# Reduce number of vehicles for now
VehicleList=VehicleList[0:para.Fleet_size]
# A Place to store future demand information
############# Need to think about data structure
futureRequest = []

# Set up a series of lists to store vehicles and persons and they will change dynamically

# A list of all Persons objects with status as 'U'
PersonU = PersonList
# A list of persons that requested a vehicle but not matched yet
PersonRequest = []
# A list of persons who are matched but not yet picked
PersonMatch = []
# A list of persons who are picked but not dropped
PersonPicked = []
# A list of persons who are served
PersonServed = []
# A list of persons who are not served, i.e., Time exceeds maxpickuptime
PersonUnServed=[]
# A list of vehicles which are idle (no match), includes both "I" and "R"
VehEmpty = [veh for veh in VehicleList]
# A list of vehicles which are enroute to pick up
VehPick = []
# A list of vehicles which are enroute to drop off
VehDrop = []
# An additional list for eligible vehicles for pickup at each time step
VehAvbl = []

# Initiate Time, time in minutes, set them in Parameter
t = para.InitialTime

# Logfile
with open(para.output_timestep_log,'w') as op_file:
    print("Fleet Size: ",len(VehicleList),file=op_file)



# Simulation Starts
while t < para.SimTime:

    # Debug
    # if t>29.1:
    #     print('Check Now')

    # Time checkpoint 1
    # check1 = time.time()

    with open(para.output_timestep_log, 'a') as op_file:
        print("",file=op_file)
        print("******Time Step*****" + str(round(t,1)) + " minutes ",file=op_file)
        print("",file=op_file)

    # Clean up VehAvbl
    VehAvbl.clear()

    # Find all passengers who made a request during the past 6 secs (status = 'U' and request_time < t)
    if len(PersonU) != 0:
        for p in PersonU:
            # Check whether a request already happened
            if p.requesttime <= t:
                # Update Person attributes
                p.status = 'R'
                PersonRequest.append(p)
                PersonU.remove(p)
    # End of Finding request persons

    # Updating vehicles, order Empty(R>I)-->Drop-->Pick
    # 1. Update vehicles who are empty
    for v in VehEmpty:
        # 1.1 If a vehicle is relocating
        if v.status == 'R':
            v.updateVehAfterTime(t)

        # 1.2 If a vehicle is idle
        if v.status == 'I':
            v.updateVehIdle(t)
            if v.status == 'R':
                ### Cal Routing Module assign a relocate destination ###
                ######### Need work##############
                newPath = rt.newRelocatePath(v, '10', od_tt, t)
                v.nextLoc = '10'
                v.timeNextLoc = od_tt[(v.currentLoc, '10')][0] + t
                v.path = newPath

    # 2. Update vehicle who is to drop off
    for v in VehDrop:
        # Check whether a drop off happened
        if v.timeNextLoc <= t: # Yes
            # Update vehicle attributes
            v.updateVehAfterDrop(t)

            # Update Person attributes, the person just dropped is the last of served person of the vehicle
            # Shifting this call to updateVehAfterDrop function
            PersonTemp = v.personServed[-1]
            PersonTemp.updatePersonAfterDrop(v)

            PersonServed.append(PersonTemp)

            ###################################################################
            # If the vehicle has only one task as to to drop off, consider bi-path
            if para.bi_criterion_flag:
                if len(v.futureTasks) ==1 and v.futureTasks[0][1] == 'D' and v.nextNode != v.nextLoc:
                    if t<=30:
                        timeperiod = 1
                    elif t<=60:
                        timeperiod = 2
                    elif t<=90:
                        timeperiod = 3
                    else:
                        timeperiod = 4
                    reward = demand_weights.lookup_demand_weights(v.currentLoc,v.nextLoc,timeperiod)
                    timeArriveNextNode = v.timeNextNode
                    # Function calls for bi criterion path finding
                    # If Policy is 2a or 2b call biobjective formulation
                    if para.bi_criterion_policy[0]=='2':
                        biPath, biPathTimeCost = pf.weightedSHP(od_tt, 24, v.nextNode, v.nextLoc,reward,1,1,timeArriveNextNode,para.bi_criterion_policy)
                    # If Policy is 1a or 1b call doubly constrained uniobjective formulation
                    elif para.bi_criterion_policy[0]=='1':
                        biPath,biPathTimeCost = pf.constrained_demand_SHP(od_tt, 24, v.nextNode, v.nextLoc, reward,para.min_demand_factor,para.max_detour_factor,timeArriveNextNode,method=para.bi_criterion_policy)
                    with open(para.output_timestep_log,'a') as op_file:
                        print("Vehicle ",v.id, " is on Bi-criterion path ",file=op_file)
                        print("Bi path ",biPath,file=op_file)
                        print("BipathTimecost ",file=op_file)


                    # Check time window
                    if biPathTimeCost + timeArriveNextNode > v.personIn[0].dropTimeLatest:
                        continue
                    else: # Change the vehicle Path
                        v.path = biPath
                        v.timeNextLoc = biPathTimeCost + timeArriveNextNode

                        with open(para.output_timestep_log,'a') as op_file:
                            print("Vehicle ",v.id, " is on Bi-criterion path ",file=op_file)
                            print("Bi path ",biPath,file=op_file)
                            print("BipathTimecost ", biPathTimeCost, file=op_file)
                            print('NextLocTime', v.timeNextLoc, file=op_file)

            # Move vehicle obj to correct list/set, no need to change if status is still "D"
            if v.status == 'I':
                VehEmpty.append(v)
                VehDrop.remove(v)
            elif v.status == 'P':
                VehPick.append(v)
                VehDrop.remove(v)

            # This part is the judgement for which vehicles are eligible for new matching
            # May need extra work to show clear policies of vehicle usage
            # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
            # if len(v.toDrop) < 3:
            if v not in VehAvbl:
                VehAvbl.append(v)
        else: # No, no drop off happened
            v.updateVehAfterTime(t)
            # This part is the judgement for which vehicles are eligible for new matching
            # May need extra work to show clear policies of vehicle usage
            # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
            # if len(v.toDrop) < 3:
            if v not in VehAvbl:
                VehAvbl.append(v)

    # 3. Update vehicles who are to pickup
    for v in VehPick:
        pickPerson = v.futureTasks[0][0]
        # Check if a pickup already happened
        if pickPerson.pickTime <= t: # Yes
            # Update Person attributes
            pickPerson.status = 'P'
            PersonPicked.append(pickPerson)
            PersonMatch.remove(pickPerson)
            # Update Vehicle attributes
            v.updateVehAfterPick(t)

            # If the vehicle has only one task as to to drop off, consider bi-path
            if para.bi_criterion_flag:
                if len(v.futureTasks) ==1 and v.futureTasks[0][1] == 'D'and v.nextNode != v.nextLoc:
                    if t<=30:
                        timeperiod = 1
                    elif t<=60:
                        timeperiod = 2
                    elif t<=90:
                        timeperiod = 3
                    else:
                        timeperiod = 4
                    reward = demand_weights.lookup_demand_weights(v.currentLoc,v.nextLoc,timeperiod)
                    timeArriveCurrentNode = v.trajectory[-1][1] + od_tt[(v.trajectory[-1][0],v.currentLoc)][0]
                    # Function calls for bi criterion path finding
                    # If Policy is 2a or 2b call biobjective formulation
                    if para.bi_criterion_policy[0] == '2':
                        biPath, biPathTimeCost = pf.weightedSHP(od_tt, 24, v.currentLoc, v.nextLoc, reward, 1, 1,
                                                                timeArriveCurrentNode, para.bi_criterion_policy)
                    # If Policy is 1a or 1b call doubly constrained uniobjective formulation
                    elif para.bi_criterion_policy[0] == '1':
                        biPath, biPathTimeCost = pf.constrained_demand_SHP(od_tt, 24, v.currentLoc, v.nextLoc, reward,
                                                                           para.min_demand_factor,
                                                                           para.max_detour_factor, timeArriveCurrentNode,
                                                                           method=para.bi_criterion_policy)

                    with open(para.output_timestep_log,'a') as op_file:
                        print("Vehicle ",v.id, " is on Bi-criterion path ",file=op_file)
                        print("Bi path ",biPath,file=op_file)
                        print("BipathTimecost ",file=op_file)

                    # Check time window
                    if biPathTimeCost + timeArriveCurrentNode > v.personIn[0].dropTimeLatest:
                        continue
                    else: # Change the vehicle Path
                        v.path = biPath
                        v.timeNextLoc = biPathTimeCost + timeArriveCurrentNode

            # Update person share trip information
            if v.occu >= 2:
                Person.updatePersonTripShare(v)
            # Move the vehicle to correct set
            if v.status =='D':
                VehDrop.append(v)
                VehPick.remove(v)

            # This part is the judgement for which vehicles are eligible for new matching
            # May need extra work to show clear policies of vehicle usage
            # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
            # if len(v.toDrop) < 3:
            if v not in VehAvbl:
                VehAvbl.append(v)

        # No pickup happened
        else:
            v.updateVehAfterTime(t)
            # This part is the judgement for which vehicles are eligible for new matching
            # May need extra work to show clear policies of vehicle usage
            # now I set it to be "If a vehicle has 3 person to serve ahead, it will not be used"
            # if len(v.toDrop) < 3:
            if v not in VehAvbl:
                VehAvbl.append(v)

    # End of Updating Vehicles

    # Available vehicles for new matching will be VehAvbl and VehEmpty
    VehAvbl = VehAvbl + VehEmpty

    # Time check point 2
    # check2 = time.time()
    # timeUpdateandRouting = check2 - check1
    # print('Time to update vehicle: ', timeUpdateandRouting)
    # Matching Part

    with open(para.output_timestep_log,"a") as op_file:
        print ("-- Before Call to Match()  perreq=",len(PersonRequest)," vehavbl=",len(VehAvbl),file=op_file)
    dummy=0
    if len(PersonRequest) == 0:
        continue
    # Match results from matching module
    matchResults = mtch.matchPaxtoVeh(PersonRequest, VehAvbl, t)
    dummy=1
    # End of Matching Part

    # Find the route for Vehicle Person objects

    # Now we need to update person/vehicle objects attributes
    for costObject in matchResults:
        vehTemp = costObject.vehicle
        perTemp = costObject.person
        PersonMatch.append(perTemp)
        ###### Check ##########
        PersonRequest.remove(perTemp)
        tasktotalcost = costObject.cost
        tasktotalpath = costObject.taskPath

        # Update vehicle status
        print ("-- In update veh status, vehicle",costObject.vehicle.id," has future tasks  ",len(costObject.vehicle.futureTasks))
        vehTemp.status = costObject.taskSequence[0][1]
        if vehTemp.status == 'P' and vehTemp not in VehPick:
            VehPick.append(vehTemp)
            if vehTemp in VehEmpty:
                VehEmpty.remove(vehTemp)
            if vehTemp in VehDrop:
                VehDrop.remove(vehTemp)
        elif vehTemp.status == 'D' and vehTemp not in VehDrop:
            VehDrop.append(vehTemp)
            if vehTemp in VehEmpty:
                VehEmpty.remove(vehTemp)
            if vehTemp in VehPick:
                VehPick.remove(vehTemp)

        # Update future tasks
        # Oct 15, the problem is here, you cannot let v.futureTasks = costObjectve.tasksequence,
        vehTemp.futureTasks = costObject.taskSequence
        vehTemp.path = tasktotalpath
        print ("For Vehicle-",vehTemp.id," Sequence")
        for v in vehTemp.futureTasks:
            print(v[0].person_id,v[1])

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
        print('No of person request remaining after call to matching module', len(PersonRequest),file=op_file)
    for v in VehicleList:
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

    t += para.TimeStep


print('This is the end of simulation...')




