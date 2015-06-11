import logging

from spynnaker.pyNN.projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neuron.synaptic_list import SynapticList
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.common.abstract_filterable_edge\
    import AbstractFilterableEdge

logger = logging.getLogger(__name__)


class DelayPartitionedEdge(ProjectionPartitionedEdge):

    def __init__(self, edge, presubvertex, presubvertex_slice, postsubvertex,
                 postsubvertex_slice, constraints):
        ProjectionPartitionedEdge.__init__(
            self, edge, presubvertex, presubvertex_slice, postsubvertex,
            postsubvertex_slice, constraints)
        AbstractFilterableEdge.__init__(self)
        self._synapse_delay_rows = None

    def get_synapse_sublist(self):
        """
        Gets the synapse list for this subedge
        """
        if self._synapse_sublist is None:
            self._calculate_synapse_sublist()
        return self._synapse_sublist

    def get_n_rows(self, graph_mapper):
        pre_vertex_slice = graph_mapper.get_subvertex_slice(
            self._pre_subvertex)
        delay_edge = graph_mapper.get_partitionable_edge_from_partitioned_edge(
            self)
        return pre_vertex_slice.n_atoms * delay_edge.num_delay_stages

    def _calculate_synapse_sublist(self):
        synapse_sublist = self._edge.synapse_list.create_atom_sublist(
            self._presubvertex_slice, self._postsubvertex_slice)

        if synapse_sublist.get_n_rows() > 256:
            raise exceptions.SynapticMaxIncomingAtomsSupportException(
                "Delay sub-vertices can only support up to 256 incoming"
                " neurons!")

        full_delay_list = list()
        for stage in range(0, self._edge.num_delay_stages):
            min_delay = ((stage + 1) * self._edge.max_delay_per_neuron) + 1
            max_delay = ((stage + 2) * self._edge.max_delay_per_neuron)
            delay_list = synapse_sublist.get_delay_sublist(
                min_delay, max_delay)
            for row in delay_list:
                row.delays -= (min_delay - 1)
            full_delay_list.extend(delay_list)

        self._synapse_sublist = SynapticList(full_delay_list)
        self._synapse_delay_rows = len(full_delay_list)

    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self._synapse_sublist = None
