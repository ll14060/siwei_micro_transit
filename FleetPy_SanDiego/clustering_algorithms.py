import os
import math
import random
import csv
import datetime
from collections import defaultdict, OrderedDict, deque  # deque if you want later
from itertools import islice
from math import radians, cos, sin, asin, sqrt
import heapq

import numpy as np
import pandas as pd
import scipy
import scipy.integrate as integrate
import matplotlib.pyplot as plt
import networkx as nx

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score

from network_algorithms import read_super_network, read_request, dijsktra_all_to_all

from setuptools import setup
from Cython.Build import cythonize

def normalized_sensitivities(agent):
    total = (
        agent.bt_0 +
        agent.bt_wk +
        agent.bt_wt +
        agent.bt_m_ivt +
        agent.bt_f_ivt +
        agent.bt_f_trfer +
        agent.bt_fare
    )
    if total == 0:
        # Avoid division by zero if all weights zero
        return 0, 0

    norm_bt_0 = agent.bt_0 / total
    norm_bt_wk = agent.bt_wk / total
    norm_bt_wt = agent.bt_wt / total
    norm_bt_m_ivt = agent.bt_m_ivt / total
    norm_bt_f_ivt = agent.bt_f_ivt / total
    norm_bt_f_trfer = agent.bt_f_trfer / total
    norm_bt_fare = agent.bt_fare / total

    time_sensitivity = (
        norm_bt_0 +
        norm_bt_wk +
        norm_bt_wt +
        norm_bt_m_ivt +
        norm_bt_f_ivt +
        norm_bt_f_trfer
    )
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
    for label, agent in zip(agents_w_sens.keys(), labels):
        cluster_to_agents[label].append(agent)

    clusters_info = []
    for cluster_id, agents in cluster_to_agents.items():
        clusters_info.append({
            "cluster_id": cluster_id,
            "centroid": centroids[cluster_id],
            "agents": agents
        })

    return clusters_info, kmeans.inertia_

#Finds best # of clusters by finding n with the highest silhouette score
def get_best_n(range_n_clusters, sens):
    silhouette_scores = {}
    for n_clusters in range_n_clusters:
        clusterer = KMeans(n_clusters=n_clusters, n_init = "auto")
        cluster_labels = clusterer.fit_predict(sens)
        silhouette_scores[n_clusters] = silhouette_score(sens, cluster_labels)
    return max(silhouette_scores, key = silhouette_scores.get)





        



    

