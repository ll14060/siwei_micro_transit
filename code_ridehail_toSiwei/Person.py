__author__ = 'Mike'
# This file defines the 'Person' Class and Object


class Person(object):
    # These are all the variables associated with a Person object

    # Fixed input parameters <-- read in from file
    person_id = -1
    pickup_location_x = -1.0
    pickup_location_y = -1.0
    request_time = -1
    dropoff_location_x = -1.0
    dropoff_location_y = -1.0
    group_size = -1
    in_veh_dist = -1  # <-- calculated based on input pickup and drop-off locations

    # Dynamically updating variables
    assign_time = -3
    pickup_time = -3
    dropoff_time = -3
    wait_assgn_time = -3
    wait_pick_time = -3
    travel_time = -3
    vehicle_id = -3
    old_vehicles = []
    status = "un_requested"
    reassigned = 0

    # The class "constructor" - It's actually an initializer
    def __init__(self, person_id, pick_spot_x, pick_spot_y, request_time, drop_spot_x, drop_spot_y, group_size):
        self.person_id = person_id
        self.pickup_location_x = pick_spot_x
        self.pickup_location_y = pick_spot_y
        self.request_time = request_time
        self.dropoff_location_x = drop_spot_x
        self.dropoff_location_y = drop_spot_y
        self.group_size = group_size
        self.in_veh_dist = abs(pick_spot_x - drop_spot_x) + abs(pick_spot_y - drop_spot_y)


# Call this function to create a person
def make_person(person_id, pick_spot_x, pick_spot_y, request_time, drop_spot_x, drop_spot_y, group_size):
    person_a = Person(person_id, pick_spot_x, pick_spot_y, request_time, drop_spot_x, drop_spot_y, group_size)
    return person_a


def get_wait_assgn_time(request_time, assgn_time):
    wait_assgn_time = assgn_time - request_time
    return wait_assgn_time


def get_wait_pick_time(request_time, pickup_time):
    wait_pick_time = pickup_time - request_time
    return wait_pick_time


def get_travel_time(pickup_time, dropoff_time):
    travel_time = dropoff_time - pickup_time
    return travel_time


def made_request():
    status = "unassigned"
    return status


def status_assigned():
    status = "assigned"
    return status


def status_in_veh():
    status = "inVeh"
    return status


def status_served():
    status = "served"
    return status


# This function updates a person status
def update_person(t, person_1, vehicle1):

    # Person currently
    # 1. has not made request yet -- "un_requested"
    # 2. has made a request, but has not been assigned to an AV -- "unassigned"
    # 3. has been assigned to an AV, but has not been picked up yet -- "assigned"
    # 4. has been reassigned to AV Y, after very recently beeing assigned to AV X -- "reassigned"
    # 5. has been picked up and is in an AV -- "inVeh"

    # When update_person is called, we know their status needs to be updated
    # "un_requested" to "unassigned"
    # "unassigned" to "assigned"
    # "assigned" to "inVeh"
    # "reassigned" to "assigned"
    # "inVeh" to "served"

    if person_1.status == "un_requested":
        # change Person status
        person_1.status = made_request()
    
    elif person_1.status == "unassigned":
        # change Person status
        person_1.status = status_assigned()
        # store the AV currently associated with person
        person_1.vehicle_id = vehicle1.vehicle_id
        # append this vehicle to list of vehicles formerly associated with person <-- for case of reassignment
        person_1.old_vehicles.append(vehicle1.vehicle_id)
        # store time of assignment
        person_1.assign_time = t
        # store how long person waited to be assigned <-- needed for output data
        person_1.wait_assgn_time = get_wait_assgn_time(person_1.request_time, person_1.assign_time)
        
    elif person_1.status == "assigned":
        # change Person status
        person_1.status = status_in_veh()
        # store the AV currently associated with person
        person_1.vehicle_id = vehicle1.vehicle_id
        # store time of pickup
        person_1.pickup_time = t
        # store how long person waited to be picked up <-- needed for output data
        person_1.wait_pick_time = get_wait_pick_time(person_1.request_time, person_1.pickup_time)

    elif person_1.status == "reassign":
        # change Person status
        person_1.status = status_assigned()
        # store the AV currently associated with person
        person_1.vehicle_id = vehicle1.vehicle_id
        # append this vehicle to list of vehicles formerly associated with person
        person_1.old_vehicles.append(vehicle1.vehicle_id)
        # add 1 to number of times person has been reassigned
        person_1.reassigned += 1

    elif person_1.status == "inVeh":
        # change Person status
        person_1.status = status_served()
        # store time of drop-off
        person_1.dropoff_time = t
        # store how long person took to travel from pick to drop <-- needed for output data
        person_1.travel_time = get_travel_time(person_1.pickup_time, person_1.dropoff_time)

    return person_1
