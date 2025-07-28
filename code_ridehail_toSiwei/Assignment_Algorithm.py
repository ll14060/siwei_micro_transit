__author__ = 'Mike'

# This file contains all the different dynamic assignment, repositioning, and joing assign-reposition strategies

# Import necessary files
import Distance
import gurobipy
import Settings as Set
import Vehicle
import Regions
import Person
import sys
import time
from random import sample


# Separate different assignment, repositioning, and assignment-repositioning strategies
# 1. Assignment-only strategies with first-come, first-serve (i.e. no math program to solve)
# 2. Assignment-only strategies with a decision problem (i.e. a math program)
# 3. Reposition-only and Joint assign-reposition strategies

#############################################################################################################
# Checks which assignment-only FCFS strategy, then sends input information to specific strategy
def assign_veh_fcfs(av_fleet, customers, assign_method, t):
    # given assign_method that is assignment-only FCFS, call specific assignment function
    if assign_method == "1_FCFS_longestIdle":
        fcfs_longest_idle(av_fleet, customers, t)       # <-- assign longest waiting person to longest idle AV
    elif assign_method == "2_FCFS_nearestIdle":
        fcfs_nearest_idle(av_fleet, customers, t)       # <-- assign longest waiting person to nearest idle AV
    elif assign_method == "3_FCFS_smartNN":
        # case A: more idle AVs than open user requests:
        # assign longest waiting person to nearest idle AV
        # case B: more open user requests than idle AVs
        # assign idle AV to nearest open user request
        fcfs_smart_nn(av_fleet, customers, t)
    elif assign_method == "4_FCFS_drop_smartNN":
        fcfs_drop_smart_nn(av_fleet, customers, t)      # <-- same as '3_FCFS_smartNN', except include en-route drop-AVs
    elif assign_method == "4a_FCFS_drop_smartNN2":
        fcfs_drop_smart_nn2(av_fleet, customers, t)     # <-- same as '3_FCFS_smartNN', except include en-route drop-AVs
    else:
        print("Error: No_FCFS_assignment_method")
    return
#############################################################################################################


#############################################################################################################
# Checks which assignment-only optimization strategy then sends input information to specific strategy
def assign_veh_opt(av_fleet, customers, assign_method, t):
    if assign_method == "5_match_idleOnly":  # assignment problem with idle AVs and open users
        opt_idle(av_fleet, customers, t)
    elif assign_method == "6_match_idlePick":
        opt_idle_pick(av_fleet, customers, t)  # assignment problem with idle+pick AVs and open+assigned users
    elif assign_method == "7_match_idleDrop":
        opt_idle_drop(av_fleet, customers, t)  # assignment problem with idle+drop AVs and open users
    elif assign_method == "7_match_idleDrop2":
        opt_idle_drop2(av_fleet, customers, t)  # assignment problem with idle+drop AVs and open users
    elif assign_method == "8_match_idlePickDrop":
        opt_idle_pick_drop(av_fleet, customers, t)  # assignment problem with idle+drop+pick AVs and open+assigned users

    # same as '5_match_idleOnly' except assignment reward replaces hard constraint on all AVs or users being assigned
    elif assign_method == "assign_idle_w_reward":
        assign_idle_w_reward(av_fleet, customers, t)
    else:
        print("Error: No_assignment_method")
    return
#############################################################################################################


# 1) i advise to give the whole area class as input parameter
# 2) the forecast will need to know which weekday it is
# 3) might be necessary to pass more parameters for my algorithm:
# - length of time horizon
# - minimal imbalance

#############################################################################################################
# Checks which reposition-only or joint reposition-assign strategy then sends input information to specific strategy
def relocate_veh(av_fleet, customers,  area, relocate_method, t, weekday):
    if relocate_method == "joint_assign-reposition":
        # relocation algorithm will not work if there are no more future requests
        if t < Set.last_request_time:
            joint_assign_repos_empty_avs(av_fleet, customers, area, t, weekday)
        else:
            assign_idle_w_reward(av_fleet, customers, t)
    else:
        print("Error: No_relocation_method")
    return
#############################################################################################################


#############################################################################################################
def fcfs_longest_idle(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of currently idle AVs, and its length
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    len_avs = len(idle_avs)
    # get list of unassigned users, and its length
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    # determine the maximum number of possible matches
    most_match_count = min(len_custs, len_avs)

    # cycle through unassigned customers, ordered in terms of elapsed wait time
    for z_match in range(most_match_count):
        # get longest wait time of unassigned customers, then get the user with this longest elapsed wait time
        min_request_time = min(list(i.request_time for i in unassign_cust))
        max_wait_cust = list(i for i in unassign_cust if i.request_time == min_request_time)[0]
        # get longest time since last drop-off, then get the AV with this longest time
        min_last_drop_time = min(list(j.last_drop_time for j in idle_avs))
        long_wait_av = list(j for j in idle_avs if j.last_drop_time == min_last_drop_time)[0]

        # assign longest wait user, to AV with longest time since last drop-off
        temp_veh_status = "base_assign"  # <-- this is to help with updating AV status
        Vehicle.update_vehicle(t, max_wait_cust, long_wait_av, Regions.SubArea, temp_veh_status)  # <-- updates AV
        Person.update_person(t, max_wait_cust, long_wait_av)  # <-- updates person

        # now remove the updated AV and the updated customer
        unassign_cust.remove(max_wait_cust)
        idle_avs.remove(long_wait_av)

    return
#############################################################################################################


#############################################################################################################
def fcfs_nearest_idle(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of currently idle AVs
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")

    # initialize list of AVs that have been assigned
    used_vehicles = []
    count_p = -1
    # loop through unassigned users
    # for each user, loop through all AVs that have not yet been assigned
    # calculate the user-to-AV distance
    # check if that distance is less than previous closest/best user-to-AV distance
    # if it is less, then temporarily store the current AV as the closest user-to-AV distance
    for i_cust in unassign_cust:
        count_p += 1
        min_dist = Set.inf  # <-- initialize minimum distance between current user and closest AV
        win_veh_index = -1
        veh_index = -1
        for j_av in idle_avs:
            veh_index += 1
            dist = Distance.dist_manhat_pick(i_cust, j_av)  # <-- returns manhattan distance

            # make sure that AV has not been previously assigned to a user
            if dist < min_dist and not (j_av.vehicle_id in used_vehicles):
                win_veh_index = veh_index
                min_dist = dist

        # check if user assigned to vehicle
        # then get the vehicle assigned to user
        # add this vehicle to list of previously assigned vehicles
        # update status of vehicle
        # update status of traveler
        if win_veh_index >= 0:  # <-- make sure user assigned to real vehicle
            # get the winning/closest AV
            win_vehicle = idle_avs[win_veh_index]
            # store this AV in the used_vehicles list
            used_vehicles.append(win_vehicle.vehicle_id)

            # now update user and AV that was assigned to it
            temp_veh_status = "base_assign"
            Vehicle.update_vehicle(t, i_cust, win_vehicle, Regions.SubArea, temp_veh_status)
            Person.update_person(t, i_cust, win_vehicle)
    return
#############################################################################################################


#############################################################################################################
def fcfs_smart_nn(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of currently idle AVs
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    len_avs = len(idle_avs)
    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    # check if there are currently more available AVs or more open customer requests

    # case 1: more available AVs then open user requests,
    # follow same logic as fcfs_nearest_idle(); i.e. assign longest waiting traveler to nearest AV

    if len_avs >= len_custs:
        used_vehicles = []
        for i_cust in unassign_cust:
            win_vehicle = Vehicle.Vehicle
            min_dist = Set.inf
            for j_av in idle_avs:
                dist = Distance.dist_manhat_pick(i_cust, j_av)
                # make sure that two persons aren't assigned to same vehicle
                if dist < min_dist and j_av not in used_vehicles:
                    win_vehicle = j_av
                    min_dist = dist
            if win_vehicle.vehicle_id >= 0:
                used_vehicles.append(win_vehicle)

                temp_veh_status = "base_assign"
                Vehicle.update_vehicle(t, i_cust, win_vehicle, Regions.SubArea, temp_veh_status)
                Person.update_person(t, i_cust, win_vehicle)

    # case 2: more open user requests than available AVs
    # in this case, the fleet is 'overwhelmed'
    # rather than waste time getting to users that have been waiting a long time, maximize utilization of AVs
    # assign newly available AVs to nearest open user request
    else:
        win_cust_list = []
        for j_av in idle_avs:
            min_dist = Set.inf
            win_cust = Person.Person
            for i_cust in unassign_cust:
                dist = Distance.dist_manhat_pick(i_cust, j_av)
                if dist < min_dist and i_cust not in win_cust_list:
                    win_cust = i_cust
                    min_dist = dist
            if win_cust.person_id >= 0:
                win_cust_list.append(win_cust)

                temp_veh_status = "base_assign"
                Vehicle.update_vehicle(t, win_cust, j_av, Regions.SubArea, temp_veh_status)
                Person.update_person(t, win_cust, j_av)
    return
#############################################################################################################


############################################################################################################
def fcfs_drop_smart_nn(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of currently idle AVs
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    # get list of AVs currently en-route to drop-off user that have not already been assigned to pick up next user
    drop_avs = list(k_av for k_av in av_fleet if k_av.status == "enroute_dropoff" and k_av.next_pickup.person_id < 0)

    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    #get combined list of idle and en-route drop-off AVs
    idle_n_drop_avs = idle_avs + drop_avs
    tot_veh_length = len(idle_n_drop_avs)

    # check if there are currently more available AVs or more open customer requests
    # however, this time available AVs include drop-off AVs.
    # otherwise the logic below is the same as fcfs_smart_nn()


    if tot_veh_length >= len_custs:
        used_vehicles = []
        for i_cust in unassign_cust:
            min_dist = Set.inf
            win_av = Vehicle.Vehicle
            for j_av in idle_n_drop_avs:
                if j_av.status == "enroute_dropoff":
                    # this distance function calculates the distance/time for drop-off AV to drop-off current passenger
                    # and pick up i_cust
                    dist = Distance.dist_manhat_drop_pick(i_cust, j_av)
                else:
                    dist = Distance.dist_manhat_pick(i_cust, j_av)
                # make sure that two persons aren't assigned to same vehicle
                if dist < min_dist and j_av not in used_vehicles:
                    win_av = j_av
                    min_dist = dist
            if win_av.vehicle_id >= 0:
                used_vehicles.append(win_av)

                if win_av.status == "enroute_dropoff":
                    temp_veh_status = "new_assign"
                elif win_av.status in ("idle", "relocating"):
                    temp_veh_status = "base_assign"
                else:
                    temp_veh_status = "wrong"

                Vehicle.update_vehicle(t, i_cust, win_av, Regions.SubArea, temp_veh_status)
                Person.update_person(t, i_cust, win_av)
    else:
        win_cust_list = []
        for j_av in idle_n_drop_avs:
            min_dist = Set.inf
            win_cust = Person.Person
            for i_cust in unassign_cust:
                if j_av.status == "enroute_dropoff":
                    dist = Distance.dist_manhat_drop_pick(i_cust, j_av)
                else:
                    dist = Distance.dist_manhat_pick(i_cust, j_av)

                if dist < min_dist and i_cust not in win_cust_list:
                    win_cust = i_cust
                    min_dist = dist

            if win_cust.person_id >= 0:
                win_cust_list.append(win_cust)

                if j_av.status == "enroute_dropoff":
                    temp_veh_status = "new_assign"
                elif j_av.status in ("idle", "relocating"):
                    temp_veh_status = "base_assign"
                else:
                    temp_veh_status = "wrong"

                Vehicle.update_vehicle(t, win_cust, j_av, Regions.SubArea, temp_veh_status)
                Person.update_person(t, win_cust, j_av)
    return
#############################################################################################################


# same as fcfs_drop_smart_nn(), except the if condition changes
# in fcfs_drop_smart_nn2(), when # idle AVs        > # open requests
# in fcfs_drop_smart_nn(),  when # idle+drop AVs    > # open user requests
# there is very little difference in results between these two
############################################################################################################
def fcfs_drop_smart_nn2(av_fleet, customers, t):
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    len_idle_avs = len(idle_avs)
    drop_avs = list(k_av for k_av in av_fleet if k_av.status == "enroute_dropoff" and k_av.next_pickup.person_id < 0)

    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    idle_n_drop_avs = idle_avs + drop_avs

    if len_idle_avs >= len_custs:
        used_vehicles = []
        for i_cust in unassign_cust:
            min_dist = Set.inf
            win_av = Vehicle.Vehicle
            for j_av in idle_n_drop_avs:
                if j_av.status == "enroute_dropoff":
                    dist = Distance.dist_manhat_drop_pick(i_cust, j_av)
                else:
                    dist = Distance.dist_manhat_pick(i_cust, j_av)
                # make sure that two persons aren't assigned to same vehicle
                if dist < min_dist and j_av not in used_vehicles:
                    win_av = j_av
                    min_dist = dist
            if win_av.vehicle_id >= 0:
                used_vehicles.append(win_av)

                if win_av.status == "enroute_dropoff":
                    temp_veh_status = "new_assign"
                elif win_av.status in ("idle", "relocating"):
                    temp_veh_status = "base_assign"
                else:
                    temp_veh_status = "wrong"

                Vehicle.update_vehicle(t, i_cust, win_av, Regions.SubArea, temp_veh_status)
                Person.update_person(t, i_cust, win_av)
    else:
        win_cust_list = []
        for j_av in idle_n_drop_avs:
            min_dist = Set.inf
            win_cust = Person.Person
            for i_cust in unassign_cust:
                if j_av.status == "enroute_dropoff":
                    dist = Distance.dist_manhat_drop_pick(i_cust, j_av)
                else:
                    dist = Distance.dist_manhat_pick(i_cust, j_av)

                if dist < min_dist and i_cust not in win_cust_list:
                    win_cust = i_cust
                    min_dist = dist

            if win_cust.person_id >= 0:
                win_cust_list.append(win_cust)

                if j_av.status == "enroute_dropoff":
                    temp_veh_status = "new_assign"
                elif j_av.status in ("idle", "relocating"):
                    temp_veh_status = "base_assign"
                else:
                    temp_veh_status = "wrong"

                Vehicle.update_vehicle(t, win_cust, j_av, Regions.SubArea, temp_veh_status)
                Person.update_person(t, win_cust, j_av)
    return
#############################################################################################################


#############################################################################################################
# Optimization Assignment Strategies
#############################################################################################################

#############################################################################################################
def opt_idle(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of currently idle AVs
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    len_idle_avs = len(idle_avs)

    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    # initialize distance matrix between current AV locations and open request pickup location
    dist_assgn = [[0 for jj in range(len_idle_avs)] for ii in range(len_custs)]
    # initialize decision variable
    # x[i,j] = 1, if AV j assigned to pick up user i
    x = [[0 for jj in range(len_idle_avs)] for ii in range(len_custs)]

    # need to determine values in the distance matrix
    # loop through all unassigned users
    # determine their elapsed wait time, and wait time penalty
    # then for each unassigned user, loop through all available AVs
    # for each AV, determine how much remaining time it has at the curb to drop-off last users
    # then determine distance between user i_pass and AV j_veh
    # assign weighted combination of distance, elapsed wait time, and curb wait time to 'dist_assign'
    count_pass = -1
    for i_pass in unassign_cust:
        count_pass += 1
        count_veh = -1
        cur_wait = t - i_pass.request_time
        elapsed_wait_penalty = cur_wait * Set.veh_speed * 2.0
        for j_veh in idle_avs:
            count_veh += 1
            av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
            dist_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) - \
                                                elapsed_wait_penalty + av_curb_wait

    t1 = time.time()


    # Gurobi Model
    gurobi_model = gurobipy.Model("idleOnly_minDist")
    gurobi_model.setParam('OutputFlag', False)

    # DECISION VARIABLES

    # objective function is simply dist_assign*x
    for i in range(len_custs):
        for j in range(len_idle_avs):
            x[i][j] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=dist_assgn[i][j], name='x_%s_%s' % (i, j))
    gurobi_model.update()

    # CONSTRAINTS

    # if the number of unassigned travelers is less than the number of idle vehicles
    # then make sure all the unassigned travelers are assigned a vehicle
    if len_custs <= len_idle_avs:
        for ii in range(len_custs):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(len_idle_avs)) == 1)
        for jj in range(len_idle_avs):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_custs)) <= 1)

    # else if the number of unassigned travelers is greater than the number of idle vehicles
    # then make sure all the idle vehicles are assigned to an unassigned traveler
    else:
        for ii in range(len_custs):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(len_idle_avs)) <= 1)
        for jj in range(len_idle_avs):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_custs)) == 1)

    gurobi_model.optimize()

    # check if Gurobi generated a solution
    # then loop through all user-AV combinations
    # check if they were matched
    # then update the status of the AV and the user
    if gurobi_model.status == gurobipy.GRB.Status.OPTIMAL:
        for m_pass in range(len_custs):
            for n_veh in range(len_idle_avs):
                if x[m_pass][n_veh].X == 1:
                    temp_veh_status = "base_assign"
                    win_cust = unassign_cust[m_pass]
                    win_av = idle_avs[n_veh]
                    Vehicle.update_vehicle(t, win_cust, win_av, Regions.SubArea, temp_veh_status)
                    Person.update_person(t, win_cust, win_av)
                    break
    else:
        sys.exit("No Optimal Solution - idleOnly_minDist")
    # print("Vehicles= ", len_veh, "  Passengers= ", len_pass, "  time=", time.time() - t1)
    return
#############################################################################################################


#############################################################################################################
def opt_idle_pick(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    # get list of assigned, but not yet picked up users
    assign_cust = list(ii_cust for ii_cust in customers if ii_cust.status == "assigned")
    # store all AVs in a new variable
    temp_av_fleet = av_fleet[:]

    # loop through all AVs in fleet
    # determine if the AV currently assigned to pick up a user that has already been re-assigned once
    for j_av in temp_av_fleet:
        i_cust = j_av.next_pickup
        if i_cust.reassigned == 1:
            assign_cust.remove(i_cust)
            temp_av_fleet.remove(j_av)

    # get list of idle AVs
    idle_avs = list(j_veh for j_veh in temp_av_fleet if j_veh.status in ("idle", "relocating"))
    # get list of en-route pickup AVs
    pick_avs = list(j_veh for j_veh in temp_av_fleet if j_veh.status == "enroute_pickup")

    # get combined list of id;e and en-route pickup AVs
    idle_n_pick_avs = idle_avs + pick_avs
    len_idle_n_pick_av = len(idle_n_pick_avs)

    # get combined list of unassigned users and assigned but not yet picked up users
    no_assign_or_pick_cust = unassign_cust + assign_cust
    len_no_assign_or_pick_cust = len(no_assign_or_pick_cust)

    # initialize distance matrix between current AV locations and open request pickup location
    dist_assgn = [[0 for j in range(len_idle_n_pick_av)] for i in range(len_no_assign_or_pick_cust)]
    # initialize decision variable
    # x[i,j] = 1, if AV j assigned to pick up user i
    x = [[0 for j in range(len_idle_n_pick_av)] for i in range(len_no_assign_or_pick_cust)]
    # initialize vector to determine if user was previously assigned
    prev_assign = [0 for z in range(len_no_assign_or_pick_cust)]

    # loop through all users
    # get their elapsed wait time and wait time penalty
    # then start looping through all AVs, for each individual users
    # see below for how dist_assign() changes based on the AVs and user being considered
    count_pass = -1
    for i_pass in no_assign_or_pick_cust:
        count_pass += 1
        count_veh = -1
        cur_wait = t - i_pass.request_time
        elapsed_wait_penalty = cur_wait * Set.veh_speed * 2.0
        for j_veh in idle_n_pick_avs:
            count_veh += 1

            # case 1:  passenger is unassigned
            if i_pass.status == "unassigned":
                # case 1a: AV is idle
                if j_veh.status in ("idle", "relocating"):
                    # this distance calculation is the same as opt_idle()
                    av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
                    dist_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) \
                                                        - elapsed_wait_penalty + av_curb_wait
                # case 1b: AV is en-route to pickup users
                elif j_veh.status == "enroute_pickup":
                    # add penalty for reassigning en-route pickup AV to a new, unassigned, user
                    dist_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) \
                                                        - elapsed_wait_penalty + Set.reassign_penalty
                else:
                    sys.exit("Something wrong with AV state - idlePick_minDist")

            # case 2: passenger is assigned but not yet picked up
            elif i_pass.status == "assigned":
                prev_assign[count_pass] = 1
                # case 2a: AV previously assigned to i_pass
                if j_veh.next_pickup == i_pass:
                    if j_veh.status == "enroute_pickup":
                        # just get remaining distance and discount elapsed wait time
                        dist_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) \
                                                            - elapsed_wait_penalty
                    else:
                        sys.exit("Something wrong with current AV-customer match - idlePick_minDist")

                # case 2b: AV is idle
                elif j_veh.status in ("idle", "relocating"):
                    # add penalty for assigning new, different, idle AV to an assigned user
                    av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
                    dist_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                        + Set.reassign_penalty + av_curb_wait
                # case 2c: AV is en-route pickup
                elif j_veh.status == "enroute_pickup":
                    # add double penalty for assigning pickup AV to different user, and
                    # assigning user to different AV
                    dist_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                        + 2 * Set.reassign_penalty
                else:
                    sys.exit("Something wrong with AV state - idlePick_minDist")
            else:
                sys.exit("Something wrong with customer state - idlePick_minDist")
    t1 = time.time()

    # Model
    gurobi_model = gurobipy.Model("idlePick_minDist")
    gurobi_model.setParam('OutputFlag', False)

    # DECISION VARIABLES
    for i in range(len_no_assign_or_pick_cust):
        for j in range(len_idle_n_pick_av):
            x[i][j] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=dist_assgn[i][j], name='x_%s_%s' % (i, j))
    gurobi_model.update()

    # CONSTRAINTS

    # Previously assigned passengers must be assigned a vehicle
    # not necessarily the same AV
    for ii in range(len_no_assign_or_pick_cust):
        gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(len_idle_n_pick_av)) - prev_assign[ii] >= 0)

    # if number of open user requests is less than the number of idle+pickup AVs, then assign all users to an AV
    if len_no_assign_or_pick_cust <= len_idle_n_pick_av:
        for ii in range(len_no_assign_or_pick_cust):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(len_idle_n_pick_av)) == 1)
        for jj in range(len_idle_n_pick_av):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_no_assign_or_pick_cust)) <= 1)

    # if number of open user requests is greater than the number of idle+pickup AVs, then assign all AVs to a user
    else:
        for ii in range(len_no_assign_or_pick_cust):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(len_idle_n_pick_av)) <= 1)
        for jj in range(len_idle_n_pick_av):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_no_assign_or_pick_cust)) == 1)

    gurobi_model.optimize()

    # check if Gurobi generated a solution
    # then loop through all user-AV combinations
    # check if they were matched
    # then update the status of the AV and the user
    # need to do special updates depending on previous states of AV and user
    if gurobi_model.status == gurobipy.GRB.Status.OPTIMAL:
        for n_veh in range(len_idle_n_pick_av):
            found = 0
            for m_pass in range(len_no_assign_or_pick_cust):
                if x[m_pass][n_veh].X == 1:
                    win_cust = no_assign_or_pick_cust[m_pass]
                    win_av = idle_n_pick_avs[n_veh]

                    if win_av.next_pickup != win_cust:

                        if win_cust.status == "unassigned":
                            Person.update_person(t, win_cust, win_av)
                        elif win_cust.status == "assigned":
                            win_cust.status = "reassign"
                            Person.update_person(t, win_cust, win_av)

                        if win_av.status in ("idle", "relocating"):
                            temp_veh_status = "base_assign"
                        elif win_av.status == "enroute_pickup":
                            temp_veh_status = "reassign"
                        else:
                            temp_veh_status = "wrong"

                        Vehicle.update_vehicle(t, win_cust, win_av, Regions.SubArea, temp_veh_status)

                    found = 1
                    break

            # this is the case in which a previously assigned AV, is no longer assigned to an user
            if found == 0:
                no_win_av = idle_n_pick_avs[n_veh]
                if no_win_av.status == "enroute_pickup":
                    temp_veh_status = "unassign"
                    Vehicle.update_vehicle(t, Person.Person, no_win_av, Regions.SubArea, temp_veh_status)
    else:
        sys.exit("No Optimal Solution - idlePick_minDist")
    # print("Vehicles= ", tot_veh_length, "  Passengers= ", len_no_assign_or_pick_cust, "  time=", time.time()-t1)
    return
#############################################################################################################


#############################################################################################################
def opt_idle_drop(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of idle AVs
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    len_idle_avs = len(idle_avs)
    # get list of drop-off AVs that do not have a next pickup already
    drop_avs = list(k_av for k_av in av_fleet if k_av.status == "enroute_dropoff" and k_av.next_pickup.person_id < 0)

    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    # get combined list of idle and drop-off AVs
    idle_n_drop_avs = idle_avs + drop_avs
    tot_veh_length = len(idle_n_drop_avs)

    # initialize cost matrix for assigning AVs to users
    cost_assgn = [[0 for j in range(tot_veh_length)] for i in range(len_custs)]
    # initialize decision variable matrix for assigning AV j to user i
    x = [[0 for j in range(tot_veh_length)] for i in range(len_custs)]


    # loop through all users
    # get their elapsed wait time
    # loop through all AVs, for each user
    # get their assignment cost values
    count_pass = -1
    for i_pass in unassign_cust:
        count_pass += 1
        count_veh = -1
        cur_wait = t - i_pass.request_time
        elapsed_wait_penalty = cur_wait * Set.veh_speed * 2.0
        for j_veh in idle_n_drop_avs:
            count_veh += 1

            # if vehicle state is enroute_dropoff - need to include dropoff distance as well
            if count_veh >= len_idle_avs:
                av_curb_wait = Set.curb_drop_time * Set.veh_speed
                cost_assgn[count_pass][count_veh] = Distance.dist_manhat_drop_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                    + Set.dropoff_penalty + av_curb_wait
            else:
                av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
                cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass,
                                                                              j_veh) - elapsed_wait_penalty + av_curb_wait

    t1 = time.time()

    # Gurobi Model
    gurobi_model = gurobipy.Model("idleDrop_minDist")
    gurobi_model.setParam('OutputFlag', False)

    # DECISION VARIABLES
    for i in range(len_custs):
        for j in range(tot_veh_length):
            x[i][j] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=cost_assgn[i][j], name='x_%s_%s' % (i, j))
    gurobi_model.update()

    # CONSTRAINTS

    # if # open user requests < # available AVs
    # then make sure each user assigned to an AV
    # and make sure each AV assigned to at most one user
    if len_custs <= tot_veh_length:
        for ii in range(len_custs):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(tot_veh_length)) == 1)
        for jj in range(tot_veh_length):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_custs)) <= 1)

    # if # open user requests ? # available AVs
    # then make sure each AV assigned to a user
    # and make sure each user assigned to at most one AV
    else:
        for ii in range(len_custs):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(tot_veh_length)) <= 1)
        for jj in range(tot_veh_length):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_custs)) == 1)

    gurobi_model.optimize()

    # check if Gurobi generated a solution
    # then loop through all user-AV combinations
    # check if they were matched
    # then update the status of the AV and the user
    # need to do special updates depending on previous states of AV and user

    if gurobi_model.status == gurobipy.GRB.Status.OPTIMAL:
        for m_pass in range(len_custs):
            for n_veh in range(tot_veh_length):
                if x[m_pass][n_veh].X == 1:
                    win_cust = unassign_cust[m_pass]
                    win_av = idle_n_drop_avs[n_veh]

                    if win_av.status in ("idle", "relocating"):
                        temp_veh_status = "base_assign"
                    elif win_av.status == "enroute_dropoff":
                        temp_veh_status = "new_assign"
                    else:
                        temp_veh_status = "wrong"

                    Vehicle.update_vehicle(t, win_cust, win_av, Regions.SubArea, temp_veh_status)
                    Person.update_person(t, win_cust, win_av)
                    break
    else:
        sys.exit("No Optimal Solution - idleDrop_minDist")
    # print("Vehicles= ", tot_veh_length, "  Passengers= ", len_pass, "  time=", time.time() - t1)
    return
#############################################################################################################


# changed one if condition and one set of constraints
#############################################################################################################
def opt_idle_drop2(av_fleet, customers, t):
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    len_idle_avs = len(idle_avs)
    drop_avs = list(k_av for k_av in av_fleet if k_av.status == "enroute_dropoff" and k_av.next_pickup.person_id < 0)

    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    idle_n_drop_avs = idle_avs + drop_avs
    tot_veh_length = len(idle_n_drop_avs)

    dist_assgn = [[0 for j in range(tot_veh_length)] for i in range(len_custs)]
    x = [[0 for j in range(tot_veh_length)] for i in range(len_custs)]

    count_pass = -1
    for i_pass in unassign_cust:
        count_pass += 1
        count_veh = -1
        cur_wait = t - i_pass.request_time
        elapsed_wait_penalty = cur_wait * Set.veh_speed * 2.0
        for j_veh in idle_n_drop_avs:
            count_veh += 1

            # if vehicle state is enroute_dropoff - need to include dropoff distance as well
            if count_veh >= len_idle_avs:
                av_curb_wait = Set.curb_drop_time * Set.veh_speed
                dist_assgn[count_pass][count_veh] = Distance.dist_manhat_drop_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                    + Set.dropoff_penalty + av_curb_wait
            else:
                av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
                dist_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass,
                                                                              j_veh) - elapsed_wait_penalty + av_curb_wait

    t1 = time.time()
    # Model
    gurobi_model = gurobipy.Model("idleDrop_minDist")
    gurobi_model.setParam('OutputFlag', False)

    # Decision Variables
    for i in range(len_custs):
        for j in range(tot_veh_length):
            x[i][j] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=dist_assgn[i][j], name='x_%s_%s' % (i, j))
    gurobi_model.update()

    # constraints
    if len_custs <= len_idle_avs:
        for ii in range(len_custs):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(tot_veh_length)) == 1)
        for jj in range(tot_veh_length):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_custs)) <= 1)

    # if # open requests > # idle AVs;
    else:
        # then, make sure the total number of assigned customers at least number of idle AVs
        gurobi_model.addConstr(
            gurobipy.quicksum(x[iii][jjj] for iii in range(len_custs) for jjj in range(tot_veh_length)) >= len_idle_avs)
        # then, assign passenger to at most one AV
        for ii in range(len_custs):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(tot_veh_length)) <= 1)
        # then, assign AV to at most one passenger
        for jj in range(tot_veh_length):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_custs)) <= 1)

    gurobi_model.optimize()

    if gurobi_model.status == gurobipy.GRB.Status.OPTIMAL:
        for m_pass in range(len_custs):
            for n_veh in range(tot_veh_length):
                if x[m_pass][n_veh].X == 1:
                    win_cust = unassign_cust[m_pass]
                    win_av = idle_n_drop_avs[n_veh]

                    if win_av.status in ("idle", "relocating"):
                        temp_veh_status = "base_assign"
                    elif win_av.status == "enroute_dropoff":
                        temp_veh_status = "new_assign"
                    else:
                        temp_veh_status = "wrong"

                    Vehicle.update_vehicle(t, win_cust, win_av, Regions.SubArea, temp_veh_status)
                    Person.update_person(t, win_cust, win_av)
                    break
    else:
        sys.exit("No Optimal Solution - idleDrop_minDist")
    # print("Vehicles= ", tot_veh_length, "  Passengers= ", len_pass, "  time=", time.time() - t1)
    return
#############################################################################################################


#############################################################################################################
def opt_idle_pick_drop(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    # get list of assigned (but not yet picked up) users
    assign_cust = list(ii_cust for ii_cust in customers if ii_cust.status == "assigned")

    # copy list of AVs
    temp_av_fleet = av_fleet[:]

    # remove AVs that already have a next pickup
    for j_av in temp_av_fleet:
        i_cust = j_av.next_pickup
        if i_cust.reassigned == 1:
            assign_cust.remove(i_cust)
            temp_av_fleet.remove(j_av)

    # get lists of idle AVs, drop AVs , and pickup AVs
    idle_avs = list(j_veh for j_veh in temp_av_fleet if j_veh.status in ("idle", "relocating"))
    drop_avs = list(j_veh for j_veh in temp_av_fleet if j_veh.status == "enroute_dropoff")
    pick_avs = list(j_veh for j_veh in temp_av_fleet if j_veh.status == "enroute_pickup")

    # get list of all AVs, ordered by idle, drop, pickup
    all_avs = idle_avs + drop_avs + pick_avs
    tot_veh_length = len(all_avs)

    # get list of all users, ordered by unassigned then assigned
    no_assign_or_pick_cust = unassign_cust + assign_cust
    len_no_assign_or_pick_cust = len(no_assign_or_pick_cust)

    # initialize matrix of cost to assign AV j to user i
    cost_assgn = [[0 for j in range(tot_veh_length)] for i in range(len_no_assign_or_pick_cust)]
    # initialize decision variable matrix for assigning AV j to user i
    x = [[0 for j in range(tot_veh_length)] for i in range(len_no_assign_or_pick_cust)]
    # initialize vector that denotes AVs that have already been asigned
    prev_assign = [0 for z in range(len_no_assign_or_pick_cust)]

    # loop through all users
    # determine cost matrix value depending on status of AV and status of user
    count_pass = -1
    for i_pass in no_assign_or_pick_cust:
        count_pass += 1
        count_veh = -1
        # determine how long user has been waiting already
        cur_wait = t - i_pass.request_time
        # assign a penalty term that will be used to reward fleet operator for assigning AV to long waiting user
        elapsed_wait_penalty = cur_wait * Set.veh_speed * 2.0
        for j_veh in all_avs:
            count_veh += 1

            # 1
            if i_pass.status == "unassigned":

                # Case 1a: unassigned user, idle AV
                # no added penalties or considerations
                if j_veh.status in ("idle", "relocating"):
                    av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
                    cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                        + av_curb_wait
                # Case 1b: unassigned user, enroute drop AV
                # need to calculate distance to drop-off in-vehicle passenger then pick up new passenger
                # add small penalty for assigning user to en-route drop-off AV which has more uncertainty than idle AV
                elif j_veh.status == "enroute_dropoff":
                    av_curb_wait = Set.curb_drop_time * Set.veh_speed
                    cost_assgn[count_pass][count_veh] = Distance.dist_manhat_drop_pick(i_pass,
                                                                                       j_veh) - elapsed_wait_penalty \
                                                        + Set.dropoff_penalty + av_curb_wait
                # Case 1c: unassigned user, enroute pickup AV
                # add small penalty for reassigning AV to new user
                elif j_veh.status == "enroute_pickup":
                    cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                        + Set.reassign_penalty
                else:
                    sys.exit("Something wrong with AV state - idlePickDrop_minDist")

            elif i_pass.status == "assigned":
                prev_assign[count_pass] = 1

                if j_veh.next_pickup == i_pass:
                    # Case 2a(i): Assigned user and the enroute pickup AV she is currently assigned to
                    if j_veh.status == "enroute_pickup":
                        cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) \
                                                            - elapsed_wait_penalty
                    # Case 2a(ii): Assigned user and her original enroute drop-off AV
                    # this shouldn't ever happen because we removed these AVs and users above
                    elif j_veh.status == "enroute_dropoff":
                        av_curb_wait = Set.curb_drop_time * Set.veh_speed
                        cost_assgn[count_pass][count_veh] = Distance.dist_manhat_drop_pick(i_pass, j_veh) \
                                                            - elapsed_wait_penalty \
                                                            + Set.dropoff_penalty + av_curb_wait
                    else:
                        sys.exit("Something wrong with current AV-customer match - idlePickDrop_minDist")

                # Case 2b: Assigned user and idle AV
                # add small penalty for reassigning user to new AV
                elif j_veh.status in ("idle", "relocating"):
                    av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
                    cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                        + Set.reassign_penalty + av_curb_wait
                # Case 2c: Assigned user and drop-off AV
                # add small penalty for reassigning user to new AV
                # add another small penalty for assigning user to drop-off AV
                elif j_veh.status == "enroute_dropoff":
                    av_curb_wait = Set.curb_drop_time * Set.veh_speed
                    cost_assgn[count_pass][count_veh] = Distance.dist_manhat_drop_pick(i_pass, j_veh) \
                                                        - elapsed_wait_penalty + Set.dropoff_penalty \
                                                        + Set.reassign_penalty + av_curb_wait
                # Case 2d: Assigned user and en-route pick AV
                # add small penalty for reassigning user to new AV
                # add small penalty for reassiging AV to new user
                elif j_veh.status == "enroute_pickup":
                    cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) - elapsed_wait_penalty \
                                                        + 2 * Set.reassign_penalty
                else:
                    sys.exit("Something wrong with AV state - idlePickDrop_minDist")
            else:
                sys.exit("Something wrong with customer state - idlePickDrop_minDist")

    t1 = time.time()

    # Gurobi Model
    gurobi_model = gurobipy.Model("idlePickDrop_minDist")
    gurobi_model.setParam('OutputFlag', False)

    # DECISION VARIABLES
    for i in range(len_no_assign_or_pick_cust):
        for j in range(tot_veh_length):
            x[i][j] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=cost_assgn[i][j], name='x_%s_%s' % (i, j))
    gurobi_model.update()

    # CONSTRAINTS

    # Previously assigned users must be assigned to an AV, not necessarily their old AV
    for ii in range(len_no_assign_or_pick_cust):
        gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(tot_veh_length)) - prev_assign[ii] >= 0)

    # if # open user requests < # available vehicles
    # then assign all users to an AV
    # and make sure each AV assigned to at most 1 user
    if len_no_assign_or_pick_cust <= tot_veh_length:
        for ii in range(len_no_assign_or_pick_cust):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(tot_veh_length)) == 1)
        for jj in range(tot_veh_length):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_no_assign_or_pick_cust)) <= 1)

    # if # open user requests > # available vehicles
    # then assign all AVs to a user
    # and make sure each user assigned to at most one AV
    else:
        for ii in range(len_no_assign_or_pick_cust):
            gurobi_model.addConstr(gurobipy.quicksum(x[ii][j] for j in range(tot_veh_length)) <= 1)
        for jj in range(tot_veh_length):
            gurobi_model.addConstr(gurobipy.quicksum(x[i][jj] for i in range(len_no_assign_or_pick_cust)) == 1)

    gurobi_model.optimize()
    
    # check if Gurobi generated a solution                                       
    # then loop through all user-AV combinations                                 
    # check if they were matched                                                 
    # then update the status of the AV and the user                              
    # need to do special updates depending on previous states of AV and user     
    if gurobi_model.status == gurobipy.GRB.Status.OPTIMAL:
        for n_veh in range(tot_veh_length):
            found = 0
            for m_pass in range(len_no_assign_or_pick_cust):
                if x[m_pass][n_veh].X == 1:
                    win_cust = no_assign_or_pick_cust[m_pass]
                    win_av = all_avs[n_veh]

                    if win_av.next_pickup != win_cust:

                        if win_cust.status == "unassigned":
                            Person.update_person(t, win_cust, win_av)
                        elif win_cust.status == "assigned":
                            win_cust.status = "reassign"
                            Person.update_person(t, win_cust, win_av)

                        if win_av.status in ("idle", "relocating"):
                            temp_veh_status = "base_assign"
                        elif win_av.status == "enroute_dropoff":
                            temp_veh_status = "new_assign"
                        elif win_av.status == "enroute_pickup":
                            temp_veh_status = "reassign"
                        else:
                            temp_veh_status = "wrong"
                        Vehicle.update_vehicle(t, win_cust, win_av, Regions.SubArea, temp_veh_status)
                    found = 1
                    break
            if found == 0:
                no_win_av = all_avs[n_veh]
                if no_win_av.status in ["enroute_pickup", "enroute_dropoff"]:
                    temp_veh_status = "unassign"
                    Vehicle.update_vehicle(t, Person.Person, no_win_av, Regions.SubArea, temp_veh_status)
    else:
        sys.exit("No Optimal Solution - idlePickDrop_minDist")
    # print("Vehicles= ", tot_veh_length, "  Passengers= ", len_no_assign_or_pick_cust, "  time=", time.time()-t1)
    return
#############################################################################################################



#############################################################################################################
def joint_assign_repos_empty_avs(av_fleet, customers, area, t, weekday):
    # Input:  complete list of AVs, complete list of users, area class, current time, day of the week

    # # get list of empty AVs
    # empty_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    # len_empty_avs = len(empty_avs)
    #
    # # get list of unassigned users
    # unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    # len_custs = len(unassign_cust)
    #
    # # initialize matrix for cost to assign AV j to user i
    # cost_assgn = [[0 for jj in range(len_empty_avs)] for ii in range(len_custs)]
    # # initialize matrix for decision variable set to assign AV j to user i
    # x_ij = [[0 for jj in range(len_empty_avs)] for ii in range(len_custs)]
    #
    # # the area class was written by my collaborator Florian Dandl
    # # get the number
    # veh_av_dict = area.getVehicleAvailabilitiesPerArea(av_fleet)
    # # initialize list of subareas and the imbalance in each subarea
    # subarea_list = []
    # imbalance_list = []
    #
    # # subarea_forecast_dict = {}            # subArea -> count
    # # this loop here returns the current imbalance in each subarea
    # subarea_forecast_dict = area.getDemandPredictionsPerArea(weekday, t, Set.predict_horizon)
    # for sa_key, c_subArea in area.sub_areas.items():
    #     subarea_list.append(c_subArea)
    #     subarea_forecast_val = subarea_forecast_dict[sa_key]
    #     av_veh_info_list = veh_av_dict[sa_key]
    #     av_veh_val = 0
    #     for entry in av_veh_info_list:
    #         (veh_counter, av_time) = entry
    #         if av_time < t + Set.predict_horizon:
    #             av_veh_val += 1
    #
    #     imbalance = subarea_forecast_val - av_veh_val
    #     imbalance_list.append(imbalance)
    #
    # # get the number of subareas
    # len_subareas = len(subarea_list)



    veh_av_dict = area.getVehicleAvailabilitiesPerArea(av_fleet)
    subarea_list = []
    imbalance_list = []

    subarea_forecast_dict = area.getDemandPredictionsPerArea(weekday, t, Set.predict_horizon)
    for sa_key, c_subArea in area.sub_areas.items():
        subarea_list.append(c_subArea)
        subarea_forecast_val = subarea_forecast_dict[sa_key]
        av_veh_info_list = veh_av_dict[sa_key]
        av_veh_val = 0
        for entry in av_veh_info_list:
            (veh_counter, av_time) = entry
            if av_time < t + Set.predict_horizon:
                av_veh_val += 1

        imbalance = subarea_forecast_val - av_veh_val
        imbalance_list.append(imbalance)

    len_subareas = len(subarea_list)

    base_empty_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))

    if len(base_empty_avs) / len(av_fleet) >= 0.5:
        checker = min(len_subareas, len(base_empty_avs))
        empty_avs = sample(base_empty_avs, checker)
    else:
        empty_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))

    len_empty_avs = len(empty_avs)

    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    cost_assgn = [[0 for jj in range(len_empty_avs)] for ii in range(len_custs)]
    # initialize matrix for decision variable set to assign AV j to user i
    x_ij = [[0 for jj in range(len_empty_avs)] for ii in range(len_custs)]



    # initialize matrix of cost to relocate AV j to subarea k
    cost_relocate = [[100000000000 for kk in range(len_subareas)] for jj in range(len_empty_avs)]
    # initialize matrix of decision variable set to relocate AV j to subarea k
    r_jk = [[0 for kk in range(len_subareas)] for jj in range(len_empty_avs)]

    # loop through all AVs
    # get remaining AV curbside time

    # loop through all users, for each AV
    # get elapsed wait time and wait time penalty
    # calculate cost to assign AV j to user i

    # then loop through all subareas, for each AV
    # determine the distance between each AV and each subarea centroid
    # assign this distance as the cost to relocate AV j to subarea k
    count_veh = -1
    for j_veh in empty_avs:
        count_veh += 1
        count_pass = -1
        av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
        for i_pass in unassign_cust:
            count_pass += 1
            cur_wait = t - i_pass.request_time
            elapsed_wait_penalty = cur_wait * Set.veh_speed * 2.0
            # cost = travel distance + remaining curb wait time - reward for assigning Av to user
            # - reward for assigning AV to long waiting user
            cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) + av_curb_wait - \
                                                Set.assign_reward - elapsed_wait_penalty

        count_subarea = -1
        # for sa_key, k_subArea in area.sub_areas.items():
        for k_subArea in subarea_list:
            count_subarea += 1
            dist_veh_subarea = Distance.dist_manhat_region(j_veh, k_subArea)
            cost_relocate[count_veh][count_subarea] = dist_veh_subarea

    t1 = time.time()

    # initialize auxilliary variables
    y_k = [0 for kk in range(len_subareas)]
    z_k = [0 for kk in range(len_subareas)]

    # Gurobi Model
    gurobi_model = gurobipy.Model("relocate_hyland")
    gurobi_model.setParam('OutputFlag', False)

    # DECISION VARIABLES
    # obj function: cost_assign[i,j]*x_ij[i,j] + cost_relocated[j,k]*r_jk[j,k] + imbalance_penalty*z_k[k]
    for j in range(len_empty_avs):
        for i in range(len_custs):
            x_ij[i][j] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=(cost_assgn[i][j]),
                                       name='x[%s,%s]' % (i, j))

        for k in range(len_subareas):
            r_jk[j][k] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=cost_relocate[j][k],
                                       name='r[%s,%s]' % (j, k))

    for k in range(len_subareas):
        y_k[k] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, lb=-100000.0,  obj=0.0,
                               name='y[%s]' % k)
        # this penalizes leaving an imbalance in a subarea
        z_k[k] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=Set.imbalance_penalty,
                               name='z[%s]' % k)

    gurobi_model.update()

    # constraints

    # Every AV can be assigned to at most one user or one subarea centroid
    for jj in range(len_empty_avs):
        gurobi_model.addConstr(gurobipy.quicksum(x_ij[i][jj] for i in range(len_custs)) +
                         gurobipy.quicksum(r_jk[jj][k] for k in range(len_subareas)) <= 1)

    # Each user can be assigned to at most one AV
    for ii in range(len_custs):
        gurobi_model.addConstr(gurobipy.quicksum(x_ij[ii][j] for j in range(len_empty_avs)) <= 1)

    # I think these next two are redundant
    for jj in range(len_empty_avs):
        gurobi_model.addConstr(gurobipy.quicksum(x_ij[i][jj] for i in range(len_custs)) <= 1)
    for jj in range(len_empty_avs):
        gurobi_model.addConstr(gurobipy.quicksum(r_jk[jj][k] for k in range(len_subareas)) <= 1)

    # this constraint defines the auxiliary variable y_k
    # then it says aux. variable z_k is greater than y_k and 0
    # z_k defines the decision variable that determines the remaining imbalance in each subarea
    for kk in range(len_subareas):
        gurobi_model.addConstr(imbalance_list[kk] - gurobipy.quicksum(r_jk[j][kk] for j in range(len_empty_avs))
                         - Set.min_imbalance == y_k[kk])
        gurobi_model.addConstr(z_k[kk] >= y_k[kk])
        gurobi_model.addConstr(z_k[kk] >= 0)

    gurobi_model.optimize()

    # check if Gurobi finds solution
    # then loop through all AVs and users
    # first check if AV j assigned to user i
    # if it did, then update status of AV and the user
    # second check if AV j assigned to subarea k
    # if it was, then update AV status
    if gurobi_model.status == gurobipy.GRB.Status.OPTIMAL:
        for n_veh in range(len_empty_avs):
            for m_pass in range(len_custs):
                if x_ij[m_pass][n_veh].X == 1:
                    temp_veh_status = "base_assign"
                    win_cust = unassign_cust[m_pass]
                    win_av = empty_avs[n_veh]
                    Vehicle.update_vehicle(t, win_cust, win_av, Regions.SubArea, temp_veh_status)
                    Person.update_person(t, win_cust, win_av)
                    break
            for p_subarea in range(len_subareas):
                if r_jk[n_veh][p_subarea].X == 1:
                    temp_veh_status = "relocate"
                    win_av = empty_avs[n_veh]
                    win_subarea = subarea_list[p_subarea]
                    Vehicle.update_vehicle(t, Person.Person, win_av, win_subarea, temp_veh_status)

    else:
        sys.exit("No Optimal Solution - relocate Hyland")
    # print("Vehicles= ", len_veh, "  Passengers= ", len_pass, "  time=", time.time() - t1)
    return


#############################################################################################################
def assign_idle_w_reward(av_fleet, customers, t):
    # Input:  complete list of AVs, complete list of users, current time

    # get list of idle AVs
    idle_avs = list(j_veh for j_veh in av_fleet if j_veh.status in ("idle", "relocating"))
    len_idle_avs = len(idle_avs)

    # get list of unassigned users
    unassign_cust = list(i_cust for i_cust in customers if i_cust.status == "unassigned")
    len_custs = len(unassign_cust)

    # initialize cost_assign matrix for assigning AVs to users
    cost_assgn = [[0 for jj in range(len_idle_avs)] for ii in range(len_custs)]
    # initialize decision variable for assigning AV j to user i
    x_ij = [[0 for jj in range(len_idle_avs)] for ii in range(len_custs)]

    # Loop through all AV
    # Get AV's remaining curbside time from last drop-off
    # Loop through all users, for each AV
    # Get user's elapsed wait time and wait time penalty
    # fill in values for cost_assign matrix
    count_veh = -1
    for j_veh in idle_avs:
        count_veh += 1
        count_pass = -1
        av_curb_wait = j_veh.curb_time_remain * Set.veh_speed
        for i_pass in unassign_cust:
            count_pass += 1
            cur_wait = t - i_pass.request_time
            elapsed_wait_penalty = cur_wait * Set.veh_speed * 2.0
            # cost = travel distance + remaining curb wait time - reward for assigning Av to user
            # - reward for assigning AV to long waiting user
            cost_assgn[count_pass][count_veh] = Distance.dist_manhat_pick(i_pass, j_veh) + av_curb_wait - \
                                                Set.assign_reward - elapsed_wait_penalty

    # Gurobi Model
    gurobi_model = gurobipy.Model("assign assign_idle_w_reward")
    gurobi_model.setParam('OutputFlag', False)

    # DECISION VARIABLES
    for j in range(len_idle_avs):
        for i in range(len_custs):
            # Multiply cost_assign[i,j] * x[i,j]
            x_ij[i][j] = gurobi_model.addVar(vtype=gurobipy.GRB.CONTINUOUS, obj=(cost_assgn[i][j]),
                                       name='x[%s,%s]' % (i, j))

    gurobi_model.update()

    # CONSTRAINTS

    # Each AV can be assigned to at most one user
    for jj in range(len_idle_avs):
        gurobi_model.addConstr(gurobipy.quicksum(x_ij[i][jj] for i in range(len_custs)) <= 1)

    # # Each user can be served by at most one AV
    for ii in range(len_custs):
        gurobi_model.addConstr(gurobipy.quicksum(x_ij[ii][j] for j in range(len_idle_avs)) <= 1)

    gurobi_model.optimize()

    # check if Gurobi found solution
    # loop through AVs and users
    # determine if veh_j assigned to user_I
    # get the assigned AV and user, and then update their statuses
    if gurobi_model.status == gurobipy.GRB.Status.OPTIMAL:
        for n_veh in range(len_idle_avs):
            for m_pass in range(len_custs):
                if x_ij[m_pass][n_veh].X == 1:
                    temp_veh_status = "base_assign"
                    win_cust = unassign_cust[m_pass]
                    win_av = idle_avs[n_veh]
                    Vehicle.update_vehicle(t, win_cust, win_av, Regions.SubArea, temp_veh_status)
                    Person.update_person(t, win_cust, win_av)
                    break
    else:
        sys.exit("No Optimal Solution - assgn Hyland")
    # print("Vehicles= ", len_veh, "  Passengers= ", len_pass, "  time=", time.time() - t1)
    return
