import logging

from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge import \
    ProjectionPartitionedEdge
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    fixed_synapse_row_io import FixedSynapseRowIO
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.utilities import constants

logger = logging.getLogger(__name__)


class ProjectionPartitionableEdge(PartitionableEdge):
    
    def __init__(self, prevertex, postvertex, machine_time_step,
                 connector=None, synapse_list=None, synapse_dynamics=None,
                 label=None):
        PartitionableEdge.__init__(self, prevertex, postvertex, label=label)

        self._connector = connector
        self._synapse_dynamics = synapse_dynamics
        self._synapse_list = synapse_list
        self._synapse_row_io = FixedSynapseRowIO()
        
        # If the synapse_list was not specified, create it using the connector
        if connector is not None and synapse_list is None:
            self._synapse_list = \
                connector.generate_synapse_list(prevertex, postvertex,
                                                1000.0 / machine_time_step)
        
        # If there are synapse dynamics for this connector, create a plastic
        # synapse list
        if synapse_dynamics is not None:
            self._synapse_row_io = synapse_dynamics.get_synapse_row_io()
    
    def create_subedge(self, presubvertex, postsubvertex, label=None):
        """
        Creates a subedge from this edge
        """
        return ProjectionPartitionedEdge(presubvertex, postsubvertex)

    def get_max_n_words(self, vertex_slice=None):
        """
        Gets the maximum number of words for a subvertex at the end of the
        connection
        :param vertex_slice: the vertex slice for this vertex which contains \
        the lo and hi atoms for this slice
        """
        if vertex_slice is None:
            return max([self._synapse_row_io.get_n_words(
                synapse_row)
                for synapse_row in self._synapse_list.get_rows()])
        else:
            return max([self._synapse_row_io.get_n_words(
                synapse_row, vertex_slice)
                for synapse_row in self._synapse_list.get_rows()])
        
    def get_n_rows(self):
        """
        Gets the number of synaptic rows coming in to a subvertex at the end of
        the connection
        """
        return self._synapse_list.get_n_rows()
    
    def get_synapse_row_io(self):
        """
        Gets the row reader and writer
        """
        return self._synapse_row_io

    def get_synaptic_list_from_machine(self, graph_mapper, placements,
                                       transceiver):
        """
        Get synaptic data for all connections in this Projection from the
        machine.
        """

        logger.debug("Reading synapse data for edge between {} and {}"
                     .format(self._pre_vertex.label, self._post_vertex.label))
        min_delay = config.get("Model", "min_delay")
        sorted_subedges = \
            sorted(graph_mapper.get_partitioned_edges_from_partitionable_edge(self),
                   key=lambda sub_edge:
                   (graph_mapper.get_subvertex_slice(
                       sub_edge.pre_subvertex).lo_atom,
                    graph_mapper.get_subvertex_slice(
                        sub_edge.post_subvertex).lo_atom))

        synaptic_list = list()
        last_pre_lo_atom = None
        progress_bar = ProgressBar(len(sorted_subedges),
                                   "progress on reading back synaptic matrix")
        for subedge in sorted_subedges:
            vertex_slice = \
                graph_mapper.get_subvertex_slice(subedge.pre_subvertex)
            pre_n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1

            sub_edge_post_vertex = \
                graph_mapper.get_vertex_from_subvertex(subedge.post_subvertex)
            rows = sub_edge_post_vertex.get_synaptic_list_from_machine(
                placements, transceiver, subedge.pre_subvertex, pre_n_atoms,
                subedge.post_subvertex,
                constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE.value,
                constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value,
                self._synapse_row_io, subedge.weight_scale)\
                .get_rows()

            pre_lo_atom = vertex_slice.lo_atom
            if ((last_pre_lo_atom is None) or
                    (last_pre_lo_atom != pre_lo_atom)):
                synaptic_list.extend(rows)
                last_pre_lo_atom = pre_lo_atom
            else:
                for i in range(len(rows)):
                    row = rows[i]
                    post_lo_atom = graph_mapper.get_subvertex_slice(
                        subedge.post_subvertex).lo_atom
                    synaptic_list[i + last_pre_lo_atom]\
                        .append(row, lo_atom=post_lo_atom)
            progress_bar.update()
        progress_bar.end()
        return SynapticList(synaptic_list)

    @property
    def synapse_dynamics(self):
        return self._synapse_dynamics

    @property
    def synapse_list(self):
        return self._synapse_list