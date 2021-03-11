from node import *
from packet import *

from scipy.spatial import distance
import math
import pandas as pd
from itertools import combinations
import networkx as nx
import uuid

class Simulator():
    def __init__(self,density, classes = {'fast':100}, arrival_rate = 1/5, energy_per_packet = 5, deltaP = 0.1, deltaW = 0.1, alpha = 0.1, radius = 50, max_bundle_size = 5, debug = False) :
        self.n_nodes = number_of_nodes(density)
        self.nodes = self.create_nodes(classes, energy_per_packet, deltaP , deltaW, alpha, debug)
        self.nodes_ids = [node.id for node in self.nodes]

        self.nodes_positions = self.get_nodes_position()
        self.radius = radius
        
        #packets
        self.max_bundle_size = max_bundle_size
        self.arrival_rate = arrival_rate
        
        #debug 
        self.debug = debug
        
        #network analysis
        self.graph = self.create_graph()

        self.copy_counter = {}
        self.received_packets = []
        
        
    def create_nodes(self, classes, energy_per_packet = 5, deltaP = 0.1, deltaW = 0.1, alpha = 0.1, debug = False):
        #create nodes according to the percentages for the classes (they should sum up to 100!)
        
        #counter to assing ids
        counter = 0
        
        #node list of the simulation
        node_list = []
        
        #create static nodes
        if 'static' in classes:
            n_static = math.floor(classes['static']*self.n_nodes/100)
            for node in range(n_static):
                node_list.append(Node(id=str(counter), dev_class='static', energy_per_packet = energy_per_packet, deltaP = deltaP, deltaW = deltaW, alpha = alpha, debug = debug))
                counter+=1
        
        #create slow nodes
        if 'slow' in classes:
            n_slow = math.floor(classes['slow']*self.n_nodes/100)
            for node in range(n_slow):
                node_list.append(Node(id=str(counter), dev_class='slow', energy_per_packet = energy_per_packet, deltaP = deltaP, deltaW = deltaW, alpha = alpha, debug = debug))
                counter+=1
                
        #create fast nodes
        if 'fast' in classes:
            n_fast = math.floor(classes['fast']*self.n_nodes/100)
        
            for node in range(n_fast):
                node_list.append(Node(id=str(counter), dev_class='fast', energy_per_packet = energy_per_packet, deltaP = deltaP, deltaW = deltaW, alpha = alpha, debug = debug))
                counter+=1
            
        return node_list
    
    def create_graph(self):
        #create the simulation graph
        
        graph = nx.Graph()
        
        for node in self.nodes:
            graph.add_node(node)
            
        return graph
        
        
    def get_nodes_position(self): 
        # get position of every node
        
        nodes_positions = [node.position for node in self.nodes]
        nodes_positions = pd.DataFrame.from_records(np.array(nodes_positions), index = self.nodes, columns = ['x', 'y'])
        return nodes_positions
    
    def move_nodes(self):
        #move every node
        
        for node in self.nodes:
            node.move()
        self.nodes_positions = self.get_nodes_position()
        
    def update_nodes_info(self):
        #update the nework: update ego graphs and the distance
        
        #combinations of all nodes
        comb = combinations(self.nodes,2) 
  
        #distance between every node: THIS IS THE MOST COMPUTING DEMANDING LINE
        distances = distance.cdist(self.nodes_positions, self.nodes_positions, 'euclidean')
        
        # spread info among nodes aboun ego graphs
        for node_pair in list(comb): 
            node1 = node_pair[0]
            node2 = node_pair[1]
            
            
            #compute distance
            #-dist = np.sqrt(np.sum(np.power(self.nodes_positions[[node1]] - self.nodes_positions[[node2]].values,2) )).values
            
            dist = distances[int(node1.id), int(node2.id)]
            
            #update distances
            if self.graph.has_edge(node1, node2):
                self.graph[node1][node2]['distance'] = float(dist)
            else:
                self.graph.add_edge(node1, node2, distance = float(dist), weight = 0.5)
                
            # if the two nodes are near and they have energy left spread node infos
            if dist < self.radius and node2.energy>0 and node1.energy>0:
                node1.get_node_connection(node2)
                node2.get_node_connection(node1)
            
            else:
                node1.node_not_near(node2)
                node2.node_not_near(node1)
                
        
        #### COMPUTE NEW Bs and crate ego graphs
        for node in self.nodes:
            old_nodes = set(node.ego_graph.nodes)
            
            #update egograph
            node.ego_graph = nx.generators.ego.ego_graph(self.graph,node, radius=self.radius, center=True, undirected=True, distance='distance')
            node.B = nx.betweenness_centrality(node.ego_graph, normalized=True, endpoints = True)[node]
        
            new_nodes = set(node.ego_graph.nodes)-old_nodes
            node.new_neighbours = new_nodes
            
        # OLD LINES
        # spread info about B
        #for node_pair in list(comb): 
        #    node1 = node_pair[0]
        #    node2 = node_pair[1]
        #    
        #    dist = np.sum(np.power(self.nodes_positions[[node1.id]] - self.nodes_positions[[node2.id]].values,2) ).values
        
        #for node in self.nodes:
        #    for neighbour in list(node.ego_graph.nodes):
        #        if neighbour!=node:
        #        
        #            node.get_node_B(neighbour)
        #            neighbour.get_node_B(node)
                
    def generate_packets(self):
        #generate packets according to a poisson distribution 
        
        count = 0
        for node in self.nodes:
            
            num_pck = np.random.poisson(self.arrival_rate) #how many pcks to generate
            for i in range(num_pck):
                
                ####generate a packet
                # get list on possible nodes
                node_ids = self.nodes_ids.copy()
                node_ids.remove(node.id) #avoid destination==source
                
                #generate a pakcet
                pck = Packet(str(uuid.uuid4().hex), source = node.id, destination = random.choice(node_ids))
                node.get_packet(pck)
                
                self.copy_counter[pck.id] = 1
                count += 1
        return count
        
    def charge_nodes(self):
        # charge node with probability 30% at each time step
        energy = 0
        for node in self.nodes:
            if node.energy<20:
                
                num = np.random.poisson(1/500)#self.arrival_rate/35)
                if num>0:
                    #print(str(node.id)+ 'charged')
                    energy += 100 - node.energy
                    node.charge_dev()
                #else:
                    #print(str(node.id)+ ' not charged,' +str(node.energy))
        return energy
    
        #for node in self.nodes:
        #    if node.energy < 10:
        #    
        #        charge_device = np.random.rand() < 0.3
        #    
        #        if charge_device:
        #            node.energy = 100
    
    def communicate(self, mode = 'MD'):
        #start a communication from a device
        #retun arrived (received) packets, dropped packets, energy spent
        
        
        
        if mode=='MD':
                
            #return values
            rec_sum = 0
            drop_sum = 0
            energy_sum = 0
        
            #if there are new packets try a new communcation with the neighbourhood
            for node in self.nodes:
                #print(str(node.id) + ' has new pck?: ' + str(node.has_new_packets) + ' has new n? ' + str(len(node.new_neighbours)>0))
                if node.has_new_packets:
                    
                    #get a list of the best receives
                    best_receivers = node.best_receivers(list(node.ego_graph.nodes))
                    # start to communicate from the best one
                    for neighbour in best_receivers:
                        if neighbour!=node: #avoid to send pcks to himself
                            
                            #start communication, get a bundle to send
                            bundle = node.start_communication(neighbour, mode = 'MD', max_bundle_size = self.max_bundle_size)
                            
                            #if the bundle has some packets inside ask to the receiver to accept
                            if(len(bundle)>0):
                                
                                if self.debug:
                                    print('Bundle size: ' + str(len(bundle)))
                                    
                                # ask to the receiver to accept or not
                                energy, deltaW, received_pcks_hops, dropped_pcks_hops, bundle = neighbour.receive(node,bundle, mode = 'MD')
                                
                                # if the receiver accepted i remove the packet from my list
                                # NOTE: commnet these 3 lines to allow copies of packets
                                if energy > 0:
                                    
                                    self.collect_packet_copies(bundle)
                                    
                                    for pck in bundle:
                                        id = pck.id
                                        if not node.packet_list[id].is_original():
                                            
                                            node.packet_list.pop(pck.id, None)
                                
                                #update weight in the simulation network
                                self.graph[node][neighbour]['weight'] += deltaW

                                #update return values
                                rec_sum += len(received_pcks_hops)
                                energy_sum += energy
                                #drop_sum += len(dropped_pcks_hops)
                                
                                # reward hops if a packet arrived
                                for received_pck in received_pcks_hops:
                                    self.received_packets.append(received_pck)
                            
                                    if self.debug:
                                        print('**ARRIVED: ' + str(received_pck) )
                                        print('Hops to reward: ' + str([x for x in received_pcks_hops[received_pck]]))
                                        print('Hops to punish' + str([x.id for x in self.nodes if x.id not in received_pcks_hops[received_pck] and received_pck in x.packet_list]))
                                        
                                    for n in self.nodes:
                                        if n.id in received_pcks_hops[received_pck]:
                                            n.P_succ = n.increaseP()
                                            n.packet_list.pop(received_pck, None)
                                
                                        elif received_pck in n.packet_list:
                                            if not n.packet_list[received_pck].is_original():
                                                delta =  n.P_succ- n.decreaseP()
                                                n.P_succ = n.decreaseP()
                                                #print('S for node ' + str(n.id) + ' decreased of ' + str(delta))
                                            n.packet_list.pop(received_pck, None)
                                
                                # punish hops if the packet was dropped
                                # NOTE: ONLY IF ALL THE PACKETS ARE SINGLE COPIES
                                #for dropped_pck in dropped_pcks_hops:

                                #    for n in self.nodes:
                                #        if n.id in dropped_pcks_hops[dropped_pck]:
                                #            n.P_succ = n.decreaseP()

                                #        elif dropped_pck in n.packet_list:
                                #            n.P_succ = n.decreaseP()
                                #            n.packet_list.pop(dropped_pck, None)
                    
                                
                                for packet in dropped_pcks_hops:
                                    #completely_dropped = True
                                    #for n in self.nodes:
                                    #    if packet in n.packet_list:
                                    #        completely_dropped = False
                                    
                                    #if completely_dropped:
                                    #    if self.debug:
                                    #        print('* DROPPED' + str(packet))
                                    #    drop_sum += 1
                                    drop_sum += 1
                        
                    #close the connection up to the next packet
                    node.has_new_packets = False
                
                elif len(node.new_neighbours)>0:
                    #print(node.new_neighbours)
                    #print(node.ego_graph.nodes)
                            
                    #get a list of the best receives
                    best_receivers = node.best_receivers(list(node.new_neighbours))
                    # start to communicate from the best one
                    for neighbour in best_receivers:
                        if neighbour!=node: #avoid to send pcks to himself
                            
                            
                            #start communication, get a bundle to send
                            bundle = node.start_communication(neighbour, mode = 'MD', max_bundle_size = self.max_bundle_size)
                            
                            #if the bundle has some packets inside ask to the receiver to accept
                            if(len(bundle)>0):
                                
                                if self.debug:
                                    print('Bundle size: ' + str(len(bundle)))
                                    
                                # ask to the receiver to accept or not
                                energy, deltaW, received_pcks_hops, dropped_pcks_hops, bundle = neighbour.receive(node,bundle, mode = 'MD')
                                
                                
                                # if the receiver accepted i remove the packet from my list
                                # NOTE: commnet these 3 lines to allow copies of packets
                                if energy > 0:
                                    self.collect_packet_copies(bundle)
                                
                                    for pck in bundle:
                                        id = pck.id
                                        if not node.packet_list[id].is_original():
                                            
                                            node.packet_list.pop(pck.id, None)
                                
                                #update weight in the simulation network
                                self.graph[node][neighbour]['weight'] += deltaW

                                #update return values
                                rec_sum += len(received_pcks_hops)
                                energy_sum += energy
                                #drop_sum += len(dropped_pcks_hops)
                                
                                # reward hops if a packet arrived
                                for received_pck in received_pcks_hops:
                                    self.received_packets.append(received_pck)
                            
                                    if self.debug:
                                        print('**ARRIVED: ' + str(received_pck) )
                                        print('Hops to reward: ' + str([x for x in received_pcks_hops[received_pck]]))
                                        print('Hops to punish' + str([x.id for x in self.nodes if x.id not in received_pcks_hops[received_pck] and received_pck in x.packet_list]))
                                        
                                    for n in self.nodes:
                                        if n.id in received_pcks_hops[received_pck]:
                                            n.P_succ = n.increaseP()
                                            n.packet_list.pop(received_pck, None)
                                
                                        elif received_pck in n.packet_list:
                                            if not n.packet_list[received_pck].is_original():
                                                #delta =  n.P_succ- n.decreaseP()
                                                n.P_succ = n.decreaseP()
                                                #print('S for node ' + str(n.id) + ' decreased of ' + str(delta))
                                            n.packet_list.pop(received_pck, None)
                                
                                # punish hops if the packet was dropped
                                # NOTE: ONLY IF ALL THE PACKETS ARE SINGLE COPIES
                                #for dropped_pck in dropped_pcks_hops:

                                #    for n in self.nodes:
                                #        if n.id in dropped_pcks_hops[dropped_pck]:
                                #            n.P_succ = n.decreaseP()

                                #        elif dropped_pck in n.packet_list:
                                #            n.P_succ = n.decreaseP()
                                #            n.packet_list.pop(dropped_pck, None)
                    
                                
                                for packet in dropped_pcks_hops:
                                    #completely_dropped = True
                                    #for n in self.nodes:
                                    #    if packet in n.packet_list:
                                    #        completely_dropped = False
                                    
                                    #if completely_dropped:
                                    #    if self.debug:
                                    #        print('* DROPPED' + str(packet))
                                    #    drop_sum += 1
                                    drop_sum += 1
                        
                    #close the connection up to the next packet
                    node.has_new_packets = False
                
                    
                    
        
            return rec_sum, drop_sum, energy_sum
            
        elif mode=='epidemic':
                
            #return values
            rec_sum = 0
            drop_sum = 0
            energy_sum = 0
        
            for node in self.nodes:
                
                # start to communicate from the best one
                for neighbour in list(node.ego_graph.nodes):
                    
                    if neighbour!=node: #avoid to send pcks to himself
                        #start communication, get a bundle to send
                        bundle = node.start_communication(neighbour, mode = 'epidemic', max_bundle_size = self.max_bundle_size)
                        
                        energy, _ , received_pcks_hops, _, bundle = neighbour.receive(node,bundle, mode = 'epidemic')
                        energy_sum += energy
                        rec_sum += len(received_pcks_hops)
                        self.collect_packet_copies(bundle)
                                
                        # remove arrived pckts
                        for received_pck in received_pcks_hops:
                            self.received_packets.append(received_pck)
                            
                            if self.debug:
                                print('**ARRIVED: ' + str(received_pck) )
                                      
                            for n in self.nodes:
                                if received_pck in n.packet_list:
                                    n.packet_list.pop(received_pck, None)
                                
            return rec_sum, 0, energy_sum
        
        
        
    def collect_packet_copies(self, bundle):
        for pck in bundle:
            self.copy_counter[pck.id] += 1
        
#@staticmethod
def start_simulation(radius = 50, arrival_rate = 1/10, energy_per_packet = 5, deltaP = 0.1, deltaW = 0.1, alpha = 0.01, simulation_len = 100, last_generation = 1, max_bundle_size = 5, debug = False, num_dev = 30):
    
    
    #importlib.reload(node)
    #importlib.reload(simulator)
    #importlib.reload(packet)

    #from simulator import *
    #from packet import *
    #from node import *

    random.seed(9)


    ##############################
    # PARAMETERS
    ##############################
    #simulation setup
    #radius = 50
    #arrival_rate = 1/10
    #energy_per_packet = 5
    #deltaP = 0.1 #sigma
    #deltaW = 0.1 #beta
    #alpha = 0.01 #alpha
    #simulation_len = 1000
    last_generated_packet = simulation_len*last_generation
    #max_bundle_size = 5

    #debug = False
    #num_dev = 30
    ###############################



    s= Simulator(num_dev/(300*150), 
                 classes = {'static':30, 'slow':50, 'fast':20} ,
                 arrival_rate = arrival_rate,
                 energy_per_packet = energy_per_packet,
                 deltaP = deltaP,
                 deltaW = deltaW, 
                 alpha = alpha,
                 max_bundle_size = max_bundle_size,
                 debug = debug)

    generated_pcks = []
    received_pcks = []
    dropped_pcks = []
    energy_consumption = []
    remaining_energy = []
    P_succ = []
    W_sum = []
    generated_counter = 0

    for i in range(simulation_len):

        #update distances, B and P_succ of near nodes
        s.update_nodes_info()

        #print(s.nodes_positions)

        #generate new pkts
        if generated_counter < last_generated_packet:
            generated_counter += 1
            generated_pcks.append(s.generate_packets())

        #for every node with at least a packet start the diffusion
        # a node decide to who he wants to send the packet
        # the reveiver decide if he wants to accept it
        # -> link weights and P_succ update 

        rec, drop, energy =  s.communicate(mode = "MD")
        received_pcks.append(rec)
        energy_consumption.append(energy)
        dropped_pcks.append(drop)

        s.charge_nodes()
        remaining_energy.append(sum([node.energy for node in s.nodes]))
        P_succ.append(sum([node.P_succ for node in s.nodes]))
        W_sum.append(sum([i[2] for i in s.graph.edges(data =  'weight')]))



        # move nodes
        s.move_nodes()


        #print( '(' + str(i) +')', end = ' ')

    return received_pcks,generated_pcks, dropped_pcks, energy_consumption, remaining_energy, P_succ, W_sum
