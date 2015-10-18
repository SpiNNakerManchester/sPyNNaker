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

        # A list of all synapse information for all the projections that are
        # represented by this edge
        self._synapse_information = [synapse_information]

        # The edge from the delay extension of the pre_vertex to the
        # post_vertex - this might be None if no long delays are present
        self._delay_edge = None

        self._stored_synaptic_data_from_machine = None

    def add_synapse_information(self, synapse_information):
        self._synapse_information.append(synapse_information)

    @property
    def synapse_information(self):
        return self._synapse_information

    @property
    def delay_edge(self):
        return self._delay_edge

    @delay_edge.setter
    def delay_edge(self, delay_edge):
        self._delay_edge = delay_edge

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
