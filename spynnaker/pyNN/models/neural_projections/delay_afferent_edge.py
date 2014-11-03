from pacman.model.partitionable_graph.partitionable_edge \
    import PartitionableEdge


class DelayAfferentPartitionableEdge(PartitionableEdge):
    
    def __init__(self, prevertex, delayvertex, label=None):
        PartitionableEdge.__init__(self, prevertex, delayvertex, label=label)