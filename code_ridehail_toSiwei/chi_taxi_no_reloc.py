__author__ = 'Mike'
# File is to do sensitivity analysis on a number of parameters easily
# this sensitivity analysis is specifically for chicago taxi data
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
taxi_chi=True

area_size_miles = [25.0]
area_size = [x * 5280.0 for x in area_size_miles]

fleet_size1 = [j for j in range(201, 201, 25)]
fleet_size2 = [450]
fleet_size = fleet_size1 + fleet_size2

assign_intervals = [30]  # seconds

assign_methods = ["3_FCFS_smartNN", "5_match_idleOnly", "8_match_idlePickDrop", "assign_Hyland"]

# assign_methods = [#"1_FCFS_longestIdle", "2_FCFS_nearestIdle",
#                "3_FCFS_smartNN",  "4_FCFS_drop_smartNN", "4a_FCFS_drop_smartNN2",
#                "5_match_idleOnly", "6_match_idlePick",
#                "7_match_idleDrop", "7_match_idleDrop2",
#                "8_match_idlePickDrop"]

dates = ["1_Sample", "2_Sample"]
#dates = ["1", "2", "3"]

#######################################################################################################################
# Create Files to Write Results
#######################################################################################################################

csv_results2 = open(
        '../results_ridehail/chicago_taxi' + '_assign_ints' + str(len(assign_intervals)) + '_fleet' +
        str(len(fleet_size)) + '_opt' + str(len(assign_method)) + '.csv', 'w')

results_writer2 = csv.writer(csv_results2, lineterminator='\n', delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_NONNUMERIC)
results_writer2.writerow(
    ["Date", "Sim Length", "Assign Interval",
     "Opt Method", "Fleet Size",
     "Mean Wait Pick", "Mean Wait Pick Peak",
     "% Empty Pick", "% Empty Relocate",
     "% Reassign", "Fleet Util",
     "#Served", "#inVeh", "#Assgnd", "#Unassgnd"])

sim_length = Set.end_sim_time - Set.start_sim_time
#######################################################################################################################
# Loop Through Simulations
#######################################################################################################################

for k_assign_int in assign_intervals:
    for q_area_size in area_size:
        for m_assign_method in assign_methods:
            for j_fleet_size in fleet_size:

                # generate fleet
                Init.generate_fleet(j_fleet_size, max_distance=q_area_size)

                results_run = []

                for i_date in dates:
                    print("date:", i_date, " fleet size:", j_fleet_size,)
                    print("Opt Method: ", m_assign_method, " assign int:", k_assign_int)

                    results = Main.main(k_assign_int, m_assign_method, date=i_date, taxi=taxi_chi)
                    results_run.append(results)
                    print(results)
                    timer = time.time() - t0
                    print(timer)

                    results_writer2.writerow(
                        [i_date, sim_length, k_assign_int,  m_assign_method, j_fleet_size,
                        results[0], results[1], results[2], results[3],
                        results[4], results[5], results[6], results[7],
                        results[8], results[9], timer])

                avg = [float(sum(col)) / len(col) for col in zip(*results_run)]

                results_writer2.writerow(
                    ["average", sim_length, k_assign_int, m_assign_method, j_fleet_size,
                    avg[0], avg[1], avg[2], avg[3],
                    avg[4], avg[5], avg[6], avg[7],
                    avg[8], avg[9], timer])

csv_results2.close()

