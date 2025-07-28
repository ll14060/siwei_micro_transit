import demand_weights as dwt
import Graph2Shape as gs
from Path_Finding import road_network
import copy
import networkx as nx
from OD_Demand import demandTable1

origin = '1'
des = '15'
time_period = 1
net = copy.deepcopy(road_network)
# Retrieve demand on each link
demand_links = dwt.lookup_demand_weights(origin,des,time_period)
# Find total demand from each node
orig_demand = {}
orig_demand_link = {}
print (type(demandTable1))
for i in range(1,25):
    o = i-1
    demand = sum(demandTable1[o])
    orig_demand[str(i)] = demand
    orig_demand_link[str(i)] = round(demand / len(net.out_edges(str(i))),1)
print ("Origin Demand ",orig_demand)
print ("Origin Demand per outgoing link ",orig_demand_link)




# K Paths
ksp = dwt.k_shortest_paths(net,origin,des,5,'traveltime')
print (ksp)
# Find shortest path from origin to destiantion
sp = nx.shortest_path(net,origin,des,'traveltime')
sp_2 = ksp[4]
# Find the links in given path
# Input: List of nodes in path
# Output: List of links in Path returned as list of tuples
def find_links_in_path(path):
    tt = 0
    dem = 0
    links_in_tuples=[]
    for n in range(0,len(path)-1):
        s = path[n]
        e = path[n+1]
        links_in_tuples.append((s,e))
        n += 1
        tt += net[s][e]['traveltime']
        dem += demand_links[(s,e)]
    print("Travel time ",tt)
    print("Demand ",dem)
    return links_in_tuples

print ("Shortest Path",sp , "Shortest Path Length ", nx.shortest_path_length(net,origin,des,'traveltime'))
print ("Alternative Path",sp_2)
print ("Shortest Path links ",find_links_in_path(sp_2))

links_in_sp = find_links_in_path(sp)
links_in_alternative_path = find_links_in_path(ksp[4])

# Add link weights to each origin
for s,e in net.edges():
    net[s][e]['pot_demand'] = round(demand_links[(s,e)],1)
    net[s][e]['all_demand'] = orig_demand_link[s]
    if (s,e) in links_in_sp:
        net[s][e]['in_sp'] = 'True'
    else:
        net[s][e]['in_sp'] = 'False'
    if (s,e) in links_in_alternative_path:
        net[s][e]['in_ap'] = 'True'
    else:
        net[s][e]['in_ap'] = 'False'
for n in net.nodes():
    net.nodes[n]['node_id'] = n
    if n == origin:
        net.nodes[n]['node_type'] = 'Origin'
    elif n == des:
        net.nodes[n]['node_type'] = 'Destination'
    else:
        net.nodes[n]['node_type'] = 'Other'

for s, e in net.edges():
    print(net[s][e])
    break

for n in net.nodes():
    print(net.nodes[n])
    break

# Convert to Shape File

# net=gs.reLocateLinks(net, offset=5000)
# gs.NetworkX2_Links_Shapefile(net,'Demand_Visualization_all_demand')
# gs.NetworkX2_Nodes_Shapefile(net,'Demand_Visualization_all_demand')