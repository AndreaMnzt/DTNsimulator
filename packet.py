import copy

class Packet:
    def __init__(self, id, source, destination):
        self.id = id
        self.source = source #node.id
        self.destination = destination #node.id
        self.hops = [source]
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