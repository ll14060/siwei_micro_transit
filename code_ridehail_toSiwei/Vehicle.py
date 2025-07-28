__author__ = 'Mike'
# This file defines the 'Vehicle' Class and Object

# Import relevant files
import Settings
import Person
import sys
import Regions


class Vehicle(object):
    # These are all the variables associated with a Vehicle object

    # static input parameters
    vehicle_id = -5
    start_location_x = -1.0
    start_location_y = -1.0
    capacity = -1

    # dynamic variables updated in simulation, needed to make decisions
    current_load = 0
    position_x = start_location_x
    position_y = start_location_y
    current_dest_x = -1.0
    current_dest_y = -1.0
    next_pickup = Person.Person
    next_drop = Person.Person
    next_sub_area = Regions.SubArea
    status = "idle"
    reassigned = 0
    curb_time_remain = 0
    last_drop_time = 0

    # output information - update throughout simulation
    total_distance = 0.0
    empty_pick_distance = 0.0
    empty_reloc_distance = 0.0
    loaded_distance = 0.0
    pass_assgn_list = []
    pass_picked_list = []
    pass_dropped_list = []
    assigned_times = []
    pickup_times = []
    dropoff_times = []
    pass_assgn_count = 0
    pass_pick_count = 0
    pass_drop_count = 0
    reposition_count = 0

    # The class "constructor" - It's actually an initializer
    def __init__(self, vehicle_id, start_location_x, start_location_y, capacity, status):
        # static input features
        self.vehicle_id = vehicle_id
        self.start_location_x = start_location_x
        self.start_location_y = start_location_y
        self.capacity = capacity

        # dynamic information needed for simulation
        self.status = status
        self.position_x = start_location_x
        self.position_y = start_location_y


##############################################################################
# function to create an instance of class/object vehicle
def make_vehicle(vehicle_id, start_location_x, start_location_y, capacity, status):
    vehicle1 = Vehicle(vehicle_id, start_location_x, start_location_y, capacity, status)
    return vehicle1
##############################################################################


##############################################################################
# Function to move vehicle every time step
def move_vehicle_manhat(t, vehicle, person, sub_area):

    # if vehicle status is 'relocating' then move it one step (veh speed x time step) toward sub_area centroid
    # if vehicle status is 'enroute_pickup' then move it one step toward passenger'spickup location
    # if vehicle status is 'enroute_dropoff' then move it one step toward passenger's drop-off location

    if vehicle.status == "relocating":
        # get x- and y- coordinates of subarea centroid
        dest_x = sub_area.relocation_destination[0]
        dest_y = sub_area.relocation_destination[1]
        # keep track of vehicle's empty relocation miles
        vehicle.empty_reloc_distance += Settings.delta_veh_dist

    elif vehicle.status == "enroute_pickup":
        # get x- and y- coordinates of passenger's pickup location
        dest_x = person.pickup_location_x
        dest_y = person.pickup_location_y

        # this is for the shared-ride case <-- not relevant for ridehail
        if vehicle.current_load > 0:
            # keep track of vehicle's loaded distance
            vehicle.loaded_distance += Settings.delta_veh_dist
        else:
            # keep track of vehicle's empty pickup distance <-- separate from empty relocation distance
            vehicle.empty_pick_distance += Settings.delta_veh_dist

    elif vehicle.status == "enroute_dropoff":
        # get x- and y- coordinates of passenger's drop-off location
        dest_x = person.dropoff_location_x
        dest_y = person.dropoff_location_y
        # keep track of vehicle's loaded distance
        vehicle.loaded_distance += Settings.delta_veh_dist

    else:
        sys.exit("Error in moveVehicle_manhat - wrong vehicle status")

    # # check for bugs - keep in code  <-- this requires all locations to have positive x- and y- coordinates
    # if dest_x < 0.0 or dest_y < 0.0:
    #     print(dest_x, dest_y)
    #     sys.exit("Error in moveVehicle_manhat - improper vehicle-person match")

    # above, we got location of where vehicle is going
    # now, we want vehicle's current location
    veh_x = vehicle.position_x
    veh_y = vehicle.position_y
    # calculate manhattan distance between vehicle's current location, and its next location
    dist_x = abs(dest_x - veh_x)
    dist_y = abs(dest_y - veh_y)
    total_dist_manhat = dist_x + dist_y

    # Now we want to check if the vehicle is at it's next location
    # If it is, then we want to update it's status, and also move it to it's destination
    # If it is not, then we want to move it one step toward it's destination

    # if the vehicle is right next to the pickup/dropoff point
    # then we need to update the status of the vehicle by calling 'update_vehicle(...)
    if total_dist_manhat < Settings.delta_veh_dist:
        temp_veh_status = "at_destination"  # update_vehicle(...) is complicated, the temp_veh_status helps
        update_vehicle(t, person, vehicle, sub_area, temp_veh_status)
        # update the total distance traveled by the vehicles
        vehicle.total_distance += total_dist_manhat

    else:
        # move vehicle one step closer to destination
        # do so in way that is proportional to remaining x- and y- distance in Manhattan plane
        proportion_x = dist_x / (dist_x + dist_y)
        proportion_y = dist_y / (dist_x + dist_y)

        # these if-else conditions just make sure the vehicle moves in the correct +/- direction
        if veh_x < dest_x:
            vehicle.position_x += proportion_x * Settings.delta_veh_dist
        else:
            vehicle.position_x += -1 * proportion_x * Settings.delta_veh_dist

        if veh_y < dest_y:
            vehicle.position_y += proportion_y * Settings.delta_veh_dist
        else:
            vehicle.position_y += -1 * proportion_y * Settings.delta_veh_dist

        # update the total distance traveled by the vehicles
        vehicle.total_distance += Settings.delta_veh_dist

    return vehicle
##############################################################################

# Not relevant for the ride-hail case, only for shared-ride case
##############################################################################
# if more than one traveler demand request in vehicle - decide which demand to drop off first
# def get_next_drop(vehicle):
#     min_dist = 10000000000
#     for i_pass in vehicle.pass_inVeh:
#         dist = abs(vehicle.position_x - i_pass.dropoff_location_x) \
#                + abs(vehicle.position_y - i_pass.dropoff_location_y)
#         if dist < min_dist:
#             min_dist = dist
#             Win_Pass = i_pass
#     return Win_Pass
##############################################################################


##############################################################################
# this function is to determine when an AV will next be available to be assigned to an open user request
# needed for the case where repositioning is considered
# returns position after last drop-off point and remaining distance to last drop-off point
def get_next_availability(vehicle):
    # initialize output variables
    # if vehicle.status is 'idle' or 'relocating',
    # then the the remaining distance is 0
    # and position of availability is the vehicle's current position
    total_rem_dist = 0
    last_x = vehicle.position_x
    last_y = vehicle.position_y

    # if vehicle.status is 'enroute_pickup', then need to determine the remaining distance to pick up user...
    # and distance between user's pickup location and drop-off location
    # position of availability is at the user's drop-off location
    if vehicle.status == "enroute_pickup":
        i_pick = vehicle.next_pickup
        total_rem_dist += abs(vehicle.position_x - i_pick.pickup_location_x) \
                          + abs(vehicle.position_y - i_pick.pickup_location_y)
        total_rem_dist += abs(i_pick.dropoff_location_x - i_pick.pickup_location_x) \
                          + abs(i_pick.dropoff_location_y - i_pick.pickup_location_y)
        last_x = i_pick.dropoff_location_x
        last_y = i_pick.dropoff_location_y

    # if vehicle.status is 'enroute_dropoff', then there are two separate cases to consider
    # case 1: the vehicle is already assigned to another user
    # in this case, need remaining drop-off distance, plus pickup distance, plus second drop-off distance
    # case 2: the vehicle is not assigned to a next user
    # in this case, only need remaining drop-off distance
    elif vehicle.status == "enroute_dropoff":
        i_pass = vehicle.next_drop
        total_rem_dist += abs(vehicle.position_x - i_pass.dropoff_location_x) \
                          + abs(vehicle.position_y - i_pass.dropoff_location_y)
        if vehicle.next_pickup.person_id >= 0:
            i_pick2 = vehicle.next_pickup
            total_rem_dist += abs(i_pass.dropoff_location_x - i_pick2.pickup_location_x) \
                              + abs(i_pass.dropoff_location_y - i_pick2.pickup_location_y)
            total_rem_dist += abs(i_pick2.dropoff_location_x - i_pick2.pickup_location_x) \
                              + abs(i_pick2.dropoff_location_y - i_pick2.pickup_location_y)
            last_x = i_pick2.dropoff_location_x
            last_y = i_pick2.dropoff_location_y
        else:
            last_x = i_pass.dropoff_location_x
            last_y = i_pass.dropoff_location_y

    return last_x, last_y, total_rem_dist
##############################################################################

##############################################################################
# # Flo code: more general - works for shared-ride case
#
#     # inVeh (drop off order according to logic from get_next_drop)
#     tmp_list_pass_inVeh = vehicle.pass_inVeh[:]
#     while len(tmp_list_pass_inVeh) > 0:
#         min_dist = 10000000000
#         for i_pass in vehicle.pass_inVeh:
#             dist = abs(last_x - i_pass.dropoff_location_x) + abs(last_y - i_pass.dropoff_location_y)
#             if dist < min_dist:
#                 min_dist = dist
#                 Win_Pass = i_pass
#         last_x = Win_Pass.dropoff_location_x
#         last_y = Win_Pass.dropoff_location_y
#         total_rem_dist += min_dist
#         tmp_list_pass_inVeh.remove(Win_Pass)
#     # toPickup (assumption: list is already sorted)
#     for w_pass in vehicle.pass_toPickup:
#         q_dist = abs(last_x - w_pass.dropoff_location_x) + abs(last_y - w_pass.dropoff_location_y)
#         last_x = w_pass.dropoff_location_x
#         last_y = w_pass.dropoff_location_y
#         total_rem_dist += min_dist
#     return (last_x, last_y, total_rem_dist)
##############################################################################


##############################################################################
# function updates the status of AV
def update_vehicle(t, person1, vehicle, sub_area, temp_veh_status):

    # Vehicle
    # 1. now just got to destination (pickup. drop-off, or centroid) location -- "at_destination"
    # 2. now just told to pickup a user, after being idle -- "base_assign"
    # 3. is en-route to drop-off user and now just given next user to pickup - "new_assign"
    # 4. now just re-assigned to user Y, after was just previously assigned to user X-- "reassign"
    # 5. now not assigned to any user, after being assigned to pickup a user  -- "unassign"
    # 6. now told to relocate to a subarea centroid -- "relocate"

    # There are a bunch of different combinations of old status to new status, depending on many factors
    # The logic here should capture all combinations for the ride-hail case

    # Option 1
    if temp_veh_status == "at_destination":

        # Option 1a - AV reached pickup location
        if vehicle.status == "enroute_pickup":
            # dynamic information
            vehicle.current_load += person1.group_size
            vehicle.position_x = person1.pickup_location_x
            vehicle.position_y = person1.pickup_location_y
            vehicle.current_dest_x = person1.dropoff_location_x
            vehicle.current_dest_y = person1.dropoff_location_y
            vehicle.next_pickup = Person.Person
            vehicle.next_drop = person1
            vehicle.next_sub_area = Regions.SubArea
            vehicle.status = "enroute_dropoff"
            vehicle.reassigned = 0
            vehicle.curb_time_remain = Settings.curb_pick_time

            # output information
            vehicle.pass_picked_list.append(person1.person_id)
            vehicle.pickup_times.append(t)
            vehicle.pass_pick_count += 1

        # Option 1b - AV reached drop-off location
        elif vehicle.status == "enroute_dropoff":
            # dynamic information
            vehicle.current_load = vehicle.current_load - person1.group_size
            vehicle.position_x = person1.dropoff_location_x
            vehicle.position_y = person1.dropoff_location_y
            vehicle.curb_time_remain = Settings.curb_drop_time
            vehicle.next_drop = Person.Person
            vehicle.next_sub_area = Regions.SubArea
            vehicle.last_drop_time = t

            # Option 1b,i
            # after drop-off, AV has next traveler to pick up
            if vehicle.next_pickup.person_id >= 0:
                # dynamic information cont.
                vehicle.current_dest_x = vehicle.next_pickup.pickup_location_x
                vehicle.current_dest_y = vehicle.next_pickup.pickup_location_y
                # vehicle.next_pickup = vehicle.next_pickup
                vehicle.status = "enroute_pickup"

            # Option 1b,ii
            # after drop-off, vehicle is now idle
            else:
                # dynamic information cont.
                vehicle.current_dest_x = vehicle.position_x
                vehicle.current_dest_y = vehicle.position_y
                vehicle.next_pickup = Person.Person
                vehicle.status = "idle"

            # output information
            vehicle.pass_dropped_list.append(person1.person_id)
            vehicle.dropoff_times.append(t)
            vehicle.pass_drop_count += 1

        # Option 1c - AV reached relocation centroid
        elif vehicle.status == "relocating":
            # dynamic information
            vehicle.position_x = sub_area.relocation_destination[0]
            vehicle.position_y = sub_area.relocation_destination[1]
            vehicle.next_sub_area = Regions.Area
            vehicle.status = "idle"

            # output information
            vehicle.reposition_count += 1

        else:
            sys.exit("At Destination, no proper Vehicle Status")

    # Option 2 - idle AV assigned to pickup a traveler, after being idle
    elif temp_veh_status == "base_assign":

        # dynamic information
        vehicle.current_dest_x = person1.pickup_location_x
        vehicle.current_dest_y = person1.pickup_location_y
        vehicle.next_pickup = person1
        vehicle.next_drop = Person.Person
        vehicle.next_sub_area = Regions.SubArea
        vehicle.status = "enroute_pickup"
        vehicle.reassigned = 0
        vehicle.curb_time_remain = 0

        # output information
        vehicle.pass_assgn_list.append(person1.person_id)
        vehicle.assigned_times.append(t)
        vehicle.pass_assgn_count += 1

    # Option 3 - En-route Drop-off AV assigned to its next pickup
    elif temp_veh_status == "new_assign":
        # dynamic information
        vehicle.next_pickup = person1
        vehicle.next_sub_area = Regions.SubArea
        # current load, position_x/y, current_dest_x/y, next_drop, status, reassigned, curb_remain_time - do not change

        # output information
        vehicle.pass_assgn_list.append(person1.person_id)
        vehicle.assigned_times.append(t)
        vehicle.pass_assgn_count += 1

    # Option 4 - AV reassigned from one traveler to another
    elif temp_veh_status == "reassign":

        # dynamic information
        vehicle.current_dest_x = person1.pickup_location_x
        vehicle.current_dest_y = person1.pickup_location_y
        vehicle.next_pickup = person1
        vehicle.next_sub_area = Regions.SubArea
        vehicle.status = "enroute_pickup"
        vehicle.reassigned = 1
        # current load, position_x/y, next_drop, status, curb_remain_time - do not change

        # output information
        vehicle.pass_assgn_list.append(person1.person_id)
        vehicle.assigned_times.append(t)
        vehicle.pass_assgn_count += 1

    # Option 5 - AV was assigned to a traveler, but no longer assigned to any traveler
    elif temp_veh_status == "unassign":

        # dynamic information
        vehicle.next_pickup = Person.Person
        vehicle.next_sub_area = Regions.SubArea
        if vehicle.next_drop.person_id < 0:
            vehicle.status = "idle"
            vehicle.current_dest_x = vehicle.position_x
            vehicle.current_dest_y = vehicle.position_y
        # current load, position_x/y, next_drop, status, reassigned, curb_remain_time - do not change

    # Option 6 - AV was assigned to relocate/reposition to a different subArea
    elif temp_veh_status == "relocate":

        # dynamic information
        vehicle.current_load = 0
        vehicle.current_dest_x = sub_area.relocation_destination[0]
        vehicle.current_dest_y = sub_area.relocation_destination[1]
        vehicle.next_pickup = Person.Person
        vehicle.next_drop = Person.Person
        vehicle.next_sub_area = sub_area
        vehicle.status = "relocating"
        vehicle.reassigned = 0

        # output information
        vehicle.reposition_count += 1

    else:
        sys.exit("update Vehicle - no Proper Vehicle Status")
