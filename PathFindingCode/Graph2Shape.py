import pandas as pd
import numpy as np
import os
import networkx as nx

import networkx as nx
import csv
import math
from scipy.misc import derivative
import scipy.integrate as integrate
import numpy as np
import random
from collections import OrderedDict
import matplotlib.pyplot as plt
import scipy
import random
import collections

class Link(object):
    """
    Class for handling link object in Transportation Networks

    Parameters
    ----------
    link_id:    int
                identifier of link

    length:     float
                length of link

    capacity:   float
                capacity of link

    alpha:      float
                first BPR function parameter, usually 0.15

    beta:       float
                second BPR function parameter, usually 4.0

    from_node:  int
                id of origin node of link

    to_node:    int
                id of destination node of link

    flow:       float
                flow on link

    free_speed: float
                free flow speed of link

    v:          float
                speed limit of link

    SO:         boolean
                True if objective is to find system optimal solution,
                False if objective is to find user equilibrium

    Attributes
    ----------
    t0:     float
            link travel time under free flow speed

    time:   float
            link travel time based on the BPR function

    """

    def __init__(self, link_id=None, length=0,
                     from_node=0, to_node=0, flow=float(0.0), free_speed=0,
                     link_id_text=str(0)):
        self.link_id = link_id
        self.link_id_text=link_id_text
        self.length = length # ft
#         self.capacity = 0.0
#         self.alpha = 0.5
#         self.beta = 4.
        self.from_node = from_node
        self.to_node = to_node
        self.timestep = 0
        self.timesteps = 60
        self.timeinterval = 15.0  # seconds
        self.free_speed = free_speed  # ft/sec = 51.33*0.681818(converting fts to mph) = 34.9977 mph, 1.4667 (converting mph to fps)
        self.free_flow_time=length/free_speed
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
#         for k, v in kwargs.items():
#             self.__dict__[k] = v
#         self.init_dynamic_link()
#         self.scalefactor = 3600.0 / self.timeinterval  # for BPR (flow/hour)
        self.u_max = self.free_speed  # mph
        # self.u_min = 10.0  # mph
        self.u_min = 10.0*1.4667  #Siwei: ft/s 10mph
#         self.v_f = self.length / self.t0  # fps
        # self.noflane=max(1.0,int(self.capacity/2000))
#         if self.k_j - int(self.k_j) == 0:
#             self.k_j += 0.00001
#         if self.link_function == "triangularFD":
#             self.k_c = 0.2 * self.k_j
#         else:
#             self.k_c = 0.5 * self.k_j
#         self.w = self.k_c / (self.k_j - self.k_c) * self.v_f
#         # self.tt_max = max([self.m_greenshield_init(vol) for vol in range(10, 50000, 10)])
#         # self.tt_max = self.m_greenshield_init(self.k_j*0.99)
#         self.v_j = self.k_j * self.length * 0.98 * self.noflane

class Node(object):
    """
    Class for handling node object in Transportation Networks

    Parameters
    ----------
    node_id:    int
                identifier of a node

    """

    def __init__(self, node_id=0, node_XCOORD=0, node_YCOORD=0):
        #         self.node_id = node_id
        #         self.node_XCOORD=node_XCOORD
        #         self.node_YCOORD=node_YCOORD

        self.node_id = node_id
        self.node_XCOORD = node_XCOORD
        self.node_YCOORD = node_YCOORD


def open_link_file(network_path):
    with open(network_path) as f:
        csvreader = csv.DictReader(f)
        nodes = {}
        links = []
        node_list =[]
        for data in csvreader:
            #             print(data)
            origin_node = str(int(data["\xef\xbb\xbfFNODE"]))
            origin_node_XCOORD =str(float(data["FRXCOORD"]))
            origin_node_YCOORD =str(float(data["FRYCOORD"]))
            id = data["ROADSEGID"]
            to_node = str(int(data["TNODE"]))
            to_node_XCOORD =str(float(data["TOXCOORD"]))
            to_node_YCOORD =str(float(data["TOYCOORD"]))
            #             capacity = float(data[self.link_fields["capacity"]])
            length = float(data["LENGTH"])  # length (ft)
            #             alpha = float(data[self.link_fields["alpha"]])
            #             beta = float(data[self.link_fields["beta"]])
            if float(data['SPEED'] ) <10.00:
                free_speed =10.00 *1.46667
            else:
                free_speed = float(data['SPEED'] ) *1.46667  # change mph to ft/s
            name =str(data['RD20FULL'])


            t0 = length / free_speed  # (sec)
            if origin_node not in nodes:
                n = Node(node_id=origin_node ,node_XCOORD=origin_node_XCOORD ,node_YCOORD=origin_node_YCOORD)
                nodes[origin_node] = n

            if to_node not in nodes:
                n = Node(node_id=to_node ,node_XCOORD=to_node_XCOORD ,node_YCOORD=to_node_YCOORD)
                nodes[to_node] = n

            l = Link(link_id=len(links), length=length,
                     from_node=origin_node, to_node=to_node, flow=float(0.0), free_speed=free_speed,
                     link_id_text=id)
            links.append(l)
    #             node_=Node(node_id = 0,self.node_XCOORD=0,self.node_YCOORD=0)

    graph = nx.Graph()

    for l in links:
        graph.add_edge(l.from_node, l.to_node, object=l, time=l.free_flow_time)

    return graph





# def open_node_file(node_path, network):
#
#
#     return

