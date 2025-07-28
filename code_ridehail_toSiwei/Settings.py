__author__ = 'Mike'
# This file contains all of the simulation parameters and parameters for the assignment-repositioning problem

# ################# Simulation Parameters ##############################

# Input data is for entire 24-hour period
# These input parameters allow modeler to control first and last request
first_request_time = 3.0 * 60 * 60
last_request_time = 24.0 * 60 * 60

# time step for the simulation
# currently this has little impact on computation time, much bigger factor is the inter-decision time
sim_time_step = 15

# Can effectively start the simulation clock at any time of day.
# I recommend starting simulation at the same as first request time or 30 minutes before first request.
start_sim_time = int(2.5 * 60 * 60)
# I recommending ending simulation about 90 minutes after last request time
end_sim_time = int(25.5 * 60 * 60)
sim_length = end_sim_time - start_sim_time  # sim length needed for simulation output statistics

# Often can be useful to also choose a peak demand period to analyze, in addition to the whole day
peak_start_time = 17.0 * 60.0 * 60.0
peak_end_time = 21.0 * 60.0 * 60.0

# When analyzing system performance, it is beneficial to cut the tails of the simulation
# That is what the metric_start and the metric_end person parameters do.
metrics_start_person = 0.1
metrics_end_person = 0.9

# Vehicle speed: the NYC/manhattan taxi data is in meters; whereas the Chicago taxi and artificial is in feet
# veh_speed = 40.0  # ft/s
veh_speed = 5.0  # m/s  #<-- average speed of vehicle in Manhattan is 5.0m/s

# the distance a vehicle travels in one time-step <-- needed to check if vehicle is at drop or pick location
delta_veh_dist = veh_speed * sim_time_step  # feet or meters

# Parameters for exact time vehicle spends at pickup location and drop-off location
# These should probably be stochastic in future work <-- Traveling repairman problem
curb_pick_time = 45.0  # seconds
curb_drop_time = 15.0  # seconds

# Actually do not need this parameter for the ride-hail case, but leaving it in for shared-ride case
veh_capacity = 5

# ################# Optimization (Assignment-Repositioning) Parameters ##############################

# Penalize re-assignment of an AV to another user <-- this would be annoying for user
# Penalize re-assignment of a user to another AV
pen_reassign = 30.0  # seconds
reassign_penalty = pen_reassign * veh_speed

# Penalize assignment of a user to an en-route drop-off AV, compared to an idle AV
pen_drop_time = 15.0
dropoff_penalty = pen_drop_time * veh_speed

# # converts wait time units to distance units
# gamma = 40.0  # 60.0 / 3.0

# reward for assigning an AV to a user  <-- only used in case where there is no constraint that all AVs must be assigned
assign_reward = 7000.0  # feet
# penalty for leaving an imbalance in a subarea
imbalance_penalty = 5000.0
# minimum expected imbalance in a subarea allowed before penalty begins accruing
min_imbalance = 1

# forecast/prediction horizon
predict_horizon = 30 * 60  # 30 minutes in units of seconds


# ################# Visualization Parameters ##############################
trajectory_store_interval = 15  # seconds
end_trajectory_store = 11.5 * 60 * 60  # seconds

# ################# Time-based Outputs Parameters ##############################
statistic_time_interval = 60  # seconds

# ################# Python Parameters ##############################

# Useful parameters to have
inf = 100000000000000
