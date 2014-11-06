from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge import\
    AbstractFilterableEdge

import logging
logger = logging.getLogger(__name__)


class DelayPartitionedProjection(ProjectionPartitionedEdge):
    
    def __init__(self, presubvertex, postsubvertex):
        ProjectionPartitionedEdge.__init__(self, presubvertex, postsubvertex)
        AbstractFilterableEdge.__init__(self)
        self._synapse_delay_rows = None
    
    def get_synapse_sublist(self, graph_mapper):
        """
        Gets the synapse list for this subedge
        """
        if self._synapse_sublist is None:
            self._calculate_synapse_sublist(graph_mapper)
        return self._synapse_sublist

    def _calculate_synapse_sublist(self, graph_mapper):
        pre_vertex_slice = graph_mapper.get_subvertex_slice(self._pre_subvertex)
        post_vertex_slice = \
            graph_mapper.get_subvertex_slice(self._post_subvertex)

        synapse_sublist = \
            graph_mapper.get_partitionable_edge_from_partitioned_edge(self).\
            synapse_list.create_atom_sublist(pre_vertex_slice,
                                             post_vertex_slice)

        if synapse_sublist.get_n_rows() > 256:
            raise exceptions.SynapticMaxIncomingAtomsSupportException(
                "Delay sub-vertices can only support up to 256 incoming"
                " neurons!")

        full_delay_list = list()
        associated_edge = \
            graph_mapper.get_partitionable_edge_from_partitioned_edge(self)
        for i in range(0, associated_edge.num_delay_stages):
            min_delay = (i * associated_edge.max_delay_per_neuron)
            max_delay = \
                min_delay + associated_edge.max_delay_per_neuron
            delay_list = \
                synapse_sublist.get_delay_sublist(min_delay, max_delay)

#                 if logger.isEnabledFor("debug"):
#                     logger.debug("    Rows for delays {} - {}:".format(
#                             min_delay, max_delay))
#                     for i in range(len(delay_list)):
#                         logger.debug("{}: {}".format(i, delay_list[i]))

            full_delay_list.extend(delay_list)

            # Add extra rows for the "missing" items, up to 256
            if (i + 1) < associated_edge.num_delay_stages:
                for _ in range(0, 256 - len(delay_list)):
                    full_delay_list.append(SynapseRowInfo([], [], [], []))
        self._synapse_sublist = SynapticList(full_delay_list)
        self._synapse_delay_rows = len(full_delay_list)
    
    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self._synapse_sublist = None