from node import *
from packet import *

from scipy.spatial import distance
import math
import pandas as pd
from itertools import combinations
import networkx as nx
import uuid

class Simulator():
    def __init__(self,density, classes = {'fast':100}, arrival_rate = 1/5) :
        self.n_nodes = number_of_nodes(density)
        self.nodes = self.create_nodes(classes)
        self.nodes_ids = [node.id for node in self.nodes]
        self.nodes_positions = self.get_nodes_position()
        self.radius = 50
        self.arrival_rate = arrival_rate
        
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
        nodes_positions = pd.DataFrame.from_records(np.array(nodes_positions), index = self.nodes, columns = ['x', 'y'])
        return nodes_positions
    
    def move_nodes(self):
        for node in self.nodes:
            node.move()
        self.nodes_positions = self.get_nodes_position()
        
    def update_nodes_info(self):
        comb = combinations(self.nodes,2) 
  
        distances = distance.cdist(self.nodes_positions, self.nodes_positions, 'euclidean')
        #print(distances)
        # Print the obtained combinations 
        for node_pair in list(comb): 
            node1 = node_pair[0]
            node2 = node_pair[1]
            
            
            
            #compute distance
            #-dist = np.sqrt(np.sum(np.power(self.nodes_positions[[node1]] - self.nodes_positions[[node2]].values,2) )).values
            
            dist = distances[int(node1.id), int(node2.id)]
            
            if self.graph.has_edge(node1, node2):
                self.graph[node1][node2]['distance'] = float(dist)
            else:
                self.graph.add_edge(node1, node2, distance = float(dist), weight = 1)
                
            # if the two nodes are near and they have energy left spread node infos
            if dist < self.radius and node2.energy>0 and node1.energy>0:
                node1.get_node_connection(node2)
                node2.get_node_connection(node1)
            
            else:
                node1.node_not_near(node2)
                node2.node_not_near(node1)
                
        #### COMPUTE NEW Bs
        for node in self.nodes:
            node.ego_graph = nx.generators.ego.ego_graph(self.graph,node, radius=self.radius, center=True, undirected=True, distance='distance')
            node.B = nx.betweenness_centrality(node.ego_graph, normalized=True, endpoints = True)[node]
        
        # spread info about B
        #for node_pair in list(comb): 
        #    node1 = node_pair[0]
        #    node2 = node_pair[1]
        #    
        #    dist = np.sum(np.power(self.nodes_positions[[node1.id]] - self.nodes_positions[[node2.id]].values,2) ).values
        
        for node in self.nodes:
            for neighbour in list(node.ego_graph.nodes):
                if neighbour!=node:
                
                    node.get_node_B(neighbour)
                    neighbour.get_node_B(node)
                
    def generate_packets(self):
        count = 0
        for node in self.nodes:
            num_pck = np.random.poisson(self.arrival_rate)
            for i in range(num_pck):
                pck = Packet(str(uuid.uuid4().hex), source = node.id, destination = random.choice(self.nodes_ids))
                node.get_packet(pck)
                count += 1
        return count
        
    def charge_nodes(self):
        for node in self.nodes:
            if node.energy < 10:
            
                charge_device = np.random.rand() < 0.3
            
                if charge_device:
                    node.energy = 100
    
    def communicate(self):
        
        rec_sum = 0
        energy_sum = 0
        
        for node in self.nodes:
            for neighbour in list(node.ego_graph.nodes):
                if neighbour!=node:
                    
                    #start communication
                    if(node.send_packets(neighbour, mode = 'DM')):
                        rec, energy = neighbour.accept_packets(node, mode = 'DM')
                        rec_sum += rec
                        energy_sum += energy
                                
                    
        return rec_sum, energy_sum
            
            
            
        
        
        