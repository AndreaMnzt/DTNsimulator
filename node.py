import random
import math
import numpy as np
import networkx as nx
from packet import *

class Node:
    
    def __init__(self, id, dev_class, energy_per_packet = 5, deltaP = 0.1, deltaW = 0.1, alpha = 0.1):
        
        self.space = [300, 150]
        
        #spacial variables
        self.id = id
        self.past_positions = np.zeros((0,2))
        self.angle = None
        self.position = Node.random_position()
        self.dev_class = dev_class
        self.speed = Node.get_speed(self.dev_class)
        self.energy = np.random.randint(0,100+1)
        self.known_nodes_info = {}
        #telecomunication values
        self.radius = 50
        self.B = 0
        self.P_succ = 0.5
        self.ego_graph = None
        
        self.deltaP = deltaP
        self.deltaW = deltaW
        self.alpha = alpha
        
        # packets
        #self.packet_list = {}
        self.packet_list = {}
        
        #communication values
        self.energy_per_packet = energy_per_packet
        
    def get_bundle(self, bundle):
        
        received_pcks_hops = {}
        for packet in bundle:
            self.packet_list[packet.id] = packet
            if packet.destination == self.id:
                received_pcks_hops[packet.id] = packet.hops

            else:
                packet.add_hop(self.id)
                
        return received_pcks_hops 
    
    def get_packet(self,packet):
        self.packet_list[packet.id] = packet
    
    def start_communication(self, node, mode = 'MD'):
        #return spent energy. If > 0 then the communication can start
        
        if mode == 'MD':   
                    
            if node!=self.id:
                bundle = self.create_bundle(node)

                #if there are pcks to send
                bundle_size = len(bundle)
                if bundle_size > 0:

                    #start the MD protocol
                    cost_per_pck = self.energy_per_packet
                    p = (100-cost_per_pck)/cost_per_pck
                    energy_cost = cost_per_pck*bundle_size
                    
                    ## A CHARGED
                    W_sum_rec = sum([i[2] for i in node.ego_graph.edges(node, 'weight')])
                    W_link_rec = self.ego_graph[node][self]['weight']
                    
                    W_sum = sum([i[2] for i in self.ego_graph.edges(self, 'weight')])
                    W_link = self.ego_graph[self][node]['weight']
                
                    node_delta_P = (node.increaseP() - node.P_succ)
                    node_delta_W = (node.increaseW(W_link) - W_link)
                    rec_utility_accept = node.B*node_delta_P*W_sum_rec + node.B*(node.increaseP())*(node.increaseW(W_link))-node.alpha*energy_cost
                    rec_utility_decline = node.P_succ*node.B*(node.deltaW)
                    
                    
                    self_delta_P = (self.increaseP() - self.P_succ)
                    self_delta_W = (self.increaseW(W_link) - W_link)
                    if rec_utility_accept > rec_utility_decline:
                        receiver_charged_utiliy = self.B*self_delta_P*W_sum + self.B*self.increaseP()*(self.increaseW(W_link))-self.alpha*energy_cost
                    else:
                        receiver_charged_utiliy = self.P_succ*self.B*(self_delta_W)
                
                    
                    if self.B < node.B:
                        receiver_not_charged_utiliy = self.B*self_delta_P*W_sum + self.B*(self.decreaseP())*(self.increaseW(W_link))-self.alpha*energy_cost
                    
                    else:
                        receiver_not_charged_utiliy = node.P_succ*node.B*(self_delta_W)
                    
                        

                    communication_payoff = p*(receiver_charged_utiliy) + (1-p)*receiver_not_charged_utiliy
                
                    no_communication_payoff = 0
                            
                            
                    if communication_payoff > no_communication_payoff and energy_cost < self.energy:
                        return bundle
                        
                        
                        
            
            return {}
        elif mode == 'epidemic':
            return 0
        else:
            print('Mode not supported')
            return 0
    
    def send(self,bundle):
        
        # loose energy
        bundle_size = len(bundle)
        energy_cost = bundle_size*self.cost_per_packet
        self.energy = self.energy - energy_cost
        
        # remove packet from list
        for pck in bundle:
            self.packet_list.pop(pck, None)
        
        
        return energy_cost
    
    def accept_communication(self, bundle, mode = 'MD'):
        if mode == 'MD':
            
            
            
            return 0
        elif mode == 'epidemic':
            return 0
        
        else:
            print('Mode not supported')
            return 0
    
    def receive(self, node, bundle, mode = 'MD'):
        if mode == 'MD':
            
            bundle_size = len(bundle)
            energy_cost = bundle_size*self.energy_per_packet
            
            if energy_cost > self.energy:
                W_sum = sum([i[2] for i in self.ego_graph.edges(self, 'weight')])
                W_link = self.ego_graph[self][node]['weight']
                
                #print(W_sum)
                U_accept = self.B*self.deltaP*W_sum + self.B*(self.increaseP())*(self.increaseW(W_link))-self.alpha*energy_cost
                U_decline = self.P_succ*self.B*(self.deltaW)
                
                #print('accept: ' + str(U_accept) + ' decline: ' + str(U_decline))
                if U_accept>U_decline:
                    
                    #print('A')
                    
                    deltaW = self.increaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight'] 
                    
                    self.ego_graph[self][node]['weight'] = self.increaseW(self.ego_graph[self][node]['weight'])
                    node.ego_graph[node][self]['weight'] = self.increaseW(self.ego_graph[node][self]['weight'])
                    
                    node.energy = node.energy - energy_cost
                    
                    received_packets_hops = self.get_bundle(bundle)
                    
                    return energy_cost, deltaW, received_packets_hops
                else:
                    deltaW = self.decreaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight']
                    
                    self.ego_graph[self][node]['weight'] = self.decreaseW(self.ego_graph[self][node]['weight'])
                    node.ego_graph[node][self]['weight'] = self.decreaseW(self.ego_graph[node][self]['weight'])
                    #print('B')
                    
                    return 0, deltaW, {}
            else:
                if self.B < node.B:
                    deltaW = self.increaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight']
                    
                    self.ego_graph[self][node]['weight']  = self.increaseW(self.ego_graph[self][node]['weight'])
                    
                    node.ego_graph[node][self]['weight'] = self.increaseW(self.ego_graph[node][self]['weight'])
                    node.energy = node.energy - energy_cost
                    
                    received_packets_hops = self.get_bundle(bundle)
                    #print('C')
                    
                    return energy_cost, deltaW, received_packets_hops
                else:
                    deltaW = self.decreaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight']
                    self.ego_graph[self][node]['weight'] - self.decreaseW(self.ego_graph[self][node]['weight'])
                    node.ego_graph[node][self]['weight'] = self.decreaseW(self.ego_graph[node][self]['weight'])
                    #print('D')
                    
                    return 0, deltaW, {}
            
        
        
        
        
    
    #method to move a node
    def move(self):
        
        if self.energy > 0:
            new_position = [-1,-1]

            n_try = 0
            while( not self.in_space_bounds(new_position) ):
                if self.angle is not None and n_try > 10: #turn around the device
                    if self.angle > math.pi:
                        self.angle = self.angle - math.pi
                    else:
                        self.angle = self.angle + math.pi
                else:
                    n_try += 1

                if self.angle == None:
                    new_angle = random.random()*2* math.pi
                else:
                    new_angle =  math.pi/2 * random.gauss(0,1/10) + self.angle

                dx = self.speed*math.cos(new_angle)
                dy = self.speed*math.sin(new_angle)
                new_x = self.position[0] + dx
                new_y = self.position[1] + dy
                new_position = np.array([new_x, new_y])

            self.angle = new_angle
            self.past_positions  = np.vstack((self.past_positions, self.position))
            self.position = new_position
        
        else:
            self.past_positions  = np.vstack((self.past_positions, self.position))
            self.position = self.position
        
            
        
    def get_node_connection(self, node):
        #for nodes with distance < radius 
        #get Beetweeness node, success probability
        #for node in all_nodes:
        #    if node_is_near(self, all_nodes[node]):
        self.known_nodes_info[node] = {'near': True} #, 'B': node.B, 'P_succ': node.P_succ}
                                      
    def get_node_B(self, node):
        self.known_nodes_info[node]['B'] = node.B
        
    def create_bundle(self, node):
        
        this_node_pcks = self.packet_list
        
        other_node_pcks = node.packet_list
        
        #new_pcks = this_node_pcks - this_node_pcks
        
        pcks_to_send = this_node_pcks.keys() - other_node_pcks.keys()
        
        debug = False
        if debug:
            print("Node of me (Node " + str(self.id) + ") has pck: " + str(this_node_pcks) )
            print("Node receiving (Node " + str(node.id) + ") has pck: " + str(other_node_pcks) )
            print("Pck to send: " + str(pcks_to_send))
        
        new_pcks_copy = {this_node_pcks[pck].create_copy() for pck in pcks_to_send}
        
        return new_pcks_copy
        
    
    def node_not_near(self, node):
        if node.id in self.known_nodes_info:
            self.known_nodes_info[node]['near'] = False
    
    def charge_dev(self):
        self.energy = 100
        
    
    def in_space_bounds(self, new_position):
        x,y = new_position
        max_x,max_y = self.space
        
        if (x>0 and x<max_x) and (y>0 and y<max_y):
            return True
        
        return False
    
        
    
    @staticmethod
    def random_position():
        return [random.randint(1,299) , random.randint(1,149)]
    
    @staticmethod
    def get_speed(dev_class):
        if dev_class == 'static':
            return 0
        elif dev_class == 'slow':
            return 1
        elif dev_class == 'fast':
            return 2
        else:
            print("Device class not supported")
            return None
        
    def increaseP(self):
        
        if self.P_succ + self.deltaP > 1:
            return 1
        
        return self.P_succ + self.deltaP 
    
    def decreaseP(self):
        
        if self.P_succ - self.deltaP < 0:
            return 0
        
        return self.P_succ - self.deltaP 
    
    
    def increaseW(self,currentW):
        
        if currentW + self.deltaW > 1:
            return 1
        
        return currentW + self.deltaW
    
    def decreaseW(self,currentW):
        
        if currentW - self.deltaW < 0:
            return 0
        
        return currentW - self.deltaW
    
        
def number_of_nodes(density):
    return 300*150*density

