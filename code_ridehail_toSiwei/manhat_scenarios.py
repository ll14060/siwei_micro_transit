__author__ = 'Mike'
# File is to do sensitivity analysis on a number of parameters easily
# this sensitivity analysis is specifically for NYC taxi data
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

visualize = True
taxi = True

fleet_sizes = [5000]
assign_intervals = [30]
relocate_intervals = [30]

assign_methods = ["assign_idle_w_reward"]

relocate_methods = ["joint_assign-reposition"]

# There are more spatial and temporal aggregation levels
xyt_strings = ["No_Relocation"]

               #"2x_8y_60min" "2x_8y_30min", "2x_8y_5min",
               # "4x_16y_60min", "4x_16y_30min", "4x_16y_5min",
               # "8x_32y_60min", "8x_32y_30min", "8x_32y_5min",
               #  "16x_64y_60min", "16x_64y_30min","16x_64y_5min",
               # "No_Relocation"]

dates = ["2016-04-{0:0>2}".format(x) for x in range(1,4)]

perfect_forecast_options = [False] # ,True
#######################################################################################################################
# Create Files to  WriteResults
#######################################################################################################################

csv_results2 = open('../results_ridehail/quest_scen_' + xyt_strings[0] + '_' + dates[0][8:10] + '_' +
                    dates[-1][8:10] + '.csv', 'w')
					
results_writer2 = csv.writer(csv_results2, lineterminator='\n', delimiter=',', quotechar='"',
                             quoting=csv.QUOTE_NONNUMERIC)

results_writer2.writerow(
    ["Date", "Sim_Length", "Assign Interval", "Relocate Interval",
     "Space-Temp Aggregation",
     "Opt Method", "Reloc Method",  "Fleet Size",
     "Mean Wait Pick", "Mean Wait Pick Peak",
     "% Empty_Pick", "% Empty_Relocate",
     "% Reassign", "Fleet Util",
     "#Served", "#inVeh", "#Assgnd", "#Unassgnd", "time"])

sim_length = Set.end_sim_time - Set.start_sim_time
#######################################################################################################################
# Loop Through Simulations
#######################################################################################################################
for k_assign_int in assign_intervals:
    for r_relocat_int in relocate_intervals:
        for d_xyt_string in xyt_strings:
            for m_assign_method in assign_methods:
                for rr_relocate_method in relocate_methods:
                    for perfect_forecast_bool in perfect_forecast_options:
                        for j_fleet_size in fleet_sizes:
                            results_run = []
                            for i_date in dates:

                                print("date #:", i_date, " Space_temp Aggregation:", d_xyt_string)
                                print("fleet size:", j_fleet_size, " assign int:", k_assign_int)
                                print("Opt Method: ", m_assign_method, " Relocate Method: ", rr_relocate_method)

                                # generate fleet
                                Init.generate_fleet(0.0, j_fleet_size, Set.veh_capacity)

                                run = False

                                try:
                                    if d_xyt_string == "No_Relocation":
                                        if len(relocate_methods) > 1:
                                            if rr_relocate_method == "Dandl":
                                                run = True
                                            else:
                                                print("Skip")
                                        else:
                                            run = True
                                    else:
                                        run = True

                                    if run:
                                        # pick correct forecast file or None (for value from forecast model)
                                        if perfect_forecast_bool:
                                            forecast_f = "../Inputs/NYC_Taxi/Prediction_Data/manhattan_trip_patterns_{0}.csv".format(d_xyt_string)
                                        else:
                                            forecast_f = None
                                        # generate fleet
                                        Init.generate_fleet(0.0, j_fleet_size, Set.veh_capacity)
                                        results = Main.main(k_assign_int, r_relocat_int,
                                                            m_assign_method, rr_relocate_method, i_date, taxi,
                                                            d_xyt_string, visualize, forecast_f)
                                        results_run.append(results)
                                        print(results)
                                        timer = time.time() - t0
                                        print(timer)

                                        results_writer2.writerow(
                                                        [i_date, sim_length, k_assign_int, r_relocat_int,
                                                        d_xyt_string, m_assign_method, rr_relocate_method, j_fleet_size,
                                                        results[0], results[1], results[2], results[3],
                                                        results[4], results[5], results[6], results[7],
                                                        results[8], results[9], timer])

                                except:
                                    print("Error")
                                    timer = time.time() - t0
                                    print(timer)

                            avg = [float(sum(col)) / len(col) for col in zip(*results_run)]
                            results_writer2.writerow(
                                    ["average", sim_length, k_assign_int, r_relocat_int,
                                     d_xyt_string, m_assign_method, rr_relocate_method, j_fleet_size,
                                     avg[0], avg[1], avg[2], avg[3],
                                     avg[4], avg[5], avg[6], avg[7],
                                     avg[8], avg[9], timer])

csv_results2.close()
