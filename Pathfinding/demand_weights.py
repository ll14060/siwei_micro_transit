import networkx as nx
import Parameter
from itertools import islice
if Parameter.network_name == 'Anaheim':
    from read_network import road_network,odtable

else:
    from Path_Finding import  road_network
    from OD_Demand import demandTable1, demandTable2, demandTable3, demandTable4


# Function to enumerate k shortest paths between source and target
def k_shortest_paths(G,source,target,k,weight=None):
    return list(islice(nx.shortest_simple_paths(G,source,target,weight=weight),k))

# Function to find k shortest paths between all origins and destinations
# k=5 for now


def findKPaths():

    # Network uses string data type nodes '1' to '24'
    # Demand table uses integer type node numbers 0 to 23
    # Be careful to avoid conflict and do appropriate typecast


    origins=[str(k) for k in range(1,25)]
    destinations=[str(k) for k in range(1,25)]
    # ksp: dictionary[o][d]=list of paths
    ksp={}
    # Find k shortest paths between each O and D
    for o in origins:
        ksp[o]={}
        for d in destinations:
            if o == d:
                continue
            if nx.has_path(road_network,o,d) == False:
                continue
            # Find 3 paths between o and d
            paths=k_shortest_paths(road_network,o,d,5,'traveltime')
            ksp[o][d]=paths
    # Paths is a list of node names
    return ksp
# Function call to find k shortest paths for all O-D pairs

# Dictionary with ksp[o][d]=list of paths
# ksp[o][d][0] gives list of nodes on the shortest path
if Parameter.network_name == 'Anaheim':
    from read_network import ksp
else:
    ksp=findKPaths()


# Function to pre-compute demand weights for all o-d pairs for a given demand time period
# Returns a dictionary of form dict[o][d][link]=link weight
def pre_compute_demand_weights(demand_time_period):

    odtable = demandTable1

    # Select demand table
    if demand_time_period == 2:
        odtable=demandTable2
    elif demand_time_period == 3:
        odtable=demandTable3
    else:
        odtable=demandTable4
    # For Sioux Falls
    origins = [str(k) for k in range(1,25)]
    destinations = [str(k) for k in range(1,25)]
    if Parameter.network_name == 'Anaheim':
        from read_network import odtablenp as odtable
        from read_network import origins,destinations

    # dwt: Dictionary with dwt[o][d][link]=weight structure 3 tier dictionary
    # link is in tuple format (sting start_node, string end node)
    dwt = {}
    # Find k shortest paths between each O and D
    for o in origins:
        dwt[o] = {}
        for d in destinations:

            # Store nodal demands for this o-d combination
            # Dictionary: key=node string value=nodal demand
            # Initialize to 0
            nodal_demand={k:0 for k in origins}
            if o == d:
                continue
            if nx.has_path(road_network, o, d) == False:
                continue
            # Initalize link weights to 0 for all links
            dwt[o][d] = {k: 0 for k in road_network.edges}
            # Find the set of all intermediate nodes in 3 shortest paths
            set1=ksp[o][d][0]
            set2 = ksp[o][d][1]
            set3 = ksp[o][d][2]
            inter_nodes = list(set(set1)|set(set2)|set(set3))
            # Find downstream nodes
            down_nodes = list(set(origins).difference(set(inter_nodes)))
            # Find nodal demand from all intermediate nodes
            for i in inter_nodes:
                # Add demand between all intermediate nodes onto nodal demands
                for j in inter_nodes:
                    if i==j:
                        continue
                    # Extract demand from od table
                    # Cast i and j
                    source=int(i)-1
                    dest = int(j)-1
                    demand = odtable[source][dest]
                    # Add to nodal demand
                    nodal_demand[i]=nodal_demand[i]+demand
                # End of j loop
            # Find demand to downstream nodes that pass through destination
            for down in down_nodes:
                # Check if destination node is in the shortest path to downstream node:
                if d in ksp[o][down][0]:
                    # Add demand to downstream node to nodal demand
                    # Typecast o,d to read data from table
                    source = int(i) - 1
                    dest = int(down) - 1
                    demand = odtable[source][dest]
                    # Add to nodal demand
                    nodal_demand[i] = nodal_demand[i] + demand


            # End of i loop: End of computing nodal demands for this o-d combination

            # Find link weights from nodal demands
            for i in inter_nodes:
                # Find all outgoing edges for each intermediate node
                outgoing_edges = road_network.out_edges([i])
                # Find the number of outgoing edges
                count_outgoing_edges = len(outgoing_edges)
                # Divide nodal demand by the number of outgoing edges and add to each link weight
                node_link_wt = nodal_demand[i] /count_outgoing_edges
                # Add this value to each outgoing edge for this o-d combination
                for edge in outgoing_edges:
                    dwt[o][d][edge]=dwt[o][d][edge] + node_link_wt
                # End of outgoing edges
            # End of inter nodes loop i
        # End of destinations loop
    # End of origins loop
    return dwt


# Function call to pre-compute demand weights for all links for all O-D combinations
dwt_1=pre_compute_demand_weights(1)
dwt_2=pre_compute_demand_weights(2)
dwt_3=pre_compute_demand_weights(3)
dwt_4=pre_compute_demand_weights(4)

# Look up Function to return link demand weights for given O-D pair and Time period
# o and d are locations in string datatype
# Increment by 1 and convert to string for use in network
# Returns dictionary of form {link:weight} where link is a tuple (source_node,destination_node)

def lookup_demand_weights(origin,destination,demand_time_period):
    # Typecast o and do to comply with network data structure:
    # o=str(origin + 1)
    # d=str(destination + 1)
    o = origin
    d = destination
    if demand_time_period == 1:
        return dwt_1[o][d]
    elif demand_time_period == 2:
        return dwt_2[o][d]
    elif demand_time_period == 3:
        return dwt_3[o][d]
    else:
        return dwt_4[o][d]


# print(lookup_demand_weights(0,11,1))