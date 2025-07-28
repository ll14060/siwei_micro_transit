from pyproj import Transformer
import os
import csv
from math import radians, cos, sin, asin, sqrt
from collections import OrderedDict
import math
import random

mile_meter = 1609.34

class Link(object):

    def __init__(self, link_id=None, length=0,
                     from_node=0, to_node=0, flow=float(0.0), free_speed=0, free_flow_travel_time=0,
                     link_type=str(0)):
        self.link_id = link_id
        # self.link_id_text=link_id_text
        self.length = length # ft

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
    node_id:    int
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

road_network_dir = "D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/"
road_network_file = os.path.join(road_network_dir, "Sacramento OSM edge network.csv")

node_location_dict = {}
osm_node_file = "D:/Ritun/Siwei_Micro_Transit/SacRT Data/Sacramento OSM networks/Sacramento OSM node network.xlsx"

# with open(osm_node_file) as f:
#     csvreader = csv.DictReader(f)
#     for data in csvreader:
#         node_id = int(data["osmid"])
#         x_coordinate = float(data["x"])
#         y_coordinate = float(data["y"])
#         node_location_dict[node_id] = (x_coordinate, y_coordinate)
total = 0
with open(osm_node_file, "rb") as f:  # Open in binary mode
    for i, line in enumerate(f):
        total +=1
        try:
            decoded_line = line.decode("utf-8")  # Try decoding as UTF-8
        except UnicodeDecodeError as e:
            print(f"Problem at line {i+1}: {e}")  # Report problematic line
            print(line)  # Print the problematic line in binary form
print(total)