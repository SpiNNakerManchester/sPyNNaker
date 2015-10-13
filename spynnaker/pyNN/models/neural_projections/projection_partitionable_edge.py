from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.utilities.progress_bar import ProgressBar

from spynnaker.pyNN.utilities import conf

from spinn_front_end_common.utilities.timer import Timer

import logging
import copy
logger = logging.getLogger(__name__)


class ProjectionPartitionableEdge(MultiCastPartitionableEdge):
    """ An edge which terminates on an AbstractPopulationVertex
    """

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        MultiCastPartitionableEdge.__init__(
            self, pre_vertex, post_vertex, label=label)
        self._synapse_information = [synapse_information]
        self._stored_synaptic_data_from_machine = None

    def add_synapse_information(self, synapse_information):
        self._synapse_information.append(synapse_information)

    @property
    def synapse_information(self):
        return self._synapse_information

    def get_n_synapse_rows(self, pre_vertex_slice=None):
        if pre_vertex_slice is not None:
            return pre_vertex_slice.n_atoms
        return self.pre_vertex.n_atoms

    def get_max_n_words(self, pre_vertex_slice, post_vertex_slice):
        """ Get the maximum number of words that any row can contain
        """
        total_length = 0
        for synapse_info in self._synapse_information:
            synapse_dynamics = synapse_info.synapse_dynamics
            synapse_structure = synapse_dynamics.get_synapse_structure()
            connector = synapse_info.connector
            total_length += synapse_structure.get_n_words_in_row(
                synapse_dynamics.get_n_connections_from_pre_vertex_maximum(
                    connector, pre_vertex_slice, post_vertex_slice))
        return total_length

    def get_synapses_size_in_bytes(self, pre_vertex_slice, post_vertex_slice):
        """ Get the total size of the synapses for this edge in bytes
        """
        total_size = 0
        for synapse_info in self._synapse_information:
            synapse_dynamics = synapse_info.synapse_dynamics
            connector = synapse_info.connector
            total_size += synapse_dynamics.get_synapses_sdram_usage_in_bytes(
                connector, pre_vertex_slice, post_vertex_slice)
        return total_size

    def get_synaptic_list_from_machine(self, graph_mapper, partitioned_graph,
                                       placements, transceiver, routing_infos):
        """
        Get synaptic data for all connections in this Projection from the
        machine.
        """
        if self._stored_synaptic_data_from_machine is None:
            timer = None
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer = Timer()
                timer.start_timing()

            subedges = \
                graph_mapper.get_partitioned_edges_from_partitionable_edge(
                    self)
            if subedges is None:
                subedges = list()

            synaptic_list = copy.copy(self._synapse_list)
            synaptic_list_rows = synaptic_list.get_rows()
            progress_bar = ProgressBar(
                len(subedges),
                "Reading back synaptic matrix for edge between"
                " {} and {}".format(self._pre_vertex.label,
                                    self._post_vertex.label))
            for subedge in subedges:
                n_rows = subedge.get_n_rows(graph_mapper)
                pre_vertex_slice = \
                    graph_mapper.get_subvertex_slice(subedge.pre_subvertex)
                post_vertex_slice = \
                    graph_mapper.get_subvertex_slice(subedge.post_subvertex)

                sub_edge_post_vertex = \
                    graph_mapper.get_vertex_from_subvertex(
                        subedge.post_subvertex)
                rows = sub_edge_post_vertex.get_synaptic_list_from_machine(
                    placements, transceiver, subedge.pre_subvertex, n_rows,
                    subedge.post_subvertex,
                    self._synapse_row_io, partitioned_graph,
                    routing_infos, subedge.weight_scales).get_rows()

                for i in range(len(rows)):
                    synaptic_list_rows[
                        i + pre_vertex_slice.lo_atom].set_slice_values(
                            rows[i], vertex_slice=post_vertex_slice)
                progress_bar.update()
            progress_bar.end()
            self._stored_synaptic_data_from_machine = synaptic_list
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                logger.info("Time to read matrix: {}".format(
                    timer.take_sample()))

        return self._stored_synaptic_data_from_machine

    def is_multi_cast_partitionable_edge(self):
        return True
