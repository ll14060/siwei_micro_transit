# This is the file to collect some performance measures

import inputs as ip
import Parameter as para
import pandas as pd
if para.network_name == 'Anaheim':
    from read_network import SPSkims as od_tt
else:
    from link_cost_cal import od_tt

def output_metrics():

    # 1. VMT of vehicles (now it is actually VHT, since OD_tt is measured in time)
    VHTTotal = 0
    VMTTotal = 0
    # 2. Idle time of vehicles
    IdleTotal = 0
    # 3. Shared time of vehicles
    ShardTotal = 0
    # 4. Stationary Time: Time when vehicle is Idle (no requests) and also not moving
    stationary_time = 0
    # 5. Empty time: Time when no one is sitting in the vehicle
    empty_time_Total = 0

    for v in ip.VehicleList:
        # 1. Calculate VMT for each vehicle
        for i in range(len(v.trajectory) - 1):
            start = v.trajectory[i][0]
            end = v.trajectory[i+1][0]
            v.vht += od_tt[(start, end)][0]
        VHTTotal += v.vht

        # 2. Idle time total
        IdleTotal += v.idlTimeCum

        # 3. Shared time total
        ShardTotal += v.shareTimeTotal

        # 4. Stationary Time total
        stationary_time += v.stationary_time

        # Empty Time Total
        empty_time_Total += v.emptyTimeCum
    # Convert VHT in Minutes to Hours
    VHTTotal /= 60
    # Convert VHT to VMT
    VMTTotal = VHTTotal * para.Avg_speed
    # Calculate AVG idle time percentage of a vehicle
    AvgIdle = (IdleTotal/len(ip.VehicleList))/para.SimTime
    AvgEmpty = (empty_time_Total/len(ip.VehicleList))/para.SimTime
    AvgStationary = (stationary_time/len(ip.VehicleList))/para.SimTime
    # Empty Vehicle Hours (Time when vehicle is moving but no pccupants)
    empty_vehicle_hours = empty_time_Total/60
    # empty_vehicle_hours = (IdleTotal - stationary_time)/60
    empty_vmt_total = empty_vehicle_hours * para.Avg_speed

    # Calculate AVG shared time percentage of a vehicle
    AVGShared = (ShardTotal/len(ip.VehicleList))/para.SimTime


    # Demand Perspective
    # 4. Total Passengers served
    # Issue: List not updated in main sim. Returns 0 value

    # ServedPersonNum = len(PersonServed)
    ServedPersonNum = 0
    # 5. Total Wait time of all Persons
    WaitTimePersonTotal = 0
    # 6. Total In vehicle time
    VehicleTimePersonTotal = 0
    for p in ip.PersonServed:
        WaitTimeTemp = p.pickTime - p.requesttime
        VehicleTimeTemp = p.dropTime - p.pickTime
        ServedPersonNum += 1


        WaitTimePersonTotal += WaitTimeTemp
        VehicleTimePersonTotal += VehicleTimeTemp


    AvgWaitPerson = WaitTimePersonTotal/ServedPersonNum
    # Debug Stationary times
    AvgVehicleTimePerson = VehicleTimePersonTotal/ServedPersonNum
    # Average occupancy = PersonVehicleTime / total VHT
    AvgOccu = (VehicleTimePersonTotal/60)/VHTTotal
    AvgTotalTT = AvgWaitPerson + AvgVehicleTimePerson
    Capacity = round((para.SimTime/AvgTotalTT) * para.Fleet_size,2)
    Supply_Ratio = round(Capacity/para.Demand_size,2)

    with open(para.output_metrics_file,'a') as op_file:
        print('Total VMT', VMTTotal,file=op_file)
        # print('Empty VMT', empty_vmt_total, file=op_file)
        print('Total VHT', VHTTotal, file=op_file)
        print('Empty VHT', empty_vehicle_hours, file=op_file)
        # Time vehicle isn't moving (either idling somehwere or at the relocation point)
        # print('Avg Stationary time Percentage of a vehicle', AvgStationary, file=op_file)
        # Time vehicle is Idle - Time when there are 0 persons in the vehicle (either stationary or moving)
        print('Avg Idle Vehicle Time Percentage of a vehicle', AvgIdle,file=op_file)
        print('Avg Empty Vehicle Time Percentage of a vehicle', AvgEmpty,file=op_file)
        print('AVG Shared time percentage of a vehicle', AVGShared,file=op_file)
        print('Number of requests served ', ServedPersonNum,file=op_file)
        print('Percentage of Requests Served ', round(100*ServedPersonNum/ip.total_demand,2),' %',file=op_file)
        print('Avg waiting time of a person before picking (min) ', AvgWaitPerson,file=op_file)
        print('Avg Travel time of a person (min) ', AvgVehicleTimePerson,file=op_file)
        print('Avg Occupancy', AvgOccu, file=op_file)

    # Update results summary csv file
    try:
        resultdf = pd.read_csv(para.output_multiscn_summary_file,index_col= 0)

    except:
        resultdf = pd.DataFrame(columns=['Bi-Criteria',	'Policy','Reward Coeff ($)','Simulation Time','# Requests','# Vehicles',	'Total VMT','Total VHT','Idle Time%','Empty Time %','Share Time %','Served','Served%','Avg Occupancy','Avg Waiting','Avg Travel','Wait+Travel','Capacity','Supply Ratio'])
    bicr = '1'
    policy = '1'
    reward_coeff = 0
    if para.bi_criterion_flag == False:
        bicr = 'False'
        policy = '-'
        reward_coeff = 0
    else:
        bicr = para.bi_criteria_condi
        policy = para.bi_criterion_policy
        reward_coeff = para.reward_coefficient

    resultdf.loc[para.current_time] = [bicr,policy,reward_coeff,para.SimTime,para.Demand_size,para.Fleet_size,VMTTotal,VHTTotal,AvgIdle,AvgEmpty,AVGShared,ServedPersonNum,round(100*ServedPersonNum/ip.total_demand,2),AvgOccu,AvgWaitPerson,AvgVehicleTimePerson,AvgTotalTT,Capacity,Supply_Ratio]
    resultdf.to_csv(para.output_multiscn_summary_file)
