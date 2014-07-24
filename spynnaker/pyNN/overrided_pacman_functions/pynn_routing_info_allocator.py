from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm


class PyNNRoutingInfoAllocator(AbstractRoutingInfoAllocatorAlgorithm):
    
    def __init__(self, graph_subgraph_mapper):
        AbstractRoutingInfoAllocatorAlgorithm.__init__(self)
        self._graph_subgraph_mapper = graph_subgraph_mapper
        self._used_masks = dict()
        
    #inhirrted from AbstractRoutingInfoAllocatorAlgorithm
    def allocate_routing_info(self, sub_graph, placements):
        
        for subvert in sub_graph.subvertices:
            for subedge in sub_graph.outgoing_subedges_from_subvertex(subvert):
                subverts_associated_vertex = \
                    self._graph_subgraph_mapper.\
                    get_vertex_from_subvertex(subvert)
                
                key, mask = \
                    subverts_associated_vertex.generate_routing_info(subedge)
                key_mask_combo = self.get_key_mask_combo(key, mask)
                subedge.key_mask_combo = key_mask_combo
                subedge.key = key
                subedge.mask = mask
                #check for storage of masks
                self.check_masks(subedge.mask, key)

    def check_masks(self, new_mask, key):
        """
        updates the used mask store based on if its alresady been used
        """
        if new_mask not in self._used_masks:
            self._used_masks[new_mask] = list()
        #add to list (newly created or otherwise)
        self._used_masks[new_mask].append(key)

    @staticmethod
    def get_key_mask_combo(key, mask):
        """
        generates a key-mask combo based off the key and mask
        """
        combo = key & mask
        return combo

