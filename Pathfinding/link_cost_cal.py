from Path_Finding import road_network
from demand_weights import ksp
import networkx as nx
import time
import Parameter as para

# Create dictionry of link costs
# Link_tt = {(1,3):[5,[1, 2, 3]]}
# Link_tt = {(O,D):[Total time, [Path]]}
start = time.time()
def cal_OD_tt():

    origins= [str(i) for i in range(1,25)]
    destinations= [str(i) for i in range(1,25)]
    od_tt={}
    for o in origins:
        for d in destinations:
            if o == d:
                od_tt[(o,d)] = [0, [o,d]]
            else:
                sp_time=nx.dijkstra_path_length(road_network,o,d,'traveltime')
                shortest_path= nx.dijkstra_path(road_network, o, d, 'traveltime')
                #shortest_path = ksp[o][d][0]
                od_tt[(o,d)] =[sp_time,shortest_path]
    return od_tt



if para.network_name != 'Anaheim':
    od_tt=cal_OD_tt()
else:
    from read_network import SPSkims
    od_tt = SPSkims
end= time.time()
# print('OD_tt generate time ', end - start)
# # print(od_tt[('1','4')])
# print(od_tt)






