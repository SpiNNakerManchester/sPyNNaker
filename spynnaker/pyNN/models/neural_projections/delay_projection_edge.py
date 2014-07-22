from spynnaker.pyNN.models.neural_projections.projection_edge import \
    ProjectionEdge
from spynnaker.pyNN.models.neural_projections.delay_projection_subedge import \
    DelayProjectionSubedge

import logging
logger = logging.getLogger(__name__)


class DelayProjectionEdge(ProjectionEdge):

    _DELAY_PAGE_SIZE = 256
    
    def __init__(self, prevertex, postvertex, machine_time_step, 
                 num_delay_stages, max_delay_per_neuron,
                 connector=None, synapse_list=None, synapse_dynamics=None,
                 label=None):
        ProjectionEdge.__init__(
            self, prevertex, postvertex, machine_time_step, connector=connector,
            synapse_list=synapse_list, synapse_dynamics=synapse_dynamics,
            label=label)
        self.num_delay_stages = num_delay_stages
        self.max_delay_per_neuron = max_delay_per_neuron
        
    def get_max_n_words(self, lo_atom=None, hi_atom=None):
        """
        Gets the maximum number of words for a subvertex at the end of the
        connection
        :param lo_atom: The start of the range of atoms in 
                                   the subvertex (default is first atom)
        :param hi_atom: The end of the range of atoms in 
                                   the subvertex (default is last atom)
        """
        return max([self._synapse_row_io.get_n_words(synapse_row, lo_atom,
                                                     hi_atom)
                    for synapse_row in self._synapse_list.get_rows()])
        
    def get_n_rows(self):
        """
        Gets the number of synaptic rows coming in to a subvertex at the end of
        the connection
        """
        n_atoms = self._pre_vertex.get_maximum_atoms_per_core()
        if self._pre_vertex.custom_max_atoms_per_core is not None:
            n_atoms = self._pre_vertex.custom_max_atoms_per_core
        if self._pre_vertex.atoms < n_atoms:
            n_atoms = self._pre_vertex.atoms
        if n_atoms > 100:
            n_atoms = 100
        return ((self._synapse_list.get_n_rows() / n_atoms) *
                self._DELAY_PAGE_SIZE * self.num_delay_stages)
    
    def create_subedge(self, presubvertex, postsubvertex, label=None):
        """
        Creates a subedge from this edge
        """
        return DelayProjectionSubedge(self, presubvertex, postsubvertex, self)
