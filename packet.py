import copy

class Packet:
    def __init__(self, id, source, destination):
        self.id = id
        self.source = source #node.id -> only the id of the node
        self.destination = destination #node.id  -> only id of the node
        self.hops = [source] #list of all hops for the packed
        self.received = False 
        self.copies = 1
        self.max_copies = 4
        
        
        
    def add_hop(self, node):
        self.hops.append(node)
        
    def remove_hop(self, node):
        self.hops.remove(node)
    
    
    def received(self):
        self.received = True
        
    def create_copy(self):
        pck_copy = copy.deepcopy(self)
        return pck_copy