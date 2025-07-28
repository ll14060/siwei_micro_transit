from collections import OrderedDict
import os
import csv
import get_microtransit_skims as mt

from csv import reader, writer
import io
import pandas as pd

def copy_csv(filename,iteration):
    indiv_output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/indiv_output_folder"
    df = pd.read_csv(filename)
    output_file_dic=new_path=os.path.join(indiv_output_folder,'iter_%s_1_user-stats.csv' % str(iteration))
    df.to_csv(output_file_dic,index=False)


# def copy_csv(csv_string,iteration):
#     indiv_output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/indiv_output_folder"
#     # Fleetpy_output_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/FleetPy_output/"
#     # Fleetpy_user_stats = os.path.join(Fleetpy_output_folder, "1_user-stats.csv")
#     new_path=os.path.join(indiv_output_folder,'iter_%s_1_user-stats.csv' % str(iteration))
#     with io.StringIO(csv_string) as csv_in, open (new_path,'w+', newline='') as out_csv:
#         csv_reader = reader(csv_in)
#         csv_writer = writer(out_csv)
#         for row in csv_reader:
#             csv_writer.writerow(row)

def update_network_files(repositioning,microtransit,headway,virstop,M_operating_hrs,fleet_size,study_area,dt_sd_full_trnst_ntwk,zonal_partition,iteration=False,iteration_debug=False,aggregation="census_track",TRPartA=False,BayesianOptimization=False):
    # path_all_

    from itertools import islice

    # Read FleetPy's output into choice model

    census_tract_tt_wait_time = OrderedDict()
    census_tract_num_rq = OrderedDict()
    census_tract_avg_wait_time = OrderedDict()

    # model rejection rate from time of day and census tract level
    census_tract_rq_served_num = OrderedDict()
    census_tract_rq_reject_num = OrderedDict()
    census_tract_reject_rate = OrderedDict()

    time_tt_drive_time = OrderedDict()
    time_tt_direct_time = OrderedDict()
    time_detour_ratio = OrderedDict()

    demand_period = OrderedDict()
    rq_served_period = OrderedDict()
    tt_wait_time_period = OrderedDict()

    # "AM"=5-10AM
    # "MD"=10-15
    # "PM"=15-20
    # "EV"=20-24

    census_tract_node, node_census_tract = mt.get_node_ct(study_area)
    print("census_tract_node", len(census_tract_node))
    print("node_census_tract", len(node_census_tract))

    if iteration_debug==True:
        num_of_nodes_walking_network=len(node_census_tract)

    for time_period in ["AM", "MD", "PM", "EV"]:
        census_tract_tt_wait_time[time_period] = OrderedDict()
        census_tract_num_rq[time_period] = OrderedDict()
        census_tract_avg_wait_time[time_period] = OrderedDict()
        time_tt_drive_time[time_period] = 0
        time_tt_direct_time[time_period] = 0
        time_detour_ratio[time_period] = 0
        demand_period[time_period] = 0
        rq_served_period[time_period] = 0
        tt_wait_time_period[time_period] = 0

        # model the rejection probability in each census tract
        census_tract_rq_served_num[time_period] = OrderedDict()
        census_tract_rq_reject_num[time_period] = OrderedDict()
        census_tract_reject_rate[time_period] = OrderedDict()

        for census_tract in census_tract_node.keys():
            census_tract_tt_wait_time[time_period][census_tract] = 0
            census_tract_num_rq[time_period][census_tract] = 0
            census_tract_avg_wait_time[time_period][census_tract] = 0
            # model the rejection probability in each census tract
            census_tract_rq_served_num[time_period][census_tract] = 0
            census_tract_rq_reject_num[time_period][census_tract] = 0
            census_tract_reject_rate[time_period][census_tract] = 0

    # D:\Siwei_Micro_Transit\FleetPy_SanDiego\studies\example_study\results\example_pool_irsonly_sc_1
    # D:\Siwei_Micro_Transit\Data\0719_input\FleetPy_output
    if repositioning==True:
        Fleetpy_output_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/studies/example_study/results/example_pool_repo_AM_sc_1"
    else:
        Fleetpy_output_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/studies/example_study/results/example_pool_irsonly_sc_1"
    # Fleetpy_output_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/FleetPy_output/"
    Fleetpy_user_stats = os.path.join(Fleetpy_output_folder, "1_user-stats.csv")

    copy_csv(Fleetpy_user_stats, iteration)
    # lines_number=10
    # i=0
    num_rq_served = 0
    with open(Fleetpy_user_stats) as f:
        #     head = list(islice(f, lines_number))# read the first 10 lines for now
        #     csvreader = csv.DictReader(head)

        csvreader = csv.DictReader(f)
        for data in csvreader:
            #         print("line:",i)
            #             print(data)
            rq_time = int(float(data["rq_time"]))
            #         request_id=float(data["start"])
            start_node = data["start"]
            start_node = int(start_node.split(';')[0])
            end_node = data["end"]
            end_node = int(end_node.split(';')[0])
            direct_route_travel_time = float(data["direct_route_travel_time"])
            direct_route_distance = float(data["direct_route_distance"])
            offers = data["offers"]
            if len(offers) > 2:
                num_rq_served += 1
                #             wait_time=offers.split(';')[0]
                #             wait_time=wait_time.split(':')[2]
                #             wait_time_=float(wait_time)

                try:
                    wait_time = offers.split(';')[0]
                    wait_time = wait_time.split(':')[2]
                    wait_time_ = float(wait_time)
                except Exception as e:
                    print("offers:", offers, "len of offers", len(offers), "\t", "wait time:", wait_time, "\t",
                          "wait_time_", wait_time_)
                    raise e

                drive_time = offers.split(';')[1]
                drive_time = drive_time.split(':')[1]
                drive_time_ = float(drive_time)

                fare = offers.split(';')[2]
                fare = fare.split(':')[1]
                fare_ = float(fare)

                #         print("rq_time","start_node","end_node","direct_route_travel_time","direct_route_distance","offers","wait_time","drive_time","fare")
                #         print(rq_time,start_node,end_node,direct_route_travel_time,direct_route_distance,"\t",offers,"\t",wait_time,drive_time,fare,"\n")
                #         i+=1

                ########################################################
                # Calculate the average waiting time by census tract
                #######################################################
                start_node_ct = node_census_tract[start_node]

                if rq_time <= (10 * 3600):
                    time_period = "AM"
                    rq_served_period[time_period] += 1
                    tt_wait_time_period[time_period] += wait_time_

                    census_tract_tt_wait_time[time_period][start_node_ct] += wait_time_
                    census_tract_num_rq[time_period][start_node_ct] += 1
                    # model rejection rate
                    census_tract_rq_served_num[time_period][start_node_ct] += 1
                elif rq_time <= (15 * 3600):
                    time_period = "MD"
                    rq_served_period[time_period] += 1
                    tt_wait_time_period[time_period] += wait_time_
                    census_tract_tt_wait_time[time_period][start_node_ct] += wait_time_
                    census_tract_num_rq[time_period][start_node_ct] += 1
                    # model rejection rate
                    census_tract_rq_served_num[time_period][start_node_ct] += 1
                elif rq_time <= (20 * 3600):
                    time_period = "PM"
                    rq_served_period[time_period] += 1
                    tt_wait_time_period[time_period] += wait_time_
                    census_tract_tt_wait_time[time_period][start_node_ct] += wait_time_
                    census_tract_num_rq[time_period][start_node_ct] += 1
                    # model rejection rate
                    census_tract_rq_served_num[time_period][start_node_ct] += 1
                else:
                    time_period = "EV"
                    rq_served_period[time_period] += 1
                    tt_wait_time_period[time_period] += wait_time_
                    census_tract_tt_wait_time[time_period][start_node_ct] += wait_time_
                    census_tract_num_rq[time_period][start_node_ct] += 1
                    # model rejection rate
                    census_tract_rq_served_num[time_period][start_node_ct] += 1

                ########################################################
                # Calculate the average time detour ratio by time of day
                #######################################################
                start_node_ct = node_census_tract[start_node]
                if rq_time <= (10 * 3600):
                    time_period = "AM"
                    time_tt_drive_time[time_period] += drive_time_
                    time_tt_direct_time[time_period] += direct_route_travel_time

                elif rq_time <= (15 * 3600):
                    time_period = "MD"
                    time_tt_drive_time[time_period] += drive_time_
                    time_tt_direct_time[time_period] += direct_route_travel_time
                elif rq_time <= (20 * 3600):
                    time_period = "PM"
                    time_tt_drive_time[time_period] += drive_time_
                    time_tt_direct_time[time_period] += direct_route_travel_time
                else:
                    time_period = "EV"
                    time_tt_drive_time[time_period] += drive_time_
                    time_tt_direct_time[time_period] += direct_route_travel_time
            else:
                start_node_ct = node_census_tract[start_node]
                if rq_time <= (10 * 3600):
                    time_period = "AM"
                    # model rejection rate
                    census_tract_rq_reject_num[time_period][start_node_ct] += 1
                elif rq_time <= (15 * 3600):
                    time_period = "MD"
                    # model rejection rate
                    census_tract_rq_reject_num[time_period][start_node_ct] += 1
                elif rq_time <= (20 * 3600):
                    time_period = "PM"
                    # model rejection rate
                    census_tract_rq_reject_num[time_period][start_node_ct] += 1
                else:
                    time_period = "EV"
                    # model rejection rate
                    census_tract_rq_reject_num[time_period][start_node_ct] += 1

    total_demand_ = 0
    for time_period in ["AM", "MD", "PM", "EV"]:
        if time_tt_direct_time[time_period] == 0:
            time_detour_ratio[time_period] = 1
        else:
            time_detour_ratio[time_period] = time_tt_drive_time[time_period] / time_tt_direct_time[time_period]
        for census_tract in census_tract_node.keys():
            #         if census_tract_num_rq[time_period][census_tract]==0:
            #             census_tract_avg_wait_time[time_period][census_tract]=tt_wait_time_period[time_period]/rq_served_period[time_period]
            #         else:
            #             census_tract_avg_wait_time[time_period][census_tract]=census_tract_tt_wait_time[time_period][census_tract]/census_tract_num_rq[time_period][census_tract]
            #         #calculate the rejection rate
            reject_num = census_tract_rq_reject_num[time_period][census_tract]
            served_num = census_tract_rq_served_num[time_period][census_tract]
            total_demand_ += reject_num
            total_demand_ += served_num

            demand_period[time_period] += reject_num
            demand_period[time_period] += served_num
            #         print("time_period",time_period,"census_tract",census_tract,"reject_num",reject_num,"served_num",served_num)
            if (reject_num + served_num) == 0:
                census_tract_reject_rate[time_period][census_tract] = 0
            else:
                census_tract_reject_rate[time_period][census_tract] = reject_num / (reject_num + served_num)
            # calculate the average waiting time per census tract, including rejection rate penalty
            if aggregation=="census_track":
                if census_tract_num_rq[time_period][census_tract] == 0:
                    if rq_served_period[time_period]!=0:
                        census_tract_avg_wait_time[time_period][census_tract] = tt_wait_time_period[time_period] / rq_served_period[time_period]
                    else:
                        census_tract_avg_wait_time[time_period][census_tract]=tt_wait_time_period["AM"] / rq_served_period["AM"] # no service in this time period - 180 waiting time
                else:
                    census_tract_avg_wait_time[time_period][census_tract] = census_tract_tt_wait_time[time_period][census_tract] / census_tract_num_rq[time_period][census_tract] + (census_tract_reject_rate[time_period][census_tract] * 100)
            if aggregation=="whole_region":
                if rq_served_period[time_period] != 0:
                    # if rejection rate=1.00, then penalty is= 600sec (10 minutes)
                    census_tract_avg_wait_time[time_period][census_tract] = tt_wait_time_period[time_period] / rq_served_period[time_period] + (census_tract_reject_rate[time_period][census_tract] * 600) # if rejection rate=1.00, then penalty is= 1,200sec (20 minutes)
                else:
                    census_tract_avg_wait_time[time_period][census_tract] = tt_wait_time_period["AM"] / rq_served_period["AM"]  # no service in this time period - 180 waiting time


    print("total microtransit demand", total_demand_, "number of requests served:", num_rq_served)
    for time_period in ["AM", "MD", "PM", "EV"]:
        print("time_period", time_period, "microtransit demand", demand_period[time_period],
              "number of requests served:", rq_served_period[time_period], "\n", "waiting time",
              census_tract_avg_wait_time[time_period], "\n", "detour_ratio", time_detour_ratio[time_period], "\n",
              "rejection rate:", census_tract_reject_rate[time_period], "\n")

        f.close()

    # final_network_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
    # initial_network_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
##################################################################################
    # if study_area == "downtown_sd":
    #     demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/demand_folder"
    #     if dt_sd_full_trnst_ntwk == True:
    #         if zonal_partition == True:
    #             initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network_4_zones"
    #         else:
    #             initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network"
    #     else:
    #         initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
    #     final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
    #     fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/example_demand/matched/example_network"
    #     output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"
    #
    # if study_area == "lemon_grove":
    #     demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/demand_folder"
    #     if zonal_partition == False:
    #         initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
    #     else:
    #         initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network_4_zones"
    #
    #     # initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
    #     final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/final_network"
    #     fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/lemon_grove_example_demand/matched/example_network"
    #     output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"
    ###############################################################

    if TRPartA == True:

        if BayesianOptimization== True:
            #output_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/output_folder" % str(study_area)
            #D:\Siwei_Micro_Transit\Bayesian_Optimization\demand_data\downtown_sd
            demand_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/demand_data/%s" % str(study_area)
            if study_area == "downtown_sd":
                # D:\Siwei_Micro_Transit\TR_PartA\Data\downtown_sd\initial_network_folder\initial_full_transit_network
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/example_demand/matched/example_network"
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_full_transit_network_4_zones" % str(
                        study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_full_transit_network" % str(
                        study_area)
            if study_area == "lemon_grove":
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/lemon_grove_example_demand/matched/lemon_grove_example_network"
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_network_4_zones" % str(
                        study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_network" % str(
                        study_area)
                    # D:\Siwei_Micro_Transit\TR_PartA\Data\lemon_grove\initial_network_folder\initial_network
            final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/final_network_folder" % str(study_area)
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/output_folder" % str(study_area)
            # D:\Siwei_Micro_Transit\TR_PartA\Data\lemon_grove\output_folder
        else:

            demand_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/demand_data/%s" % str(study_area)
            if study_area == "downtown_sd":
                # D:\Siwei_Micro_Transit\TR_PartA\Data\downtown_sd\initial_network_folder\initial_full_transit_network
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/example_demand/matched/example_network"
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_full_transit_network_4_zones" % str(
                        study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_full_transit_network" % str(
                        study_area)
            if study_area == "lemon_grove":
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/lemon_grove_example_demand/matched/lemon_grove_example_network"
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_network_4_zones" % str(
                        study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_network" % str(
                        study_area)
                    # D:\Siwei_Micro_Transit\TR_PartA\Data\lemon_grove\initial_network_folder\initial_network
            final_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/final_network_folder" % str(study_area)
            output_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/output_folder" % str(study_area)
            # D:\Siwei_Micro_Transit\TR_PartA\Data\lemon_grove\output_folder


    else:
        if study_area == "downtown_sd":
            demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/demand_folder"
            if dt_sd_full_trnst_ntwk == True:
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network_4_zones"
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network"
            else:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
            final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
            fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/example_demand/matched/example_network"
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"

        if study_area == "lemon_grove":

            demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/demand_folder"
            if zonal_partition == False:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
            else:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network_4_zones"
            final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/final_network"
            fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/lemon_grove_example_demand/matched/lemon_grove_example_network"
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"

    headway_scenarios = [20, 30, 60]
    # microtransit_scenarios = ["micro", "non_micro"]
    time_periods = ["AM", "MD", "PM", "EV"]

    # for virstop in [50, 75, 100]:
    #     for headway in headway_scenarios:
    #         for microtransit in microtransit_scenarios:
    if microtransit=="micro":
        for time_period in time_periods:
            final_super_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit),str(fleet_size),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))
            initial_super_network_dir = os.path.join(initial_network_folder,"initial_super_network_%s_hw_%s_virstop_%s.csv" % (str(microtransit), str(headway), str(virstop)))# initial_super_network[microtransit][headway][virstop][time_period]=n_a.read_super_network(initial_super_network_dir)
            #os.path.join(initial_network_folder,"initial_super_network_%s_hw_%s_virstop_%s.csv" % (str(microtransit), str(headway), str(virstop)))  # initial_super_network[microtransit][headway][virstop][time_period]=n_a.read_super_network(initial_super_network_dir)

            if iteration_debug==True:
                debug_final_super_network_dir = os.path.join(final_network_folder,"debug_iter_%s_final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(iteration),str(microtransit),str(fleet_size),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))
                with open(debug_final_super_network_dir, 'w+', newline='') as csvfile_debug:
                    fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type","route"]
                    writer = csv.DictWriter(csvfile_debug, fieldnames=fieldnames)
                    writer.writeheader()

                    with open(initial_super_network_dir) as f_W:
                        csvreader = csv.DictReader(f_W)
                        # depart_time	start	end	trip_id

                        for data in csvreader:
                            #             print(data)
                            link_type = int(data["link_type"])
                            from_node = int(data["from_node"])
                            to_node = int(data["to_node"])
                            distance = float(data["distance"])
                            travel_time = float(data["travel_time"])
                            route = int(data["route"])

                            if link_type == 5:  # adjust the microtransit waiting time according to fleetpy results
                                if from_node <= 731:
                                    census_tract = node_census_tract[from_node]
                                    travel_time = census_tract_avg_wait_time[time_period][census_tract]  # update the connector link travel time as the waiting time

                            if link_type == 4:
                                travel_time = travel_time * time_detour_ratio[time_period]

                            writer.writerow({'from_node': from_node, 'to_node': to_node, 'distance': distance,
                                             'travel_time': travel_time, "link_type": link_type,"route":route})

                        f_W.close()
                csvfile_debug.close()


            with open(final_super_network_dir, 'w+', newline='') as csvfile:
                fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type","route"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                with open(initial_super_network_dir) as f_W:
                    csvreader = csv.DictReader(f_W)
                    # depart_time	start	end	trip_id

                    for data in csvreader:
                        #             print(data)
                        link_type = int(data["link_type"])
                        from_node = int(data["from_node"])
                        to_node = int(data["to_node"])
                        distance = float(data["distance"])
                        travel_time = float(data["travel_time"])
                        route = int(data["route"])

                        if link_type == 5:  # adjust the microtransit waiting time according to fleetpy results
                            if from_node <= 731:
                                census_tract = node_census_tract[from_node]
                                travel_time = census_tract_avg_wait_time[time_period][census_tract]  # update the connector link travel time as the waiting time

                        if link_type == 4:
                            travel_time = travel_time * time_detour_ratio[time_period]

                        writer.writerow({'from_node': from_node, 'to_node': to_node, 'distance': distance,'travel_time': travel_time, "link_type": link_type,"route":route})

                    f_W.close()
            csvfile.close()
    elif microtransit =="micro_only":
        #final_super_network_dir[microtransit][virstop][M_operating_hrs][time_period][fleet_size] = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_virstop_%s.csv" % (str(microtransit), str(fleet_size),str(M_operating_hrs), str(time_period), str(virstop)))
        for time_period in time_periods:
            final_super_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_virstop_%s.csv" % (str(microtransit), str(fleet_size),str(M_operating_hrs), str(time_period), str(virstop)))

            initial_super_network_dir = os.path.join(initial_network_folder, "initial_super_network_%s_virstop_%s.csv" % (str(microtransit), str(virstop)))  # initial_super_network[microtransit][headway][virstop][time_period]=n_a.read_super_network(initial_super_network_dir)

            if iteration_debug == True:
                debug_final_super_network_dir = os.path.join(final_network_folder,
                                                             "debug_iter_%s_final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (
                                                             str(iteration), str(microtransit), str(fleet_size),
                                                             str(M_operating_hrs), str(time_period), str(headway),
                                                             str(virstop)))
                with open(debug_final_super_network_dir, 'w+', newline='') as csvfile_debug:
                    fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type", "route"]
                    writer = csv.DictWriter(csvfile_debug, fieldnames=fieldnames)
                    writer.writeheader()

                    with open(initial_super_network_dir) as f_W:
                        csvreader = csv.DictReader(f_W)
                        # depart_time	start	end	trip_id

                        for data in csvreader:
                            #             print(data)
                            link_type = int(data["link_type"])
                            from_node = int(data["from_node"])
                            to_node = int(data["to_node"])
                            distance = float(data["distance"])
                            travel_time = float(data["travel_time"])
                            route = int(data["route"])

                            if link_type == 5:  # adjust the microtransit waiting time according to fleetpy results
                                if from_node <= 731:
                                    census_tract = node_census_tract[from_node]
                                    travel_time = census_tract_avg_wait_time[time_period][
                                        census_tract]  # update the connector link travel time as the waiting time

                            if link_type == 4:
                                travel_time = travel_time * time_detour_ratio[time_period]

                            writer.writerow({'from_node': from_node, 'to_node': to_node, 'distance': distance,
                                             'travel_time': travel_time, "link_type": link_type, "route": route})

                        f_W.close()
                csvfile_debug.close()

            with open(final_super_network_dir, 'w+', newline='') as csvfile:
                fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type", "route"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                with open(initial_super_network_dir) as f_W:
                    csvreader = csv.DictReader(f_W)
                    # depart_time	start	end	trip_id

                    for data in csvreader:
                        #             print(data)
                        link_type = int(data["link_type"])
                        from_node = int(data["from_node"])
                        to_node = int(data["to_node"])
                        distance = float(data["distance"])
                        travel_time = float(data["travel_time"])
                        route = int(data["route"])

                        if link_type == 5:  # adjust the microtransit waiting time according to fleetpy results
                            if from_node <= 731:
                                census_tract = node_census_tract[from_node]
                                travel_time = census_tract_avg_wait_time[time_period][census_tract]  # update the connector link travel time as the waiting time

                        if link_type == 4:
                            travel_time = travel_time * time_detour_ratio[time_period]

                        writer.writerow({'from_node': from_node, 'to_node': to_node, 'distance': distance,
                                         'travel_time': travel_time, "link_type": link_type, "route": route})

                    f_W.close()
            csvfile.close()

def cal_iter_micro_link_diff(headway,virstop,M_operating_hrs,fleet_size,study_area,debug):
    if study_area == "downtown_sd":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/demand_folder"
        initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/example_demand/matched/example_network"
        output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"

    if study_area == "lemon_grove":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/demand_folder"
        initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_SanDiego/data/demand/lemon_grove_example_demand/matched/example_network"
        output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"
    time_periods = ["AM", "MD", "PM", "EV"]
    microtransit = "micro"
    micro_transit_travel_link=OrderedDict()
    micro_transit_waiting_link=OrderedDict()

    micro_transit_travel_link_diff=OrderedDict()
    micro_transit_waiting_link_diff=OrderedDict()
    for time_period in time_periods:
        micro_transit_travel_link_diff[time_period] = OrderedDict()
        micro_transit_waiting_link_diff[time_period] = OrderedDict()

    for iteration in range(4):
        micro_transit_travel_link[iteration] = OrderedDict()
        micro_transit_waiting_link[iteration]  = OrderedDict()
        for time_period in time_periods:
            micro_transit_travel_link[iteration][time_period] = OrderedDict()
            micro_transit_waiting_link[iteration][time_period] = OrderedDict()

    for iteration in range(4):
        for time_period in time_periods:
            debug_final_super_network_dir = os.path.join(final_network_folder,"debug_iter_%s_final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(iteration),
                                                           str(microtransit), str(fleet_size),str(M_operating_hrs), str(time_period), str(headway),str(virstop)))
            with open(debug_final_super_network_dir) as csvfile_debug:
                csvreader = csv.DictReader(csvfile_debug)
                # depart_time	start	end	trip_id
                for data in csvreader:
                    #             print(data)
                    link_type = int(data["link_type"])
                    from_node = int(data["from_node"])
                    to_node = int(data["to_node"])
                    distance = float(data["distance"])
                    travel_time = float(data["travel_time"])
                    if link_type==4:
                        micro_transit_travel_link[iteration][time_period][(from_node,to_node)] = travel_time
                        micro_transit_travel_link_diff[time_period][(from_node, to_node)]=0
                    if link_type==5:
                        micro_transit_waiting_link[iteration][time_period][(from_node, to_node)] = travel_time
                        micro_transit_waiting_link_diff[time_period][(from_node, to_node)] =0
            csvfile_debug.close()

    for iteration in range(1,3):
        if iteration>0:
            for time_period in time_periods:
                for (from_node,to_node) in micro_transit_travel_link[iteration][time_period]:
                    micro_transit_travel_link_diff[time_period][(from_node,to_node)] += micro_transit_travel_link[iteration][time_period][(from_node,to_node)]-micro_transit_travel_link[iteration-1][time_period][(from_node,to_node)]

                for (from_node,to_node) in micro_transit_waiting_link[iteration][time_period]:
                    micro_transit_waiting_link_diff[time_period][(from_node,to_node)] += micro_transit_waiting_link[iteration][time_period][(from_node,to_node)]-micro_transit_waiting_link[iteration-1][time_period][(from_node,to_node)]

    if debug==True:
        debug_network_trvl_time_diff_dir = os.path.join(final_network_folder,
                                                 "debug_trvl_time_diff_final_super_network_%s_fsize_%s_ophr_%s_hw_%s_virstop_%s.csv" % (
                                                 str(microtransit), str(fleet_size),
                                                 str(M_operating_hrs), str(headway), str(virstop)))
    else:
        debug_network_trvl_time_diff_dir = os.path.join(final_network_folder,
                                                 "trvl_time_diff_final_super_network_%s_fsize_%s_ophr_%s_hw_%s_virstop_%s.csv" % (
                                                 str(microtransit), str(fleet_size),
                                                 str(M_operating_hrs), str(headway), str(virstop)))
    with open(debug_network_trvl_time_diff_dir, 'w+', newline='') as csvfile_diff:
        fieldnames = ["from_node","to_node","link_type","diff_AM", "diff_MD", "diff_PM", "diff_EV"]
        writer = csv.DictWriter(csvfile_diff, fieldnames=fieldnames)
        writer.writeheader()
        time_period="AM"
        for (from_node,to_node) in micro_transit_travel_link_diff[time_period]:
            link_type=4
            diff_AM = micro_transit_travel_link_diff["AM"][(from_node,to_node)]
            diff_MD = micro_transit_travel_link_diff["MD"][(from_node, to_node)]
            diff_PM = micro_transit_travel_link_diff["PM"][(from_node, to_node)]
            diff_EV = micro_transit_travel_link_diff["EV"][(from_node, to_node)]
            writer.writerow({'from_node': from_node, 'to_node': to_node, "link_type": link_type,'diff_AM': diff_AM, 'diff_MD': diff_MD,
                             "diff_PM":diff_PM,"diff_EV":diff_EV
                 })

        for (from_node,to_node) in micro_transit_waiting_link_diff[time_period]:
            link_type=5
            diff_AM = micro_transit_waiting_link_diff["AM"][(from_node,to_node)]
            diff_MD = micro_transit_waiting_link_diff["MD"][(from_node, to_node)]
            diff_PM = micro_transit_waiting_link_diff["PM"][(from_node, to_node)]
            diff_EV = micro_transit_waiting_link_diff["EV"][(from_node, to_node)]
            writer.writerow({'from_node': from_node, 'to_node': to_node, "link_type": link_type,'diff_AM': diff_AM, 'diff_MD': diff_MD,
                             "diff_PM":diff_PM,"diff_EV":diff_EV
                 })

    # return None

if __name__ == '__main__':
#    ["downtown_sd", "lemon_grove"]
    study_area = "lemon_grove"
    operating_period_1 = ["AM", "PM"]  # 10 hr
    operating_period_2 = ["AM", "MD", "PM"]  # 15hr
    operating_period_3 = ["AM", "MD", "PM", "EV"]  # 19hr
    debug_mode=True

    if debug_mode==True:
        operating_periods_scenarios = [operating_period_3] #just for testing
        # virtual_stop_scenarios = [75,100]  # just for testing
        # headway_scenarios = [30,60]  # just for testing
        # fleet_size_scenarios = [2,3,4]
        virtual_stop_scenarios = [75]  # just for testing
        headway_scenarios = [30]  # just for testing
        fleet_size_scenarios = [2]
    else:
        operating_periods_scenarios = [operating_period_1]  # just for testing [operating_period_1,operating_period_2]
        virtual_stop_scenarios = [75] #[75,100]
        headway_scenarios = [15] #[30,60] # Downtown SD is every 15 minutes
        # headway_scenarios = [20,30, 60]
        fleet_size_scenarios = [15] #[10,20]

    num_headway_scen = 0
    for headway in headway_scenarios:  # put bus design parameter in the most outer loop
        for virstop in virtual_stop_scenarios:  # virtual stops - not necessarily influence the cost, but will influence the mobility
            for fleet_size in fleet_size_scenarios:  # fleetsize - influence the cost & mobility
                for operating_periods in operating_periods_scenarios:  # fleetsize - influence the cost & mobility
                    if operating_periods == ["AM", "MD", "PM", "EV"]:
                        M_operating_hrs = 19
                    elif operating_periods == ["AM", "MD", "PM"]:
                        M_operating_hrs = 15
                    else:
                        M_operating_hrs = 10

                    cal_iter_micro_link_diff(headway, virstop, M_operating_hrs, fleet_size, study_area,debug_mode)