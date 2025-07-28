import json
import networkx as nx
import pickle
import pandas as pd
import Parameter
import geopandas as gpd
from math import ceil
network_name="Anaheim"
# Load projected nodes shape files for anaheim
anaheim_nodes_gis = gpd.read_file(network_name+r'\shape_file\anaheim_nodes_projected.shp')


# Load networkx graph from pickle file

road_network = nx.read_gpickle(network_name+"\\Revised\\anaheim_nxgraph.pickle")
number_of_nodes = road_network.number_of_nodes()
# Test
# print("No of Nodes: ",road_network.number_of_nodes())
# print("No of Edges: ",road_network.number_of_edges())
# for s,e in road_network.edges():
#     print(road_network[s][e])
#     break

# Read SP Travel Times and Paths Skims as dictinary from Pickle



# Read K Shortest Paths
with open(network_name+"\\Revised\\anaheim_k_paths.json","r") as file:
    data = file.read()
ksp = json.loads(data)
# Test
# print(ksp['1']['15'])

# Load revised O-D table
# Origin and Destination are integers in OD table
# odtable = pd.read_csv(network_name+"\\anaheim_revised_odtable_excl_freeways.csv",index_col=0)
odtable = pd.read_csv(network_name+r'\Revised\anaheim_odtable.csv',index_col=0)

# Change data types of source and destination to int to keep consistency
odtable.columns = odtable.columns.astype(int)
odtable.index = odtable.index.astype(int)

# Creating multiple OD tables based on simultation time
# Entry in the original OD tables is the average trips per hour
# Split it into multiple 30 min periods such that the average over the entire time period is (odtable/2) value,
# which is the average trip rate in 30 minutes time
if Parameter.SimTime == 180:
    no_of_time_periods = int(Parameter.SimTime/30)
else:
    # 24 hour simulation
    no_of_time_periods = 5
# Create list of dataframes, one for each timeperiod
odtable_time = []
# Different methods to impute demand, based on whether it is 24 hour or 180 minute simulation
if Parameter.SimTime == 180:
    # Method to compute odtables for different time windows
    # Convert the input OD tables into a triangular distribution
    # If there are odd number of time periods t, weights would be 1,2,..ceil(t/2),...2,1 for each time window
    # If there are even number of time periods t, weights would be 1,2,3...t/2,t/2,...3,2,1
    # Odd time periods have 1 peak window, Even have two peak windows

    max_adj_factor = ceil(no_of_time_periods/2)
    if Parameter.demand_distr == 'uniform':
        demand_adj_factor =[1 for i in range(no_of_time_periods)]
    # If distr is not uniform, make demand peak and then drop over the time periods
    else:
        demand_adj_factor = [i + 1 if i < no_of_time_periods / 2 else no_of_time_periods - i for i in                             range(no_of_time_periods)]
    # Convert to pmfs
    demand_adj_factor = [i/sum(demand_adj_factor) for i in demand_adj_factor]
    print(demand_adj_factor)
    # Populate time window od tables based on these adjustment factors
    # Divide this value by 2, because original odtable has demand for 60 minutes, we need to create demand for 30 min time periods
    # Multiply this by (no_of_time_periods), because odtable demand is only for one hour and each time period is 30 minutes
    # Also extract actual demand for shared rides by using mode share parameter
    odtable_time =[odtable * Parameter.shared_ride_mode_share * demand_adj_factor[t]/2 * no_of_time_periods for t in range(no_of_time_periods)]
# 24 hour simulation
else:
    # Creating multiple OD tables based on simultation time
    # Entry in the original OD tables is the average trips per hour for AM period
    # Split it into AM, MID, PM, NIGHT, EARLY (0,1,2,3,4)

    # Create list of dataframes, one for each timeperiod
    # t=0,AM: 0600-1000
    # t=1,MID: 1000-1500
    # t=2,PM: 1500-1900
    # t=3, NIGHT: 1900-0300
    # t=4, EARLY:0300-0600

    # List to store relative demand of time periods wrt AM
    demand_adj_factor = [1, 0.6, 0.85, 0.3, 0.1]
    # List to store number of hours in each time period
    no_of_hours = [4, 5, 4, 8, 3]

    # Find od table for each time period

    odtable_time = [odtable * Parameter.shared_ride_mode_share * demand_adj_factor[t] * no_of_hours[t] for t in
                    range(5)]

    # # Test
    #
    # print(odtable.loc[1, 2] * Parameter.shared_ride_mode_share)
    # for t in range(5):
    #     print(odtable_time[t].loc[1, 2])
    # print("Total trips in OD tables for each time period ")
    # for t in range(5):
    #     print("Time period ", t)
    #     print(odtable_time[t].to_numpy().sum())
    #     print("Trip rate (per hour)", odtable_time[t].to_numpy().sum() / no_of_hours[t])

# Test
# print(Parameter.shared_ride_mode_share * odtable.to_numpy().sum())
# print(odtable.loc[1,2])
# for t in range(no_of_time_periods):
#     print(odtable_time[t].loc[1,2])


print("Anaheim Demand and Network Loaded ")

# Identify external stations

external_stations = [7,86,23,22,21,5,20,19,18,17,4,16,3,15,14,2,13,26,12,1,11,29,10,9,8]


# Identify zone centroids to remove
# Demand to be spread across actual nodes instead of zone centroids
centroids_to_remove = [37,34,30,24,25,26,31,27,28,32,33,29,35,36,38]
centroids_to_remove = sorted(centroids_to_remove)
# print("No of external stations ",len(external_stations))



origins = [str(k) for k in list(odtable.index)]
destinations = [str(k) for k in list(odtable.columns)]








# Find nodes that are associated with freeway links
freeway_nodes = []
# Find links that are on freeways
freeway_edges = []
# Find links that are freeway ramps
freeway_ramps = []
all_freeway_edges = []
for s,e,data in road_network.edges(data=True):
    # Pre-process
    # Round all link travel times to one decimal digit precision
    data['traveltime'] = round(data['traveltime'],1)
    # Pre-process, increase travel times on centroid connectors
    if data['speed'] == 8855:
        data['traveltime'] = 2
    if data['speed'] == 4842:
        all_freeway_edges.append((s,e))
    # Check if it is a freeway link (based on speed limit)
    if data['speed'] == 4842 and int(s) not in external_stations and int(e) not in external_stations:  # Speed limit on freeways
        freeway_edges.append((s, e))
        if s not in freeway_nodes:
            freeway_nodes.append(s)
        if e not in freeway_nodes:
            freeway_nodes.append(e)

# Check for ramps

for s,e in road_network.edges():
    if (s in freeway_nodes and e not in freeway_nodes) or (s not in freeway_nodes and e in freeway_nodes):
        freeway_ramps.append((s,e))

# print("Number of freeway nodes: ",len(freeway_nodes))
# print("Number of freeway ramps: ",len(freeway_ramps))
# Allowed freeway edges: Edges from/to external station nodes on freeways
allowed_freeway_edges = [s for s in all_freeway_edges if s not in freeway_edges]
# print("Allowed freeway edges # ",len(allowed_freeway_edges))

# print("Number of freeway nodes that are not external stations: ",len(freeway_nodes))
# Remove freeway nodes that are connected to freeway external stations
for s,e in allowed_freeway_edges:
    if s in freeway_nodes:
        freeway_nodes.remove(s)
    if e in freeway_nodes:
        freeway_nodes.remove(e)

print("Number of freeway links ",len(freeway_edges))
print("Number of non permitted freeway nodes, ", len(freeway_nodes))
# Permitted nodes: All nodes in the network except for freeway nodes
permitted_nodes = [n for n in road_network.nodes() if n not in freeway_nodes]
print("Number of oermitted  nodes ",len(permitted_nodes))



# Test
print("Demand gen rate (per hour)",Parameter.shared_ride_mode_share * odtable.to_numpy().sum())
sum_trips=[odtable_time[t].to_numpy().sum() for t in range(no_of_time_periods)]
# print ("Requests in each time period (30 min) ")
# print(sum_trips)
# print(sum(sum_trips))




with open(network_name + "\\Revised\\Anaheim_SPskims.pickle", 'rb') as file:
    data = file.read()
SPSkims = pickle.loads(data)
# Test
# print("SPSkim ", SPSkims[('1', '15')])
# print("SPSkim ", SPSkims[('169', '168')])



# print("Centroids to remove ",centroids_to_remove)
# List of nodes in network

network_nodes = road_network.nodes()
