__author__ = 'Mike'
# This file handles the simulation, for a given set of input values

# Files to import
import csv
import Vehicle
import Person
import Assignment_Algorithm as AA
import numpy
import datetime
import Regions
import Settings as Set


def main(assign_int, assign_method, relocat_int=100, relocate_method="None", date_1="2016-04-01", taxi=False, NYC=False,
         xyt_string="No_Relocation", forecast_f=None, out_statistics=True, visualize=False):

    # xyt string denotes the spatial-temporal resolution of forecasts
    # if there is no forecasts, there is no repositioning
    if xyt_string != "No_Relocation":
        # Initialize
        (sim_year, sim_month, sim_day) = [int(x) for x in date_1.split("-")]
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dater = datetime.date(sim_year, sim_month, sim_day)
        day_number = dater.weekday()
        weekday = week[day_number]

    ##################################################################################################
    # Input Information - Customer Demand
    ##################################################################################################

    # check if taxi data or artificial input data
    if taxi:
        # check if NYC or Chicago taxi data
        (sim_year, sim_month, sim_day) = [int(x) for x in date_1.split("-")]
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dater = datetime.date(sim_year, sim_month, sim_day)

        if NYC:
            file_str = "../Inputs/NYC_Taxi/Request_Data/" + str(dater) + "__manhattan_yellow_taxi_requests.csv"
            # _10percent.csv"  # <-- this is for case where we only want to do 10% of all demand
        else:
            file_str = "../Inputs/Chicago_Taxi/Taxi_Demand_Day" + str(dater) + ".csv"

    else:
        file_str = "../Inputs/Artificial/Demand_Requests.csv"
    demand_file = open(file_str, 'r')

    # read in information about all customers, line-by-line
    demand_reader = csv.reader(demand_file)

    # initialize list of users
    customers = []
    count = 0
    request_rate = 0
    count_first_request_set = 0


    for i_row in demand_reader:
        count += 1
        if count > 1:  # <-- do not read in header row
            person_id = int(i_row[0])
            request_time = int(i_row[1])
            pick_x = float(i_row[2])
            pick_y = float(i_row[3])
            drop_x = float(i_row[4])
            drop_y = float(i_row[5])
            grp_size = int(i_row[6])
            # check to make sure the request is within the demand request analysis period in Settings
            if request_time > Set.first_request_time  and  request_time < Set.last_request_time:
                # create a person object, and store that person object in list of users
                customers.append(Person.make_person(person_id, pick_x, pick_y, request_time, drop_x, drop_y, grp_size))

                if request_time <= Set.first_request_time + Set.statistic_time_interval:
                    count_first_request_set += 1

    request_rate = count_first_request_set / (1.0 * Set.statistic_time_interval)


    ##################################################################################################
    # Input Information - AV Initial Positions
    ##################################################################################################

    # check if taxi data or artificial input data
    if taxi:
        file_str2 = "../Inputs/Artificial/Vehicles_Taxi.csv"
    else:
        file_str2 = "../Inputs/Artificial/Vehicles_Taxi.csv"

    veh_file = open(file_str2, 'r')
    vehicle_reader = csv.reader(veh_file)

    # read in information about all AVs, line-by-line
    av_fleet = []
    cnt = 0
    for j_row in vehicle_reader:
        cnt += 1
        if cnt > 1:
            vehicle_id = int(j_row[0])
            start_x = float(j_row[1])
            start_y = float(j_row[2])
            capacity = int(j_row[3])
            veh_status = "idle"
            # create a vehicle object, and store that vehicle object in list of AVs
            av_fleet.append(Vehicle.make_vehicle(vehicle_id, start_x, start_y, capacity, veh_status))

    ##################################################################################################
    # Input Information - Regions/subAreas
    ##################################################################################################

    # Florian Dandl wrote this part of the code
    ############
    # create a list with all sub_area objects
    # and/or create a list with all subArea-time periods
    # it seems like you might already be reading in the files in Regions, but still need a list of all sub_area objects
    ############
    # Comment FD: the idea is that the main area class does all the work and returns dictionaries for
    # 1) demand forecast
    # 2) vehicle availability
    # with the subarea_key as key of the respective dictionary and the respective quantity as value
    # the respective destination centers can be called by
    # area.sub_areas[subarea_key].relocation_destination
    #
    # read information of area depending on
    # a) xyt_string
    # b) forecast_f [optional, if not given, the value from the forecast model will be read]
    # format of xyt_string: 2x_8y_5min
    # format of xy_string: 2x_8y

    if xyt_string != "No_Relocation":
        xy_string = "_".join(xyt_string.split("_")[:2])
        prediction_csv_file = "../Inputs/NYC_Taxi/Prediction_Data/prediction_areas_{0}.csv".format(xy_string)
        # region_csv_file = "prediction_areas_{0}.csv".format(xy_string)
        if forecast_f:
            region_csv_file = forecast_f
            date_str = date_1
        else:
            region_csv_file = "../Inputs/NYC_Taxi/Prediction_Data/manhattan_trip_patterns_{0}_only_predictions.csv".format(xyt_string)
            date_str = None
        relocation_destination_f = "../Inputs/NYC_Taxi/Prediction_Data/demand_center_points_{0}.csv".format(xy_string)
        area = Regions.Area(region_csv_file, prediction_csv_file, relocation_destination_f, date_str)


    if visualize:
        d = (datetime.datetime.today())
        file_string = '../results_ridehail/' + str(d.year) + '_' + str(d.month) + '_' + str(d.day) + \
                    '_' + str(d.hour) + '_' + str(d.minute) + 'visualize.csv'

        csv_viz = open(file_string, 'w')
        viz_writer = csv.writer(csv_viz, lineterminator='\n', delimiter=',', quotechar='"',
                                     quoting=csv.QUOTE_NONNUMERIC)
        header_list = ["time"]
        temper = ["vehicle_status", "vehicle_position_x", "vehicle_position_y", "vehicle_occupancy"]
        header_list.append(temper)
        viz_writer.writerow(header_list)
        veh_id_list = [-1]
        for jj_veh in av_fleet:
            veh_id_list.append(jj_veh.vehicle_id)

        viz_writer.writerow(veh_id_list)


    if out_statistics:
        if xyt_string == "No_Relocation":
            relocate_method = "No_Repos"
        d = (datetime.datetime.today())
        file_string = '../results_ridehail/' + str(d.year) + '_' + str(d.month) + '_' + str(d.day) + \
                      '_' + str(d.hour) + '_' + str(d.minute) + 'statistics_' + date_1 + str(relocate_method) + '.csv'


        stat_viz = open(file_string, 'w')
        stat_writer = csv.writer(stat_viz, lineterminator='\n', delimiter=',', quotechar='"',
                                quoting=csv.QUOTE_NONNUMERIC)
        # header_list_stat = []

        fleet_size_print = "fleet_size, " + str(len(av_fleet))
        stat_writer.writerow([fleet_size_print])

        header_stat = ["time_step, new_request_rate, users_waiting_for_match, users_waiting_for_pickup, "
                       "users_in_vehicle, idle_fleet, pickup_fleet, drop_off_fleet, repositioning_fleet" ]

        # header_stat = ["time_step", "new_request_rate", "users_waiting_for_match", "users_waiting_for_pickup", "users_in_vehicle",
        #                     "idle_fleet", "pickup_fleet", "drop_off_fleet", "repositioning_fleet" ]
        stat_writer.writerow(header_stat)


    ##################################################################################################
    # Simulation
    ##################################################################################################

    # Initialize Vectors
    i_person = 0
    i_person_old = 0

    # Begin time-driven simulation
    for t in range(Set.start_sim_time, Set.end_sim_time, Set.sim_time_step):

        # For visualization purposes, would want to store vehicle trajectories
        veh_info_list = []
        if visualize and t % Set.trajectory_store_interval == 0 and t < Set.end_trajectory_store:
            veh_info_list.append(t)
            for j_veh in av_fleet:
                veh_info_list.append([j_veh.status, int(j_veh.position_x), int(j_veh.position_y), j_veh.current_load])

            viz_writer.writerow(veh_info_list)

        # display current statuses of AVs and customers
        # this is useful for debugging, but it increases operational speed
        if t % 900 == 0:
            len_idle = len(list(j_veh for j_veh in av_fleet if j_veh.status == "idle"))
            len_relocate = len(list(j_veh for j_veh in av_fleet if j_veh.status == "relocating"))
            len_pick = len(list(j_veh for j_veh in av_fleet if j_veh.status == "enroute_pickup"))
            len_drop = len(list(j_veh for j_veh in av_fleet if j_veh.status == "enroute_dropoff"))
            print("hour: " + str(t/3600) + " idle:" + str(len_idle) + " relocate:" + str(len_relocate)
                + " pick:" + str(len_pick) + " drop:" + str(len_drop))
            len_unassigned = len(list(i for i in customers if i.status == "unassigned"))
            len_assigned = len(list(i for i in customers if i.status == "assigned"))
            len_in_veh = len(list(i for i in customers if i.status == "inVeh"))
            len_served = len(list(i for i in customers if i.status == "served"))
            print("unassigned:" + str(len_unassigned) + " assigned:" + str(len_assigned)
                + " inVeh:" + str(len_in_veh) + " served:" + str(len_served))

        if out_statistics and t % Set.statistic_time_interval == 0:
            len_idle = len(list(j_veh for j_veh in av_fleet if j_veh.status == "idle"))
            len_relocate = len(list(j_veh for j_veh in av_fleet if j_veh.status == "relocating"))
            len_pick = len(list(j_veh for j_veh in av_fleet if j_veh.status == "enroute_pickup"))
            len_drop = len(list(j_veh for j_veh in av_fleet if j_veh.status == "enroute_dropoff"))

            len_unassigned = len(list(i for i in customers if i.status == "unassigned"))
            len_assigned = len(list(i for i in customers if i.status == "assigned"))
            len_in_veh = len(list(i for i in customers if i.status == "inVeh"))
            # len_served = len(list(i for i in customers if i.status == "served"))

            if t == Set.first_request_time:
                stat_writer.writerow([t, request_rate, len_unassigned, len_assigned, len_in_veh,
                                      len_idle, len_pick, len_drop, len_relocate])

            elif t >= Set.start_sim_time + Set.statistic_time_interval:
                request_rate = (i_person - i_person_old) / (1.0 * Set.statistic_time_interval)
                stat_writer.writerow([t, request_rate, len_unassigned, len_assigned, len_in_veh,
                                     len_idle, len_pick, len_drop, len_relocate])


            i_person_old = i_person


        # loop through all AVs in the fleet
        # then move them one step toward their next location
        for j_av in av_fleet:

            ##################################################################################################
            # if AV has remaining wait time at pickup or drop-off location
            # decrease curb time of AV by one time-step (Set.sim_time_step)
            if j_av.curb_time_remain > 0:
                j_av.curb_time_remain -= Set.sim_time_step

            ##################################################################################################
            # move relocating AVs
            elif j_av.status == "relocating":
                # get the AVs next sub_area
                sub_area = j_av.next_sub_area
                # move AV one-step (Set.sim_time_step * Set.veh_speed) toward sub_area centroid
                # if AV then reaches sub_area centroid, the move_vehicle_manhat(...) function with call update_veh(..)
                Vehicle.move_vehicle_manhat(t, j_av, Person.Person, sub_area)

            ##################################################################################################
            # move en_route drop-off AVs
            elif j_av.status == "enroute_dropoff":
                # get the AVs next passenger drop-off
                person_drop = j_av.next_drop
                # move AV one-step (Set.sim_time_step * Set.veh_speed) toward user drop-off location
                # if AV then reaches drop-off location, the move_vehicle_manhat(...) function with call update_veh(..)
                Vehicle.move_vehicle_manhat(t, j_av, person_drop, Regions.SubArea)

                # if AV's status changes, then AV dropped off user, thus user status needs to change
                if j_av.status != "enroute_dropoff":
                    Person.update_person(t, person_drop, j_av)

            ##################################################################################################
            # move en_route pickup AVs
            elif j_av.status == "enroute_pickup":
                # get the AVs next passenger pickup
                person_pick = j_av.next_pickup
                # move AV one-step (Set.sim_time_step * Set.veh_speed) toward user pickup location
                # if AV then reaches pickup location, the move_vehicle_manhat(...) function with call update_veh(..)
                Vehicle.move_vehicle_manhat(t, j_av, person_pick, Regions.SubArea)

                # if AV's status changes, then AV picked up user, thus, user status needs to change
                if j_av.status != "enroute_pickup":
                    Person.update_person(t, person_pick, j_av)

        ##################################################################################################
        # check if there are new user requests, between current time step, and last time step
        if i_person < len(customers):
            while customers[i_person].request_time <= t:
                # get new user request
                i_request = customers[i_person]
                # update status of new user request from "unrequested" to "unassigned"
                Person.update_person(t, i_request, Vehicle.Vehicle)
                i_person += 1
                if i_person == len(customers):
                    break

    ###################################################################################################
    # Assign AVs to customer requests, or subAreas
    ###################################################################################################
        # Get the number of idle AVs and unassigned customers
        count_avail_veh = len(list(j for j in av_fleet
                                   if j.status in ["idle", "enroute_dropoff", "relocating"]
                                   and j.next_pickup.person_id < 0))
        count_unassigned = len(list(i for i in customers if i.status == "unassigned"))

    # Check if assignment is FCFS or optimization-based
    ###################################################################################################
    # Assign using FCFS methods
        if "FCFS" in assign_method:

            # check if repositioning is being done
            if xyt_string == "No_Relocation":  # <-- Assign FCFS, no repositioning
                # check if there is actually any available AVs or unassigned users to assign
                if count_unassigned > 0 and count_avail_veh > 0:
                    # assign using FCFS assign_method. The assign_method is an input to Main(...)
                    AA.assign_veh_fcfs(av_fleet, customers, assign_method, t)

            else:  # Assign FCFS, then reposition
                # check if there are avail AVs, unassigned customers, and it is assignment time
                if t % assign_int == 0 and count_unassigned > 0 and count_avail_veh > 0:
                    if relocate_method != "joint_assign-reposition" or  xyt_string == "No_Relocation":
                        AA.assign_veh_fcfs(av_fleet, customers, assign_method, t)

                # check if there are avail AVs and it is repositioning time
                #if t % relocat_int == 0 and count_avail_veh > 0 and xyt_string != "No_Relocation":
                if t % relocat_int == 0 and count_avail_veh > 0:
                    AA.relocate_veh(av_fleet, customers, area, relocate_method, t, weekday)

    ###################################################################################################
    # Assign using Optimization-based methods
        else:
            # Every X seconds assign customers in the waiting queue to an AV
            if t % assign_int == 0 and count_unassigned > 0 and count_avail_veh > 0:
                if relocate_method != "joint_assign-reposition" or xyt_string == "No_Relocation":
                    AA.assign_veh_opt(av_fleet, customers, assign_method, t)

            if t % relocat_int == 0 and count_avail_veh > 0 and xyt_string != "No_Relocation":
                AA.relocate_veh(av_fleet, customers, area, relocate_method, t, weekday)
                # see comments in 'Assign using FCFS'

    ##################################################################################################
    # Simulation Over
    ##################################################################################################


    ##################################################################################################
    # Customer and AV Results
    ##################################################################################################
    # These two files output information about every user and every AV, respectivey
    # They are useful/necessary for debugging but increase computational time and are not helpful with many scenarios

    # remove edge effects, only count middle X% from Settings file
    start_person = round(Set.metrics_start_person * len(customers))
    end_person = round(Set.metrics_end_person * len(customers))

    metric_people = customers[start_person:end_person]
    # num_metric_people = len(metric_people)

    # These two files output information about every user and every AV, respectivey
    # They are useful/necessary for debugging but increase computational time and are not helpful with many scenarios



    ###### Customer Results ###############
    file_string1 = '../results_ridehail/' + str(d.year) + '_' + str(d.month) + '_' + str(d.day) + \
                  '_' + str(d.hour) + '_' + str(d.minute) + 'travelers_' + date_1 + str(relocate_method) + '.csv'
    csv_traveler = open(file_string1, 'w')
    traveler_writer = csv.writer(csv_traveler, lineterminator='\n', delimiter=',', quotechar='"',
                                 quoting=csv.QUOTE_NONNUMERIC)

    #  Header
    header_traveler = ["person_id", "request_time", "wait_assgn_time","wait_pick_time", "ivtt"]
    traveler_writer.writerow(header_traveler)

    for j_person in customers:
        traveler_writer.writerow([j_person.person_id, j_person.request_time,  j_person.wait_assgn_time,
                                  j_person.wait_pick_time, j_person.travel_time])


    # ####### AV Results ###############
    # file_string2 = '../Results_Rev2/taxi_veh_results'+ '_hold' + str(assign_int) + '_fleet' + str(len(customers)) \
    #                + '_opt' + str(assign_method)  +'.csv'
    # csv_vehicle = open(file_string2, 'w')
    # vehicle_writer = csv.writer(csv_vehicle, lineterminator='\n', delimiter=',', quotechar='"',
    #                             quoting=csv.QUOTE_NONNUMERIC)
    #
    # #  Header
    # vehicle_writer.writerow(["vehicle_id", "distance", "pass_assgn", "pass_pick", "pass_drop",
    #                          "pass_drop_list"])
    #
    # cum_distance = 0
    # for k_vehicle in av_fleet:
    #     cum_distance += k_vehicle.total_distance
    #     vehicle_writer.writerow([k_vehicle.vehicle_id, k_vehicle.total_distance, k_vehicle.pass_assgn_count,
    #                              k_vehicle.pass_pick_count, k_vehicle.pass_drop_count, k_vehicle.pass_dropped_list])
    # if taxi:
    #     cum_distance = cum_distance/1000.0
    #     vehicle_writer.writerow(["cum_distance_km", cum_distance])
    # else:
    #     cum_distance = cum_distance/5280.0
    #     vehicle_writer.writerow(["cum_distance_ft", cum_distance])

    ##################################################################################################
    # Calculate Performance Metrics for Single Simulation
    ##################################################################################################

    # Customer Metrics ###############

    # Incomplete Customers Metrics
    num_served = (list(p.status for p in customers)).count("served")
    num_in_veh = (list(p.status for p in customers)).count("inVeh")
    num_assgnd = (list(p.status for p in customers)).count("assigned")
    num_unassgnd = (list(p.status for p in customers)).count("unassigned")
    print("num_served", num_served)

    perc_reassigned = round(numpy.mean(list(p.reassigned for p in metric_people if p.status == "served")), 2)
    mean_wait_pick = int(numpy.mean(list(p.wait_pick_time for p in metric_people if p.status == "served")))

    # other output metrics
    # sd_wait_pick = int(numpy.std(list(p.wait_pick_time for p in metric_people if p.status == "served")))
    # mean_wait_assgn = int(numpy.mean(list(p.wait_assgn_time for p in metric_people if p.status == "served")))
    # sd_wait_assgn = int(numpy.std(list(p.wait_assgn_time for p in metric_people if p.status == "served")))

    # more of an input parameter than output parameter
    # mean_trip_dist = round(numpy.mean(list(p.in_veh_dist for p in metric_people if p.status == "served"))/5280, 3)
    # sd_trip_dist = round(numpy.std(list(p.in_veh_dist for p in metric_people if p.status == "served"))/5280, 3)

    # AV Metrics ###############
    mean_wait_pick_peak = -1.0

    # taxi data is in meters, whereas artifical data is in feet
    if taxi:
        # check to make sure there is a peak period
        if Set.end_sim_time > Set.peak_start_time and Set.start_sim_time < Set.peak_end_time:
            mean_wait_pick_peak = int(numpy.mean(list(p.wait_pick_time for p in metric_people
                                                      if p.status == "served"
                                                      and p.request_time > Set.peak_start_time
                                                      and p.request_time < Set.peak_end_time)))


        tot_fleet_dist = int(sum(list(v.total_distance for v in av_fleet))/1000.0)  # km
        mean_tot_veh_dist = round(numpy.mean(list(v.total_distance for v in av_fleet))/1000.0, 2)  # km
    
        empty_pick_fleet_dist = int(sum(list(v.empty_pick_distance for v in av_fleet))/1000.0)  # km
        empty_reloc_fleet_dist = int(sum(list(v.empty_reloc_distance for v in av_fleet))/1000.0)  # km

        fleet_hours = ((mean_tot_veh_dist*1000.0)/Set.veh_speed)/3600.0
        
    else:
        if Set.end_sim_time > Set.peak_start_time and Set.start_sim_time < Set.peak_end_time:
            mean_wait_pick_peak = int(numpy.mean(list(p.wait_pick_time for p in metric_people
                                                      if p.status == "served"
                                                      and p.request_time > Set.peak_start_time
                                                      and p.request_time < Set.peak_end_time)))

        tot_fleet_dist = int(sum(list(v.total_distance for v in av_fleet))/5280.0)  # miles
        mean_tot_veh_dist = round(numpy.mean(list(v.total_distance for v in av_fleet))/5280.0, 2)  # miles

        empty_pick_fleet_dist = int(sum(list(v.empty_pick_distance for v in av_fleet))/5280.0)  # miles
        empty_reloc_fleet_dist = int(sum(list(v.empty_reloc_distance for v in av_fleet))/5280.0)  # km

        fleet_hours = ((mean_tot_veh_dist*5280.0)/Set.veh_speed)/3600.0

    perc_empty_pick_dist = round(empty_pick_fleet_dist / float(tot_fleet_dist), 3)
    perc_empty_reloc_dist = round(empty_reloc_fleet_dist / float(tot_fleet_dist), 3)
    fleet_utilization = round(fleet_hours / (Set.sim_length / 3600.0), 2)

    # output vector, containing key metrics
    sim_results = [mean_wait_pick, mean_wait_pick_peak,
                   perc_empty_pick_dist, perc_empty_reloc_dist,
                   perc_reassigned, fleet_utilization,
                   num_served, num_in_veh, num_assgnd, num_unassgnd]

    return sim_results

#[144, 183, 0.223, 0.0, 0.0, 0.46, 321755, 0, 0, 0]