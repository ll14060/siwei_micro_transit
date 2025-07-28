import networkx as nx
import random
from Path_Finding import road_network
from scipy.stats import describe

tt_list=[]
for s,e,val in road_network.edges(data=True):
    tt_list.append(val['traveltime'])


tt_norm=[]
for s,e,val in road_network.edges(data=True):
    val['traveltime_norm'] = 4 * ((val['traveltime'] - min(tt_list))/(max(tt_list) -min(tt_list))) + 1

    tt_norm.append(val['traveltime_norm'])
print(min(tt_norm),max(tt_norm))
SP = nx.shortest_path(road_network,'1','10','traveltime')

tt_sp = [ road_network[SP[i]][SP[i+1]]['traveltime'] for i in range(len(SP)-1)]
ntt_sp = [ road_network[SP[i]][SP[i+1]]['traveltime_norm'] for i in range(len(SP)-1)]
print("Travel time on SP links ",tt_sp)
print("Norm Travel Time on SP links",ntt_sp)
print ("Total Travel time on SP ",nx.shortest_path_length(road_network,'1','10','traveltime'))
print("Total Norm TT on SP ",sum(ntt_sp))
SP2 = nx.shortest_path(road_network,'1','10','traveltime_norm')
tt_sp2 = [ road_network[SP2[i]][SP2[i+1]]['traveltime'] for i in range(len(SP2)-1)]
ntt_sp2 = [ road_network[SP2[i]][SP2[i+1]]['traveltime_norm'] for i in range(len(SP2)-1)]
print(" Travel Time on SP2 links ",tt_sp2)
print(" Total Travel Time on SP2 ",sum(tt_sp2))
print("Normal Travel Time on SP2 links ",ntt_sp2)
print ("Total Norm Travel Time on SP2 ",nx.shortest_path_length(road_network,'1','10','traveltime_norm'))

print ("SP ", SP)
print("SP norm ", SP2)
print (SP == SP2)

count_true = 0
count_false = 0
false_od=[]
origins = [str(i) for i in range(1,25)]
dest = [str(i) for i in range(1,25)]

# Check if SPs are same

for o in origins:
    for d in dest:
        if o == d:
            continue
        SP = nx.shortest_path(road_network,o,d,'traveltime')
        SP2 = nx.shortest_path(road_network, o, d, 'traveltime_norm')
        if SP == SP2:
            count_true += 1
        else:
            count_false += 1
            false_od.append((o,d))


print("True count ",count_true)
print("Mismatch ",count_false)
print("Mismatching ods ",false_od)
#print(describe(tt_list))