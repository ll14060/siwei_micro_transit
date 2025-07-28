# This Module include multiple path finding algorithms

from gurobipy import *
import networkx as nx
import matplotlib.pyplot as plt
import Graph2Shape as gs
import Parameter as para
from read_network import network_nodes
#####################################################################################################
# Parameters
# Network file txt name
networkName = 'SiouxFallsNetwork.txt'
network_path="SiouxFalls/SiouxFalls_net.tntp"
demand_path="SiouxFalls/SiouxFalls_trips.tntp"
node_path="SiouxFalls/SiouxFalls_node.tntp"
# Network nodes position for visiualization (may not needed)
# # Node_pos for Nguen_Duplis Network
# node_pos = {1: (-1, 1), 2: (2, -1), 3: (1, -2), 4: (-2, 0), 5: (-1, 0), 6: (0, 0), 7: (1, 0), 8: (2, 0),
#                9: (-1, -1), 10: (0, -1), 11: (1, -1), 12: (0, 1), 13:(0, -2)}
# Node_pos for Sioux Falls network
node_pos = node_pos = {1: (-2, 3), 2: (1, 3), 3: (-2, 2), 4: (-1, 2), 5: (0, 2), 6: (1, 2), 7: (2, 1), 8: (1, 1),
                       9: (0, 1), 10: (0, 0), 11: (-1, 0), 12: (-2, 0), 13:(-2, -4), 14:(-1, -2), 15:(0, -2), 16:(1, 0),
                       17:(1, -1), 18:(2, 0), 19:(1, -2), 20:(1, -4), 21:(0, -4), 22:(0,-3), 23:(-1, -3), 24:(-1,-4)}

# Cost and Reward coefficient, sum = 1
cost_coeff = 0.5
reward_coeff = 0.5
######################################################################################################


# Function to load network data from .tntp file onto a networkx digraph

def readNetwork():
    network = nx.DiGraph()
    # Updates node and link attributes to the networkx digraph
    network = gs.open_link_file(network_path)
    gs.open_node_file(node_path, network)
    return network

# This function process network file to extract link names, link cost and reward
def networkProcess(networkName):

    # Reading Data
    f = open(networkName, "r")
    # networkx digraph to store the network

    # The first line is "Number of Nodes: n"
    line = f.readline()
    # End of the line is marked by a "\n" as enter
    line = line.strip('\n')
    data = line.split(':')
    # The second line is "Number of Links: n"
    num_nodes = int(data[1])
    line = f.readline()
    # End of the line is marked by a "\n" as enter
    line = line.strip('\n')
    data = line.split(':')
    num_links = int(data[1])
    # The third line is the title "From Node, To Node, Cost, Reward"
    line = f.readline()

    # Starting from the fourth line are the data
    line =f.readline()

    # Set up hash table for optimization input parameters
    # links are the name of links as (i, j), in a Gurobi tuplelist
    links = tuplelist()
    # Cost Cij and reward rij are in dictionaries
    linkCost  = {}
    linkReward = {}

    # While(len(line)), means moving through the entire line
    while(len(line)):
        # A line ends with '\n'
        line = line.strip('\n')
        # Comma deliminator
        data = line.split(',')
        # Sequence as "From Node, To Node, Cost, Reward"
        from_node = int(data[0])
        to_node = int(data[1])
        cost_ij = float(data[2])
        reward_ij = float(data[3])
        # Add link to digraph        G.add_edge(from_node,to_node,cost_ij=cost_ij,reward_ij=reward_ij)        # Append to dictionaries
        links.append((from_node,to_node))
        linkCost[from_node, to_node] = cost_ij
        linkReward[from_node, to_node] = reward_ij
        # Read next line
        line = f.readline()

    # Close the file in a polite manner
    f.close()

    # Will return 6 items
    return num_nodes, num_links, links, linkCost, linkReward



# Function to normalize the link costs to a (a,b) range, if any of the weighted link costs are negative
# Input: Dictionary with key as (i,j) link and value as weighted link cost
# Ouput: Dictionary with normalized rescaled link costs in (a,b) range

def normalize_cost(weightedCost,a,b):

    min_cost = min(weightedCost.values())
    max_cost = max(weightedCost.values())
    # If all values are the same then set the value to 0
    if max_cost == min_cost:
        norm_Cost = {i: 0 for i in weightedCost.keys()}
    else:
        norm_Cost = {i: (b-a)*(weightedCost[i] - min_cost)/(max_cost - min_cost) + a for i in weightedCost.keys()}
    return norm_Cost




######################################################################################################
# The followings are LP based path finding algorithms
######################################################################################################


# This is an optimization based on LP formulation of SHP
# The obj of this one is min (a*cij*xij + b*rij*xij)
# It is a weighted method for muti objective
def weightedSHP(costTime, num_nodes, origin, destination, reward, cost_coeff, reward_coeff, currenttime,method):
    cost_coeff = para.cost_coefficient
    reward_coeff = para.reward_coefficient
    # Initiate Model
    m = Model('WSHP')

    # Retrieve link costs
    linkCost = {}
    for i in reward.keys():
        linkCost.update({i: costTime[i][0]})

    # combine cost and reward to get new weighted cost
    cost_coeff = para.cost_coefficient
    reward_coeff = para.reward_coefficient
    weightedCost = {}
    for (i, j) in reward.keys():
        weightedCost.update({(i,j):(cost_coeff*linkCost[(i, j)] - reward_coeff*reward[(i, j)])})
    # Check if any of the weightedCosts are negative

    negative_cost_links = {}

    for (i,j) in weightedCost.keys():
        if weightedCost[(i,j)] <= 0:
            negative_cost_links[(i,j)] = weightedCost[(i,j)]
    # If there are negative costs, then change the values based on the method selected
    if len(negative_cost_links) > 0:
        with open(para.output_timestep_log, "a") as op_file:
            print('There are negative weighted link costs ', file=op_file)
        # If Method 2a, then change all negative values to a small number
        if method == '2a':
            [negative_cost_links.update({key:0.001}) for key in negative_cost_links.keys()]
            weightedCost.update(negative_cost_links)
            with open(para.output_timestep_log, "a") as op_file:
                print('Negative weighted link costs changed to 0.001 ', file=op_file)
        # If method 2b, normalize the negative weights alone to a range of very small numbers (0.001,0.002)
        elif method == '2b':
            negative_cost_links = normalize_cost(negative_cost_links,0.001,0.002)
            weightedCost.update(negative_cost_links)
            with open(para.output_timestep_log, "a") as op_file:
                print('Negative weighted link costs normalized to (0.001,0.002) range ', file=op_file)

    # Construct links as a tuple list
    links = tuplelist()
    for i,j in reward.keys():
        links.append((i, j))


    # Add Vars and objs
    x = m.addVars(links, vtype = GRB.BINARY, obj=weightedCost, name ="flow")

    # Add Standard Constraints
    # Flow constraint for each node
    #
    for i in network_nodes:
        # Flow preservation constraint
        # m.addConstr( sum(x[i,j] for i,j in links.select(i, '*')) - sum(x[j,i] for j,i in links.select('*',i)) ==
        #              (1 if i==origin else -1 if i==destination else 0 ),'node%s_' % i )
        # # Repeated node visit elimination constraint
        # m.addConstr(sum(x[i,j] for i,j in links.select(i, '*')) <= (1 if i != destination else 0))
        # m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) <= (1 if i != origin else 0))

        if i == origin:
            m.addConstr(sum(x[i, j] for i, j in links.select(i, '*')) == 1)
            m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) == 0)
        elif i == destination:
            m.addConstr(sum(x[i, j] for i, j in links.select(i, '*')) == 0)
            m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) == 1)
        else:
            m.addConstr(sum(x[i, j] for i, j in links.select(i, '*')) <= 1)
            m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) <= 1)
            m.addConstr(sum(x[i, j] for i, j in links.select(i, '*')) - sum(x[j, i] for j, i in links.select('*', i)) == 0)

    # Adding subtour elimination

            # m.setObjective(GRB.MINIMIZE)
    m.update()
    # model_log = "model_bicriterion_from__" + str(origin) + "to_" + str(destination)
    # model_log = model_log + ".lp"
    # m.write(model_log)
    m.optimize()

    if m.status == GRB.Status.OPTIMAL:
        # Dictionary stores optimal links with key as source node and value as destination node of the link
        optimalLinks = {}
        optimalRoute = [(origin, currenttime)]
        optimalRouteTimeCost = 0
        # print('The final solution is:')
    for i, j in links:
        if x[i, j].x > 0.1:

            # Key is origin node of link, value is destination node of link
            optimalLinks[i] = j
            optimalRouteTimeCost += costTime[(i,j)][0]

    optimalRouteTimeCost = round(optimalRouteTimeCost,1)
    
    leadingNode = origin
    LeadingNodeTime = currenttime
    # Trace path from origin to destination until destination is reached
    # Set reached destination flag as false
    # This will be set to True when the destination node is reached
    reached_dest_flag = False
    while not reached_dest_flag:
        i = leadingNode
        j = optimalLinks[leadingNode]
        optimalRoute.append((j, round(LeadingNodeTime+costTime[(i,j)][0],1)))
        # Update leading node
        leadingNode = j
        LeadingNodeTime = LeadingNodeTime + costTime[(i,j)][0]

        # If second node is the destination, then set destination reached flag to True
        if leadingNode == destination:
            reached_dest_flag = True

            # print(i, j, x[i,j].x, reward.get((i,j)))

    return optimalRoute, optimalRouteTimeCost
    # end of optimization


# Function to find the demand along a given path
# Input path and demand link weights
# Path is either list type, or dictionary type, with keys as start nodes and values end node of each link in the path
# Returns demand along the path

def cal_demand_along_path(path,link_demand):

    demand = 0
    # If path is in list type
    if isinstance(path,list):
        for i in range(0,len(path)-1):
            demand += link_demand[(path[i],path[i+1])]
    # Else path is a dictionary object
    else:
        for i in path.keys():
            demand += link_demand[(i, path[i])]

    return demand

# Function to find the traveltime along a given path
# Input path and link cost dictionary
# Path is either list type, or dictionary type, with keys as start nodes and values end node of each link in the path
# Returns travel time along the path

def cal_cost_along_path(path,link_cost):

    traveltime = 0
    # If path is in list type
    if isinstance(path,list):
        for i in range(0,len(path)-1):
            traveltime += link_cost[(path[i],path[i+1])]
    # Else path is a dictionary object
    else:
        for i in path.keys():
            traveltime += link_cost[(i, path[i])]

    return traveltime
# Function to find demand along path Version 2
# Input, links in optimal path is dictionary, from optimal solution with key, start node, value, end node for each link in optimal path

    # This is an optimization based on LP formulation of SHP
    # The obj of this one is min cost, with a min demand on path constraint
    # Input: Method, '1a' or '1b', details in Parameters.py

def constrained_demand_SHP(costTime, num_nodes, origin, destination, reward, min_demand_factor, max_detour_factor,currenttime,method):


    # Initiate Model
    m = Model('C_D_SHP')

    shortest_path = nx.shortest_path(road_network,origin,destination,'traveltime')
    demand_in_sp = cal_demand_along_path(shortest_path,reward)
    # Find shortest path length
    # Change later to use pre-computed value
    time_in_sp = nx.shortest_path_length(road_network,origin,destination,'traveltime')

    # Convert costTime to costDollar
    linkCost = {}
    for i in costTime.keys():
        linkCost.update({i: costTime[i][0]})

    # combine cost and reward to get new weighted cost
    # cost_coeff = para.cost_coefficient
    # reward_coeff = para.reward_coefficient
    # weightedCost = {}
    # for (i, j) in reward.keys():
    #     weightedCost.update({(i, j): (cost_coeff * costDollar[(i, j)])})
    # for (i,j) in weightedCost.keys():
    #     if weightedCost[(i,j)] <= 0:
    #         print ((i.j), ": ",weightedCost[(i,j)])
    # Construct links as a tuple list
    links = tuplelist()
    for i, j in reward.keys():
        links.append((i, j))

    # Construct a node List
    nodes_list=[]
    for i, j in reward.keys():
        if i not in nodes_list:
            nodes_list.append(i)
        if j not in nodes_list:
            nodes_list.append(j)


    # Add Vars and objs
    # Objective (minimize cost)
    x = m.addVars(links, vtype=GRB.BINARY, obj=linkCost, name="flow")
    t = m.addVars(nodes_list, vtype=GRB.CONTINUOUS, name='ArrivTime')

    # Add Standard Constraints
    # Flow constraint for each node
    #
    for i in network_nodes:
        # Flow preservation constraint
        # m.addConstr( sum(x[i,j] for i,j in links.select(i, '*')) - sum(x[j,i] for j,i in links.select('*',i)) ==
        #              (1 if i==origin else -1 if i==destination else 0 ),'node%s_' % i )
        # # Repeated node visit elimination constraint
        # m.addConstr(sum(x[i,j] for i,j in links.select(i, '*')) <= (1 if i != destination else 0))
        # m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) <= (1 if i != origin else 0))

        if i == origin:
            m.addConstr(sum(x[i, j] for i, j in links.select(i, '*')) == 1)
            m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) == 0)
        elif i == destination:
            m.addConstr(sum(x[i, j] for i, j in links.select(i, '*')) == 0)
            m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) == 1)
        else:
            m.addConstr(sum(x[i, j] for i, j in links.select(i, '*')) <= 1)
            m.addConstr(sum(x[j, i] for j, i in links.select('*', i)) <= 1)
            m.addConstr(
                sum(x[i, j] for i, j in links.select(i, '*')) - sum(x[j, i] for j, i in links.select('*', i)) == 0)

    # Add Minimum demand constraint
    m.addConstr(sum(x[i, j] * reward[(i, j)] for i, j in links) >= min_demand_factor * demand_in_sp, name='Min_Demand')
    # Add maximum detour constraint
    m.addConstr(sum(x[i, j] * linkCost[(i, j)] for i, j in links) <= max_detour_factor * time_in_sp, name='Max_Detour')

    # Add a group of subtour elimination constraints
    for i, j in reward.keys():
        m.addConstr(t[i] + linkCost[(i, j)] <= t[j] + (1 - x[i, j])*100000)

    # Add a initial time for origin
    m.addConstr(t[origin] == 0)
    # m.setObjective(GRB.MINIMIZE)
    m.update()
    model_log = "model_unicriterion_from__" + str(origin) + "to_" + str(destination)
    model_log = model_log + ".lp"
    # m.write(model_log)
    m.optimize()
    # Flag variable to choose whether to return shortest path as optimal solution
    sp_as_opt_spln_flag = False
    # Dictionary stores optimal links with key as source node and value as destination node of the link
    optimalLinks = {}
    optimalRoute = [(origin, currenttime)]
    optimalRouteTimeCost = 0
    optimalRouteDemand = 0



    if m.status == GRB.Status.OPTIMAL:
        with open(para.output_timestep_log, "a") as op_file:
            print('Optimal Bicriterion path found ', file=op_file)
        # Retreive optimal solution path, optimal solution travel time and demand
        for i, j in links:
            if x[i, j].x > 0.1:
                # Key is origin node of link, value is destination node of link
                optimalLinks[i] = j
                optimalRouteTimeCost += costTime[(i, j)][0]
                optimalRouteDemand += reward[(i,j)]

        # If bi-criterion Policy is '1b' then check trade-off between travel time and cost
        # on optimal solution path versus shortest path to decide actual solution

        if method == '1b':

            weighted_cost_sp = para.cost_coefficient * time_in_sp - para.reward_coefficient * demand_in_sp
            weighted_cost_bp = para.cost_coefficient * optimalRouteTimeCost - para.reward_coefficient * optimalRouteDemand

            # If weighted biobjective cost on Shortest Path is less than BiCriterion Path
            # Then return shortest path as optimal solution
            # Else do nothing, retain optimal solution returned by solver
            dummy = 0
            if weighted_cost_sp < weighted_cost_bp:
                sp_as_opt_spln_flag = True
                with open(para.output_timestep_log, "a") as op_file:
                    print('Not Worth Taking BiCriterion Path, Taking Shortest Path', file=op_file)
            else:
                with open(para.output_timestep_log, "a") as op_file:
                    print('Worth Taking BiCriterion Path', file=op_file)

    # Return shortest path as optimal solution, either if no optimal solution found
    #                                           or if Policy 1b deems Shortest Path is the better solution
    elif m.status != GRB.Status.OPTIMAL or sp_as_opt_spln_flag:

        if m.status!= GRB.Status.OPTIMAL:
            with open(para.output_timestep_log, "a") as op_file:
                print('No Optimal Solution Found, Taking Shortest Path', file=op_file)
        optimalRouteTimeCost = time_in_sp
        optimalRouteDemand = demand_in_sp
        # Reset optima links returned by solver
        optimalLinks.clear()
        # Add optimal links based on shortest path
        for i in range(0,len(shortest_path)-1):
            optimalLinks[shortest_path[i]] = shortest_path[i+1]

    else:
        # Error in Solving Bicriterion Path
        with open(para.output_timestep_log, "a") as op_file:
            print('Error in Bi Criterion Path solution', file=op_file)

    # Debug Note
    # Subtour will casuse the calculation of optimal route and optimal route time unmatched. Need to fix that

    leadingNode = origin
    LeadingNodeTime = currenttime
    # Trace path from origin to destination until destination is reached
    # Set reached destination flag as false
    # This will be set to True when the destination node is reached
    reached_dest_flag = False
    while not reached_dest_flag:
        i = leadingNode
        j = optimalLinks[i]
        optimalRoute.append((j, LeadingNodeTime + costTime[(i, j)][0]))
        # Update leading node
        leadingNode = j
        LeadingNodeTime += costTime[(i, j)][0]

        # If leading node is the destination, then set destination reached flag to True
        if leadingNode == destination:
            reached_dest_flag = True

            # print(i, j, x[i,j].x, reward.get((i,j)))

    return optimalRoute, optimalRouteTimeCost
# end of optimization

    # # The following draws the graph
    # # Create Graph
    # G=nx.DiGraph()
    # # G=nx.MultiDiGraph()
    # list_nodes = list(range(1, num_nodes+1))
    # G.add_nodes_from(list_nodes)
    # for i,j in links:
    #     G.add_edge(i,j)
    #
    # # Adding the position attribute to each node
    # node_pos = node_pos
    #
    # # Create a list of edges in shortest path
    # red_edges = [(i,j) for i,j in links if x[i,j].x > 0]
    #
    # #Create a list of nodes in shortest path
    # sp = [ i for i,j in links if x[i,j].x > 0 ]
    # sp.append(destination)
    #
    # # If the node is in the shortest path, set it to red, else set it to white color
    # node_col = ['white' if not node in sp else 'red' for node in G.nodes()]
    # # If the edge is in the shortest path set it to red, else set it to white color
    # edge_col = ['black' if not edge in red_edges else 'red' for edge in G.edges()]
    # # Draw the nodes
    # nx.draw_networkx(G,node_pos, node_color= node_col, node_size=450)
    # # Draw the node labels
    # # nx.draw_networkx_labels(G1, node_pos,node_color= node_col)
    # # Draw the edges
    # nx.draw_networkx_edges(G, node_pos,edge_color= edge_col)
    # # Draw the edge labels
    # #     nx.draw_networkx_edge_labels(G, node_pos,edge_color= edge_col, edge_labels=cost)
    # # Remove the axis
    # plt.axis('off')

    # Show the plot
    # plt.show()

######################################################################################################
# This is an optimization based on LP formulation of SHP
# The obj of this one is min cijxij as total link cost
# It uses reward as a constraint
def SHPwithConstr(cost, links, num_nodes, origin, destination, reward, rewardTotal, node_pos):
    # Initiate Model
    m = Model('SHPC')

    # Add Vars and objs
    x = m.addVars(links, vtype = GRB.BINARY, obj=cost, name ="flow")

    # Add Standard Constraints
    for i in range(1, num_nodes+1):
        m.addConstr( sum(x[i,j] for i,j in links.select(i, '*')) - sum(x[j,i] for j,i in links.select('*',i)) ==
                     (1 if i==origin else -1 if i==destination else 0 ),'node%s_' % i )

    # Add Minimum reward constraint
    m.addConstr(sum(x[i,j]*reward[(i, j)] for i,j in links) >= rewardTotal, name = 'Reward')

    m.optimize()

    if m.status == GRB.Status.OPTIMAL:
        print('The final solution is:')
    for i,j in links:
        if(x[i,j].x > 0):
            print(i, j, x[i,j].x, reward.get((i,j)))

    # end of optimization

    # The following draws the graph
    # Create Graph
    G=nx.DiGraph()
    # G=nx.MultiGraph()
    list_nodes = list(range(1, num_nodes+1))
    G.add_nodes_from(list_nodes)
    for i,j in links:
        G.add_edge(i,j)

    # Adding the position attribute to each node
    node_pos = node_pos

    # Create a list of edges in shortest path
    red_edges = [(i,j) for i,j in links if x[i,j].x > 0]

    #Create a list of nodes in shortest path
    sp = [ i for i,j in links if x[i,j].x > 0 ]
    sp.append(destination)

    # If the node is in the shortest path, set it to red, else set it to white color
    node_col = ['white' if not node in sp else 'red' for node in G.nodes()]
    # If the edge is in the shortest path set it to red, else set it to white color
    edge_col = ['black' if not edge in red_edges else 'red' for edge in G.edges()]
    # Draw the nodes
    nx.draw_networkx(G,node_pos, node_color= node_col, node_size=450)
    # Draw the node labels
    # nx.draw_networkx_labels(G1, node_pos,node_color= node_col)
    # Draw the edges
    nx.draw_networkx_edges(G, node_pos,edge_color= edge_col)
    #     # Draw the edge labels
    #     nx.draw_networkx_edge_labels(G, node_pos,edge_color= edge_col, edge_labels=cost)
    # Remove the axis
    plt.axis('off')

    # Show the plot
    plt.show()

######################################################################################################
#Testing code
######################################################################################################
# num_links, links, cij, rij = networkProcess(networkName)
# origin =1
# destination =20
#
# # # Calculating SHP based on reward constraint
# # for rt in range(0, 48, 6):
# #     SHPwithConstr(cij, links, num_nodes, origin, destination, rij, rt, node_pos)
#
# # Calculating SHP based on weighted reward
# for i in range(0,2,2):
#     cost_coeff = 10/10
#     reward_coeff = 1 - i/10
#     weightedSHP(cij, num_nodes, origin, destination, rij, node_pos, cost_coeff, reward_coeff)
#

# Load network data
road_network=readNetwork()

# Create dictionry of link costs
# Link_tt = {(1,3):[5,[1, 2, 3]]}
# Link_tt = {(O,D):[Total time, [Path]]}

