import os
import csv
from collections import OrderedDict
import heapq
import network_algorithms as n_a
import pandas as pd

network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
asim_output_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/ActivitySim_output"
# time_periods = ["AM", "MD", "PM", "EV"]
# microtransit_scenarios = ["micro", "non_micro"]
microtransit_setup_scenarios = ["micro", "non_micro","micro_only"]
#
headway_scenarios = [20, 30, 60]
virtual_stop_scenarios = [50, 75, 100]

output_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"
mgra_pop_inc_dir=os.path.join(asim_output_folder,"MGRA_pop_inc.csv")

# Fleetpy_output_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/studies/example_study/results/example_pool_irsonly_sc_1"


def create_mgra_pop_income_table(study_area):
    #MGRA	population	avg_income

    if study_area == "downtown_sd":
        mgra_pop_inc_dir=os.path.join(asim_output_folder,"%s_MGRA_pop_inc.csv"% str(study_area))
        mgra_file_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
        mgra_file_dir = os.path.join(mgra_file_folder,"MGRA_study_area.csv")

    if study_area == "lemon_grove":
        mgra_pop_inc_dir=os.path.join(asim_output_folder,"%s_MGRA_pop_inc.csv"% str(study_area))
        mgra_file_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove"
        mgra_file_dir = os.path.join(mgra_file_folder,"Lemon_grove_MGRA.csv")

    large_sd_region_mgra = os.path.join(asim_output_folder,"larger_SANDAG_MGRA_income.csv")
    study_area_mgra_list=[]
    with open(mgra_file_dir) as f:
        csvreader = csv.DictReader(f)
        for data in csvreader:
            # MGRA = int(data["MGRA"])
            MGRA = int(data["MGRA"])
            if MGRA not in study_area_mgra_list:
                study_area_mgra_list.append(MGRA)
    f.close()
    with open(mgra_pop_inc_dir, 'w+', newline='') as csvfile:
        fieldnames = ["MGRA", "population", "avg_income"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        with open(large_sd_region_mgra) as f:
            csvreader = csv.DictReader(f)
            for data in csvreader:
                MGRA = int(data["MGRA"])
                if MGRA in study_area_mgra_list:
                    population = int(data["population"])
                    avg_income = float(data["avg_income"])
                    writer.writerow({"MGRA": MGRA, "population": population, "avg_income": avg_income})

        f.close()
    csvfile.close()

def create_adjacent_MGRA_file(study_area):

    if study_area == "downtown_sd":
        mgra_file_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
        mgra_file_dir = os.path.join(mgra_file_folder,"MGRA_study_area.csv")
        adjacent_mgra_dir = os.path.join(asim_output_folder, "%s_MGRA_adj.csv" % str(study_area))
        MGRA_nodes_mapping_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/MGRA_nodes_mapping"

    if study_area == "lemon_grove":
        mgra_file_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove"
        mgra_file_dir = os.path.join(mgra_file_folder, "Lemon_grove_MGRA.csv")
        adjacent_mgra_dir = os.path.join(asim_output_folder, "%s_MGRA_adj.csv" % str(study_area))
        MGRA_nodes_mapping_folder = "D:/Ritun/Siwei_Micro_Transit/Ritun/Lemon Grove/MGRA_Node_Mapping"

    MGRA_nodes_mapping_dir= os.path.join(MGRA_nodes_mapping_folder,"MGRA_Nodes_mapping.csv")
    study_area_mgra_list=[]
    with open(MGRA_nodes_mapping_dir) as f:
        csvreader = csv.DictReader(f)
        for data in csvreader:
            # MGRA = int(data["MGRA"])
            MGRA = int(data["MGRA"])
            if MGRA not in study_area_mgra_list:
                study_area_mgra_list.append(MGRA)
    f.close()

    blank_MGRA_list=[]
    non_blank_MGRA_list=[]
    with open(mgra_file_dir) as f:
        # MGRA	nodes
        csvreader = csv.DictReader(f)
        for data in csvreader:
            MGRA = int(data["MGRA"])
            if MGRA not in study_area_mgra_list:
                blank_MGRA_list.append(MGRA)
            else:
                non_blank_MGRA_list.append(MGRA)
    f.close()

    adj_mgra_dict=OrderedDict()
    for MGRA in blank_MGRA_list:
        up_mgra_num=0
        down_mgra_num=0
        adj_mgra_dict[MGRA]=[]
        for i in range(50):
            if (MGRA+i) in non_blank_MGRA_list:
                up_mgra_num+=1
                adj_mgra_dict[MGRA].append(MGRA+i)
                if up_mgra_num==2:
                    break
        for i in range(50):
            if (MGRA-i) in non_blank_MGRA_list:
                down_mgra_num+=1
                adj_mgra_dict[MGRA].append(MGRA-i)
                if down_mgra_num==2:
                    break


    with open(adjacent_mgra_dir, 'w+', newline='') as csvfile:
        fieldnames = ["Blank MGRA","Adjacent Non-Blank MGRAs"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for MGRA in adj_mgra_dict:
            adj_mgra_list=adj_mgra_dict[MGRA]
            adj_mgra_list_str=str(adj_mgra_list)
            adj_mgra_list_str_final=adj_mgra_list_str[1:-1]
            writer.writerow({"Blank MGRA": MGRA, "Adjacent Non-Blank MGRAs": adj_mgra_list_str_final})


    csvfile.close()


def get_MGRA_pop(study_area):
    if study_area == "downtown_sd":
        mgra_pop_inc_dir=os.path.join(asim_output_folder,"%s_MGRA_pop_inc.csv"% str(study_area))

    if study_area == "lemon_grove":
        mgra_pop_inc_dir=os.path.join(asim_output_folder,"%s_MGRA_pop_inc.csv"% str(study_area))
    MGRA_pop_percent=OrderedDict()
    MGRA_pop_dict = OrderedDict()
    tot_pop=0
    with open(mgra_pop_inc_dir) as f:
        csvreader = csv.DictReader(f)
        for data in csvreader:
            # MGRA = int(data["MGRA"])
            pop = int(data["population"])
            tot_pop += pop
    f.close()
    with open(mgra_pop_inc_dir) as f:
        csvreader = csv.DictReader(f)
        for data in csvreader:
            MGRA=int(data["MGRA"])
            pop=int(data["population"])
            MGRA_pop_dict[MGRA]=pop
            MGRA_pop_percent[MGRA]=pop/tot_pop

    f.close()
    return MGRA_pop_dict,MGRA_pop_percent

def get_blank_adjacent_MGRA(study_area):
    if study_area == "downtown_sd":
        adjacent_mgra_dir = os.path.join(asim_output_folder, "%s_MGRA_adj.csv" % str(study_area))

    if study_area == "lemon_grove":
        adjacent_mgra_dir = os.path.join(asim_output_folder, "%s_MGRA_adj.csv" % str(study_area))


    MGRA_adj_dict=OrderedDict()
    with open(adjacent_mgra_dir) as f:
        csvreader = csv.DictReader(f)
        for data in csvreader:
            blank_MGRA=int(data["Blank MGRA"])
            adjacent_mgra_list=str(data["Adjacent Non-Blank MGRAs"])
            if len(adjacent_mgra_list)<=4:
                adjacent_mgra=int(adjacent_mgra_list)
            else:
                adjacent_mgra = int(adjacent_mgra_list.split(',')[0])
            MGRA_adj_dict[blank_MGRA]=adjacent_mgra

    f.close()
    return MGRA_adj_dict





def get_fleetpy_demand_nodes():
    # network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
    pre_node_dir = os.path.join(network_folder, 'pre_nodes.csv')
    # pre_node_dir
    # census_tract	node_in_fleetpy	is_demand_node
    census_tract_node = OrderedDict()
    node_census_tract = OrderedDict()
    demand_nodes_fleetpy = []
    with open(pre_node_dir) as f:
        csvreader = csv.DictReader(f)
        for data in csvreader:
            is_demand_node = int(float(data["is_demand_node"]))
            if is_demand_node == 1:
                census_tract = int(float(data["census_tract"]))
                if census_tract not in census_tract_node:
                    census_tract_node[census_tract] = []
                node_id = int(float(data["node_in_fleetpy"]))
                if node_id not in census_tract_node[census_tract]:
                    census_tract_node[census_tract].append(node_id)

                if node_id not in node_census_tract:
                    node_census_tract[node_id] = census_tract

                if node_id not in demand_nodes_fleetpy:
                    demand_nodes_fleetpy.append(node_id)
    f.close()
    return demand_nodes_fleetpy

def create_nodes_emp_dict(study_area,dt_sd_full_trnst_ntwk,zonal_partition=False,debug=False):

    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
    output_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"
    MGRA_nodes_mapping_folder="D:/Ritun/Siwei_Micro_Transit/Data/0719_input/MGRA_nodes_mapping"

    network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
    SANDAG_landuse=os.path.join(network_folder,"final_land_use.csv")
    if study_area == "downtown_sd":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/demand_folder"
        if dt_sd_full_trnst_ntwk == True:
            if zonal_partition == True:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network_4_zones"
            else:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network"
        else:
            initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
        output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"
        MGRA_nodes_mapping_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/MGRA_nodes_mapping"

    if study_area == "lemon_grove":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/demand_folder"
        initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/lemon_grove_example_demand/matched/example_network"
        output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"
        MGRA_nodes_mapping_folder = "D:/Ritun/Siwei_Micro_Transit/Ritun/Lemon Grove/MGRA_Node_Mapping"

    headway = 20
    microtransit = "micro"
    time_period = "AM"
    virstop=100
    initial_super_network_dir=os.path.join(initial_network_folder,"initial_super_network_%s_hw_%s_virstop_%s.csv" % (str(microtransit), str(headway), str(virstop)))# initial_super_network[microtransit][headway][virstop][time_period]=n_a.read_super_network(initial_super_network_dir)
    network_nodes=[]
    with open(initial_super_network_dir) as super_network:
        csvreader = csv.DictReader(super_network)
        for data in csvreader:
            #from_node	to_node

            from_node = int(data["from_node"])
            to_node = int(data["to_node"])
            if from_node not in network_nodes:
                network_nodes.append(from_node)
            if to_node not in network_nodes:
                network_nodes.append(to_node)
        super_network.close()


    super_network_emp=os.path.join(output_folder,"super_network_nodes_emp.csv")



    # MGRA_nodes_mapping=os.path.join(MGRA_nodes_mapping_folder,"MGRA_demand_nodes_mapping.csv")
    Nodes_MGRA_mapping = os.path.join(MGRA_nodes_mapping_folder, "Nodes_MGRA_mapping.csv")
    MGRA_node_dict=OrderedDict()
    MGRA_emp=OrderedDict()
    nodes_emp = OrderedDict()
    demand_nodes_fleetpy=get_fleetpy_demand_nodes()
    # print("number of demand nodes:",len(demand_nodes_fleetpy),"demand nodes list:",demand_nodes_fleetpy)
    # node_MGRA_dict=OrderedDict()
    with open(Nodes_MGRA_mapping) as f_N_MGRA_mapping:
        csvreader = csv.DictReader(f_N_MGRA_mapping)
        # depart_time	start	end	trip_id

        for data in csvreader:
            #             print(data)
            MGRA = int(data["MGRA"])
            node = int(data["node"])
            # print("data",data)
            if node in demand_nodes_fleetpy:
                if MGRA not in MGRA_node_dict:
                    MGRA_node_dict[MGRA] = []

                if node not in MGRA_node_dict[MGRA]:
                    # if node in demand_nodes_fleetpy:
                        MGRA_node_dict[MGRA].append(node)

    f_N_MGRA_mapping.close()
    MGRA_node_dict = OrderedDict(sorted(MGRA_node_dict.items()))

    if debug==True:
        nodes_in_MGRA_node_dict=[]
        for MGRA in MGRA_node_dict:
            node_list=MGRA_node_dict[MGRA]
            for node in node_list:
                if node not in nodes_in_MGRA_node_dict:
                    nodes_in_MGRA_node_dict.append(node)

        print("number of MGRA",len(MGRA_node_dict),"number of nodes in nodes_in_MGRA_node_dict",len(nodes_in_MGRA_node_dict))



    total_emp=0
    with open(SANDAG_landuse) as f_landuse:
        csvreader = csv.DictReader(f_landuse)
        #depart_time	start	end	trip_id

        for data in csvreader:
    #             print(data)
            MGRA = int(data["zone_id"])-100000
            TOTEMP=int(data["TOTEMP"])
            MGRA_emp[MGRA]=TOTEMP
            if MGRA in MGRA_node_dict:
                Nodes_list=MGRA_node_dict[MGRA]
                total_emp+=TOTEMP
                for node in Nodes_list:
                    if node not in nodes_emp:
                        nodes_emp[node]=TOTEMP/len(Nodes_list)

    f_landuse.close()
    for node in network_nodes:
        if node not in nodes_emp:
            nodes_emp[node]=0
    nodes_emp = OrderedDict(sorted(nodes_emp.items()))
    print("total employment in the whole region:",total_emp,"total number of MGRAs:",len(MGRA_node_dict))
    return nodes_emp,MGRA_node_dict


def acc_dijsktra_source_to_all_heap(graph, initial, verbose=False):
    # Define a class Node to store the values
    class Heap_Node:
        def __init__(self, v, temp):
            self.node_id = v
            self.temp = temp

        # define a comparator method to compare distance of two nodes
        def __lt__(self, other):
            return self.temp < other.temp

    visited_temp = {initial: 0}  # dictionary: {node: the weights from source to a visited node}
    path = {}
    # time_limits = minutes * 60
    try:
        (nodes, edges) = (set(graph.nodes), graph.edges)
        costs = graph.costs
    except:  # for NetworkX
        (nodes, edges) = (set(graph.nodes()), graph)  # Siwei: set - sort the graph.nodes
        costs = []
    # define a priority queue as the heap
    heap_q = []
    heapq.heappush(heap_q, Heap_Node(initial, 0))

    while heap_q:

        smallest_node = heapq.heappop(heap_q)  # 11/02: Heap: get the smallest value item from the heap
        #         print("smallest_node",smallest_node)
        min_node = smallest_node.node_id
        #         nodes.remove(min_node)  # find the min_node to close, remove the recent close node from the open node list
        permanent = visited_temp[min_node]
        if min_node in edges:
            for edge in edges[min_node]:

                link_travel_time = graph.get_edge_data(min_node, edge)["object"].free_flow_time  # Siwei: get link travel time
                temp = permanent + link_travel_time  # Siwei: temp -> the criteria used for closing a node: travel time for UE

                # if temp >= time_limits:
                #     #                     print("edge:",edge,"temp",temp)
                #     break

                if edge not in visited_temp or temp < visited_temp[edge]:
                    visited_temp[edge] = temp
                    path[edge] = (min_node, link_travel_time)
                    heapq.heappush(heap_q,Heap_Node(edge, temp))  # 11/02: Heap: push the new calculated nodes into heap

                if verbose == True:
                    try:
                        print("Permanent:", permanent, "i:", min_node, "j:", edge, "Link cost:", link_travel_time,
                              "Temp Cost:", visited_temp[edge])
                    except:
                        aaa = 0
    #                 num_nodes+=1
    #         print("number of nodes:",num_nodes)
    return visited_temp, path

def accessibility_calculation(dt_sd_full_trnst_ntwk,zonal_partition,headway,virstop,microtransit,time_period,all_node_emp,MGRA_node_dict,M_operating_hrs=False,fleet_size=False,study_area=False,TRPartA=False,BayesianOptimization=False,test_scen=False,debug_mode=False,debug=False):

    if study_area == "downtown_sd":
        if TRPartA==True:

            if BayesianOptimization==True:
                demand_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/demand_data/%s" % str(study_area)
                if dt_sd_full_trnst_ntwk == True:
                    if zonal_partition == True:
                        initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_full_transit_network_4_zones" % str(study_area)
                    else:
                        initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_full_transit_network" % str(study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"

                final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/final_network_folder" % str(study_area)
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
                output_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/output_folder" % str(study_area)
            else:
                demand_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/demand_data/%s" % str(study_area)
                if dt_sd_full_trnst_ntwk == True:
                    if zonal_partition == True:
                        initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_full_transit_network_4_zones" % str(study_area)
                    else:
                        initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_full_transit_network" % str(study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"

                final_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/final_network_folder" % str(study_area)
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
                output_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/output_folder" % str(study_area)
        else:
            demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/demand_folder"
            if dt_sd_full_trnst_ntwk == True:
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network_4_zones"
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network"
            else:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
            final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
            fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"

    if study_area == "lemon_grove":
        if TRPartA == True:
            if BayesianOptimization == True:
                demand_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/demand_data/%s" % str(study_area)
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_full_transit_network_4_zones" % str(study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/initial_network_folder/initial_full_transit_network" % str(study_area)
                final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/final_network_folder" % str(study_area)
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
                output_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/output_folder" % str(study_area)
            else:
                demand_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/demand_data/%s" % str(study_area)
                if zonal_partition == True:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_full_transit_network_4_zones" % str(study_area)
                else:
                    initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/initial_network_folder/initial_full_transit_network" % str(study_area)
                final_network_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/final_network_folder" % str(study_area)
                fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
                output_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/output_folder" % str(study_area)
        else:
            demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/demand_folder"
            if zonal_partition == False:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
            else:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network_4_zones"
            # initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
            final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/final_network"
            fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/lemon_grove_example_demand/matched/example_network"
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"

    minutes_set = [5, 10,15]
    minute_acc_emp = OrderedDict()
    demand_nodes_fleetpy=get_fleetpy_demand_nodes()
    if microtransit=="micro":
        # T_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit),str(fleet_size),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))
        T_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit),str(fleet_size),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))
        # T_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit), str(fleet_size), str(M_operating_hrs),str(time_period), str(headway), str(virstop)))
    elif microtransit=="micro_only":
        T_network_dir= os.path.join(final_network_folder, "final_super_network_%s_fsize_%s_ophr_%s_%s_virstop_%s.csv" % (str(microtransit), str(fleet_size), str(M_operating_hrs), str(time_period), str(virstop)))

    else:
        T_network_dir = os.path.join(initial_network_folder,"initial_super_network_%s_hw_%s.csv" % (str(microtransit), str(headway)))
    #final_super_network_dir = os.path.join(final_network_folder,"final_super_network_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))

    T_network = n_a.read_super_network(T_network_dir)
    minute_acc_emp = OrderedDict()



    for initial in demand_nodes_fleetpy:
        visited_temp, path = acc_dijsktra_source_to_all_heap(T_network, initial, verbose=False)
        visited_temp = dict(sorted(visited_temp.items(), key=lambda item: item[1]))
        minute_acc_emp[initial] = OrderedDict()

        for minutes in minutes_set:
            # time_limits = minutes * 60
            minute_acc_emp[initial][minutes] = 0

        for visited_node in visited_temp:
            for minutes in minutes_set:
                if visited_temp[visited_node] <= 60 * minutes:
                    minute_acc_emp[initial][minutes] += all_node_emp[visited_node]

        # for minutes in minutes_set:
        #     time_limits = minutes * 60
        #     minute_acc_emp[initial][minutes] = 0
        #     if debug == True:
        #         print("microtransit", microtransit, "headway", headway, "virstop", virstop, "time_period",
        #               time_period,
        #               "minutes", minutes)
        #     for visited_node in visited_temp:
        #         if visited_temp[visited_node]<=time_limits:
        #             minute_acc_emp[initial][minutes] += all_node_emp[visited_node]
    if microtransit=="micro":
        output_acc_dir=os.path.join(output_folder,"debug_%s_acc_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s_scen_%s.csv" % (str(debug_mode),str(microtransit),str(fleet_size),str(M_operating_hrs),str(time_period), str(headway),str(virstop),str(test_scen)))
    elif microtransit =="micro_only":
        output_acc_dir = os.path.join(output_folder,"debug_%s_acc_super_network_%s_fsize_%s_ophr_%s_%s_virstop_%s_scen_%s.csv" % (str(debug_mode), str(microtransit), str(fleet_size), str(M_operating_hrs),str(time_period), str(virstop),str(test_scen)))

    else:
        output_acc_dir = os.path.join(output_folder, "acc_super_network_%s_%s.csv" % (str(headway), str(microtransit)))
    minute_acc_MGRA_avg_emp=OrderedDict()

    for MGRA in MGRA_node_dict:
        node_list = MGRA_node_dict[MGRA]
        if MGRA not in minute_acc_MGRA_avg_emp:
            minute_acc_MGRA_avg_emp[MGRA] = OrderedDict()

        for minutes in minutes_set:
            if minutes not in minute_acc_MGRA_avg_emp:
                minute_acc_MGRA_avg_emp[MGRA][minutes] = OrderedDict()
            minute_acc_MGRA_tot_emp = 0
            for node in node_list:
                minute_acc_MGRA_tot_emp += minute_acc_emp[node][minutes]
            minute_acc_MGRA_avg_emp[MGRA][minutes]=minute_acc_MGRA_tot_emp/ len(node_list)


    with open(output_acc_dir, 'w+', newline='') as csvfile:
        # fieldnames = ["MGRA", "emp_5min", "emp_10min", "emp_15min", "emp_20min","emp_30min","emp_40min"]
        fieldnames = ["MGRA", "population", "emp_5min", "emp_10min","emp_15min", "weighted_5min", "weighted_10min","weighted_15min"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        MGRA_pop_dict,MGRA_pop_percent=get_MGRA_pop(study_area)
        MGRA_adj_dict=get_blank_adjacent_MGRA(study_area)
        emp_5_min=0
        emp_10_min=0
        emp_15_min = 0
        weighted_5_min=0
        weighted_10_min=0
        weighted_15_min = 0
        tot_weighted_5_min = 0
        tot_weighted_10_min = 0
        tot_weighted_15_min = 0
        for MGRA in MGRA_pop_percent:
            MGRA_pop=MGRA_pop_dict[MGRA]
            if MGRA in minute_acc_MGRA_avg_emp:
                emp_5_min=minute_acc_MGRA_avg_emp[MGRA][5]
                emp_10_min=minute_acc_MGRA_avg_emp[MGRA][10]
                emp_15_min = minute_acc_MGRA_avg_emp[MGRA][15]
                weighted_5_min=emp_5_min*MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]
            elif MGRA in MGRA_adj_dict:
                adjacent_MGRA=MGRA_adj_dict[MGRA]
                if adjacent_MGRA in minute_acc_MGRA_avg_emp:
                    emp_5_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][5]
                    emp_10_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][10]
                    emp_15_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][15]
                else:
                    if study_area == "downtown_sd":
                        emp_5_min = 5325
                        emp_10_min = 34870
                        emp_15_min = 49336
                    if study_area == "lemon_grove":
                        emp_5_min = 431
                        emp_10_min = 5074
                        emp_15_min = 6341
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]
            else:
                if study_area == "downtown_sd":
                    emp_5_min=5325
                    emp_10_min=34870
                    emp_15_min = 49336
                if study_area == "lemon_grove":
                    emp_5_min = 431
                    emp_10_min = 5074
                    emp_15_min = 6341
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]


            tot_weighted_5_min += weighted_5_min
            tot_weighted_10_min += weighted_10_min
            tot_weighted_15_min += weighted_15_min
            writer.writerow({"MGRA": MGRA, "population": MGRA_pop, "emp_5min": emp_5_min, "emp_10min": emp_10_min,"emp_15min": emp_15_min,"weighted_5min": weighted_5_min, "weighted_10min": weighted_10_min,"weighted_15min": weighted_15_min})


        # for MGRA in MGRA_node_dict:
        #     # writer.writerow(
        #     #     {"MGRA":MGRA, "emp_5min":minute_acc_MGRA_avg_emp[MGRA][5], "emp_10min":minute_acc_MGRA_avg_emp[MGRA][10],
        #     #      "emp_15min":minute_acc_MGRA_avg_emp[MGRA][15], "emp_20min":minute_acc_MGRA_avg_emp[MGRA][20],
        #     #      "emp_30min":minute_acc_MGRA_avg_emp[MGRA][30],"emp_40min":minute_acc_MGRA_avg_emp[MGRA][40]})
        #     writer.writerow(
        #         {"MGRA": MGRA, "emp_5min": emp_5_min,
        #          "emp_10min": emp_10_min })

    csvfile.close()


    return tot_weighted_5_min,tot_weighted_10_min,tot_weighted_15_min


def all_scenario_micro_acc_calculation(microtransit_run,headway, virstop,M_operating_hrs,fleet_size,study_area,debug_mode,dt_sd_full_trnst_ntwk,zonal_partition,TRPartA,BayesianOptimization,test_scen):
    all_node_emp, MGRA_node_dict = create_nodes_emp_dict(study_area,dt_sd_full_trnst_ntwk)
    # microtransit == "micro"
    avg_period_total_weighted_5_min = 0
    avg_period_total_weighted_10_min = 0
    avg_period_total_weighted_15_min = 0

    if M_operating_hrs==10:
        time_periods = ["AM", "PM"] #10 hr
    elif M_operating_hrs==15:
        time_periods = ["AM", "MD", "PM"] #15hr
    else:
        time_periods = ["AM", "MD", "PM", "EV"] #19hr


    # for microtransit in microtransit_setup_scenarios:
    #     if microtransit != "non_micro":
    for time_period in time_periods:
        tot_weighted_5_min,tot_weighted_10_min, tot_weighted_15_min= accessibility_calculation(dt_sd_full_trnst_ntwk,zonal_partition,headway, virstop, microtransit_run, time_period, all_node_emp, MGRA_node_dict, M_operating_hrs,fleet_size,study_area,TRPartA,BayesianOptimization,test_scen,debug_mode,debug=False)
        avg_period_total_weighted_5_min += tot_weighted_5_min
        avg_period_total_weighted_10_min += tot_weighted_10_min
        avg_period_total_weighted_15_min += tot_weighted_15_min
        #
    avg_period_total_weighted_5_min = avg_period_total_weighted_5_min/len(time_periods)
    avg_period_total_weighted_10_min = avg_period_total_weighted_10_min/len(time_periods)
    avg_period_total_weighted_15_min = avg_period_total_weighted_15_min / len(time_periods)

    print("Microtransit Accessibility calculation - finished.")
    return avg_period_total_weighted_5_min,avg_period_total_weighted_10_min,avg_period_total_weighted_15_min


def all_scenario_fixed_acc_calculation(headway,study_area,debug_mode,dt_sd_full_trnst_ntwk,test_scenario,TRPartA,BayesianOptimization,zonal_partition=False,debug=False):
    all_node_emp, MGRA_node_dict = create_nodes_emp_dict(study_area,dt_sd_full_trnst_ntwk)
    # microtransit == "micro"
    # for microtransit in microtransit_scenarios:
    #     if microtransit == "non_micro":
    #         for time_period in time_periods:
    #             minute_acc_MGRA_avg_emp = accessibility_calculation(headway, virstop, microtransit, time_period, all_node_emp, MGRA_node_dict, debug=False)
    microtransit="non_micro"


    # minutes_set = [5, 10, 15, 20, 30, 40]
    minutes_set = [5, 10, 15]
    minute_acc_emp = OrderedDict()
    demand_nodes_fleetpy = get_fleetpy_demand_nodes()
    if study_area == "downtown_sd":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/demand_folder"
        if dt_sd_full_trnst_ntwk == True:
            if zonal_partition == True:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network_4_zones"
            else:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network"
        else:
            initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
        if TRPartA==True:
            output_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/output_folder" % str(study_area)
        else:
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"

    if study_area == "lemon_grove":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/demand_folder"
        if zonal_partition == False:
            initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
        else:
            initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network_4_zones"
        # initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/lemon_grove_example_demand/matched/example_network"
        if TRPartA==True:
            if BayesianOptimization==True:
                #D:\Siwei_Micro_Transit\Bayesian_Optimization\downtown_sd\output_folder
                output_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/output_folder" % str(study_area)
            else:
                output_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/output_folder" % str(study_area)
        else:
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"

    T_network_dir = os.path.join(initial_network_folder,"initial_super_network_%s_hw_%s.csv" % (str(microtransit), str(headway)))
    # final_super_network_dir = os.path.join(final_network_folder,"final_super_network_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))

    T_network = n_a.read_super_network(T_network_dir)
    minute_acc_emp = OrderedDict()

    for initial in demand_nodes_fleetpy:
        visited_temp, path = acc_dijsktra_source_to_all_heap(T_network, initial, verbose=False)
        visited_temp = dict(sorted(visited_temp.items(), key=lambda item: item[1]))
        minute_acc_emp[initial] = OrderedDict()
        # for minutes in minutes_set:
        #     time_limits = minutes * 60
        #     minute_acc_emp[initial][minutes] = 0
        #     if debug == True:
        #         print("headway", headway)
        for minutes in minutes_set:
            # time_limits = minutes * 60
            minute_acc_emp[initial][minutes] = 0

        for visited_node in visited_temp:
            for minutes in minutes_set:
                if visited_temp[visited_node] <= 60 * minutes:
                    minute_acc_emp[initial][minutes] += all_node_emp[visited_node]



        # for minutes in minutes_set:
        #     time_limits = minutes * 60
        #     minute_acc_emp[initial][minutes] = 0
        #     if debug == True:
        #         print("headway", headway)
        #     for visited_node in visited_temp:
        #         if visited_temp[visited_node] <= time_limits:
        #             minute_acc_emp[initial][minutes] += all_node_emp[visited_node]

    output_acc_dir = os.path.join(output_folder, "debug_%s_acc_super_network_%s_%s.csv" % (str(debug_mode),str(microtransit),str(headway)))
    minute_acc_MGRA_avg_emp = OrderedDict()

    for MGRA in MGRA_node_dict:
        node_list = MGRA_node_dict[MGRA]
        if MGRA not in minute_acc_MGRA_avg_emp:
            minute_acc_MGRA_avg_emp[MGRA] = OrderedDict()

        for minutes in minutes_set:
            if minutes not in minute_acc_MGRA_avg_emp:
                minute_acc_MGRA_avg_emp[MGRA][minutes] = OrderedDict()
            minute_acc_MGRA_tot_emp = 0
            for node in node_list:
                minute_acc_MGRA_tot_emp += minute_acc_emp[node][minutes]
            minute_acc_MGRA_avg_emp[MGRA][minutes] = minute_acc_MGRA_tot_emp / len(node_list)

    with open(output_acc_dir, 'w+', newline='') as csvfile:
        # fieldnames = ["MGRA", "emp_5min", "emp_10min", "emp_15min", "emp_20min", "emp_30min", "emp_40min"]

        fieldnames = ["MGRA", "population", "emp_5min", "emp_10min","emp_15min", "weighted_5min", "weighted_10min","weighted_15min"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        MGRA_pop_dict, MGRA_pop_percent = get_MGRA_pop(study_area)
        MGRA_adj_dict = get_blank_adjacent_MGRA(study_area)
        emp_5_min = 0
        emp_10_min = 0
        emp_15_min = 0
        weighted_5_min = 0
        weighted_10_min = 0
        weighted_15_min = 0
        tot_weighted_5_min = 0
        tot_weighted_10_min = 0
        tot_weighted_15_min = 0
        for MGRA in MGRA_pop_percent:
            MGRA_pop = MGRA_pop_dict[MGRA]
            if MGRA in minute_acc_MGRA_avg_emp:
                emp_5_min = minute_acc_MGRA_avg_emp[MGRA][5]
                emp_10_min = minute_acc_MGRA_avg_emp[MGRA][10]
                emp_15_min = minute_acc_MGRA_avg_emp[MGRA][15]
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]
            elif MGRA in MGRA_adj_dict:
                adjacent_MGRA = MGRA_adj_dict[MGRA]
                if adjacent_MGRA in minute_acc_MGRA_avg_emp:
                    emp_5_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][5]
                    emp_10_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][10]
                    emp_15_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][15]
                else:
                    if study_area == "downtown_sd":
                        emp_5_min = 2217.137
                        emp_10_min = 9231.608
                        emp_15_min = 21320.35
                    if study_area == "lemon_grove":
                        emp_5_min = 156
                        emp_10_min = 486
                        emp_15_min = 1020
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]
            else:
                if study_area == "downtown_sd":
                    emp_5_min = 2217.137
                    emp_10_min = 9231.608
                    emp_15_min = 21320.35
                if study_area == "lemon_grove":
                    emp_5_min = 156
                    emp_10_min = 486
                    emp_15_min = 1020
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]

            tot_weighted_5_min += weighted_5_min
            tot_weighted_10_min += weighted_10_min
            tot_weighted_15_min += weighted_15_min
            writer.writerow({"MGRA": MGRA, "population": MGRA_pop, "emp_5min": emp_5_min, "emp_10min": emp_10_min,"emp_15min":emp_15_min,
                             "weighted_5min": weighted_5_min, "weighted_10min": weighted_10_min,"weighted_15min":weighted_15_min})

        # fieldnames = ["MGRA", "emp_5min", "emp_10min", "emp_15min", "emp_20min"]
        # writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # writer.writeheader()
        #
        # for MGRA in MGRA_node_dict:
        #     # writer.writerow(
        #     #     {"MGRA": MGRA, "emp_5min": minute_acc_MGRA_avg_emp[MGRA][5],
        #     #      "emp_10min": minute_acc_MGRA_avg_emp[MGRA][10],
        #     #      "emp_15min": minute_acc_MGRA_avg_emp[MGRA][15], "emp_20min": minute_acc_MGRA_avg_emp[MGRA][20],
        #     #      "emp_30min": minute_acc_MGRA_avg_emp[MGRA][30], "emp_40min": minute_acc_MGRA_avg_emp[MGRA][40]})
        #     writer.writerow(
        #         {"MGRA": MGRA, "emp_5min": minute_acc_MGRA_avg_emp[MGRA][5],
        #          "emp_10min": minute_acc_MGRA_avg_emp[MGRA][10],
        #          "emp_15min": minute_acc_MGRA_avg_emp[MGRA][15], "emp_20min": minute_acc_MGRA_avg_emp[MGRA][20]})

    csvfile.close()
    print("Fix transit headway %s Accessibility calculation - finished." % str(headway))
    return tot_weighted_5_min,tot_weighted_10_min,tot_weighted_15_min

def get_fleetpy_eval_output_metrics(repositioning):
    if repositioning == True:
        Fleetpy_output_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/studies/example_study/results/example_pool_repo_AM_sc_1"
    else:
        Fleetpy_output_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/studies/example_study/results/example_pool_irsonly_sc_1"
    Fleetpy_eval_file = os.path.join(Fleetpy_output_folder, "standard_eval.csv")
    df = pd.read_csv(Fleetpy_eval_file, index_col=0, header=0)
    util_rate=df.loc["% fleet utilization"]["MoD_0"]
    # util_rate_=util_rate["MoD_0"]
    veh_occ = df.loc["occupancy"]["MoD_0"]
    total_vkm = df.loc["total vkm"]["MoD_0"]
    total_vmt = total_vkm/1.609
    empty_vkm = df.loc["% empty vkm"]["MoD_0"]
    avg_speed_kmh = df.loc["avg driving velocity [km/h]"]["MoD_0"]
    avg_speed_mph = avg_speed_kmh/1.609
    print("util_rate(%)",util_rate,"veh_occ",veh_occ,"total_vmt (miles)",total_vmt,"empty_vkm(%)",empty_vkm,"avg_speed (vmp)",avg_speed_mph)
    return util_rate,veh_occ,total_vmt,empty_vkm,avg_speed_mph

def get_transit_line_dist(study_area,dt_sd_full_trnst_ntwk):
    if study_area == "downtown_sd":
        if dt_sd_full_trnst_ntwk==True:
            network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/Downtown_SD_New_Transit_network/Road_network"
            new_transit_network_file = os.path.join(network_folder, "super_network_transit_edges.csv")
        else:
            network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
            new_transit_network_file = os.path.join(network_folder, "new_nodes_transit_network.csv")

    if study_area == "lemon_grove":
        network_folder = "D:/Ritun/Siwei_Micro_Transit/Ritun/Lemon Grove"
        new_transit_network_file = os.path.join(network_folder, "super_network_transit_edges.csv")

    with open(new_transit_network_file) as transit_network:
        csvreader = csv.DictReader(transit_network)
        routes=[]
        for data in csvreader:
            route_id = int(data["route"])
            if route_id not in routes:
                routes.append(route_id)
    transit_network.close()
    # routes=[1,2,3,4,5]
    # new_transit_network_file = os.path.join(network_folder, "new_nodes_transit_network.csv")

    with open(new_transit_network_file) as transit_network:
        csvreader = csv.DictReader(transit_network)

        pre_route_id=0
        pre_start_node=0
        transit_rt_dist_dict=OrderedDict()
        transit_line_dist_list=[]
        transit_rt_stps_dict=OrderedDict()
        for route_id in routes:
            transit_rt_dist_dict[route_id]=[]
            transit_rt_stps_dict[route_id]=[]
        for data in csvreader:
            #from_node	to_node	distance (meters)	travel_time (sec)	route


            from_node = int(data["from_node"])
            route_id = int(data["route"])
            distance = float(data["distance (meters)"])
            # print("route_id", route_id,"distance",distance)
            if route_id in transit_rt_dist_dict:
                if distance not in transit_rt_dist_dict[route_id]:
                    transit_rt_dist_dict[route_id].append(distance)
            if from_node not in transit_rt_stps_dict[route_id]:
                transit_rt_stps_dict[route_id].append(from_node)

        transit_network.close()
    # print("start_node_route",start_node_route,"end_node_route",end_node_route)
    num_ts_stops = 0
    for route_id in routes:
        route_dist_list=transit_rt_dist_dict[route_id]
        # print("route",route_id,"dist_list",transit_rt_dist_dict[route_id])
        route_tt_dist = sum(route_dist_list)/1609
        num_ts_stops = len(transit_rt_stps_dict[route_id])
        transit_line_dist_list.append((route_id,route_tt_dist,num_ts_stops))

    print("transit_line_dist_list (route_id,miles,num_stops)",transit_line_dist_list)

    return transit_line_dist_list

def get_transit_line_duration(study_area,dt_sd_full_trnst_ntwk,transit_line_dist_list):
    transit_line_duration = OrderedDict()
    dwell_time = 3 / 60  # unit hour
    dead_end_time = 20 / 60  # unit hour - (10min) on one end
    if study_area == "downtown_sd":
        if dt_sd_full_trnst_ntwk == False:
            for (route_id, dist, num_stops) in transit_line_dist_list:
                if route_id == 1:  # Speed of Route 1: 35 miles per hour=15.65 meter/sec
                    avg_speed = 35
                if route_id == 2:  # Speed of Route 2: 40 miles per hour=17.88 meter/sec
                    avg_speed = 40
                if route_id == 3:  # Speed of Route 3: 45 miles per hour=20.12 meter/sec
                    avg_speed = 45
                if route_id == 4:  # Speed of Route 4: 25 miles per hour=11.18 meter/sec
                    avg_speed = 25
                if route_id == 5:  # Speed of Route 5: 30 miles per hour=13.41 meter/sec
                    avg_speed = 30
                transit_line_duration[route_id] = dist / avg_speed + num_stops * dwell_time + dead_end_time  # dwell time (3min/stop), dead-end times (10min)
        else:
            avg_speed = 30
            for (route_id, dist, num_stops) in transit_line_dist_list:
                transit_line_duration[route_id] = dist / avg_speed + num_stops * dwell_time + dead_end_time  # dwell time (3min/stop), dead-end times (10min)
    if study_area == "lemon_grove":
        avg_speed = 30
        for (route_id, dist, num_stops) in transit_line_dist_list:
            transit_line_duration[route_id] = dist / avg_speed + num_stops * dwell_time + dead_end_time  # dwell time (3min/stop), dead-end times (10min)

    return transit_line_duration

def get_transit_link_info(study_area,dt_sd_full_trnst_ntwk):
    if study_area == "downtown_sd":
        if dt_sd_full_trnst_ntwk==True:
            network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/Downtown_SD_New_Transit_network/Road_network"
            new_transit_network_file = os.path.join(network_folder, "super_network_transit_edges.csv")
        else:
            network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
            new_transit_network_file = os.path.join(network_folder, "new_nodes_transit_network.csv")

    if study_area == "lemon_grove":
        network_folder = "D:/Ritun/Siwei_Micro_Transit/Ritun/Lemon Grove"
        new_transit_network_file = os.path.join(network_folder, "super_network_transit_edges.csv")

    transit_link_list=[]
    with open(new_transit_network_file) as transit_network:
        csvreader = csv.DictReader(transit_network)
        routes=[]
        for data in csvreader:
            # route_id = int(data["route"])
            from_node = int(data["from_node"])
            to_node = int(data["to_node"])
            transit_link_list.append((from_node,to_node))
    transit_network.close()



    return transit_link_list

def vmt_and_link_dict_creation(time_periods,transit_link_list):
    transit_link_vmt = OrderedDict()
    transit_link_pax = OrderedDict()
    off_micro_transit_link_pax = OrderedDict()
    off_micro_transit_link_vmt = OrderedDict()
    for time_period in time_periods:
        transit_link_vmt[time_period] = OrderedDict()
        off_micro_transit_link_vmt[time_period] = OrderedDict()
        transit_link_pax[time_period] = OrderedDict()
        off_micro_transit_link_pax[time_period] = OrderedDict()
        for (from_node, to_node) in transit_link_list:
            transit_link_vmt[time_period][(from_node, to_node)] = 0
            off_micro_transit_link_vmt[time_period][(from_node, to_node)] = 0
            transit_link_pax[time_period][(from_node, to_node)] = 0
            off_micro_transit_link_pax[time_period][(from_node, to_node)] = 0

    return transit_link_vmt,transit_link_pax,off_micro_transit_link_pax,off_micro_transit_link_vmt

def write_fixed_transit_link_vmt(study_area,dt_sd_full_trnst_ntwk,fleet_size,M_operating_hrs,headway,virstop,transit_link_vmt,transit_link_pax,TRPartA,BayesianOptimization,test_scenario,debug_mode,microtransit):
    if study_area == "downtown_sd":
        if dt_sd_full_trnst_ntwk==True:
            network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/Downtown_SD_New_Transit_network/Road_network"
            new_transit_network_file = os.path.join(network_folder, "super_network_transit_edges.csv")
        else:
            network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
            new_transit_network_file = os.path.join(network_folder, "new_nodes_transit_network.csv")
        # network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input"
        # new_transit_network_file = os.path.join(network_folder, "new_nodes_transit_network.csv")
        if TRPartA==True:
            #D:\Siwei_Micro_Transit\TR_PartA\Data\downtown_sd\output_folder
            if BayesianOptimization==True:
                output_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/output_folder" % str(study_area)
                transit_link_vmt_output = os.path.join(output_folder,"debug_%s_%s_%s_%s_op_hr_%s_hw_%s_virstop_%s_transit_edges_rders_scen_%s.csv" % (str(debug_mode), str(study_area), str(microtransit),str(fleet_size), str(M_operating_hrs), str(headway),str(virstop), str(test_scenario)))

            else:
                output_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/output_folder" % str(study_area)
                transit_link_vmt_output = os.path.join(output_folder,"debug_%s_%s_%s_%s_op_hr_%s_hw_%s_virstop_%s_transit_edges_rders_scen_%s.csv" % (str(debug_mode), str(study_area), str(microtransit), str(fleet_size),str(M_operating_hrs), str(headway), str(virstop),str(test_scenario)))
        else:
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"
            transit_link_vmt_output = os.path.join(output_folder, "debug_%s_%s_%s_%s_op_hr_%s_hw_%s_virstop_%s_transit_edges_rders.csv" % (str(debug_mode),str(study_area),str(microtransit),str(fleet_size),str(M_operating_hrs), str(headway), str(virstop)))

    if study_area == "lemon_grove":
        network_folder = "D:/Ritun/Siwei_Micro_Transit/Ritun/Lemon Grove"
        new_transit_network_file = os.path.join(network_folder, "super_network_transit_edges.csv")
        # output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"
        # transit_link_vmt_output = os.path.join(output_folder, "debug_%s_%s_%s_%s_op_hr_%s_hw_%s_virstop_%s_transit_edges_rders.csv" % (str(debug_mode),str(study_area),str(microtransit),str(fleet_size),str(M_operating_hrs), str(headway), str(virstop)))
        if TRPartA == True:
            if BayesianOptimization==True:
                output_folder = "D:/Ritun/Siwei_Micro_Transit/Bayesian_Optimization/%s/output_folder" % str(study_area)
                transit_link_vmt_output = os.path.join(output_folder,"debug_%s_%s_%s_%s_op_hr_%s_hw_%s_virstop_%s_transit_edges_rders_scen_%s.csv" % (str(debug_mode), str(study_area), str(microtransit),str(fleet_size), str(M_operating_hrs), str(headway),str(virstop), str(test_scenario)))

            else:
                output_folder = "D:/Ritun/Siwei_Micro_Transit/TR_PartA/Data/%s/output_folder" % str(study_area)
                transit_link_vmt_output = os.path.join(output_folder,"debug_%s_%s_%s_%s_op_hr_%s_hw_%s_virstop_%s_transit_edges_rders_scen_%s.csv" % (str(debug_mode), str(study_area), str(microtransit), str(fleet_size),str(M_operating_hrs), str(headway), str(virstop),str(test_scenario)))
        else:
            output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"
            transit_link_vmt_output = os.path.join(output_folder, "debug_%s_%s_%s_%s_op_hr_%s_hw_%s_virstop_%s_transit_edges_rders.csv" % (str(debug_mode), str(study_area), str(microtransit), str(fleet_size),str(M_operating_hrs), str(headway), str(virstop)))

    transit_link_list = []
    with open(transit_link_vmt_output, 'w+', newline='') as csvfile:
        #from_node	to_node	distance (meters)	travel_time	link_type	route

        fieldnames = ["from_node", "to_node", "distance (meters)","travel_time","link_type","route",
                      "rdrs_AM","rdrs_MD","rdrs_PM","rdrs_EV","tt_rdrs"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        with open(new_transit_network_file) as transit_network:
            csvreader = csv.DictReader(transit_network)
            routes = []
            for data in csvreader:
                # route_id = int(data["route"])
                from_node = int(data["from_node"])
                to_node = int(data["to_node"])
                distance = float(data["distance (meters)"])
                if study_area=="downtown_sd":
                    if dt_sd_full_trnst_ntwk==True:
                        travel_time = float(data["travel_time"])
                    else:
                        travel_time = float(data["travel_time (sec)"])
                if study_area == "lemon_grove":
                    travel_time = float(data["travel_time"])
                link_type = int(1)
                route = int(data["route"])
                vmt_AM = float(transit_link_vmt["AM"][(from_node, to_node)])
                vmt_MD = float(transit_link_vmt["MD"][(from_node, to_node)])
                vmt_PM = float(transit_link_vmt["PM"][(from_node, to_node)])
                vmt_EV = float(transit_link_vmt["EV"][(from_node, to_node)])

                rdrs_AM = float(transit_link_pax["AM"][(from_node, to_node)])
                rdrs_MD = float(transit_link_pax["MD"][(from_node, to_node)])
                rdrs_PM = float(transit_link_pax["PM"][(from_node, to_node)])
                rdrs_EV = float(transit_link_pax["EV"][(from_node, to_node)])
                tt_rdrs = rdrs_AM + rdrs_MD + rdrs_PM + rdrs_EV

                writer.writerow({"from_node": from_node, "to_node": to_node, "distance (meters)": distance,"travel_time": travel_time,"link_type": link_type,
                                 "route": route,"rdrs_AM": rdrs_AM,"rdrs_MD": rdrs_MD,"rdrs_PM": rdrs_PM,"rdrs_EV": rdrs_EV,"tt_rdrs":tt_rdrs})

        transit_network.close()
    csvfile.close()
    # return

if __name__ == '__main__':
    headway=15
    virstop=75
    time_period="AM"
    M_operating_hrs=10
    fleet_size=10
    debug_mode = False
    dt_sd_full_trnst_ntwk=True
    # microtransit="micro"
    # nodes_emp,MGRA_node_dict=create_nodes_emp_dict(debug=True)
    # tot_weighted_5_min_F,tot_weighted_10_min_F,tot_weighted_15_min_F=all_scenario_fixed_acc_calculation(headway,debug=False)
    # avg_period_total_weighted_5_min,avg_period_total_weighted_10_min,avg_period_total_weighted_15_min=all_scenario_micro_acc_calculation(headway, virstop,M_operating_hrs,fleet_size)
    study_area="downtown_sd"
    # create_mgra_pop_income_table(study_area)
    # create_adjacent_MGRA_file(study_area)
    # print("number of nodes_emp",minute_acc_emp)
    zonal_partition=True

    if study_area == "downtown_sd":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/demand_folder"
        if dt_sd_full_trnst_ntwk == True:
            if zonal_partition == True:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network_4_zones"
            else:
                initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_full_transit_network"
        else:
            initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/example_demand/matched/example_network"
        output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/output_folder"

    if study_area == "lemon_grove":
        demand_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/demand_folder"
        if zonal_partition == False:
            initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
        else:
            initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network_4_zones"
        # initial_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/initial_network"
        final_network_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/final_network"
        fleetpy_demand_folder = "D:/Ritun/Siwei_Micro_Transit/FleetPy_Sacramento/data/demand/lemon_grove_example_demand/matched/example_network"
        output_folder = "D:/Ritun/Siwei_Micro_Transit/Data/0719_input/lemon_grove/output_folder"

    minutes_set = [5, 10, 15]
    # minute_acc_emp = OrderedDict()
    all_node_emp, MGRA_node_dict = create_nodes_emp_dict(study_area,dt_sd_full_trnst_ntwk)
    demand_nodes_fleetpy = get_fleetpy_demand_nodes()
    microtransit="micro"
    if microtransit == "micro":
        # T_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit),str(fleet_size),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))
        T_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit), str(fleet_size), str(M_operating_hrs), str(time_period),
                                     str(headway), str(virstop)))
        # T_network_dir = os.path.join(final_network_folder,"final_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit), str(fleet_size), str(M_operating_hrs),str(time_period), str(headway), str(virstop)))
    elif microtransit == "micro_only":
        T_network_dir = os.path.join(final_network_folder, "final_super_network_%s_fsize_%s_ophr_%s_%s_virstop_%s.csv" % ( str(microtransit), str(fleet_size), str(M_operating_hrs), str(time_period),
                                     str(virstop)))

    else:
        T_network_dir = os.path.join(initial_network_folder,"initial_super_network_%s_hw_%s.csv" % (str(microtransit), str(headway)))
    # final_super_network_dir = os.path.join(final_network_folder,"final_super_network_%s_ophr_%s_%s_hw_%s_virstop_%s.csv" % (str(microtransit),str(M_operating_hrs),str(time_period), str(headway),str(virstop)))

    T_network = n_a.read_super_network(T_network_dir)
    minute_acc_emp = OrderedDict()

    for initial in demand_nodes_fleetpy:
        visited_temp, path = acc_dijsktra_source_to_all_heap(T_network, initial, verbose=False)
        visited_temp = dict(sorted(visited_temp.items(), key=lambda item: item[1]))
        minute_acc_emp[initial] = OrderedDict()

        for minutes in minutes_set:
            # time_limits = minutes * 60
            minute_acc_emp[initial][minutes] = 0

        for visited_node in visited_temp:
            for minutes in minutes_set:
                if visited_temp[visited_node] <= 60 * minutes:
                    minute_acc_emp[initial][minutes] += all_node_emp[visited_node]


    if microtransit == "micro":
        output_acc_dir = os.path.join(output_folder,
                                      "debug_%s_acc_super_network_%s_fsize_%s_ophr_%s_%s_hw_%s_virstop_%s_new.csv" % (str(debug_mode), str(microtransit), str(fleet_size), str(M_operating_hrs),
                                      str(time_period), str(headway), str(virstop)))
    elif microtransit == "micro_only":
        output_acc_dir = os.path.join(output_folder,
                                      "debug_%s_acc_super_network_%s_fsize_%s_ophr_%s_%s_virstop_%s_new.csv" % (str(debug_mode), str(microtransit), str(fleet_size), str(M_operating_hrs),
                                      str(time_period), str(virstop)))

    else:
        output_acc_dir = os.path.join(output_folder, "acc_super_network_%s_%s_new.csv" % (str(headway), str(microtransit)))
    minute_acc_MGRA_avg_emp = OrderedDict()

    for MGRA in MGRA_node_dict:
        node_list = MGRA_node_dict[MGRA]
        if MGRA not in minute_acc_MGRA_avg_emp:
            minute_acc_MGRA_avg_emp[MGRA] = OrderedDict()

        for minutes in minutes_set:
            if minutes not in minute_acc_MGRA_avg_emp:
                minute_acc_MGRA_avg_emp[MGRA][minutes] = OrderedDict()
            minute_acc_MGRA_tot_emp = 0
            for node in node_list:
                minute_acc_MGRA_tot_emp += minute_acc_emp[node][minutes]
            minute_acc_MGRA_avg_emp[MGRA][minutes] = minute_acc_MGRA_tot_emp / len(node_list)
    aaa=0

    with open(output_acc_dir, 'w+', newline='') as csvfile:
        # fieldnames = ["MGRA", "emp_5min", "emp_10min", "emp_15min", "emp_20min","emp_30min","emp_40min"]
        fieldnames = ["MGRA", "population", "emp_5min", "emp_10min", "emp_15min", "weighted_5min", "weighted_10min",
                      "weighted_15min"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        MGRA_pop_dict, MGRA_pop_percent = get_MGRA_pop(study_area)
        MGRA_adj_dict = get_blank_adjacent_MGRA(study_area)
        emp_5_min = 0
        emp_10_min = 0
        emp_15_min = 0
        weighted_5_min = 0
        weighted_10_min = 0
        weighted_15_min = 0
        tot_weighted_5_min = 0
        tot_weighted_10_min = 0
        tot_weighted_15_min = 0
        for MGRA in MGRA_pop_percent:
            MGRA_pop = MGRA_pop_dict[MGRA]
            if MGRA in minute_acc_MGRA_avg_emp:
                emp_5_min = minute_acc_MGRA_avg_emp[MGRA][5]
                emp_10_min = minute_acc_MGRA_avg_emp[MGRA][10]
                emp_15_min = minute_acc_MGRA_avg_emp[MGRA][15]
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]
            elif MGRA in MGRA_adj_dict:
                adjacent_MGRA = MGRA_adj_dict[MGRA]
                if adjacent_MGRA in minute_acc_MGRA_avg_emp:
                    emp_5_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][5]
                    emp_10_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][10]
                    emp_15_min = minute_acc_MGRA_avg_emp[adjacent_MGRA][15]
                else:
                    if study_area == "downtown_sd":
                        emp_5_min = 5325
                        emp_10_min = 34870
                        emp_15_min = 49336
                    if study_area == "lemon_grove":
                        emp_5_min = 431
                        emp_10_min = 5074
                        emp_15_min = 6341
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]
            else:
                if study_area == "downtown_sd":
                    emp_5_min = 5325
                    emp_10_min = 34870
                    emp_15_min = 49336
                if study_area == "lemon_grove":
                    emp_5_min = 431
                    emp_10_min = 5074
                    emp_15_min = 6341
                weighted_5_min = emp_5_min * MGRA_pop_percent[MGRA]
                weighted_10_min = emp_10_min * MGRA_pop_percent[MGRA]
                weighted_15_min = emp_15_min * MGRA_pop_percent[MGRA]

            tot_weighted_5_min += weighted_5_min
            tot_weighted_10_min += weighted_10_min
            tot_weighted_15_min += weighted_15_min
            writer.writerow({"MGRA": MGRA, "population": MGRA_pop, "emp_5min": emp_5_min, "emp_10min": emp_10_min,
                             "emp_15min": emp_15_min, "weighted_5min": weighted_5_min,
                             "weighted_10min": weighted_10_min, "weighted_15min": weighted_15_min})

        # for MGRA in MGRA_node_dict:
        #     # writer.writerow(
        #     #     {"MGRA":MGRA, "emp_5min":minute_acc_MGRA_avg_emp[MGRA][5], "emp_10min":minute_acc_MGRA_avg_emp[MGRA][10],
        #     #      "emp_15min":minute_acc_MGRA_avg_emp[MGRA][15], "emp_20min":minute_acc_MGRA_avg_emp[MGRA][20],
        #     #      "emp_30min":minute_acc_MGRA_avg_emp[MGRA][30],"emp_40min":minute_acc_MGRA_avg_emp[MGRA][40]})
        #     writer.writerow(
        #         {"MGRA": MGRA, "emp_5min": emp_5_min,
        #          "emp_10min": emp_10_min })

    csvfile.close()

    # util_rate,veh_occ,total_vmt,empty_vkm,avg_speed_mph=get_fleetpy_eval_output_metrics()
    # transit_line_dist_list=get_transit_line_dist()