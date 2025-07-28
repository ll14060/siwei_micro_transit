__author__ = 'Mike'
# File is to do sensitivity analysis on a number of parameters easily
# this sensitivity analysis is specifically for artifical demand data
# see 'manhat_taxi_w_reloc' file for explanation of what is going on in this file

import Settings as Set
import Initialize as Init
import Main
import csv
import time


t0 = time.time()

#######################################################################################################################
# Inputs for Simulation Runs
#######################################################################################################################
visualize = False

area_size_miles = [8.0]  # , 16.0 4.0, miles
area_size = [x * 5280.0 for x in area_size_miles]  # feet

# requests_per_hour = [900, 1000, 1100, 1200, 1300]
requests_per_hour = [300]

demand_Type = ["O_Uniform_D_Uniform"]   # "O_Cluster_D_Cluster",

fleet_size1 = [j for j in range(120, 161, 15)]
fleet_size2 = [j for j in range(175, 201, 25)]
fleet_size = fleet_size1 + fleet_size2

assign_intervals = [15]  # seconds

assign_methods = [#"1_FCFS_longestIdle", "2_FCFS_nearestIdle",
               "3_FCFS_smartNN",  "4_FCFS_drop_smartNN", "4a_FCFS_drop_smartNN2",
               "5_match_idleOnly", "6_match_idlePick",
               "7_match_idleDrop", "7_match_idleDrop2",
               "8_match_idlePickDrop"]

#######################################################################################################################
# Create Files to Write Results
#######################################################################################################################

csv_results2 = open(
    '../results_ridehail/artificial' + '_holds' + str(len(assign_intervals)) + '_fleet'
    + str(len(fleet_size)) + '_opt' + str(len(assign_method)) + '.csv', 'w')

results_writer2 = csv.writer(csv_results2, lineterminator='\n', delimiter=',', quotechar='"',
                             quoting=csv.QUOTE_NONNUMERIC)
results_writer2.writerow(
    ["Run", "Sim Length", "Assign Interval",
     "Opt Method", "Fleet Size",
     "Mean Wait Pick", "Mean Wait Pick Peak",
     "% Empty_Pick", "% Empty_Relocate",
     "% Reassign", "Fleet Util",
     "#Served", "#inVeh", "#Assgnd", "#Unassgnd"])

sim_length = Set.end_sim_time - Set.start_sim_time
#######################################################################################################################
# Loop Through Simulations
#######################################################################################################################

for a_demand_rate in requests_per_hour:
    for k_assign_int in assign_intervals:
        for p_demand_type in demand_Type:
            for q_area_size in area_size:
                for m_assign_method in assign_methods:
                    for j_fleet_size in fleet_size:
                        jj_fleet_size = j_fleet_size + int(((q_area_size / 5280.0) - 4.0) * 25)

                        results_run = []
                        for i_run in range(0, 2):

                            print("run #:", i_run, " fleet size:", jj_fleet_size,)
                            print("Opt Method: ", m_assign_method, " assign int:", k_assign_int)

                            # generate random demand
                            Init.generate_demand(Set.last_request_time, a_demand_rate, q_area_size,
                                                 p_demand_type)
                            # generate fleet
                            Init.generate_fleet(jj_fleet_size,  max_distance=q_area_size)

                            results = Main.main(k_assign_int, m_assign_method)
                            results_run.append(results)
                            print(results)
                            timer = time.time() - t0
                            print(timer)

                            results_writer2.writerow(
                                [i_run, sim_length, k_assign_int,  m_assign_method, jj_fleet_size,
                                 results[0], results[1], results[2], results[3],
                                 results[4], results[5], results[6], results[7],
                                 results[8], results[9], timer])

                        avg = [float(sum(col)) / len(col) for col in zip(*results_run)]
                        results_writer2.writerow(
                            ["average", sim_length, k_assign_int, m_assign_method, jj_fleet_size,
                             avg[0], avg[1], avg[2], avg[3],
                             avg[4], avg[5], avg[6], avg[7],
                             avg[8], avg[9], timer])


csv_results2.close()
