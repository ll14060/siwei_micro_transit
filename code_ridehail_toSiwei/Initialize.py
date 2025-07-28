__author__ = 'Mike'
# File is used to generate demand in the artificial demand case
# File is used to give AVs initial positions

import random
import numpy
import csv
import Settings as Set


def generate_demand(requests_per_hour, max_distance,  demand_type, max_group_size=1):
    simul_len = (Set.sim_length / 3600.0)  # convert seconds to hours
    num_requests = int(simul_len * requests_per_hour)

    my_lambda = Set.sim_length / float(num_requests)

    # get list of exponentially distributed inter-arrival times
    demand_times = numpy.random.exponential(my_lambda, num_requests)
    # convert that list into Poisson distributed list of arrival times
    demand_times = numpy.cumsum(demand_times)

    # get 20% and 80% of corner x- and y- distance of square service regions
    # this is needed if the user origins and/or destinations are 'clustered'
    temp_x = [0.2, 0.2, 0.8, 0.8]
    cluster_x = [x*max_distance for x in temp_x]
    temp_y = [0.2, 0.8, 0.2, 0.8]
    cluster_y = [y*max_distance for y in temp_y]

    demand_file = open('../Inputs/Artificial/Demand_Requests.csv', 'w')
    writer = csv.writer(demand_file, lineterminator='\n', delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(["person_id", "request_time", "start_x", "start_y",  "dropoff_x", "dropoff_y", "group_size"])

    # set minimum trip distance to prevent weird results
    min_allow_dist = 0.8 * 5280.0

    # create user requests and print them to file 'Demand_Requests.csv
    for i in range(num_requests):
        a = i  # <-- user id
        b = int(demand_times[i])  # just take request time from previously generated list

        temp_dist = 0.0

        while temp_dist < min_allow_dist:

            # check if spatial distribution is uniform OD, uniform O-cluster D, or cluster OD
            # c,d,e,f are the origin_x, origin_y, destination_x, and destination_y of the user

            if demand_type == "O_Uniform_D_Uniform":
                c = round(max_distance*random.random(), 4)
                d = round(max_distance*random.random(), 4)
                e = round(max_distance*random.random(), 4)
                f = round(max_distance*random.random(), 4)
                temp_dist = abs(c-e) + abs(d-f)  # need this to make sure greater than min distance

            elif demand_type == "O_Uniform_D_Cluster":
                c = round(max_distance*random.random(), 4)
                d = round(max_distance*random.random(), 4)

                # get one of four cluster points
                drop_select = random.randint(0, 3)

                # with cluster point, draw from random normal around cluster ceter
                e = cluster_x[drop_select] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                # make sure the point is in the actual service region and not negative  <-- probably can remove this
                while e < 0:
                    e = cluster_x[drop_select] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)

                f = cluster_y[drop_select] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                while f < 0:
                    f = cluster_y[drop_select] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)

                temp_dist = abs(c-e) + abs(d-f)

            elif demand_type == "O_Cluster_D_Cluster":
                origin = random.randint(0, 3)
                dest = random.randint(0, 3)
                while origin == dest:
                    origin = random.randint(0, 3)
                    dest = random.randint(0, 3)

                c = cluster_x[origin] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                while c < 0:
                    c = cluster_x[origin] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                d = cluster_y[origin] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                while d < 0:
                    d = cluster_y[origin] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)

                e = cluster_x[dest] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                while e < 0:
                    e = cluster_x[dest] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                f = cluster_y[dest] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                while f < 0:
                    f = cluster_y[dest] + round(numpy.random.normal(0, 0.05*max_distance, 1)[0], 4)
                temp_dist = abs(c-e) + abs(d-f)
            else:
                print("Error: Need Demand Distribution")

        g = random.randint(1, max_group_size)
        row = [a, b, c, d, e, f, g]
        # print to file ["person_id", "request_time", "start_x", "start_y",  "dropoff_x", "dropoff_y", "group_size"]
        writer.writerow(row)
    demand_file.close()
    return


# function to generate AVs initial locations
def generate_fleet(num_avs, NYC=False, max_distance=0.0):
    csv_av_file = open('../Inputs/Artificial/Vehicles_Taxi.csv', 'w')
    writer = csv.writer(csv_av_file, lineterminator='\n', delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(["vehicle_id", "start_x", "start_y", "capacity"])

    # temp_x = [0.2, 0.2, 0.7, 0.7]
    # cluster_x = [xx*max_distance for xx in temp_x]
    # temp_y = [0.2, 0.7, 0.2, 0.7]
    # cluster_y = [yy*max_distance for yy in temp_y]

    # hard code location of taxi for Manhattan NYC case
    if NYC:
        for my_id in range(num_avs):
            x = 1541.0
            y = 6802.0
            cap = Set.veh_capacity
            rw = [my_id, x, y, cap]
            writer.writerow(rw)
    # for all other cases, just put them in the middle of the service region
    else:
        for my_id in range(num_avs):
            x = 0.5 * max_distance
            y = 0.5 * max_distance
            cap = Set.veh_capacity
            rw = [my_id, x, y, cap]
            writer.writerow(rw)

    csv_av_file.close()
    return
