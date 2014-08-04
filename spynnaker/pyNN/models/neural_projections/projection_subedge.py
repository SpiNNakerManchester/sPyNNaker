from pacman.model.subgraph.subedge import Subedge


class ProjectionSubedge(Subedge):
    
    def __init__(self, presubvertex, postsubvertex, associated_edge):
        Subedge.__init__(self, presubvertex, postsubvertex)
        self._synapse_sublist = None
        self._associated_edge = associated_edge

    
    def get_synapse_sublist(self):
        """
        Gets the synapse list for this subedge
        """
        if self._synapse_sublist is None:
            self._synapse_sublist = \
                self._associated_edge.get_synaptic_data().create_atom_sublist(
                    self._pre_subvertex.lo_atom, self._pre_subvertex.hi_atom,
                    self._post_subvertex.lo_atom, self._post_subvertex.hi_atom)
        return self._synapse_sublist
    
    def get_synaptic_data(self, spinnaker, min_delay):
        """
        Get synaptic data for all connections in this Projection.
        """
        return self._post_subvertex.vertex.get_synaptic_data(
            spinnaker, self._pre_subvertex, self._pre_subvertex.n_atoms,
            self._post_subvertex, self._associated_edge.synapse_row_io)
    
    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self._synapse_sublist = None

    def is_connected(self):
        """determines if theres an actual connection in this subedge in temrs of
        synaptic data

        """
        if self._synapse_sublist is None:
            self.get_synapse_sublist()

        return self._synapse_sublist.is_connected(
            self._pre_subvertex.lo_atom, self._pre_subvertex.hi_atom,
            self._post_subvertex.lo_atom, self.post_subvertex.hi_atom)