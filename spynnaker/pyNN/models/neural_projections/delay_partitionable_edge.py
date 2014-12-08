from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from spynnaker.pyNN.models.neural_projections.delay_partitioned_edge \
    import DelayPartitionedEdge

import logging
logger = logging.getLogger(__name__)


class DelayPartitionableEdge(ProjectionPartitionableEdge):

    def __init__(self, presynaptic_population, postsynaptic_population,
                 machine_time_step, num_delay_stages, max_delay_per_neuron,
                 connector=None, synapse_list=None, synapse_dynamics=None,
                 label=None):
        ProjectionPartitionableEdge.__init__(self,
                                             presynaptic_population,
                                             postsynaptic_population,
                                             machine_time_step,
                                             connector=connector,
                                             synapse_list=synapse_list,
                                             synapse_dynamics=synapse_dynamics,
                                             label=label)
        self._pre_vertex = presynaptic_population._internal_delay_vertex

    @property
    def num_delay_stages(self):
        return self._pre_vertex.max_stages

    @property
    def max_delay_per_neuron(self):
        return self._pre_vertex.max_delay_per_neuron

    def _get_delay_stage_max_n_words(self, vertex_slice, stage):
        min_delay = ((stage + 1) * self.max_delay_per_neuron) + 1
        max_delay = min_delay + self.max_delay_per_neuron
        conns = self.synapse_list.get_max_n_connections(
            vertex_slice=vertex_slice, lo_delay=min_delay, hi_delay=max_delay)
        return conns

    def get_max_n_words(self, vertex_slice=None):
        """
        Gets the maximum number of words for a subvertex at the end of the
        connection
        :param lo_atom: The start of the range of atoms in
                                   the subvertex (default is first atom)
        :param hi_atom: The end of the range of atoms in
                                   the subvertex (default is last atom)
        """
        return max([self._get_delay_stage_max_n_words(vertex_slice, stage)
                    for stage in range(self._pre_vertex.max_stages)])

    def get_n_rows(self):
        """
        Gets the number of synaptic rows coming in to a vertex at the end of
        the connection
        """
        return self._synapse_list.get_n_rows() * self._pre_vertex.max_stages

    def create_subedge(self, presubvertex, postsubvertex, label=None):
        """
        Creates a subedge from this edge
        """
        return DelayPartitionedEdge(presubvertex, postsubvertex)
