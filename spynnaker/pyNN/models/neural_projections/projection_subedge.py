from pacman103.lib.graph import Subedge

class ProjectionSubedge(Subedge):
    
    def __init__(self, edge, presubvertex, postsubvertex):
        super(ProjectionSubedge, self).__init__(edge, presubvertex, 
                postsubvertex)
        
        self.synapse_sublist = None
    
    def get_synapse_sublist(self):
        """
        Gets the synapse list for this subedge
        """
        if self.synapse_sublist is None:
            
            self.synapse_sublist = self.edge.synapse_list.create_atom_sublist(
                    self.presubvertex.lo_atom, self.presubvertex.hi_atom,
                    self.postsubvertex.lo_atom, self.postsubvertex.hi_atom)
        return self.synapse_sublist
    
    def get_synaptic_data(self, controller, min_delay):
        '''
        Get synaptic data for all connections in this Projection.
        '''
        return self.postsubvertex.vertex.get_synaptic_data(
                controller, self.presubvertex, self.presubvertex.n_atoms,
                self.postsubvertex, self.edge.synapse_row_io)
    
    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self.synapse_sublist = None

