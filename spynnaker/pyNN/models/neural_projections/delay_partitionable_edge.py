from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge import \
    ProjectionPartitionableEdge
from spynnaker.pyNN.models.neural_projections.delay_partitioned_projection import \
    DelayPartitionedProjection

import logging
logger = logging.getLogger(__name__)


class DelayPartitionableEdge(ProjectionPartitionableEdge):

    _DELAY_PAGE_SIZE = 256
    
    def __init__(self, prevertex, postvertex, machine_time_step, 
                 num_delay_stages, max_delay_per_neuron,
                 connector=None, synapse_list=None, synapse_dynamics=None,
                 label=None):
        ProjectionPartitionableEdge.__init__(
            self, prevertex, postvertex, machine_time_step, connector=connector,
            synapse_list=synapse_list, synapse_dynamics=synapse_dynamics,
            label=label)
        self._num_delay_stages = num_delay_stages
        self._max_delay_per_neuron = max_delay_per_neuron

    @property
    def num_delay_stages(self):
        return self._num_delay_stages

    @property
    def max_delay_per_neuron(self):
        return self._max_delay_per_neuron
        
    def get_max_n_words(self, vertex_slice=None):
        """
        Gets the maximum number of words for a subvertex at the end of the
        connection
        :param lo_atom: The start of the range of atoms in 
                                   the subvertex (default is first atom)
        :param hi_atom: The end of the range of atoms in 
                                   the subvertex (default is last atom)
        """
        return max([self._synapse_row_io.get_n_words(synapse_row, vertex_slice)
                    for synapse_row in self._synapse_list.get_rows()])
        
    def get_n_rows(self):
        """
        Gets the number of synaptic rows coming in to a subvertex at the end of
        the connection
        """
        n_atoms = self._pre_vertex.get_max_atoms_per_core()
        return ((self._synapse_list.get_n_rows() / n_atoms) *
                self._DELAY_PAGE_SIZE * self._num_delay_stages)
    
    def create_subedge(self, presubvertex, postsubvertex, label=None):
        """
        Creates a subedge from this edge
        """
        return DelayPartitionedProjection(presubvertex, postsubvertex)
