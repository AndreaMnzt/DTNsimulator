class Packet:
    def __init__(self, id, source, destination):
        self.id = id
        self.source = source #node.id
        self.destination = destination #node.id
        self.hops = [source]
        self.received = False
        
    def add_hop(self, node):
        self.hops.append(node)
        
    def received(self):
        self.received = True