__author__ = 'Mike'
# File is to do sensitivity analysis on a number of parameters easily
# this sensitivity analysis is specifically for NYC taxi data

import Settings as Set
import Initialize as Init
import Main
import csv
import time


t0 = time.time()

#######################################################################################################################
# Inputs for Simulation Runs
#######################################################################################################################
viz_set = False   # are we going to output trajectories to visualize?
taxi = True         # are we using taxi data as input? YES
NYC_true = True     # is this NYC taxi data? YES
out_statistics = True

# can have multiple values in these sets to do sensitivity analysis
fleet_sizes = [6000, 7000]        # AV fleet size <-- super important parameters
assign_intervals = [15]     # how many seconds between calling assignment method
relocate_intervals = [15]   # how many seconds between calling repositioning methods

# what assignment methods to consider in sensitivity analysis
assign_methods = ["3_FCFS_smartNN"]

    # [#"1_FCFS_longestIdle", "2_FCFS_nearestIdle",
    #            "3_FCFS_smartNN",  "4_FCFS_drop_smartNN", "4a_FCFS_drop_smartNN2",
    #            "5_match_idleOnly", "6_match_idlePick",
    #            "7_match_idleDrop", "7_match_idleDrop2",
    #            "8_match_idlePickDrop"]

# what relocation methods to consider in sensitivity analysis
relocate_methods = ["joint_assign-reposition"]  # "Dandl"

# what spatial-temporal aggregation levels for forecasts to consider in sensitivity analysis
xyt_strings = ["No_Relocation"]

    # ["No_Relocation",
    #            "2x_8y_60min", "2x_8y_5min",
    #            "4x_16y_60min", "4x_16y_5min",
    #             "16x_64y_60min", "16x_64y_5min" ]

# what taxi input file dates to consider in forecasts
dates = ["2016-04-{0:0>2}".format(x) for x in range(1, 21,19)]

# are we using perfect forecasts or model forecasts, or both
perf_frcst_optns = [False]

#######################################################################################################################
# Create Files to  WriteResults
#######################################################################################################################

csv_results2 = open(
    '../results_ridehail/manhat_assign_repos' + '_holds' + str(len(assign_intervals)) + '_fleet'
    + str(len(fleet_sizes)) + '_opt' + str(len(assign_methods)) + '.csv', 'w')

results_writer2 = csv.writer(csv_results2, lineterminator='\n', delimiter=',', quotechar='"',
                             quoting=csv.QUOTE_NONNUMERIC)
results_writer2.writerow(
    ["Date", "Sim Length", "Assign Interval", "Relocate Interval",
     "Space-Temp Aggregation",
     "Opt Method", "Reloc Method",  "Fleet Size",
     "Mean Wait Pick", "Mean Wait Pick Peak",
     "% Empty_Pick", "% Empty_Relocate",
     "% Reassign", "Fleet Util",
     "#Served", "#inVeh", "#Assgnd", "#Unassgnd"])


#######################################################################################################################
# Loop Through Simulations
#######################################################################################################################
for k_assign_int in assign_intervals:
    for r_relocat_int in relocate_intervals:
        for d_xyt_string in xyt_strings:
            for m_assign_method in assign_methods:
                for rr_relocate_method in relocate_methods:
                    for j_fleet_size in fleet_sizes:
                        for o_frcst_opt in perf_frcst_optns:
                            results_run = []
                            for i_date in dates:

                                # output information about current scenario in Python Console/Terminal
                                print("date #:", i_date, " Space_temp Aggregation:", d_xyt_string)
                                print("fleet size:", j_fleet_size, " assign int:", k_assign_int)
                                print("Opt Method: ", m_assign_method, " Relocate Method: ", rr_relocate_method)

                                # generate fleet
                                Init.generate_fleet(j_fleet_size, NYC = NYC_true)

                                run = False

                                # try:
                                if d_xyt_string == "No_Relocation":
                                    if len(relocate_methods) > 1:
                                        if rr_relocate_method == "Dandl":
                                            run = True
                                        else:
                                            print("Skip")  # only need to run one 'No_Relocation' case
                                    else:
                                        run = True
                                else:
                                    run = True

                                if run:
                                    # call Main and run simulation
                                    results = Main.main(k_assign_int, m_assign_method, r_relocat_int, rr_relocate_method,
                                                        i_date, taxi, NYC_true, d_xyt_string, o_frcst_opt, out_statistics,
                                                        visualize=viz_set)

                                    # store results from last scenario/day in array
                                    results_run.append(results)
                                    print(results)
                                    print(time.time() - t0)

                                # except:
                                #     print("Error")
                                #     print(time.time() - t0)

                            if run:
                                # take average across all taxi day instances
                                avg = [float(sum(col)) / len(col) for col in zip(*results_run)]
                                sim_length = Set.end_sim_time - Set.start_sim_time
                                # print average values across 30 days to file
                                results_writer2.writerow(
                                    [i_date, sim_length, k_assign_int, r_relocat_int,
                                     d_xyt_string, m_assign_method, rr_relocate_method, j_fleet_size,
                                     avg[0], avg[1], avg[2], avg[3],
                                     avg[4], avg[5], avg[6], avg[7], avg[8]])


csv_results2.close()
