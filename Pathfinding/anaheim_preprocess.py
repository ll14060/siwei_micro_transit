from read_network import odtable,external_stations,freeway_nodes,centroids_to_remove,road_network
import pandas as pd
import geopandas as gpd
import networkx as nx
# New OD table to include more nodes, by extrapolating demand from other zones
revised_odtable = pd.DataFrame()
nodes_zones = gpd.read_file(r"I:\UCI\GSR Projects\Bi-criterion Path Finding for shared Vehicles\Read Network from TNTP\Anaheim\shape_file\Node_Zone_Spatial_Join.shp")
freeway_nodes = [int(f) for f in freeway_nodes]


# print(nodes_zones.columns)
# Exclude nodes that are on freeways, but not external stations
nodes_zones = nodes_zones[~nodes_zones['id'].isin(freeway_nodes)]
print("Number of nodes after removing freeway nodes ",len(nodes_zones))
print(odtable.index)
print(odtable.columns)
print(len(odtable.index))
print(len(odtable.columns))

#print(len(nodes_zones))
# print(nodes_zones.columns)
# print(len(nodes_zones[nodes_zones['dist_miles'] >= 1.1]))


# Maximum distance from zone to node to extract demand from
max_node_zone_dist = 10 # 1.1 miles
min_node_zone_dist = 0.1
# id is node id, id_1 is the nearest zone id


del_counter = 0
for o in odtable.index:
    # Find all nodes which have zone o closest to them and within the max dist threshold
    nearby_os = nodes_zones[(nodes_zones['id_1'] == o) & (nodes_zones['dist_miles'] <= max_node_zone_dist) & (nodes_zones['dist_miles'] > min_node_zone_dist)][['id','dist_miles']]




    for d in odtable.columns:
        # O-D pairs and distances
        # Distance is the sume of the origin node from origin zone and dest node from dest zone
        # This calculation is to weigh trips from O and D zones to nearby nodes based on how far they are from the centrodis
        ods = {}
        # Skip intrazonal trips
        if o == d:
            continue
        # Find nearby destination nodes
        nearby_ds = nodes_zones[(nodes_zones['id_1'] == d) & (nodes_zones['dist_miles'] <= max_node_zone_dist) & (
                        nodes_zones['dist_miles'] > min_node_zone_dist)][['id', 'dist_miles']]
        # Dict[(o,d)] = combined distance
        ods[(o,d)] = 0
        # If no nodes have o or d as closest zone
        if len(nearby_os) == 0 and len(nearby_ds) == 0:
            ods[(o, d)] = 1
        # Else, other cases
        else:
            # If no origin nodes have origin zone as their closest
            # Then spread to all nodes close to destination
            if len(nearby_os) == 0:
                for index,row in nearby_ds.iterrows():
                    ods[(o, int(row['id']))] = round(row['dist_miles'], 2)

            # If no nodes close to destination zone
            # Then spread from nodes close to origin zone to destination
            elif len(nearby_ds) == 0:
                for index,row in nearby_os.iterrows():
                    ods[(int(row['id']),d)] = round(row['dist_miles'], 2)


            else:
                # Find combinations of o-d
                od_combinations_df = nearby_os.merge(nearby_ds,how='cross')
                # print(od_combinations_df[0:5])
                # print(len(nearby_os),len(nearby_ds),len(od_combinations_df))
                for index,row in od_combinations_df.iterrows():
                    ods[(int(row['id_x']),int(row['id_y']))] = round(row['dist_miles_x'] + row['dist_miles_y'],2)


            delete_ods = []
            # Remove all o-d pairs that are in centroids that need to be removed
            for orig,dest in ods.keys():
                if orig in centroids_to_remove or dest in centroids_to_remove:
                    delete_ods.append((orig,dest))
                    del_counter += 1
            [ods.pop(key) for key in delete_ods]
            # Invert values by subtracting from max, to make lower distances have higher weights
            ods = {k:max(ods.values())-ods[k] for k in ods.keys()}

            # Rescale to make sum of values to 1
            ods = {k:ods[k]/sum(ods.values()) for k in ods.keys()}
            ods = {k:round(ods[k],2) for k in ods.keys()}
            # print(ods)
            # print(sum(ods.values()))



        # Spread out demand from Origin Zone to Dest Zone to all nearby od pairs based on the weights calculated above
        demand_reduction_factor = 1.0
        # Reduce demand to 20% of original value if any of the zones are external stations
        if o in external_stations or d in external_stations:
            demand_reduction_factor = 0.2
        # Create new entry in the revised od table
        for src,dest in ods.keys():
            revised_odtable.loc[src,dest] = round(demand_reduction_factor * odtable.loc[o,d] * ods[(src,dest)],1)


# Replace all null values with 0
revised_odtable.fillna(0,inplace=True)
print("Total trips in original od table", odtable.to_numpy().sum())

print("Total trips in revised od table ",revised_odtable.to_numpy().sum())
# Save to file
revised_odtable.to_csv(r'I:\UCI\GSR Projects\Bi-criterion Path Finding for shared Vehicles\Read Network from TNTP\Anaheim\anaheim_revised_odtable_excl_freeways_and_centroids.csv')
print("Done revising OD table")
print("No of od pairs removed ",del_counter)


# Remove centroids and centroid connectors from original network
edges_to_delete = []
for s,e in road_network.edges():
    if int(s) in centroids_to_remove or int(e) in centroids_to_remove:
        edges_to_delete.append((s,e))
centroids_to_remove = [str(c) for c in centroids_to_remove]
print("No of links and nodes before removing centroid connectors ",road_network.number_of_edges(),road_network.number_of_nodes())
road_network.remove_edges_from(edges_to_delete)
road_network.remove_nodes_from(centroids_to_remove)
print("No of links and nodes after removing centroid connectors ",road_network.number_of_edges(),road_network.number_of_nodes())
# Save new network to pickle file
nx.write_gpickle(road_network,r'I:\UCI\GSR Projects\Bi-criterion Path Finding for shared Vehicles\Read Network from TNTP\Anaheim\anaheim_network_revised.pickle')











# # Find travel time skims
# # # Save shortest path costs and skims
SPSkims = {}
import pickle
for o in road_network.nodes():
    for d in road_network.nodes():
        cost = 0
        path = []
        if not nx.has_path(road_network,o,d):
            cost = float('inf')
        else:
            cost = round(nx.shortest_path_length(road_network,o,d,'traveltime'),1)
            path = nx.shortest_path(road_network,o,d,'traveltime')
        SPSkims[(str(o),str(d))] = [cost,path]
        print(o,d)

data = pickle.dumps(SPSkims)
with open(r'I:\UCI\GSR Projects\Bi-criterion Path Finding for shared Vehicles\Read Network from TNTP\Anaheim\Anaheim_SPskims.pickle','wb') as file:
    file.write(data)

# Find K Shortest Paths



import json
from itertools import islice
# Function to find path length along a given path based on given weight attribute
def pathLength(G ,path ,weight):
    path_length =0
    for i in range(0 ,len(path ) -1):
        path_length +=G[path[i]][path[ i +1]][weight]
    return path_length

# Function to enumerate k shortest paths between source and target
def k_shortest_paths(G ,source ,target ,k ,weight='traveltime'):
    return list(islice(nx.shortest_simple_paths(G ,source ,target ,weight=weight) ,k))

# Function to compute k shortest paths for all O-D pairs
# And remove paths that exceed the max detour ratio

def findKPaths(network ,origins, destinations):

    count = 0


    ksp ={}
    # Find k shortest paths between each O and D
    for o in origins:
        ksp[o] ={}
        for d in destinations:

            if o == d:
                continue
            if nx.has_path(network ,o ,d) == False:
                continue
            count = count + 1
            paths =k_shortest_paths(network ,o ,d ,5 ,'traveltime')
            ksp[o][d] =paths
            print (" Paths between " ,count ," OD pairs calculated ")
    return ksp


output_path=r'I:\UCI\GSR Projects\Bi-criterion Path Finding for shared Vehicles\Read Network from TNTP\Anaheim'
origins = road_network.nodes()
dest = road_network.nodes()
origins = [str(o) for o in origins]
dest = [str(d) for d in dest]
ksp=findKPaths(road_network,origins,dest)




# Save as pickle file
data = json.dumps(ksp)
with open(r'I:\UCI\GSR Projects\Bi-criterion Path Finding for shared Vehicles\Read Network from TNTP\Anaheim\anaheim_k_paths.json',"w") as f:
    f.write(data)
f.close()