import network_algorithms

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
import numpy as np

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
    for agent in agent_list:
        agents_w_sens[agent] = normalized_sensitivities(agent)
        


        



    

