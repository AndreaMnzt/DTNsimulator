import random
import math
import numpy as np
import networkx as nx

class Node:
    
    def __init__(self, id, dev_class):
        
        self.space = [300, 150]
        
        #spacial variables
        self.id = id
        self.past_positions = np.zeros((0,2))
        self.angle = None
        self.position = Node.random_position()
        self.dev_class = dev_class
        self.speed = Node.get_speed(self.dev_class)
        self.energy = 100
        self.known_nodes_info = {}
        #telecomunication values
        self.radius = 50
        self.B = 0
        self.P_succ = 1
        self.ego_graph = None
        #self.egonetwork.add_node(self.id) 
        
    #method to move a node
    def move(self):
        
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
        
    def get_node_connection(self, node):
        #for nodes with distance < radius 
        #get Beetweeness node, success probability
        #for node in all_nodes:
        #    if node_is_near(self, all_nodes[node]):
        self.known_nodes_info[node.id] = {'near': True, 'B': node.B, 'P_succ': node.P_succ}
    
    def get_node_B(self, node):
        self.known_nodes_info[node.id]['B'] = node.B
    
    
    def node_not_near(self, node):
        if node.id in self.known_nodes_info:
            self.known_nodes_info[node.id]['near'] = False
    
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
        
        
def number_of_nodes(density):
    return 300*150*density