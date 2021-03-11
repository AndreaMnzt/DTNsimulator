import random
import math
import numpy as np
import networkx as nx
from packet import *
import itertools

class Node:
    
    def __init__(self, id, dev_class, energy_per_packet = 5, deltaP = 0.1, deltaW = 0.1, alpha = 0.1, debug = False):
        
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
        self.ego_graph = nx.Graph()
        
        self.deltaP = deltaP
        self.deltaW = deltaW
        self.alpha = alpha
        
        # packets
        self.packet_list = {} #list of the current packet to send
        self.has_new_packets = False #used to send the packets
        self.new_neighbours = {}
        
        #communication values
        self.energy_per_packet = energy_per_packet
        
        #debug
        self.debug = debug
        
    def get_bundle(self, bundle):
        #add a bundle to paateket_list
        #return the hops of the packet if this node was the destination
        
        received_pcks_hops = {}
        for packet in bundle:
            if packet.destination == self.id:
                received_pcks_hops[packet.id] = packet.hops

            else:
                packet.add_hop(self.id)
                self.packet_list[packet.id] = packet

                
        return received_pcks_hops
    
    def drop_bundle(self, bundle):
        #drop a bundle when a node lie
        #return hops for the packet arrived and hops for the packet dropped
        
        
        received_pcks_hops = {}
        dropped_pcks_hops = {}
        
        
        for packet in bundle:
            if packet.destination == self.id:
                #packet.add_hop(self.id) #TO REWARD DESTINATION TOO
                received_pcks_hops[packet.id] = packet.hops
            else:
                dropped_pcks_hops[packet.id] = packet.hops

        return received_pcks_hops, dropped_pcks_hops
    
    def get_packet(self,packet):
        #add a packet to the packet list
        
        self.packet_list[packet.id] = packet
        
        self.has_new_packets = True
    
    
    def start_communication(self, node, mode = 'MD', max_bundle_size = 5):
        #start a communication between self and node
        #return the bundle to be sent to node
        
        if mode == 'MD':   
                    
            if node.id != self.id:                 
                
                #craete a bundle for node
                bundle = self.create_bundle(node, max_bundle_size)
                
                
                #if there are pcks to send, compute the payoff and decide to accept the communication
                bundle_size = len(bundle)
                if bundle_size > 0:

                    #compute expected payoff to decide to start the communication
                    result, payoff = self.compute_sender_payoff(node, bundle)
                    
                    
                    if result == 'accept':
                        return bundle
                    
                    return {}
                else:
                    #if self.debug:
                    #    print('No packet to send')
                    return {}
        
        elif mode == 'epidemic':
            if node.id != self.id:                 
                
                #craete a bundle for node
                bundle = self.create_bundle(node, max_bundle_size)
                bundle_size = len(bundle)
                energy_cost = bundle_size*self.energy_per_packet
                
                #if there are pcks to send, compute the payoff and decide to accept the communication
                bundle_size = len(bundle)
                if bundle_size > 0 and self.energy >= energy_cost:
                    return bundle
                
                
                
                return {}
            
            
            
            
            return {}
        
        else:
            print('Mode not supported')
            return 0
    
    #def send(self,bundle):
    #    
    #    # loose energy
    #    bundle_size = len(bundle)
    #    energy_cost = bundle_size*self.cost_per_packet
    #    self.energy = self.energy - energy_cost
    #  
    #   # remove packet from list
    #    for pck in bundle:
    #        self.packet_list.pop(pck, None)  
    #    return energy_cost
        
    def receive(self, node, bundle, mode = 'MD'):
        #decide to accept the communication from a node
        # return energy_cost, deltaW, received_packets_hops, dropped_packets_hops
        
        if mode == 'MD':
            
            bundle_size = len(bundle)
            energy_cost = bundle_size*self.energy_per_packet
            
            #compute sum of all the weights in the ego graph
            W_self_sum = sum([i[2] for i in self.ego_graph.edges(self, 'weight')])
            
            #compute sum of all the weights in the ego graph
            W_node_sum = sum([i[2] for i in node.ego_graph.edges(node, 'weight')])
            
            
            # left brach of the game -> receiver has enough energy
            if energy_cost <= self.energy:
                
                
                #current weight of the edge
                W_link = self.ego_graph[self][node]['weight']
                
                self_delta_W = (self.increaseW(W_link) - W_link)
                self_decrease_W = (self.decreaseW(W_link) - W_link)
                
                self_delta_P = (self.increaseP() - self.P_succ)
        
                
                #compute the payoff
                U_accept = self.B*self_delta_P*W_self_sum + self.B*(self.increaseP())*(self_delta_W)-self.alpha*energy_cost
                U_decline = self.P_succ*self.B*(self_decrease_W)
                
                #if the receiver accepts
                if U_accept>U_decline:
                    if self.debug:
                        print(str(self.id) + ' does accept to communicate with ' + str(node.id) + ': ' + str(U_accept) + '>' + str(U_decline))
                    
                    deltaW = self.increaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight'] 
                    
                    #update weights in the ego graphs
                    self.ego_graph[self][node]['weight'] = self.increaseW(self.ego_graph[self][node]['weight'])
                    node.ego_graph[node][self]['weight'] = node.increaseW(node.ego_graph[node][self]['weight'])
                    
                    # energy cost for the sender
                    node.energy = node.energy - energy_cost
                    
                    #if sone packets arrived at destination return the hops for the packets
                    received_packets_hops = self.get_bundle(bundle)
                    self.has_new_packets = True
                    
                    #no packets can be dropped here
                    dropped_packets_hops = {}
                    
                    return energy_cost, deltaW, received_packets_hops, dropped_packets_hops, bundle
                
                #if receiver declines maybe 
                else:
                    
                    #update weights in the ego graphs
                    deltaW = self.decreaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight']
                    node.ego_graph[node][self]['weight'] = node.decreaseW(node.ego_graph[node][self]['weight'])
                    self.ego_graph[self][node]['weight'] = self.decreaseW(self.ego_graph[self][node]['weight'])
                    
                    
                    if self.debug:
                        print(str(self.id) + ' does not accept to communicate with ' + str(node.id) + ': ' + str(U_accept) + '>' + str(U_decline))
                    
                    # no trasmission, no cost
                    energy_cost = 0
                    
                    #no packet has been sent
                    received_packets_hops = {}
                    
                    #no packet can be dropped here
                    dropped_packets_hops = {}
                    
                    #empty received bundle
                    bundle = {}
                    return energy_cost, deltaW, received_packets_hops, dropped_packets_hops, bundle
                
            else: #no energy! right branch of the game
                if self.debug:
                    print("Not charged: needed " + str(energy_cost) + ', available:' + str(self.energy))
                
                if self.B*self.P_succ*W_self_sum < node.B*node.P_succ*W_node_sum: #i want to keep the contact with a big player: I LIE
                #if self.B < node.B: #i want to keep the contact with a big player: I LIE
                    
                    # update egograph weight
                    deltaW = self.increaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight']
                    self.ego_graph[self][node]['weight']  = self.increaseW(self.ego_graph[self][node]['weight'])
                    node.ego_graph[node][self]['weight'] = node.increaseW(node.ego_graph[node][self]['weight'])
                    
                    #cost for the sender
                    node.energy = node.energy - energy_cost
                    
                    #drop the bundle, I am a liar
                    received_packets_hops, dropped_packets_hops = self.drop_bundle(bundle)
                    
                    if self.debug:
                        print(str(self.id) + ' lie: communicate with ' + str(node.id))
                        print('since ' + str(self.energy) + '<' + str(energy_cost))
                    
                    return energy_cost, deltaW, received_packets_hops, dropped_packets_hops, bundle
                else:
                    
                    # i don't care about this node, let's drop the edge
                    
                    #update egograph weight
                    deltaW = self.decreaseW(self.ego_graph[self][node]['weight']) - self.ego_graph[self][node]['weight']
                    self.ego_graph[self][node]['weight'] = self.decreaseW(self.ego_graph[self][node]['weight'])
                    node.ego_graph[node][self]['weight'] = node.decreaseW(node.ego_graph[node][self]['weight'])
                    
                    if self.debug:
                        print(str(self.id) + " do not lie: don't communicate with " + str(node.id) + ': ' + str(energy_cost) + '>' + str(self.energy))
                    
                    energy_cost = 0 #no trasmission, no cost
                    received_packets_hops = {} #no arrived packets
                    dropped_packets_hops = {} #no arrived packets, no dropped
                    bundle = {} #empty bundle
                    
                    return energy_cost, deltaW, received_packets_hops, dropped_packets_hops, bundle
            
        elif mode == 'epidemic':
            
            bundle_size = len(bundle)
            energy_cost = bundle_size*self.energy_per_packet
            
            received_packets = self.get_bundle(bundle)
            
            node.energy =  node.energy - energy_cost
            
            return energy_cost, 0, received_packets, {}, bundle
            
            #else:
            #    if self.debug:
            #        print('Energy: ' + str(energy_cost) + ' > available:' + str(self.energy))
            
            
            #return 0, 0, {}, {}
        
        
        
    
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
        
                
        
    # not used    
    def get_node_connection(self, node):
        #for nodes with distance < radius 
        #get Beetweeness node, success probability
        #for node in all_nodes:
        #    if node_is_near(self, all_nodes[node]):
        self.known_nodes_info[node] = {'near': True} #, 'B': node.B, 'P_succ': node.P_succ}
              
    # not used
    def get_node_B(self, node):
        self.known_nodes_info[node]['B'] = node.B
        
    
    def create_bundle(self, node, max_bundle_size = 5):
        #create bundle for node
        
        this_node_pcks = self.packet_list
        
        other_node_pcks = node.packet_list
        
        pcks_to_send = this_node_pcks.keys() - other_node_pcks.keys()
        
        # get at most max_bundle_size
        
        pcks_to_send = list(itertools.islice(pcks_to_send, max_bundle_size))
        
        #if self.debug:
        #    print("Node of me (Node " + str(self.id) + ") has pck: " + str(this_node_pcks) )
        #    print("Node receiving (Node " + str(node.id) + ") has pck: " + str(other_node_pcks) )
        #    print("Pck to send: " + str(pcks_to_send))
        
        new_pcks_copy = {this_node_pcks[pck].create_copy() for pck in pcks_to_send}
        
        return new_pcks_copy
        
    
    def node_not_near(self, node):
        if node.id in self.known_nodes_info:
            self.known_nodes_info[node]['near'] = False
    
    #charge a device
    def charge_dev(self):
        self.energy = 100
        #if True:
        #    print('dev ' + str(self.id) + ' charged')
        
    # check if the positin is inside the simulation space
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
    
    def compute_sender_payoff(self, node, bundle):
        #start the MD protocol
        
        ### ENERGY ########################################################################
        bundle_size = len(bundle)
        cost_per_pck = self.energy_per_packet
        energy_cost = cost_per_pck*bundle_size
        p = (100-energy_cost)/100
        ####################################################################################         
            
            
            
        ###### IF R IS CHARGED ################################################################
        
        ### W_tot for both nodes
        W_sum_rec = sum([i[2] for i in node.ego_graph.edges(node, 'weight')])
        W_sum = sum([i[2] for i in self.ego_graph.edges(self, 'weight')])
        
        ### LINK STRENGTH, THEY ARE EQUAL
        W_link_rec = self.ego_graph[node][self]['weight']
        W_link = self.ego_graph[self][node]['weight']
               
        ### POSITIVE AND NEGATIVE VARIATION OF P OF RECEIVER
        node_delta_P = (node.increaseP() - node.P_succ)

        ### POSITIVE AND NEGATIVE VARIATION OF P OF SENDER
        self_delta_P = (self.increaseP() - self.P_succ)

        ### POSITIVE AND NEGATIVE VARIATION OF LINK STRENTH
        node_delta_W = (node.increaseW(W_link) - W_link)
        self_decrease_W = (self.decreaseW(W_link) - W_link)
        self_increaseW = self.increaseW(W_link) - W_link
            
        
        ### -> compute payoffs for receiver
        rec_utility_accept = node.B*node_delta_P*W_sum_rec + node.B*(node.increaseP())*(node_delta_W)-node.alpha*energy_cost
        rec_utility_decline = node.P_succ*node.B*(self_decrease_W)
                    
        
        self_delta_P = (self.increaseP() - self.P_succ)
        self_delta_W = (self.increaseW(W_link) - W_link)
                    
        ### DOES THE RECEIVER ACCEPTS (WHEN CHARGED)
        
        if rec_utility_accept > rec_utility_decline:
                
            # if the receiver accepts them 
            receiver_charged_utiliy = self.B*self_delta_P*W_sum + self.B*self.increaseP()*(self_increaseW)-self.alpha*energy_cost
            
        else:
            receiver_charged_utiliy = self.P_succ*self.B*(self_decrease_W)
        #################################################################################     
        
        
        
        
        ######## A NOT CHARGED ##########################################################
        if self.B*self.P_succ*W_sum > node.B*node.P_succ*W_sum_rec:
        #if self.B > node.B:
            
            
            self_decrease_P = self.decreaseP() - self.P_succ 
            self_increaseW = self.increaseW(W_link) - W_link
            receiver_not_charged_utiliy = self.B*self_decrease_P*W_sum + self.B*(self.decreaseP())*(self_increaseW)-self.alpha*energy_cost
                   
        else:
            self_decrease_W = (self.decreaseW(W_link) - W_link)
            receiver_not_charged_utiliy = self.P_succ*self.B*(self_decrease_W)
        #################################################################################            
               
            
            
        ###### EXPECTED PAYOFF ###########################################################
        communication_payoff = p*(receiver_charged_utiliy) + (1-p)*receiver_not_charged_utiliy
        no_communication_payoff = 0
        
        #print('sender:')
        #print(receiver_charged_utiliy)
        #print(receiver_not_charged_utiliy)
        
        
        ##### DECISION OF SENDER #######################################################                    
        debug = True
        if self.debug:
            if communication_payoff > no_communication_payoff and energy_cost <= self.energy:
                print('- ' + str(self.id) + " wants to communicate with " + str(node.id) + ': ' + str(communication_payoff))
            else:
                print('- ' +str(self.id) + " don't want to communicate with " + str(node.id) +': ' + str(communication_payoff) + 'energy: need ' + str(energy_cost) + 'available: ' + str(self.energy))
                    
                        
        if communication_payoff > no_communication_payoff and energy_cost <= self.energy:
            return 'accept', communication_payoff
        return 'decline', no_communication_payoff
        ##################################################################################
    
    def best_receivers(self,node_list):
        # return sorted list of best receiver for the bundle, base on their values
        if self.debug:
            print('### Sensing the channel ###')
        
        best_receivers = {}
        
        for node in node_list:
            if node.id != self.id:
        
                bundle = self.create_bundle(node)
                bundle_size = len(bundle)
                if bundle_size > 0:
                    best_receivers[node] = self.compute_sender_payoff(node, bundle)
            
        if len(best_receivers)>0:
            sorted_best_receiver = dict(sorted(best_receivers.items(), key=lambda item: item[1], reverse=True))
        else:
            sorted_best_receiver = {}
        
        if self.debug:
            print("### Channel sensed ###")
                  
        return sorted_best_receiver
                    
        
    
    
def number_of_nodes(density):
    return 300*150*density

