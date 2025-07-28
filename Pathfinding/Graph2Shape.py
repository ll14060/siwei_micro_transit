import networkx as nx
import sqlite3
from shapely.geometry import mapping, Polygon, Point, LineString, shape
import fiona
import numpy as np
import random
import os



def reLocateLinks(graph, offset=5000):
    """
    Method for modifying links in graph

    Parameter
    ---------
    graph:  networkx DiGraph
            graph to present
    """
    nodeposition = nx.get_node_attributes(graph, "pos")
    #print (graph.edges)

    for edge in graph.edges():
        snode, enode = edge[0], edge[1]
        px1, py1 = nodeposition[snode][0], nodeposition[snode][1]
        px2, py2 = nodeposition[enode][0], nodeposition[enode][1]
        fx, fy, tx, ty = reLocateAlink(px1, py1, px2, py2, offset=offset)
        graph[snode][enode]["pos_fnode"] = (fx, fy)
        graph[snode][enode]["pos_tnode"] = (tx, ty)
    return graph
def reLocateAlink(px1, py1, px2, py2, offset=0.5):
    """
    Method for adjusting location of a link

    Parameters
    ----------
    px1:    float
            x coordinate of a node

    py1:    float
            y coordinate of a node

    px2:    float
            x coordinate of another node

    py2:    float
            y coordinate of another node
    Returns
    -------
    fx:     float
            new coordinate of px1

    fy:     float
            new coordinate of py1

    tx:     float
            new coordinate of px2

    ty:     float
            new coordinate of py2
    """
    x1, y1 = float(px1), float(py1)
    x2, y2 = float(px2), float(py2)
    dist = (x1 - x2) ** 2 + (y1 - y2) ** 2
    dist = abs(dist ** 0.5)
    sin = (y2 - y1) / dist
    cos = (x2 - x1) / dist
    if x2 - x1 != 0:
        tan = (y2 - y1) / (x2 - x1)
    else:
        tan = 1
    if abs(tan) >= 1:
        fx, fy = x1 + offset * sin, y1 - offset * cos
        tx, ty = x2 + offset * sin, y2 - offset * cos
    else:
        fx, fy = x1 + offset * sin, y1 - offset * cos
        tx, ty = x2 + offset * sin, y2 - offset * cos
    return fx, fy, tx, ty


def NeworkX2Pyplot(graph, savefilename=None):
    import matplotlib.pyplot as plt
    plt.figure(1)
    # plt.subplot(211);
    # plt.axis('off')

    for fnode in graph:
        for enode in graph[fnode]:
            graph[fnode][enode]["volume"] = graph[fnode][enode]["object"].flow
    volumes = nx.get_edge_attributes(graph, "volume")
    volumes = list(volumes.values())
    max_volume = max(volumes)
    pos = nx.get_node_attributes(graph, "pos")
    edgewidth = 0.5
    nx.draw_networkx_edges(graph, pos, width=edgewidth, label=volumes)
    nx.draw_networkx_nodes(graph, pos, with_labels=True)
    # labels = bch.G.node.keys()
    nx.draw_networkx_labels(graph, pos, font_size=5)
    nx.draw_networkx_edge_labels(graph, pos=nx.spring_layout(graph))
    plt.show()
    if savefilename!=None:
        plt.savefig(savefilename)



def NetworkX2_Nodes_Shapefile(graph,foldername, filename=None, schema=None):

    nodeset = graph.nodes()
    source = os.getcwd()
    target = source + "\\Output\\" + foldername
    try:
        if not os.path.exists(target):
            os.makedirs(source + "\\Output\\" + foldername)
        os.chdir(source + "\\Output\\" + foldername)
        print("Success")
    except:
        print("Exception creating subfolde")
    if schema==None:
        properties={"id":"str"}
        for r in range(10):
            index = random.randint(0,len(nodeset)-1)
            for p in graph.nodes[list(nodeset)[index]]:
                if p not in properties:
                    dtype= p
                    if isinstance(dtype,int):
                        properties[p]="int"
                    elif isinstance(dtype,float):
                        properties[p] = "float"
                    elif isinstance(dtype,str):
                        properties[p] = "str"
        schema = {
            'geometry': 'Point',
            'properties': properties,
        }

    # Write a new Shapefile
    if filename==None:
        nodefilename= "nodes.shp"
    else:
        nodefilename = filename+"_nodes.shp"
    with fiona.open(nodefilename, 'w', 'ESRI Shapefile', schema) as c:
        ## If there are multiple geometries, put the "for" loop here
        for n in nodeset:
            pos = graph.nodes[n]["pos"]
            eproperty={}
            for p in properties:
                eproperty[p]=None
            for p in graph.nodes[n]:
                dtype= graph.nodes[n][p]
                if isinstance(dtype,int):
                    eproperty[p]= graph.nodes[n][p]
                elif isinstance(dtype,float):
                    eproperty[p] = graph.nodes[n][p]
                elif isinstance(dtype, str):
                    eproperty[p] = str(graph.nodes[n][p])
            eproperty["id"] = n
            c.write({
                'geometry': mapping(Point(pos)),
                'properties': eproperty,
            })
            #print(n, pos)
    # Move back to source directory
    os.chdir(source)
def NetworkX2_Links_Shapefile(graph, foldername,filename=None, schema=None):
    linkset = graph.edges()
    source = os.getcwd()
    target = source+"\\Output\\"+foldername
    try:
        if not os.path.exists(target):
            os.makedirs(source+"\\Output\\"+foldername)
        os.chdir(source+"\\Output\\"+foldername)
        print ("Success")
    except:
        print ("Exception creating subfolde")
    if schema==None:
        properties={"id":"str"}
        for r in range(10):
            index = random.randint(0,len(linkset)-1)
            for p in graph.edges[list(linkset)[index]]:
                if p not in properties:
                    dtype = graph.edges[list(linkset)[index]][p]
                    try:
                        dtype = float(dtype)
                    except:
                        pass
                    if isinstance(dtype,int):
                        properties[p]="int"
                    elif isinstance(dtype,float):
                        properties[p] = "float"
                    elif isinstance(dtype,str):
                        properties[p] = "str"


        schema = {
            'geometry': "LineString",
            'properties': properties,
            #'properties': {"id":"int"},
        }

    # Write a new Shapefile
    if filename==None:
        linkfilename= "links.shp"
    else:
        linkfilename = filename+"_links.shp"
    with fiona.open(linkfilename, 'w', 'ESRI Shapefile', schema) as c:
        ## If there are multiple geometries, put the "for" loop here
        for (fnode, enode) in linkset:
            f_pos = graph.nodes[fnode]["pos"]
            e_pos = graph.nodes[enode]["pos"]
            x0, y0 = graph[fnode][enode]["pos_fnode"][0], graph[fnode][enode]["pos_fnode"][1]
            x1, y1 = graph[fnode][enode]["pos_tnode"][0], graph[fnode][enode]["pos_tnode"][1]
            eproperty={}
            poly1 = LineString([(0, 0), (0, 1), (1, 1)])
            poly1 = LineString([(x0, y0), (x1,y1)])
            for p in properties:
                eproperty[p]=None
            for p in graph[fnode][enode]:
                dtype= graph[fnode][enode][p]
                try:
                    dtype = float(dtype)
                except:
                    pass
                if isinstance(dtype,int):
                    eproperty[p]= dtype
                elif isinstance(dtype,float):
                    eproperty[p] = dtype
                elif isinstance(dtype, str):
                    eproperty[p] = dtype
                else:
                    pass


            eproperty["id"]=str(fnode)+"_"+str(enode)
            c.write({
                'geometry': mapping(poly1),
                'properties': eproperty,
            })
    # Move back to source directory
    os.chdir(source)
def open_link_file(link_file):
    f = open(link_file)
    lines = f.readlines()
    f.close()
    link_fields = {"from": 1, "to": 2, "capacity": 3, "length": 4, "t0": 5, \
                   "B": 6, "beta": 7, "V": 8}
    links_info = []
    header_found = False
    graph = nx.DiGraph()
    for line in lines:
        if not header_found and line.startswith("~"):
            header_found = True
        elif header_found:
            links_info.append(line)
    link_id = 0
    for line in links_info:
        link_id=link_id+1
        data = line.split("\t")
        try:
            origin_node = str(int(data[link_fields["from"]]))
        except IndexError:
            continue
        to_node = str(int(data[link_fields["to"]]))
        capacity = float(data[link_fields["capacity"]])
        length = float(data[link_fields["length"]])
        alpha = float(data[link_fields["B"]])
        beta = float(data[link_fields["beta"]])
        ff_time=float(data[link_fields["t0"]])
        graph.add_edge(origin_node, to_node, cost_ij=ff_time,reward_ij=0, length=length, capacity=capacity, traveltime=ff_time,
                         demand_flow=0, link_id=link_id, alpha=alpha, beta=beta)

    return graph

def open_node_file(node_file, graph):
    """
    Method for opening node file, containing position information of nodes \n
    This method adds 'pos' key-value pair in graph variable
    """
    f = open(node_file)
    print (graph.nodes)
    n = 0
    for i in f:
        row = i.split("	")
        if n == 0:
            n += 1

        else:

                if node_file == "berlin-center_node.tntp":
                    ind, x, y = str(int(row[0])), float(row[1]), float(row[3])
                else:
                    ind, x, y = str((row[0])), float(row[1]), float(row[2])

                graph.nodes[ind]["pos"] = (x,y)
                #graph.add_node(ind,pos=(x,y))
            # except:
            #     print ("prashnam")
            #     print(row)
    f.close()

if __name__ =="__main__":
    datafolder = "./SiouxFalls/"
    link_file = datafolder + "SiouxFalls_net.tntp"
    node_file = datafolder + "SiouxFalls_node.tntp"
    graph = open_link_file(link_file)
    open_node_file(node_file, graph)
    graph=reLocateLinks(graph, offset=5000)
    NetworkX2_Links_Shapefile(graph)
    NetworkX2_Nodes_Shapefile(graph)
    print("completed")

