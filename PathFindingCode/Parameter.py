
import json
from datetime import datetime
# A Section of Parameters
# Network name
network_name = 'Anaheim'
# Time Parameter Section
# Total simulation time, in minutes
# For anaheim, simtime should be in multiples of 30
SimTime = 180 #1440 for 24 hour period, 180 for 3 hour simulation

# Demand Time Period (Not used), currently demand time period is constantly fixed at 30 minutes
DemandTime = 30
demand_distr = 'uniform'  # uniform, non-uniform
# modal share of shared ride trips, to calculate demand for shared rides from all demand
shared_ride_mode_share = 0.05 # Percentage

# Random Seed


seed = 677

# Time step to check vehicle and passenger status
TimeStep = 0.1
InitialTime = 0
# Maximum Idle ti2me before relocate
maxIdlTime = 5


# Maximum additional pickup wait time for passengers
maxPickUpWaitTime = 15
# Maximum Pickup Reward
maxPickupReward = 200

Fleet_size = 50
Demand_size = 300
# Slice demand from larger number of requests
Avg_speed = 40 # miles per hour


# Logging Data
output_timestep_log="output_timestep_log.txt"


# Bi Criterion path parameters
# Bi Criteria condition parameter
# Condition 1: if a vehicle has only one task and is a dropoff task, consider bi-path
# Condition 2: if a vehicle has two dropoff tasks consider bi-path
# Condition 3: if a vehicle has only one person to serve, regardless of picking or dropping, consider bi-path
bi_criteria_condi = '1'

bi_criterion_flag = False
# Bi Crtierion Policy:
# 1a: Double constrained - when there is no optimal solution, then go on shortest path,
# 1b: Double constrained - even if there is optimal solution, check trade-off between demand and detour
#                                                             based on bi-obj function, if satisfied, then
#                                                             accept, else use shortest path
# 1c: Future Update for any other double constrained method, (1b + iterative optimization?)
# 2a: bi crtierion objective: with all negative weights changed to a very small number 0.001
# 2b: bi crtierion objective: with all negative weights scaled to a very small number in the range 0.001 - 0.002
# Update in the parameters.json file, not here
bi_criterion_policy = '2b'
cost_coefficient = 0.5   # ($ cost per minute)
reward_coefficient = 2.0  # ($ reward per potential demand )

# Setting the lower bound of demand relative to shortest path demand
# Look for other smarter ways to set bounds, absolute or relative and combinatio of absolute and relative, based on some lit review
min_demand_factor = 1.025
max_detour_factor = 1.5   # 1.5 times time on shortest path or 10 minutes, whichever is lesser
max_absolute_detour = 10  # 10 minutes
# File name to store output metrics
output_metrics_file = ""
# File to store summary of output metrics across multiple runs
output_multiscn_summary_file = " "
current_time = ""
# Function to update parameters by reading from the json file
# USeful for batch run
def update_parameters():
    with open("parameters.json",'r') as file:
        data = file.read()
    para_dict = json.loads(data)
    global Demand_size
    Demand_size = para_dict["request_size"]
    global Fleet_size
    Fleet_size = para_dict["fleet_size"]
    global bi_criterion_flag
    if para_dict["bicr_flag"] == 'True':
        bi_criterion_flag = True
    else:
        bi_criterion_flag = False
    global bi_criterion_policy
    bi_criterion_policy = para_dict["bicr_policy"]
    global bi_criteria_condi
    bi_criteria_condi = para_dict["bicr_condi"]
    global reward_coefficient
    reward_coefficient = para_dict["reward_coeff"]
    # Output Metrics Mile
    global current_time
    current_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    global output_multiscn_summary_file
    if demand_distr == 'uniform':
        output_multiscn_summary_file = "batch_summary_uniform_demand_"+network_name+"_t_"+str(SimTime)+"_min.csv"
    else:
        output_multiscn_summary_file = "batch_summary_" + network_name+"_t_"+str(SimTime)+"_min.csv"
    global output_metrics_file
    output_metrics_file="output_metrics_"+current_time+"_"+network_name+"_p_"+str(Demand_size)+"_v_"+str(Fleet_size)+"_"
    if bi_criterion_flag:
        output_metrics_file = output_metrics_file+"bicriterion_"+bi_criterion_policy+"_cost_"+str(cost_coefficient)+"_reward_"+str(reward_coefficient)+".txt"
    else:
        output_metrics_file = output_metrics_file + "myopic.txt"

    import os
    if not os.path.exists(os.getcwd()+"\\Output"):
        os.makedirs(os.getcwd()+"\\Output")
    output_metrics_file = os.getcwd()+"\\Output\\"+output_metrics_file
    output_multiscn_summary_file = os.getcwd()+"\\Output\\"+ output_multiscn_summary_file
    print(output_metrics_file)
    with open(output_metrics_file,'w') as op_file:
        print(" ",file=op_file)
        print(" ", file=op_file)
        print("------------------ ", file=op_file)
        print(" ", file=op_file)
        print("Bi Criterion Flag ",bi_criterion_flag,file=op_file)
        if bi_criterion_flag:
            print("Bi Criterion policy ", bi_criterion_policy, file=op_file)
            print("Bi Criterion condition ", bi_criteria_condi, file=op_file)
            if bi_criterion_policy != '1a':
                print("Cost Coefficient ($/min) ", cost_coefficient, file=op_file)
                print("Reward Coefficient($/demand) ", reward_coefficient, file=op_file)
        print("Fleet Size ",Fleet_size,file=op_file)
        print("# Requests ", Demand_size, file=op_file)
        print("Max Pickup Wait Time (mins) ", maxPickUpWaitTime, file=op_file)
        print("Max Pickup Cost for Vehicle (mins) ", maxPickupReward, file=op_file)
        print("Simulation Start Time ", InitialTime, file=op_file)
        print("Simulation End Time ", SimTime, file=op_file)
        print("*********************************************", file=op_file)
        print(" ",file=op_file)
        print(" ", file=op_file)


