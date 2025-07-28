__author__ = 'Mike'
# this file calculates the distance between two points for various different cases
# euclidean or  manhattan distance
# vehicle to pickup location, drop-off location, or subarea centroid
# vehicle to drop-off user A then pickup user B
import math


def dist_euclid(person, vehicle):
    x_pass = person.pickup_location_x
    y_pass = person.pickup_location_y
    x_veh = vehicle.position_x
    y_veh = vehicle.position_y
    dist_euclid1 = math.sqrt((x_veh - x_pass) ** 2 + (y_veh - y_pass) ** 2)

    return dist_euclid1


def dist_manhat_pick(person, vehicle):
    x_pass = person.pickup_location_x
    y_pass = person.pickup_location_y
    x_veh = vehicle.position_x
    y_veh = vehicle.position_y
    dist_manhat1 = abs(x_veh - x_pass) + abs(y_veh - y_pass)

    return dist_manhat1


def dist_manhat_region(vehicle, subArea):
    x_veh = vehicle.position_x
    y_veh = vehicle.position_y
    (x_sa, y_sa) = subArea.relocation_destination
    dist_manhat_r = abs(x_sa - x_veh) + abs(y_sa - y_veh)

    return dist_manhat_r


def dist_manhat_drop_pick(person, vehicle):
    # distance from AVs location to drop off current user ('vehicle.next_drop') then pick up next user (i.e. 'person')
    x_veh = vehicle.position_x
    y_veh = vehicle.position_y
    x_drop1 = vehicle.next_drop.dropoff_location_x
    y_drop1 = vehicle.next_drop.dropoff_location_y
    dist_manhat1 = abs(x_drop1 - x_veh) + abs(y_drop1 - y_veh)

    x_pick2 = person.pickup_location_x
    y_pick2 = person.pickup_location_y
    dist_manhat2 = abs(x_pick2 - x_drop1) + abs(y_pick2 - y_drop1)

    tot_dist = dist_manhat1 + dist_manhat2

    return tot_dist
