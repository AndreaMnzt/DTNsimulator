from node import *
import math
import pandas as pd
from itertools import combinations
import networkx as nx

class Simulator():
    def __init__(self,density, classes = {'fast':100}) :
        self.n_nodes = number_of_nodes(density)
        self.nodes = self.create_nodes(classes)
        self.nodes_ids = [node.id for node in self.nodes]
        self.nodes_positions = self.get_nodes_position()
        self.radius = 50
        
        #network analysis
        self.graph = self.create_graph()
        
    def create_nodes(self, classes):
        counter = 0
        node_list = []
        
        
        if 'static' in classes:
            n_static = math.floor(classes['static']*self.n_nodes/100)
            for node in range(n_static):
                node_list.append(Node(id=str(counter), dev_class='static'))
                counter+=1
        
        
        if 'slow' in classes:
            n_slow = math.floor(classes['slow']*self.n_nodes/100)
            for node in range(n_slow):
                node_list.append(Node(id=str(counter), dev_class='slow'))
                counter+=1
        
        if 'fast' in classes:
            n_fast = math.floor(classes['fast']*self.n_nodes/100)
        
            for node in range(n_fast):
                node_list.append(Node(id=str(counter), dev_class='fast'))
                counter+=1
            
        return node_list
    
    def create_graph(self):
        graph = nx.Graph()
        
        for node in self.nodes_ids:
            graph.add_node(node)
            
        return graph
        
        
    def get_nodes_position(self): 
        nodes_positions = [node.position for node in self.nodes]
        nodes_positions = pd.DataFrame.from_records(np.array(nodes_positions).T, columns = self.nodes_ids, index = ['x', 'y'])
        return nodes_positions
    
    def move_nodes(self):
        for node in self.nodes:
            node.move()
        self.nodes_positions = self.get_nodes_position()
        
    def update_nodes_info(self):
        comb = combinations(self.nodes,2) 
  
        # Print the obtained combinations 
        for node_pair in list(comb): 
            node1 = node_pair[0]
            node2 = node_pair[1]
            
            
            
            #compute distance
            dist = np.sqrt(np.sum(np.power(self.nodes_positions[[node1.id]] - self.nodes_positions[[node2.id]].values,2) )).values
            
            if self.graph.has_edge(node1.id, node2.id):
                self.graph[node1.id][node2.id]['distance'] = float(dist)
            else:
                self.graph.add_edge(node1.id, node2.id, distance = float(dist), weight = 1)
                
            if dist < self.radius:
                node1.get_node_connection(node2)
                node2.get_node_connection(node1)
            
            else:
                node1.node_not_near(node2)
                node2.node_not_near(node1)
                
        #### COMPUTE NEW Bs
        for node in self.nodes:
            egograph = nx.generators.ego.ego_graph(self.graph,node.id, radius=self.radius, center=True, undirected=True, distance='distance')
            node.B = nx.betweenness_centrality(egograph, normalized=True, endpoints = True)[node.id]
        
        for node_pair in list(comb): 
            node1 = node_pair[0]
            node2 = node_pair[1]
            
            dist = np.sum(np.power(self.nodes_positions[[node1.id]] - self.nodes_positions[[node2.id]].values,2) ).values
            if dist < self.radius:
                node1.get_node_B(node2)
                node2.get_node_B(node1)