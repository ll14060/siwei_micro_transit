# Note: Demand table has origins and destinations as integer type

import networkx as nx
import Parameter
from itertools import islice
from read_network import road_network,odtable,odtable_time,no_of_time_periods,ksp,freeway_nodes,origins,destinations,freeway_edges,freeway_ramps,anaheim_nodes_gis,SPSkims
import pickle
import time
import math
import shapely

# Function to find time period for 24 hour simulation
def find_time_period_24_hour(t):
    # AM (0600 - 1000)
    if t < 240:
        return 0
    # MID (1000 - 1500)
    elif t < 540:
        return 1
    # PM (1500 - 1900)
    elif t < 780:
        return 2
    # NIGHT (1900 - 0300)
    elif t < 1260:
        return 3
    # EARLY MORNING (0300 - 0600)
    else:
        return 4
# Function to find the nearby node with the highest demand for a given location
# For relocation purpose
# Return location (node id) with highest demand in the current time window

def find_nearby_demand_node(current_location,current_time):

    origin = int(current_location)
    # Retrieve coordinates of origin
    o_x = anaheim_nodes_gis[anaheim_nodes_gis['id'] == origin]['geometry'].x.iloc[0]
    o_y = anaheim_nodes_gis[anaheim_nodes_gis['id'] == origin]['geometry'].y.iloc[0]
    center = (o_x,o_y)
    # Draw a buffer around the current location with a euclidean radius of 2.5 miles
    buf = shapely.geometry.Point(center).buffer(2.5 * 5280)
    # Find all nodes within the buffer
    mask = anaheim_nodes_gis.within(buf)
    nearby_nodes = anaheim_nodes_gis.loc[mask, 'id'].to_list()

    nearby_nodes = [n for n in nearby_nodes if str(n) in origins]

    # Find the demand node from nearby nodes with the highest demand for the given time period
    if Parameter.SimTime == 180:
        demand_time_period = int(current_time/30)
    else: # 24 hour simulation
        demand_time_period = find_time_period_24_hour(current_time)
    if current_time >= Parameter.SimTime:
        demand_time_period = no_of_time_periods - 1
    max_demand = 0
    max_demand_node = str(current_location)
    for n in nearby_nodes:
        demand = odtable_time[demand_time_period].loc[n,:].to_numpy().sum()
        if demand > max_demand:
            max_demand = demand
            max_demand_node = str(n)

    return max_demand_node

# Function to find en-route demand nodes between an origin and a destination
# o and d are integers
# max_detour is in miles, euclidean distance in miles
def find_enroute_nodes(origin,destination):


    # Find centre of ellipse
    origin = int(origin)
    destination = int(destination)
    # Find coordinates of origin and destination
    o_x = anaheim_nodes_gis[anaheim_nodes_gis['id'] == origin]['geometry'].x.iloc[0]
    o_y = anaheim_nodes_gis[anaheim_nodes_gis['id'] == origin]['geometry'].y.iloc[0]
    d_x = anaheim_nodes_gis[anaheim_nodes_gis['id'] == destination]['geometry'].x.iloc[0]
    d_y = anaheim_nodes_gis[anaheim_nodes_gis['id'] == destination]['geometry'].y.iloc[0]

    # Calculate distance in feet
    dist = ((o_x - d_x)**2 + (o_y - d_y)**2)**0.5
    # Find max detour, either based on absolute or relative value
    # It is either 25% of trip length or a maximum of 5 miles, whichever is less
    max_detour = 0.25 * dist
    if max_detour >= 5*5280:
        max_detour = 5 * 5280
    # Find ellipse parameters
    centre_x = (o_x + d_x) / 2
    centre_y = (o_y + d_y) / 2
    # Find length of major axis and minor axis
    trip_length_eucledian = dist
    # Major axis length is the length of the trip (that connects the focal points of the ellipse)
    # and the maximum detour that is allowed
    # Ellipse is constructed with the origin and destiantion as its foci
    # And major axis as trip length+max detour
    # Using ellipse property that sume of the focal distances of any point on the ellipse = major axis length
    major_axis = trip_length_eucledian + max_detour
    a = major_axis / 2
    c = trip_length_eucledian / 2
    eccentricity = c / a
    b = a * math.sqrt(1 - math.pow(eccentricity, 2))
    # a,b represent semi major axis values
    # Find angle between trip and x axis
    alpha = math.atan2(d_y - o_y, d_x - o_x)
    # Convert to degrees
    alpha = alpha * 180 / math.pi
    # Ellipse Parameters
    # Center,major/minor axes,angle with x-axis
    ellipse = ((centre_x, centre_y), (a, b), alpha)
    # Create a unit circle around center point
    circ = shapely.geometry.Point(ellipse[0]).buffer(1)
    # Create ellipse along x and y
    ell = shapely.affinity.scale(circ, int(ellipse[1][0]), int(ellipse[1][1]))
    # Rotate the ellipse to get the Detour Zone
    detour_zone = shapely.affinity.rotate(ell, ellipse[2])

    mask = anaheim_nodes_gis.within(detour_zone)
    nodes_enroute = anaheim_nodes_gis.loc[mask,'id'].to_list()

    # Remove freeway nodes and other 'non demand' nodes from nodes enroute
    nodes_enroute = [str(i) for i in nodes_enroute if str(i) not in freeway_nodes and str(i) in origins]

    return nodes_enroute


# Function to pre-compute demand weights for all o-d pairs for a given demand time period
# Returns a dictionary of form dict[o][d][link]=link weight
def pre_compute_demand_weights(demand_time_period=0):
    # dwt: Dictionary with dwt[o][d][link]=weight structure 3 tier dictionary
    # link is in tuple format (sting start_node, string end node)
    dwt = {}
    # Find k shortest paths between each O and D
    od_counter = 0
    for o in origins:
        dwt[o] = {}
        for d in destinations:
            od_counter += 1
            print("Time period ",demand_time_period," # OD pairs ",od_counter)
            # Store nodal demands for this o-d combination
            # Dictionary: key=node string value=nodal demand
            # Initialize to 0
            nodal_demand={k:0 for k in origins}
            if o == d:
                continue
            # if nx.has_path(road_network, o, d) == False:
            #     continue
            # Initalize link weights to 0 for all links
            dwt[o][d] = {k: 0 for k in road_network.edges}
            # # Find the set of all intermediate nodes in 3 shortest paths
            # set1 = ksp[o][d][0]
            # set2 = []
            # set3 = []
            # if len(ksp[o][d]) >= 2:
            #     set2 = ksp[o][d][1]
            # if len(ksp[o][d]) >= 3:
            #     set3 = ksp[o][d][2]
            # Change code here to include new method to find en-route nodes
            inter_nodes = find_enroute_nodes(int(o),int(d))

            # Find downstream nodes
            down_nodes = list(set(origins).difference(set(inter_nodes)))
            # Remove all downstream freeway nodes and non destination nodes
            down_nodes = [d for d in down_nodes if d not in freeway_nodes and d in destinations]
            # Only keep down stream nodes whose shortest path from an intermediate node pass through the destination node
            down_nodes = [down for down in down_nodes for i in inter_nodes if d in ksp[i][down][0]]
            # ------ The below method has been changed to reflect All or Nothing SP assignment on links
            # Find nodal demand from all intermediate nodes
            # for i in inter_nodes:
            #     # Add demand between all intermediate nodes onto nodal demands
            #     for j in inter_nodes:
            #         if i==j:
            #             continue
            #         # Extract demand from od table
            #         # Cast i and j
            #         source=int(i)
            #         dest = int(j)
            #         demand = odtable.loc[source,dest]
            #         # Add to nodal demand
            #         nodal_demand[i]=nodal_demand[i]+demand
            #     # End of j loop
            #     # Find demand to downstream nodes that pass through destination
            #     # Change made to also include demand to downstream nodes from intermediate nodes
            #     for down in down_nodes:
            #         # Check if destination node is in the shortest path to downstream node:
            #         if d in ksp[i][down][0]:
            #             # Add demand to downstream node to nodal demand
            #             # Typecast o,d to read data from table
            #             source = int(i)
            #             dest = int(down)
            #             demand = odtable.loc[source, dest]
            #             # Add to nodal demand
            #             nodal_demand[i] = nodal_demand[i] + demand

            # End of i loop: End of computing nodal demands for this o-d combination

            # Find link reward values based on demand between all inter nodes to inter nodes + down nodes
            for i in inter_nodes:
                # Find all outgoing edges for each intermediate node
                outgoing_edges = road_network.out_edges([i])
                # Exclude freeway edges and freeway ramps from outgoing edges
                outgoing_edges = [e for e in outgoing_edges if e not in freeway_edges+freeway_ramps]
                # Find the number of outgoing edges
                count_outgoing_edges = len(outgoing_edges)
                # Check this
                if count_outgoing_edges == 0:
                    continue
                # Change to All or Nothing SP assignment here
                # Check if the edge is present in the shortest path from o to inter or down nodes
                # If present, then add demand to that link
                for edge in outgoing_edges:
                    for n in inter_nodes+down_nodes:
                        if i == n:
                            continue
                        # SPSkims[(i,n)][1][1] gives the immediate node on the SP from i to n
                        if edge[1] == SPSkims[(i,n)][1][1]:
                            dwt[o][d][edge]=dwt[o][d][edge] + odtable_time[demand_time_period].loc[int(i),int(n)]
                # End of outgoing edges
            # End of inter nodes loop i
        # End of destinations loop
    # End of origins loop
    return dwt


# Pre compute demand weights for all O-D pairs for all time periods.
# Save to pickle
# Stored as a list of dictionaries
# Each index in list corresponds to time period
# Dictionary key dict[o][d][link]


# file_name = Parameter.network_name + r'\Demand_Link_Rewards\ellipse_t_0_anaheim_simtime_'+str(Parameter.SimTime)+'_demtime_'+str(Parameter.DemandTime)+'_modeshare_'+str(Parameter.shared_ride_mode_share)+".pickle"
# start = time.time()
#
# # demand_link_weights_time = [pre_compute_demand_weights(t) for t in range(no_of_time_periods)]
# # For now, due to long run time, computing link rewards for different time periods based on demand adj factor
# # Due to long run time
# from read_network import demand_adj_factor
# demand_link_weights_time = []
# demand_link_weights_time = demand_link_weights_time + [pre_compute_demand_weights(0)]
# # Save to pickle file
#
# data = pickle.dumps(demand_link_weights_time)
# with open(file_name,'wb') as file:
#     file.write(data)
# print(f'Time to Calculate Demand Link Weights: {time.time() - start}')
# # Imputing rewards for other time periods (This can be done because we know the demand distribution)
# # Imputed from the adjustment factors
# start = time.time()
# for t in range(1,no_of_time_periods):
#     dwt = {}
#     for o in origins:
#         od_counter = 0
#         dwt[o] = {}
#         for d in destinations:
#             od_counter += 1
#             print("Time period ", t, " # OD pairs ", od_counter)
#             if o == d:
#                 continue
#             dwt[o][d] = {k: round(demand_link_weights_time[0][o][d][k] * (demand_adj_factor[t]/demand_adj_factor[0]),1) for k in demand_link_weights_time[0][o][d].keys()}
#     demand_link_weights_time = demand_link_weights_time + [dwt]
#
# data = pickle.dumps(demand_link_weights_time)

# with open(file_name,'wb') as file:
#     file.write(data)
# print(f'Time to Impute Demand Link Weights: {time.time() - start}')
# Load from file
start = time.time()
# 3 hour am period simulation
if Parameter.SimTime == 180:
    if Parameter.demand_distr == 'uniform':
        file_name = Parameter.network_name + r'\Demand_Link_Rewards\ellipse_t_180_mins_uniform_anaheim_demtime_30_modeshare_0.05.pickle'
    else:
        file_name = Parameter.network_name + r'\Demand_Link_Rewards\ellipse_t_all_anaheim_simtime_'+str(Parameter.SimTime)+'_demtime_'+str(Parameter.DemandTime)+'_modeshare_'+str(Parameter.shared_ride_mode_share)+".pickle"
# 24 hour simulation
elif Parameter.SimTime == 1440:
    file_name = Parameter.network_name + r'\Demand_Link_Rewards\ellipse_t_24hr_anaheim_demtime_' + str(
        Parameter.DemandTime) + '_modeshare_' + str(Parameter.shared_ride_mode_share) + ".pickle"
with open(file_name,'rb') as file:
     data = file.read()
demand_link_weights_time = pickle.loads(data)
print(f'Time to Load Demand Link Weights from Pickle : {time.time() - start}')
# # Look up Function to return link demand weights for given O-D pair and Time period
# o and d are locations in string datatype

# Returns dictionary of form {link:weight} where link is a tuple (source_node,destination_node)

def lookup_demand_weights(origin,destination,demand_time_period=1):
    # Typecast o and do to comply with network data structure:
    # o=str(origin + 1)
    # d=str(destination + 1)
    o = origin
    d = destination
    # Time period for cool down period post simulation
    if demand_time_period >= no_of_time_periods:
        demand_time_period = no_of_time_periods - 1
    return demand_link_weights_time[demand_time_period][o][d]


print(lookup_demand_weights('373','371',0)[('373','372')])
print(lookup_demand_weights('373','371',1)[('373','372')])
print(lookup_demand_weights('373','371',2)[('373','372')])
print(lookup_demand_weights('373','371',3)[('373','372')])
print(lookup_demand_weights('373','371',4)[('373','372')])
print(lookup_demand_weights('373','371',5)[('373','372')])

