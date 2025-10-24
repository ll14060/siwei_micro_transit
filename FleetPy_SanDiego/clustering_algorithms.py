import os
import random
import csv
import datetime
from collections import defaultdict, OrderedDict, deque  
from itertools import islice
from math import radians, cos, sin, asin, sqrt
import heapq

import numpy as np
import pandas as pd
import scipy.integrate as integrate
import matplotlib.pyplot as plt
import networkx as nx

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score

from network_algorithms import read_super_network, read_request, get_link_type_from_O_to_D

from numba import njit

from setuptools import setup
from Cython.Build import cythonize

import psutil
import multiprocessing

def normalized_sensitivities(agent):
    total = (
        agent.bt_m_ivt + #in vehicle time motor transit
        agent.income #fare
    )
    if total == 0:
        # Avoid division by zero if+ all weights zero
        return 0, 0

    norm_bt_m_ivt = agent.bt_m_ivt / total
    norm_bt_fare = agent.income / total

    time_sensitivity = norm_bt_m_ivt
    income_sensitivity = norm_bt_fare

    return [time_sensitivity, income_sensitivity]

def clustering(agent_list):
    agents_w_sens = {}
    range_n_clusters= [2,3,4,5,6]

    for agent in agent_list:
        agents_w_sens[agent] = normalized_sensitivities(agent)

    kmeans_array = np.array(list(agents_w_sens.values()))
    best_n = get_best_n(range_n_clusters, kmeans_array)
    kmeans = KMeans(n_clusters=best_n, n_init="auto")
    labels = kmeans.fit_predict(kmeans_array)

    clustered_agents = {agent: label for agent, label in zip(agents_w_sens.keys(), labels)}
    centroids = kmeans.cluster_centers_

    cluster_to_agents = defaultdict(list)
    for agent, label in zip(agents_w_sens.keys(), labels):
        agent.cluster_id = label
        cluster_to_agents[label].append(agent)

    am = md = pm = ev = 0
    for agent in agent_list:
        t = agent.rq_time  # assuming rq_time is in seconds
        if t <= 10 * 3600:
            am += 1
        elif t <= 15 * 3600:
            md += 1
        elif t <= 20 * 3600:
            pm += 1
        else:
            ev += 1
    
    counts = {
        "AM": am,
        "MD": md,
        "PM": pm,
        "EV": ev
    }

    centroid_profile = {
        "time_period" : max(counts, key=counts.get),
        
        "income": np.mean([a.income for a in agent_list]),
        "bt_m_ivt": np.mean([a.bt_m_ivt for a in agent_list]),

        # car preferences
        "bt_c_0": np.mean([a.bt_c_0 for a in agent_list]),
        "bt_c_ivt": np.mean([a.bt_c_ivt for a in agent_list]),
        "bt_c_gas": np.mean([a.bt_c_gas for a in agent_list]),

        # transit preferences
        "bt_t_0": np.mean([a.bt_t_0 for a in agent_list]),
        "bt_t_wk": np.mean([a.bt_t_wk for a in agent_list]),
        "bt_f_ivt": np.mean([a.bt_f_ivt for a in agent_list]),
        "bt_f_wt": np.mean([a.bt_f_wt for a in agent_list]),
        "bt_f_trfer": np.mean([a.bt_f_trfer for a in agent_list]),
        "bt_t_fr": np.mean([a.bt_t_fr for a in agent_list]),

        # microtransit preferences
        "bt_m_wt": np.mean([a.bt_m_wt for a in agent_list]),

        # accessibility / socio-demographic
        "transit_15min_acc": np.mean([a.transit_15min_acc for a in agent_list]),
    }

    clusters_info = []
    for cluster_id, agent_list in cluster_to_agents.items():
        clusters_info.append({
            "cluster_id": cluster_id,
            "centroid": centroids[cluster_id],
            "cluster_profile": centroid_profile,
            "agent_list": agent_list
        })

    return clusters_info

#Finds best # of clusters by finding n with the highest silhouette score
def get_best_n(range_n_clusters, sens):
    silhouette_scores = {}
    for n_clusters in range_n_clusters:
        clusterer = KMeans(n_clusters=n_clusters, n_init = "auto")
        cluster_labels = clusterer.fit_predict(sens)
        silhouette_scores[n_clusters] = silhouette_score(sens, cluster_labels)
    return max(silhouette_scores, key = silhouette_scores.get)

class HeapNode:
    def __init__(self, node_id, cost):
        self.node_id = node_id
        self.cost = cost

    def __lt__(self, other):
        return self.cost < other.cost

def extract_cluster_attributes(centroid_profile):
    return {
        # time period:
        "time_period": centroid_profile["time_period"],
        # car preferences
        "bt_c_0": centroid_profile["bt_c_0"],
        "bt_c_ivt": centroid_profile["bt_c_ivt"],
        "bt_c_gas": centroid_profile["bt_c_gas"],

        # transit preferences
        "bt_t_0": centroid_profile["bt_t_0"],
        "bt_t_wk": centroid_profile["bt_t_wk"],
        "bt_f_wt": centroid_profile["bt_f_wt"],
        "bt_f_ivt": centroid_profile["bt_f_ivt"],
        "bt_f_trfer": centroid_profile["bt_f_trfer"],
        "bt_t_fr": centroid_profile["bt_t_fr"],

        # microtransit preferences
        "bt_m_wt": centroid_profile["bt_m_wt"],
        "bt_m_ivt": centroid_profile["bt_m_ivt"],

        # demographics
        "income": centroid_profile["income"],
        "transit_15min_acc": centroid_profile["transit_15min_acc"],
    }

def calculate_fare_factors(study_area, cluster_attrs, test_scenario, PkFareFactor, OffPkFareFactor, 
                           Fixed2MicroFactor, Micro2FixedFactor, dt_sd_full_trnst_ntwk):
    income = cluster_attrs["income"]
    time_period = cluster_attrs["time_period"]
    transit_15min_acc = cluster_attrs["transit_15min_acc"]

    # Thresholds by study area
    if study_area == "downtown_sd":
        low_acc_thrshd = 34986
        high_acc_thrshd = 43787
    elif study_area == "lemon_grove":
        low_acc_thrshd = 562
        high_acc_thrshd = 2297
    else:
        low_acc_thrshd, high_acc_thrshd = None, None

    # Scenario 1: Income-based fare factor
    low_income_threshold = 31850
    low_income_factor = 1
    if test_scenario == 1:
        low_income_factor = 0.5 if income <= low_income_threshold else 1

    # Scenario 2, 8, 10: Peak/Off-peak fare factor
    peak_factor = 1
    if test_scenario == 2:
        peak_factor = 1.5 if time_period in ["AM", "PM"] else 0.5
    elif test_scenario == 8:
        peak_factor = 1 if time_period in ["AM", "PM"] else 0.5
    elif test_scenario == 10:
        peak_factor = PkFareFactor if time_period in ["AM", "PM"] else OffPkFareFactor

    # Scenario 3 and 9: Accessibility-based fare factor
    acc_factor = 1
    if test_scenario in [3, 9] and low_acc_thrshd is not None and high_acc_thrshd is not None:
        if transit_15min_acc <= low_acc_thrshd:
            acc_factor = 0.5
        elif transit_15min_acc <= high_acc_thrshd:
            acc_factor = 1
        else:
            acc_factor = 1.5 if test_scenario == 3 else 1

    return {
        "low_income_factor": low_income_factor,
        "peak_factor": peak_factor,
        "acc_factor": acc_factor
    }

def calculate_link_cost(
    study_area, dt_sd_full_trnst_ntwk, test_scenario, microtransit_start_fare,
    microtransit_dist_based_rate, transit_fare_set, Fixed2MicroFactor, Micro2FixedFactor,
    cluster_attrs, link_data, min_node, edge, path, IsMicroLink, IsFixedLink
):

    link_travel_time = link_data.free_flow_time
    link_type_ = link_data.link_type
    link_length = link_data.length
    route = link_data.route

    # Extract agent's value of time parameters
    bt_t_wk = cluster_attrs["bt_t_wk"]
    bt_f_ivt = cluster_attrs["bt_f_ivt"]
    bt_f_wt = cluster_attrs["bt_f_wt"]
    bt_t_fr = cluster_attrs["bt_t_fr"]
    bt_f_trfer = cluster_attrs["bt_f_trfer"]
    bt_m_ivt = cluster_attrs["bt_m_ivt"]
    bt_m_wt = cluster_attrs["bt_m_wt"]
    bt_c_ivt = cluster_attrs["bt_c_ivt"]
    bt_c_gas = cluster_attrs["bt_c_gas"]

    low_income_factor = cluster_attrs.get("low_income_factor", 1)
    peak_factor = cluster_attrs.get("peak_factor", 1)
    acc_factor = cluster_attrs.get("acc_factor", 1)

    # Get previous link type from path
    if min_node != cluster_attrs["initial"]:
        _, _, link_type_pre, _ = path[min_node]
    else:
        link_type_pre = 0

    # Initialize fare variables
    transit_fare = 0
    micro_fare = 0
    gas_cost = 0

    # Calculate generalized link cost by link type
    if link_type_ == 0:  # walking link
        generalized_link_travel_time = bt_t_wk * link_travel_time / 60

    elif link_type_ == 1:  # transit in-vehicle link
        generalized_link_travel_time = bt_f_ivt * link_travel_time / 60

    elif link_type_ == 2:  # fixed route transit waiting link
        # Calculate transit fare logic based on study_area and network
        if study_area == "downtown_sd":
            if dt_sd_full_trnst_ntwk:
                if min_node <= 731 and 732 <= edge <= 871:
                    if link_type_pre != 2:
                        transit_fare = transit_fare_set
            else:
                if min_node <= 731 and 732 <= edge <= 772:
                    if link_type_pre != 2:
                        transit_fare = transit_fare_set
        elif study_area == "lemon_grove":
            if min_node <= 1098 and 1099 <= edge <= 1170:
                if link_type_pre != 2:
                    transit_fare = transit_fare_set

        # Adjust fare if scenario and micro link conditions
        if IsMicroLink and test_scenario in [4, 7, 10]:
            if test_scenario == 10:
                transit_fare = transit_fare_set * Micro2FixedFactor
            else:
                transit_fare = 0

        generalized_link_travel_time = bt_f_wt * link_travel_time / 60 + bt_t_fr * transit_fare

    elif link_type_ == 3:  # transfer link
        generalized_link_travel_time = bt_f_trfer * link_travel_time / 60

    elif link_type_ == 4:  # microtransit in-vehicle
        if test_scenario == 5:
            micro_fare = 0
        else:
            micro_fare = microtransit_dist_based_rate * link_length * low_income_factor * peak_factor * acc_factor
            if IsFixedLink and test_scenario in [4, 7, 10]:
                if test_scenario == 10:
                    micro_fare = micro_fare * Fixed2MicroFactor
                else:
                    micro_fare = micro_fare * 0.5

        generalized_link_travel_time = bt_m_ivt * link_travel_time / 60 + bt_t_fr * micro_fare

    elif link_type_ == 5:  # microtransit waiting
        if test_scenario == 5:
            micro_fare = 0
            if study_area == "downtown_sd" and dt_sd_full_trnst_ntwk:
                if min_node <= 731 and 872 <= edge <= 1603:
                    micro_fare = transit_fare_set
            if study_area == "lemon_grove":
                if min_node <= 1098 and 1171 <= edge <= 2269:
                    micro_fare = transit_fare_set

            generalized_link_travel_time = bt_m_wt * link_travel_time / 60 + bt_t_fr * micro_fare
        elif test_scenario in [6, 7, 10]:
            micro_fare = 0
            if study_area == "downtown_sd" and dt_sd_full_trnst_ntwk:
                if min_node <= 731 and 872 <= edge <= 1603:
                    if test_scenario == 10:
                        micro_fare = microtransit_start_fare * Fixed2MicroFactor
                    elif test_scenario == 7:
                        micro_fare = microtransit_start_fare * 0.5
                    else:
                        micro_fare = microtransit_start_fare
            if study_area == "lemon_grove":
                if min_node <= 1098 and 1171 <= edge <= 2269:
                    if test_scenario == 10:
                        micro_fare = microtransit_start_fare * Fixed2MicroFactor
                    elif test_scenario == 7:
                        micro_fare = microtransit_start_fare * 0.5
                    else:
                        micro_fare = microtransit_start_fare

            generalized_link_travel_time = bt_m_wt * link_travel_time / 60 + bt_t_fr * micro_fare
        else:
            generalized_link_travel_time = bt_m_wt * link_travel_time / 60

    elif link_type_ == 7:  # auto network link
        gas_cost = 0.00019 * link_length
        generalized_link_travel_time = bt_c_ivt * link_travel_time / 60 + bt_c_gas * gas_cost
    else:
        gas_cost = 0
        generalized_link_travel_time = 0  # fallback

    return generalized_link_travel_time, transit_fare, micro_fare, gas_cost

def dijkstra_search(
    graph, initial, mode, cluster_attrs, test_scenario, 
    study_area, dt_sd_full_trnst_ntwk, transit_fare_set, microtransit_start_fare,
    microtransit_dist_based_rate, PkFareFactor, OffPkFareFactor, Fixed2MicroFactor, Micro2FixedFactor,
    verbose=False
):
    heap_q = []
    if mode == "T":
        visited_temp = {initial: cluster_attrs["bt_t_0"]}
        heapq.heappush(heap_q, HeapNode(initial, cluster_attrs["bt_t_0"]))
    elif mode == "C":
        visited_temp = {initial: cluster_attrs["bt_c_0"]}
        heapq.heappush(heap_q, HeapNode(initial, cluster_attrs["bt_c_0"]))
    else:
        raise ValueError("Unsupported mode: choose 'T' or 'C'")

    time_visited_temp = {initial: 0}
    dist_visited_temp = {initial: 0}
    fare_visited_temp = {initial: 0}
    F_fare_visited_temp = {initial: 0}
    M_fare_visited_temp = {initial: 0}
    auto_gas_visited_temp = {initial: 0}

    path = {}
    time_path = {}
    dist_path = {}

    try:
        (nodes, edges) = (set(graph.nodes), graph.edges)
        costs = graph.costs
    except:  # for NetworkX
        (nodes, edges) = (set(graph.nodes()), graph)  
        costs = []

    while heap_q:
        if verbose:
            print("----------------------------------")

        smallest_node = heapq.heappop(heap_q)
        min_node = smallest_node.node_id

        permanent = visited_temp[min_node]
        time_permanent = time_visited_temp[min_node]
        dist_permanent = dist_visited_temp[min_node]
        fare_permanent = fare_visited_temp[min_node]
        F_fare_permanent = F_fare_visited_temp[min_node]
        M_fare_permanent = M_fare_visited_temp[min_node]
        auto_gas_permanent = auto_gas_visited_temp[min_node]

        if min_node in edges:
            if min_node != cluster_attrs["initial"]:
                IsMicroLink, IsFixedLink, _ = get_link_type_from_O_to_D(cluster_attrs["initial"], min_node, path)
            else:
                IsMicroLink, IsFixedLink = False, False

            for edge in edges[min_node]:
                edge_data = graph.get_edge_data(min_node, edge)["object"]
                generalized_link_travel_time, transit_fare, micro_fare, gas_cost = calculate_link_cost(
                    study_area, dt_sd_full_trnst_ntwk, test_scenario, microtransit_start_fare,
                    microtransit_dist_based_rate, transit_fare_set, Fixed2MicroFactor, Micro2FixedFactor,
                    {**cluster_attrs, **{
                        "low_income_factor": cluster_attrs.get("low_income_factor", 1),
                        "peak_factor": cluster_attrs.get("peak_factor", 1),
                        "acc_factor": cluster_attrs.get("acc_factor", 1)
                    }},
                    edge_data, min_node, edge, path, IsMicroLink, IsFixedLink
                )

                temp = permanent + generalized_link_travel_time
                time_temp = time_permanent + edge_data.free_flow_time
                dist_temp = dist_permanent + edge_data.length

                if mode == "T":
                    fare_temp = fare_permanent + transit_fare + micro_fare
                    F_fare_temp = F_fare_permanent + transit_fare
                    M_fare_temp = M_fare_permanent + micro_fare
                    auto_gas_temp = 0
                else:
                    fare_temp = fare_permanent + gas_cost
                    auto_gas_temp = auto_gas_permanent + gas_cost
                    F_fare_temp = 0
                    M_fare_temp = 0

                if edge not in visited_temp or temp < visited_temp[edge]:
                    visited_temp[edge] = temp
                    path[edge] = (min_node, temp, edge_data.link_type, getattr(edge_data, "route", None))
                    heapq.heappush(heap_q, HeapNode(edge, temp))

                    time_visited_temp[edge] = time_temp
                    dist_visited_temp[edge] = dist_temp
                    fare_visited_temp[edge] = fare_temp
                    F_fare_visited_temp[edge] = F_fare_temp
                    M_fare_visited_temp[edge] = M_fare_temp
                    auto_gas_visited_temp[edge] = auto_gas_temp

                    time_path[edge] = (min_node, time_temp, edge_data.link_type, getattr(edge_data, "route", None))
                    dist_path[edge] = (min_node, dist_temp, edge_data.link_type, getattr(edge_data, "route", None))

                if verbose:
                    print(
                        f"Permanent: {permanent}, i: {min_node}, j: {edge}, Link cost: {generalized_link_travel_time}, Temp Cost: {visited_temp[edge]}"
                    )

    return visited_temp, time_visited_temp, dist_visited_temp, fare_visited_temp, F_fare_visited_temp, M_fare_visited_temp, path, time_path, dist_path

def generalized_cost_dijkstra_cluster_source_to_all(
    study_area, graph, cluster, transit_fare_set, microtransit_start_fare, microtransit_dist_based_rate,
    dt_sd_full_trnst_ntwk, PkFareFactor, OffPkFareFactor, Fixed2MicroFactor, Micro2FixedFactor,
    test_scenario, mode, verbose=False
):
    # Extract cluster attributes
    cluster_attrs = extract_cluster_attributes(cluster["cluster_profile"])
    cluster_attrs["initial"] = cluster["initial"]

    # Calculate fare factors and add them to cluster_attrs
    fare_factors = calculate_fare_factors(
        study_area, cluster_attrs, test_scenario, PkFareFactor, OffPkFareFactor,
        Fixed2MicroFactor, Micro2FixedFactor, dt_sd_full_trnst_ntwk
    )

    cluster_attrs.update(fare_factors)

    # Run Dijkstra search
    results = dijkstra_search(
        graph, cluster_attrs["initial"], mode, cluster_attrs, test_scenario,
        study_area, dt_sd_full_trnst_ntwk, transit_fare_set, microtransit_start_fare,
        microtransit_dist_based_rate, PkFareFactor, OffPkFareFactor, Fixed2MicroFactor, Micro2FixedFactor,
        verbose
    )

    return results

def reconstruct_path_and_metrics(agent, cluster_paths):
    cp = cluster_paths[agent.cluster_id][agent.rq_O]

    visited_temp = cp["visited_temp"]
    time_visited_temp = cp["time_visited_temp"]
    dist_visited_temp = cp["dist_visited_temp"]
    fare_visited_temp = cp["fare_visited_temp"]
    F_fare_visited_temp = cp["F_fare_visited_temp"]
    M_fare_visited_temp = cp["M_fare_visited_temp"]
    path = cp["path"]
    time_path = cp["time_path"]
    dist_path = cp["dist_path"]

    if agent.rq_D not in cluster_paths[agent.cluster_id]:
        print(f"Destination {agent.rq_D} not in visited_temp")
        return None

    # Reconstruct path as a dict of tuples: path[node] = (prev_node, cost, link_type, route)
    shortest_path = {}
    current_node = agent.rq_D
    while current_node != agent.rq_O:
        if current_node not in path:
            # No complete path back to origin
            return None
        prev_node, cost, link_type, route = path[current_node]  # unpack existing tuple
        shortest_path[current_node] = (prev_node, cost, link_type, route)
        current_node = prev_node
    # origin has no previous node
    shortest_path[agent.rq_O] = (None, 0, None, None)

    # Reconstruct time_path as a dict: time_path[node] = (prev_node, time)
    time_path_single = {}
    current_node = agent.rq_D
    while current_node != agent.rq_O:
        if current_node not in time_path:
            return None
        prev_node, time, link_type, route = time_path[current_node]  # unpack tuple
        time_path_single[current_node] = (prev_node, time, link_type, route)
        current_node = prev_node
    # origin
    time_path_single[agent.rq_O] = (None, 0)

    # Reconstruct dist_path as a dict: dist_path[node] = (prev_node, distance)
    dist_path_single = {}
    current_node = agent.rq_D
    while current_node != agent.rq_O:
        if current_node not in dist_path:
            return None
        prev_node, dist, link_type, route = dist_path[current_node]  # unpack tuple
        dist_path_single[current_node] = (prev_node, dist, link_type, route)
        current_node = prev_node
    # origin
    dist_path_single[agent.rq_O] = (None, 0)

    return (
        visited_temp,
        time_visited_temp,
        dist_visited_temp,
        fare_visited_temp,
        F_fare_visited_temp,
        M_fare_visited_temp,
        shortest_path,
        time_path_single,
        dist_path_single
    )




    

