import pandas as pd
import os
import csv
import random
import numpy as np
import math
from collections import OrderedDict
from collections import Counter
import random
from math import radians, cos, sin, asin, sqrt

mile_meter = 1609.34

class Link(object):

    def __init__(self, link_id=None, length=0,
                     from_node=0, to_node=0, flow=float(0.0), free_speed=0, free_flow_travel_time=0,
                     link_type=str(0)):
        self.link_id = link_id
        # self.link_id_text=link_id_text
        self.length = length   # ft
        self.from_node = from_node
        self.to_node = to_node
        self.timestep = 0
        self.timesteps = 60
        self.timeinterval = 15.0  # seconds
        self.free_speed = free_speed  # ft/sec = 51.33*0.681818(converting fts to mph) = 34.9977 mph, 1.4667 (converting mph to fps)
        self.free_flow_time=free_flow_travel_time
        self._time = None
        self.density = 0.0  # veh/mile (ft to miles = ft*5280.0)
        # self.k_j = 160.002  # if we set this value to decimal, we can have a very low chance that fails to derivative.
        self.k_j = 160.002/5280.0  #0316 Siwei: k_j -> veh/ft
        self.v = 0.  # mph
        self.flow = flow  # vehicles, vph(bpr)
        self.k_t = 0.0
        self.use_exact = False
        self.truncate=False
        self.link_function = "m_Greenshield"  # "bpr", "m_Greenshield","triangularFD"
        self.SO = False
        self.random_init_vol = False

        self.u_max = self.free_speed  # mph
        # self.u_min = 10.0  # mph
        self.u_min = 10.0*1.4667  #Siwei: ft/s 10mph
        self.route = 0
        self.link_type=link_type

class Node(object):
    """
    Class for handling node object in Transportation Networks
    Parameters
    ----------
    node_id: int
            identifier of a node
    """
    def __init__(self, node_id=0, node_XCOORD=0, node_YCOORD=0, is_stop_only=False, census_tract=0, node_in_fleetpy=0,
                 is_demand_node=0):
        self.node_id = node_id
        self.node_XCOORD = node_XCOORD
        self.node_YCOORD = node_YCOORD
        self.is_stop_only = is_stop_only
        self.census_tract = census_tract
        self.node_in_fleetpy = node_in_fleetpy
        self.is_demand_node = is_demand_node

def create_network_from_raw_edges(network_folder):
    pre_node_fields = ["node_index", "is_stop_only", "pos_x", "pos_y", "node_in_fleetpy",
                       "is_demand_node"]
    edge_fields = ["from_node", "to_node", "distance", 'maxspeed']
    network_file = 'D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM edge network trial speed adjusted.csv'
    pre_node_dir = os.path.join(network_folder, 'pre_nodes.csv')
    pre_edges_dir = os.path.join(network_folder, 'pre_edges_without_travel_time.csv')
    demand_nodes_dir=os.path.join(network_folder,'demand_nodes.csv')
    demand_nodes = []
    n_demand_links = 0
    with open(pre_node_dir, 'w+', newline='') as csvfile_nodes:
        writer_node = csv.writer(csvfile_nodes, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer_node.writerow(pre_node_fields)
        with open(pre_edges_dir, "w+", newline='') as csvfile_edges:
            writer_edge = csv.writer(csvfile_edges, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer_edge.writerow(edge_fields)
            with open(network_file) as f:
                csvreader = csv.DictReader(f)
                nodes = {}
                links = []
                node_list = []
                for data in csvreader:
                    origin_node = int(data["u"])
                    origin_node_XCOORD= float(node_location_dict[origin_node][0])
                    origin_node_YCOORD= float(node_location_dict[origin_node][1])
                    to_node = int(data["v"])
                    to_node_XCOORD= float(node_location_dict[to_node][0])
                    to_node_YCOORD= float(node_location_dict[to_node][1])
                    distance=data["length"]  # length (meter) #TODO
                    speed=data['maxspeed']

                    edge_row_AB = [int(origin_node), int(to_node), float(distance), speed]
                    edge_row_BA = [int(to_node), int(origin_node), float(distance), speed]
                    writer_edge.writerow(edge_row_AB)
                    writer_edge.writerow(edge_row_BA)

                    if origin_node not in nodes:
                        if random.random() < 0.0035:
                            n = Node(node_id = origin_node, node_XCOORD = origin_node_XCOORD,
                                     node_YCOORD=origin_node_YCOORD, is_stop_only = True)
                        else:
                            n = Node(node_id = origin_node, node_XCOORD = origin_node_XCOORD,
                                     node_YCOORD = origin_node_YCOORD)
                        nodes[origin_node] = n
                    if to_node not in nodes:
                        if random.random() < 0.0035:
                            n = Node(node_id = to_node, node_XCOORD = to_node_XCOORD, node_YCOORD = to_node_YCOORD,
                                     is_stop_only = True)
                        else:
                            n = Node(node_id = to_node, node_XCOORD = to_node_XCOORD, node_YCOORD = to_node_YCOORD)
                        nodes[to_node] = n

                    l = Link(link_id = len(links), length = distance,
                             from_node = origin_node, to_node = to_node, flow = float(0.0))
                    links.append(l)
            f.close()
        csvfile_edges.close()
        nodes_keys = list(nodes.keys())
        nodes_keys.sort()
        sorted_nodes = {i: nodes[i] for i in nodes_keys}
        i = 0
        for keys in sorted_nodes:
            sorted_nodes[keys].node_in_fleetpy = i
            if keys in demand_nodes:
                sorted_nodes[keys].is_demand_node = 1
            node_row = [int(sorted_nodes[keys].node_id), sorted_nodes[keys].is_stop_only,
                        float(sorted_nodes[keys].node_XCOORD), float(sorted_nodes[keys].node_YCOORD), int(sorted_nodes[keys].node_in_fleetpy),
                        int(sorted_nodes[keys].is_demand_node)]
            writer_node.writerow(node_row)
            i += 1
    csvfile_nodes.close()

    # print("census tract:", len(census_track_list))
    # print("number of demand links:", n_demand_links, "number of demand nodes:", len(demand_nodes))
    # return demand_nodes

def demand_nodes():
    file_edge="D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM edge network trial speed adjusted.csv"
    demand_node = []
    n_demand_link = 0
    with open(file_edge) as file:
        csvreader = csv.DictReader(file)
        for data in csvreader:
            speed=int(data['maxspeed'])
            if speed<=25:
                n_demand_link += 1
                if data['u'] not in demand_node:
                    demand_node.append(data['u'])
                if data['v'] not in demand_node:
                    demand_node.append(data['v'])
    # print("number of demand nodes:", len(demand_node), "number of demand links:", n_demand_link)
    return demand_node, n_demand_link

def get_demand_node_lat_long(demand_node):
    file_edge_raw="D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM edge network trial speed adjusted.csv"
    file_node_raw="D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM node network.csv"
    demand_node_lat_lon_file="D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/demand_node_lat_lon.csv"
    node_lat_lon_dict={}
    with open(file_node_raw) as node_file:
        csvreader=csv.DictReader(node_file)
        for data in csvreader:
            node_lat_lon_dict[data["osmid"]]=(data['y'],data['x'])
    node_file.close()
    with open(demand_node_lat_lon_file, 'w+', newline='') as demand_file:
        demand_fields=["node","lat","lon"]
        writer_node = csv.writer(demand_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer_node.writerow(demand_fields)
        for node in demand_node:
            demand_node_lat, demand_node_lon=node_lat_lon_dict[node]
            row = [node, demand_node_lat, demand_node_lon]
            writer_node.writerow(row)
    demand_file.close()

def pre_edge_travel_time_assignment(network_folder):
    pre_edges_file_without_travel_time = os.path.join(network_folder, 'pre_edges_without_travel_time.csv')
    pre_edges_file_with_travel_time = os.path.join(network_folder, 'pre_edges.csv')
    df_edges=pd.read_csv(pre_edges_file_without_travel_time)
    df_edges['travel_time']=(df_edges['distance']/(df_edges['maxspeed']/2.23694))
    df_edges.to_csv(pre_edges_file_with_travel_time, index=False)

def write_node_edge_from_pre_node_edge(network_folder):
    pre_node_dir=os.path.join(network_folder,'pre_nodes.csv')
    pre_edges_dir=os.path.join(network_folder,'pre_edges.csv')
    node_dir = os.path.join(network_folder, 'nodes.csv')
    edges_dir = os.path.join(network_folder, 'edges.csv')
    node_fields = ["node_index", "is_stop_only", "pos_x", "pos_y"]
    ##############################
    # Adjust node files
    ###########################
    fleetpy_demand_node = []
    with open(node_dir, 'w+', newline='') as csvfile_nodes:
        writer_node = csv.writer(csvfile_nodes, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer_node.writerow(node_fields)
        with open(pre_node_dir) as f_nodes:
            csvreader = csv.DictReader(f_nodes)
            nodes_fleetpy = {}
            for data in csvreader:
                node_index = int(data["node_index"])
                node_in_fleetpy = int(data["node_in_fleetpy"])
                is_stop_only = data["is_stop_only"]
                pos_x = data["pos_x"]
                pos_y = data["pos_y"]
                is_demand_node = int(data["is_demand_node"])
                if is_demand_node == 1:
                    fleetpy_demand_node.append(node_in_fleetpy)
                if node_index not in nodes_fleetpy:
                    nodes_fleetpy[node_index] = node_in_fleetpy
                node_row = [int(node_in_fleetpy), is_stop_only, pos_x, pos_y]
                writer_node.writerow(node_row)
        f_nodes.close()
    csvfile_nodes.close()
    #########################
    # Adjust edge files
    ##############################
    with open(edges_dir, "w+", newline='') as csvfile_edges:
        writer_edge = csv.writer(csvfile_edges, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        edge_fields = ["from_node", "to_node", "distance", "travel_time"]
        writer_edge.writerow(edge_fields)
        with open(pre_edges_dir) as f_edges:
            csvreader = csv.DictReader(f_edges)
            for data in csvreader:
                # edge_fields=["from_node","to_node","distance","travel_time","source_edge_id"]
                from_node = nodes_fleetpy[int(data["from_node"])]
                to_node = nodes_fleetpy[int(data["to_node"])]
                distance = data["distance"]
                travel_time = data["travel_time"]
                edge_row = [from_node, to_node, distance, travel_time]
                writer_edge.writerow(edge_row)
        f_edges.close()
    csvfile_edges.close()
    return nodes_fleetpy, fleetpy_demand_node

def read_transit_nodes(transit_node_file):
    transit_nodes_list=[]
    with open(transit_node_file) as f_old:
        csvreader = csv.DictReader(f_old)
        for data in csvreader:
            if data["stop_id"]:
                stop_id = int(data["stop_id"])
                if stop_id not in transit_nodes_list:
                    transit_nodes_list.append(stop_id)
    f_old.close()
    transit_nodes_list = sorted(transit_nodes_list)
    return transit_nodes_list

# Python 3 program to calculate Distance Between Two Points on Earth
def calculate_distance(lat1, lat2, lon1, lon2):
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
    # calculate the result
    return (c * r)

def get_transit_node_lat_lon(transit_node_file):
    transit_node_lat_lon = OrderedDict()
    transit_walk_nodes=OrderedDict()
    walk_transit_nodes=OrderedDict()
    with open(transit_node_file) as f_old:
        csvreader = csv.DictReader(f_old)
        for data in csvreader:
            stop_id = int(data["stop_id"])
            stop_lat = float(data["stop_lat"])
            stop_lon = float(data["stop_lon"])
            transit_node_lat_lon[stop_id]=(stop_lat,stop_lon)
    f_old.close()
    return transit_node_lat_lon

def get_walk_node_lat_lon(node_file):
    walk_node_lat_lon=OrderedDict()
    with open(node_file) as f_old:
        csvreader = csv.DictReader(f_old)
        for data in csvreader:
            node_index = int(data["node_index"])
            node_lat = float(data["pos_y"])
            node_lon = float(data["pos_x"])
            walk_node_lat_lon[node_index]=(node_lat,node_lon)
    f_old.close()
    return walk_node_lat_lon

def construct_supernetwork_walk_links(network_folder,supernetwork_folder):
    walk_network_edges = os.path.join(supernetwork_folder,'super_network_walk_edges.csv')
    road_network_edges = os.path.join(network_folder, 'edges.csv')
    with open(walk_network_edges, 'w+', newline='') as f_new:
        fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type"]
        writer = csv.DictWriter(f_new, fieldnames=fieldnames)
        writer.writeheader()
        with open(road_network_edges) as f_old:
            csvreader = csv.DictReader(f_old)
            for data in csvreader:
                from_node = int(data["from_node"])
                to_node = int(data["to_node"])
                dist = float(data["distance"])
                travel_time = dist/1.6   #distance in meter/1.6 meter per second  ### What is the walking speed????
                link_type = int(0)
                writer.writerow({"from_node": from_node, "to_node": to_node, "distance": dist, "travel_time": travel_time,
                                 "link_type": link_type})
        f_old.close()
    f_new.close()
    return True

def construct_super_network_transit_links(supernetwork_folder, raw_transit_edge_file):
    super_network_transit_edges_file = os.path.join(supernetwork_folder,'super_network_transit_edges.csv')
    with open(super_network_transit_edges_file, 'w+', newline='') as f_new:
        fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type","route"] #route
        writer = csv.DictWriter(f_new, fieldnames=fieldnames)
        writer.writeheader()
        with open(raw_transit_edge_file) as f_old:
            csvreader = csv.DictReader(f_old)
            for data in csvreader:
                from_node = int(data["from_node"])
                from_node_F=transit_stop_super_network_dict[from_node]
                to_node = int(data["to_node"])
                to_node_F=transit_stop_super_network_dict[to_node]
                dist = float(data["distance"]) # 1mile=1609.34meter   ##confirm unit of distance
                travel_time = float(data["travel_time"]) # second
                route_id = 1
                route_id_str=str(data["route_id"])                  ######### To be done #########
                if route_id_str =='F20':
                    route_id=550
                else:
                    route_id = int(route_id_str)
                link_type = int(1)
                writer.writerow({"from_node": from_node_F, "to_node": to_node_F, "distance": dist, "travel_time": travel_time,
                                 "link_type": link_type,"route":route_id})
        f_old.close()
    return True

def construct_super_network_microtransit_edges(network_folder, road_network_edges_file):
    super_network_micro_transit_edges_file = os.path.join(network_folder,'super_network_micro_transit_edges.csv')
    with open(super_network_micro_transit_edges_file, 'w+', newline='') as f_new:
        fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type"]
        writer = csv.DictWriter(f_new, fieldnames=fieldnames)
        writer.writeheader()
        with open(road_network_edges_file) as f_old:
            csvreader = csv.DictReader(f_old)
            for data in csvreader:
                from_node = int(data["from_node"])
                from_node_M=walk_M_tr_node_dict[from_node]
                to_node = int(data["to_node"])
                to_node_M=walk_M_tr_node_dict[to_node]
                dist = float(data["distance"]) # meter
                travel_time = float(data["travel_time"])*1.4 # second            #### Is the 1.4 multiplier for detour ratio ####
                link_type = int(4)
                writer.writerow({"from_node": from_node_M, "to_node": to_node_M, "distance": dist, "travel_time": travel_time,
                                 "link_type": link_type})
        f_old.close()
    f_new.close()

def construct_vitual_stops(network_folder, road_node_file):
    virtual_stop_dict = OrderedDict()
    for percentage in [50, 75, 100]:
        micro_transit_virtual_stops = os.path.join(network_folder,"micro_transit_%s_percent_virtual_stops.csv" % str(percentage))
        virtual_stop_dict[percentage] = []
        with open(micro_transit_virtual_stops, 'w+', newline='') as f_new:
            fieldnames = ["node_index", "is_stop_only", "pos_x", "pos_y", "node_in_micro_network"]
            writer = csv.DictWriter(f_new, fieldnames=fieldnames)
            writer.writeheader()
            with open(road_node_file) as f_old:
                csvreader = csv.DictReader(f_old)
                for data in csvreader:
                    node_index = int(data["node_index"])
                    is_stop_only = str(data["is_stop_only"])
                    pos_x = float(data["pos_x"])
                    pos_y = float(data["pos_y"])
                    node_in_micro_network = walk_M_tr_node_dict[node_index]
                    ran_num = random.random()
                    if ran_num <= (percentage / 100):
                        if node_index not in virtual_stop_dict[percentage]:
                            virtual_stop_dict[percentage].append(node_index)
                        writer.writerow(
                            {"node_index": node_index, "is_stop_only": is_stop_only, "pos_x": pos_x, "pos_y": pos_y,
                             "node_in_micro_network": node_in_micro_network})
            f_old.close()
        f_new.close()
    return virtual_stop_dict

def get_transit_link_route(network_folder, raw_transit_edge_file):
    lemon_grove_network_folder = "D:/Ritun/Siwei_Micro_Transit/Ritun/Lemon Grove/"
    old_super_transit_network = os.path.join(network_folder, "super_network_transit_edges.csv")      # without route id
    # new_super_transit_network = os.path.join(network_folder, "new_super_network_transit_edges.csv")  # adding route id
    raw_super_transit_network = raw_transit_edge_file    # original node id  ## This is same as the original transit edge file as in this case the study area is not a subset of the whole sacramento region
    raw_travel_time_nodes = OrderedDict()
    old_travel_time_nodes = OrderedDict()
    transit_nodes = []
    with open(old_super_transit_network) as f_W:
        csvreader = csv.DictReader(f_W)
        for data in csvreader:
            from_node_o = int(data["from_node"])
            to_node_o = int(data["to_node"])
            travel_time = float(data["travel_time"])
            old_travel_time_nodes[travel_time] = (from_node_o, to_node_o)
            if from_node_o not in transit_nodes:
                transit_nodes.append(from_node_o)
            if to_node_o not in transit_nodes:
                transit_nodes.append(to_node_o)
    f_W.close()
    with open(raw_super_transit_network) as f_W:
        csvreader = csv.DictReader(f_W)
        for data in csvreader:
            from_node_r = int(data["from_node"])
            to_node_r = int(data["to_node"])
            travel_time = float(data["travel_time"])
            raw_travel_time_nodes[travel_time] = (from_node_r, to_node_r)
    f_W.close()

    transit_node_raw_old_dict = OrderedDict()
    transit_node_raw_old_dict_rev = OrderedDict()
    for travel_time in old_travel_time_nodes:
        (from_node_o, to_node_o) = old_travel_time_nodes[travel_time]
        (from_node_r, to_node_r) = raw_travel_time_nodes[travel_time]
        if from_node_r not in transit_node_raw_old_dict:
            transit_node_raw_old_dict[from_node_r] = from_node_o
        if to_node_r not in transit_node_raw_old_dict:
            transit_node_raw_old_dict[to_node_r] = to_node_o

        if from_node_o not in transit_node_raw_old_dict_rev:
            transit_node_raw_old_dict_rev[from_node_o] = from_node_r
        if to_node_o not in transit_node_raw_old_dict_rev:
            transit_node_raw_old_dict_rev[to_node_o] = to_node_r
    print("transit_nodes", len(transit_nodes))
    print("transit_node_raw_old_dict", len(transit_node_raw_old_dict), "transit_node_raw_old_dict_rev",
          len(transit_node_raw_old_dict_rev))

    transit_link_route = OrderedDict()
    new_transit_network = os.path.join(network_folder, "raw_transit_edge_file_csv.csv")
    old_super_transit_network = os.path.join(network_folder,
                                                     "super_network_transit_edges.csv")  # without route id
    with open(new_transit_network) as new_transit_f:
        csvreader = csv.DictReader(new_transit_f)
        for data in csvreader:
            transit_route = OrderedDict()
            from_node = int(data["from_node"])
            to_node = int(data["to_node"])
            from_node_sp_network = transit_node_raw_old_dict[from_node]
            to_node_sp_network = transit_node_raw_old_dict[to_node]
            route_id_str=str(data["route_id"])
            if route_id_str =='F20':
                route_id=550
            else:
                route_id = int(route_id_str)
            transit_link_route[(from_node_sp_network, to_node_sp_network)] = route_id
    new_transit_f.close()
    return transit_link_route

def create_walk_transit_node_match(transit_node_lat_lon,walk_node_lat_lon,transit_walk_nodes_match_file):
    transit_walk_node_match_dict = OrderedDict()
    with open(transit_walk_nodes_match_file, 'w+', newline='') as csvfile:
        fieldnames = ["stop_id", "stop_lat", "stop_lon", "walk_node"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for transit_stop in transit_node_lat_lon:
            (stop_lat,stop_lon)=transit_node_lat_lon[transit_stop]
            min_dist=math.inf
            min_wlk_node_index=None
            for walk_node in walk_node_lat_lon:
                (node_lat, node_lon)=walk_node_lat_lon[walk_node]
                trst_wlk_dist=calculate_distance(stop_lat, node_lat, stop_lon, node_lon)    ## this is on km
                if trst_wlk_dist<=min_dist:
                    min_dist=trst_wlk_dist
                    min_wlk_node_index=walk_node
            transit_walk_node_match_dict[transit_stop]=min_wlk_node_index
            writer.writerow({'stop_id': transit_stop, 'stop_lat': stop_lat, 'stop_lon': stop_lon, "walk_node": min_wlk_node_index})
    return transit_walk_node_match_dict

def construct_initial_network(initial_network_folder, network_folder):
    headway_scenarios = [10, 15, 20, 30, 60]
    microtransit_scenarios = ["micro", "non_micro"]
    time_periods = ["AM", "MD", "PM", "EV"]
    transit_link_route = get_transit_link_route()
    initial_network_folder = initial_network_folder
    network_folder = network_folder
    for virstop in [50, 75, 100]:
        for headway in headway_scenarios:
            for microtransit in microtransit_scenarios:
                if microtransit == "micro":
                    initial_network_scen_dir = os.path.join(initial_network_folder,
                                                                "initial_super_network_%s_hw_%s_virstop_%s.csv" % (
                                                                str(microtransit), str(headway), str(virstop)))
                    with open(initial_network_scen_dir, 'w+', newline='') as csvfile:
                        fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type", "route"]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        WalkMicroFix_network = os.path.join(initial_network_folder,
                                                                    "super_network_%s_virstop_%s_hw_edges.csv" % (
                                                                    str(virstop), str(20)))
                        with open(WalkMicroFix_network) as f_W:
                            csvreader = csv.DictReader(f_W)
                            for data in csvreader:
                                link_type = int(data["link_type"])
                                from_node = int(data["from_node"])
                                to_node = int(data["to_node"])
                                distance = float(data["distance"])
                                if link_type == 1:
                                    route = transit_link_route[(from_node, to_node)]
                                else:
                                    route = int(-1)
                                if link_type == 0:
                                    walk_speed = 1.251  # 1.251 meter/secon, 2.8mile/hr
                                    travel_time = distance / walk_speed
                                else:
                                    travel_time = float(data["travel_time"])
                                if link_type == 2:
                                    if travel_time > 0:
                                        waiting_time = headway * 60 / 2  # transit stop waiting time according to headway
                                        travel_time = waiting_time
                                if microtransit == "non_micro":
                                    if link_type == 4 or link_type == 5:
                                        break
                                writer.writerow({'from_node': from_node, 'to_node': to_node, 'distance': distance,
                                                     'travel_time': travel_time, "link_type": link_type,
                                                     "route": route})
                        f_W.close()
                    csvfile.close()

def get_the_virtual_stops(percentage,network_folder):
    micro_transit_virtual_stops = os.path.join(network_folder,"micro_transit_%s_percent_virtual_stops.csv" % str(percentage))
    virtual_stop_list = []
    with open(micro_transit_virtual_stops) as f_old:
        csvreader = csv.DictReader(f_old)
        for data in csvreader:
            node_index = int(data["node_index"])
            if node_index not in virtual_stop_list:
                virtual_stop_list.append(node_index)
    f_old.close()
    return virtual_stop_list

def construct_final_supernetwork_edges(supernetwork_folder, supernetwork_transit_stop_walk_node_match_dict):
    # final_super_network_nodes = os.path.join(new_network_folder, "super_network_nodes.csv")
    for headway in [10, 15, 20, 30, 60]:  # [20,30,60]
        for percentage in [50, 75, 100]:  # [50,75,100]
            final_super_network_edges = os.path.join(supernetwork_folder, "super_network_%s_virstop_%s_hw_edges.csv" % (
            str(percentage), str(headway)))
            # virtual_stop_dict[percentage]=[]
            with open(final_super_network_edges, 'w+', newline='') as f_new:
                fieldnames = ["from_node", "to_node", "distance", "travel_time", "link_type", "route"]
                writer = csv.DictWriter(f_new, fieldnames=fieldnames)
                writer.writeheader()

                # read the walking network
                walk_network_edges = os.path.join(supernetwork_folder, "super_network_walk_edges.csv")
                with open(walk_network_edges) as f_old:
                    csvreader = csv.DictReader(f_old)
                    for data in csvreader:
                        from_node = int(data["from_node"])
                        to_node = int(data["to_node"])
                        distance = float(data["distance"])
                        travel_time = float(data["travel_time"])
                        link_type = int(data["link_type"])
                        writer.writerow({"from_node": from_node, "to_node": to_node, "distance": distance,
                                         "travel_time": travel_time,
                                         "link_type": link_type, "route": int(-1)})
                f_old.close()

                # read the fixed transit network
                super_network_transit_edges = os.path.join(supernetwork_folder, "super_network_transit_edges.csv")
                with open(super_network_transit_edges) as f_old:
                    csvreader = csv.DictReader(f_old)
                    transit_stop_list = []
                    for data in csvreader:
                        from_node = int(data["from_node"])
                        from_node_walk = supernetwork_transit_stop_walk_node_match_dict[from_node]
                        to_node = int(data["to_node"])
                        to_node_walk = supernetwork_transit_stop_walk_node_match_dict[to_node]
                        distance = float(data["distance"])
                        travel_time = float(data["travel_time"])
                        link_type = int(data["link_type"])
                        route_id = int(data["route"])
                        wait_time_F = headway * 60 / 2
                        writer.writerow({"from_node": from_node, "to_node": to_node, "distance": distance,
                                         "travel_time": travel_time, "link_type": link_type, "route": route_id})
                        # write walk to fixed transit connecting link
                        if from_node not in transit_stop_list:
                            transit_stop_list.append(from_node)
                            writer.writerow({"from_node": from_node_walk, "to_node": from_node, "distance": 0,
                                             "travel_time": wait_time_F, "link_type": int(2), "route": int(-1)})
                            writer.writerow(
                                {"from_node": from_node, "to_node": from_node_walk, "distance": 0, "travel_time": 0,
                                 "link_type": int(2), "route": int(-1)})
                        if to_node not in transit_stop_list:
                            transit_stop_list.append(to_node)
                            writer.writerow({"from_node": to_node_walk, "to_node": to_node, "distance": 0,
                                             "travel_time": wait_time_F, "link_type": int(2), "route": int(-1)})
                            writer.writerow(
                                {"from_node": to_node, "to_node": to_node_walk, "distance": 0, "travel_time": 0,
                                 "link_type": int(2), "route": int(-1)})
                    aaa = 0
                f_old.close()

                # write the microtransit edges
                super_network_micro_transit_edges = os.path.join(supernetwork_folder,
                                                                 "super_network_micro_transit_edges.csv")
                with open(super_network_micro_transit_edges) as f_old:
                    csvreader = csv.DictReader(f_old)
                    virtual_stop_list = []
                    for data in csvreader:
                        from_node = int(data["from_node"])
                        # M_tr_walk_node_dict[node_id] = walk_node
                        from_node_walk = M_tr_walk_node_dict[from_node]
                        to_node = int(data["to_node"])
                        to_node_walk = M_tr_walk_node_dict[to_node]
                        distance = float(data["distance"])
                        travel_time = float(data["travel_time"])
                        link_type = int(data["link_type"])
                        wait_time_M = 180
                        writer.writerow({"from_node": from_node, "to_node": to_node, "distance": distance,
                                         "travel_time": travel_time, "link_type": link_type, "route": int(-1)})
                        # write walk to micro transit connecting link
                        if from_node_walk in virtual_stop_dict[percentage]:
                            if from_node_walk not in virtual_stop_list:
                                virtual_stop_list.append(from_node_walk)
                                writer.writerow({"from_node": from_node_walk, "to_node": from_node, "distance": 0,
                                                 "travel_time": wait_time_M, "link_type": int(5), "route": int(-1)})
                                writer.writerow(
                                    {"from_node": from_node, "to_node": from_node_walk, "distance": 0, "travel_time": 0,
                                     "link_type": int(5), "route": int(-1)})
                        if to_node_walk in virtual_stop_dict[percentage]:
                            if to_node_walk not in virtual_stop_list:
                                virtual_stop_list.append(to_node_walk)
                                writer.writerow({"from_node": to_node_walk, "to_node": to_node, "distance": 0,
                                                 "travel_time": wait_time_M, "link_type": int(5), "route": int(-1)})
                                writer.writerow(
                                    {"from_node": to_node, "to_node": to_node_walk, "distance": 0, "travel_time": 0,
                                     "link_type": int(5), "route": int(-1)})
                    virtual_stop_list = sorted(virtual_stop_list)
                    aaa = 0
                f_old.close()
            f_new.close()

road_network_dir = "D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/"
road_network_file = os.path.join(road_network_dir, "Sacramento OSM edge network.csv")
df_edges = pd.read_csv("D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM edge network.csv")
df_nodes = pd.read_excel("D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM node network.xlsx")
new_df_edges = pd.read_csv("D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM edge network trial speed adjusted.csv")

node_location_dict = {}
for i in range(56524):
    node_location_dict[df_nodes['osmid'][i]]=(df_nodes['x'][i], df_nodes['y'][i])

network_folder = "D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/New/Revision_02"
create_network_from_raw_edges(network_folder)
demand_node, _ = demand_nodes()
get_demand_node_lat_long(demand_node)
pre_edge_travel_time_assignment(network_folder)
nodes_fleetpy,fleetpy_demand_node = write_node_edge_from_pre_node_edge(network_folder)

transit_node_file="D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento transit networks/SACRT transit network files/SACRT_node_file.txt"
transit_nodes_list = read_transit_nodes(transit_node_file)
transit_node_lat_lon=get_transit_node_lat_lon(transit_node_file)
raw_road_node_file=os.path.join(network_folder, 'nodes.csv')
walk_node_lat_lon=get_walk_node_lat_lon(raw_road_node_file)

supernetwork_folder="D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/New/Revision_02/supernetwork_folder"
construct_supernetwork_walk_links(network_folder,supernetwork_folder)

transit_stop_super_network_dict=OrderedDict()
transit_node_start_id = len(walk_node_lat_lon)
for stop_id in transit_node_lat_lon:
    transit_stop_super_network_dict[stop_id]=transit_node_start_id
    transit_node_start_id+=1

raw_transit_edge_file='D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento transit networks/SACRT transit network files/raw_transit_edge_file_csv.csv'
construct_super_network_transit_links(supernetwork_folder, raw_transit_edge_file)

M_tr_walk_node_dict = OrderedDict()
walk_M_tr_node_dict = OrderedDict()
microtransit_node_start_id=transit_node_start_id
for walk_node in walk_node_lat_lon:
    M_tr_walk_node_dict[microtransit_node_start_id]=walk_node
    walk_M_tr_node_dict[walk_node] = microtransit_node_start_id
    microtransit_node_start_id+=1
road_network_edges_file = os.path.join(network_folder,"edges.csv")
construct_super_network_microtransit_edges(supernetwork_folder, road_network_edges_file)

virtual_stop_dict = construct_vitual_stops(network_folder,raw_road_node_file)
transit_walk_nodes_match_file = os.path.join(network_folder, 'transit_walk_nodes_match.csv')
transit_walk_node_match_dict = create_walk_transit_node_match(transit_node_lat_lon,walk_node_lat_lon,transit_walk_nodes_match_file)

supernetwork_transit_stop_walk_node_match_dict=OrderedDict()
with open(transit_walk_nodes_match_file) as f_old:
    csvreader = csv.DictReader(f_old)
    for data in csvreader:
        stop_id = int(data["stop_id"])
        super_stop_id=transit_stop_super_network_dict[stop_id] #convert the original stop id to super network transit stop id
        walk_node = int(data["walk_node"])
        supernetwork_transit_stop_walk_node_match_dict[super_stop_id]=walk_node
f_old.close()

final_super_network_nodes = os.path.join(supernetwork_folder, "super_network_nodes.csv")

construct_final_supernetwork_edges(supernetwork_folder,supernetwork_transit_stop_walk_node_match_dict)
# ----------------------------------------------------------------------------------------------------------------------









# ----------------------------------------------------------------------------------------------------------------------

